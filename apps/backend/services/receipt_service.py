import io
import json
import math
import os
import re
import smtplib
import pdfplumber
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.analytics import Product
from email.message import EmailMessage
import smtplib 

# Función auxiliar para limpiar y convertir números con formato colombiano a float
def limpiar_numero_colombiano(val) -> float:
    v = str(val).strip().lower()
    if not v or v in ['nan', 'none', 'null', '']: 
        return 0.0
    
    # 1. Elimina TODO lo que no sea número, coma, punto o signo negativo
    v = re.sub(r'[^\d,.-]', '', v)
    if not v or v == '-': 
        return 0.0
    
    # 2. Lógica de formato (Puntos de miles y comas decimales)
    if ',' in v and '.' in v:
        if v.rfind('.') < v.rfind(','):
            v = v.replace('.', '').replace(',', '.')
        else:
            v = v.replace(',', '')
    elif ',' in v:
        v = v.replace(',', '.')
    elif '.' in v:
        # Si tiene punto y exactamente 3 dígitos al final, asumimos que son miles (ej. 6.494)
        if len(v.split('.')[-1]) == 3:
            v = v.replace('.', '')
            
    try:
        res = float(v)
        # 3. Blindaje absoluto contra NaN
        return 0.0 if math.isnan(res) else res
    except ValueError:
        return 0.0


# Función para extraer datos de cabecera de la factura desde el PDF
def extraer_cabecera_pdf(pdf_bytes: bytes) -> dict:
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            if len(pdf.pages) > 0:
                text = pdf.pages[0].extract_text()
    except Exception as e:
        print(f"Error extrayendo texto para cabecera: {e}")

    # Valores por defecto en caso de que la factura esté en formato imagen o muy corrupta
    datos = {
        "numero": "PENDIENTE",
        "fecha": "",
        "fechaven": "",
        "nit_emisor": "",
        "nit_cliente": ""
    }

    if not text:
        return datos

    # 1. Buscar Fechas (Soporta DD.MM.YYYY, DD-MM-YYYY o DD/MM/YYYY)
    fechas = re.findall(r'(\d{2}[./-]\d{2}[./-]\d{4})', text)
    if len(fechas) >= 1:
        datos["fecha"] = fechas[0].replace('.', '-').replace('/', '-')
    if len(fechas) >= 2:
        datos["fechaven"] = fechas[1].replace('.', '-').replace('/', '-')

    # 2. Buscar NIT del emisor (Ej: NIT. 890.301.163-3)
    nit_emisor_match = re.search(r'NIT\.?\s*([0-9]{3}\.?[0-9]{3}\.?[0-9]{3}-[0-9])', text, re.IGNORECASE)
    if nit_emisor_match:
        # Limpiamos puntos pero dejamos el guion para el DV
        datos["nit_emisor"] = nit_emisor_match.group(1).replace('.', '')

    # 3. Buscar NIT del cliente (Ej: ID:901370244 o C.C. 123456)
    nit_cliente_match = re.search(r'(?:ID:|C\.C\.|NIT\.?)[^\d]*([0-9]{8,11})', text, re.IGNORECASE)
    if nit_cliente_match:
        datos["nit_cliente"] = nit_cliente_match.group(1)

    # 4. Buscar Número de Factura (Buscamos números largos aislados que no sean teléfonos o NITs)
    # Colombina usa 10 dígitos (ej. 4305300257)
    numeros_largos = re.findall(r'\b\d{6,15}\b', text)
    for num in numeros_largos:
        # Validamos que no sea un teléfono común ni el NIT del cliente
        if not num.startswith('3') and num not in datos.values():
            datos["numero"] = num
            break

    return datos

# --------------Función principal que procesa el DataFrame y hace la homologación-----------------
def process_receipt_logic(df: pd.DataFrame, db: Session, datos_cabecera: dict):
    
    # 1. Encontrar cabecera
    cabecera_idx = -1
    for i in range(min(40, len(df))):
        row_str = " ".join([str(val).lower() for val in df.iloc[i]]).replace('\n', ' ')
        if ("codigo" in row_str or "referencia" in row_str) and ("descrip" in row_str):
            cabecera_idx = i
            break
            
    if cabecera_idx == -1:
        raise ValueError("No pude identificar la tabla en el PDF.")

    df.columns = [str(c).strip().lower().replace('\n', ' ') for c in df.iloc[cabecera_idx]]
    df = df.iloc[cabecera_idx + 1:].reset_index(drop=True)

    # Limpieza básica: eliminar espacios extra y saltos de línea en todo el DataFrame
    df = df.map(lambda x: str(x).strip().replace('\n', ' ') if pd.notnull(x) else x)

    # Eliminar los duplicados exactos que a veces aparecen en las tablas extraídas de PDFs
    df = df.drop_duplicates().reset_index(drop=True)
    
    # 2. Mapeo
    mapeo = {
        "ref": ["codigo", "referencia", "item", "#codigo"],
        "desc": ["descripcion", "descripción", "producto", "detalle"],
        "cant": ["cantidad", "unidad", "despachada"],
        "costo": ["costo", "precio", "valor unitario", "precio unid"]
    }

    cols_reales = {}
    for clave, sinonimos in mapeo.items():
        for col in df.columns:
            if any(sin in col for sin in sinonimos):
                cols_reales[clave] = col
                break
        if clave not in cols_reales:
            raise ValueError(f"Falta columna obligatoria: {clave}")

    # 3. Procesamiento y Consolidación 
    unique_items_map = {}
    
    for _, row in df.iterrows():
        raw_ref = str(row[cols_reales['ref']]).strip()
        ref = raw_ref.split()[-1] if raw_ref else ""
        
        desc = str(row[cols_reales['desc']]).strip()
        
        if not ref or not any(char.isdigit() for char in ref): 
            continue

        raw_row_data = str(row[cols_reales['costo']])
        partes = raw_row_data.split()
        
        if len(partes) < 2:
            continue
        
        cantidad = limpiar_numero_colombiano(partes[0])
        costo = limpiar_numero_colombiano(partes[1])
        
        if cantidad <= 0: 
            continue 

        if ref in unique_items_map:
            unique_items_map[ref]['cantidad'] = cantidad
        else:
            db_product = db.query(Product).filter(
                (func.lower(Product.name) == func.lower(desc)) | (Product.sku == ref)
            ).first()

            unique_items_map[ref] = {
                "sku": ref,
                "nombre": db_product.name if db_product else desc,
                "cantidad": cantidad,
                "costo": costo,
                "homologado": bool(db_product)
            }

    items = list(unique_items_map.values())

    # 4. Construcción del JSON Oficial de Exportación
    nit_completo = datos_cabecera.get("nit_emisor", "")
    items_syscafe = []
    for item in items:
        # Cálculos obligatorios para SysCafé basados en tu data limpia
        vrtotal = item["cantidad"] * item["costo"]
        piva = 19.0
        vriva = vrtotal * (piva / 100)

        items_syscafe.append({
            "referencia": item["sku"],
            "nombre": item["nombre"], # CAMBIO 3: Agregado el nombre
            "servicio": "",
            "cant": item["cantidad"],
            "precio": item["costo"],
            "vrunit": item["costo"],
            "vrtotal": vrtotal,
            "piva": piva,
            "vriva": vriva,
            "vrico": 0.0
        })

    syscafe_json = [
        {
            "tipo": "FV2",
            "numero": datos_cabecera.get("numero", "PENDIENTE"),
            "noext": "1",
            "fecha": datos_cabecera.get("fecha", ""),
            "fechaven": datos_cabecera.get("fechaven", ""),
            "fpago": "001",
            "nit": nit_completo,
            "vendedor": "",
            "ccosto": "001",
            "succosto": "001001",
            "detalle": "COMPRA A PROVEEDOR",
            "obs": "Factura procesada automáticamente",
            "items": items_syscafe,
            "cliente": {
                "nit": datos_cabecera.get("nit_cliente", ""),
                "dv": "0",
                "claseid": "C",
                "nom1": "SUPERDULCES",
                "nom2": "SAS",
                "ape1": "",
                "ape2": ""
            }
        }
    ]

    return {
        "items": items,
        "resumen": {
            "total_items": len(items),
            "homologados_exitosos": sum(1 for i in items if i["homologado"]),
            "pendientes_revision": sum(1 for i in items if not i["homologado"])
        },
        "syscafe_json": syscafe_json
    }


# LÓGICA EN SEGUNDO PLANO: Envío del correo con plantilla HTML y adjunto
def send_html_email_task(invoice_id: int, file_name: str, nit: str, total_items: int, json_data: list):
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    target_email = os.getenv("TARGET_EMAIL")

    if not all([smtp_user, smtp_password, target_email]):
        print("❌ Error SMTP: Faltan variables de entorno (SMTP_USER, SMTP_PASSWORD o TARGET_EMAIL)")
        return

    # 1. Crear el contenedor del mensaje
    msg = EmailMessage()
    msg['Subject'] = f'📊 Reporte de Factura Procesada - ID #{invoice_id}'
    msg['From'] = smtp_user
    msg['To'] = target_email

    # 2. Versión en texto plano (Fallback si el gestor de correo no soporta HTML)
    text_fallback = f"""
    Hola,
    Se ha procesado con éxito la factura ID #{invoice_id}.
    - Archivo original: {file_name}
    - NIT Emisor: {nit}
    - Total de ítems estructurados: {total_items}
    
    El documento estructurado en formato JSON se encuentra adjunto a este correo.
    """
    msg.set_content(text_fallback)

    # 3. Diseño de la Plantilla HTML (Estilos inline para compatibilidad con Gmail/Outlook)
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; color: #333333; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #e1e5eb; }}
            .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: #ffffff; padding: 30px 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; letter-spacing: 0.5px; }}
            .header p {{ margin: 5px 0 0 0; opacity: 0.8; font-size: 14px; }}
            .content {{ padding: 30px 25px; }}
            .welcome {{ font-size: 16px; color: #4a5568; line-height: 1.6; margin-bottom: 25px; }}
            .card {{ background-color: #f8fafc; border-left: 4px solid #2a5298; padding: 20px; border-radius: 0 6px 6px 0; margin-bottom: 25px; }}
            .card-title {{ font-weight: bold; color: #1e3c72; margin-bottom: 12px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }}
            .info-grid {{ display: table; width: 100%; }}
            .info-row {{ display: table-row; }}
            .info-label {{ display: table-cell; padding: 6px 0; font-weight: 600; color: #4a5568; width: 40%; font-size: 14px; }}
            .info-value {{ display: table-cell; padding: 6px 0; color: #1a202c; font-size: 14px; }}
            .footer {{ background-color: #f1f5f9; text-align: center; padding: 15px; font-size: 12px; color: #718096; border-top: 1px solid #e2e8f0; }}
            .badge {{ background-color: #def7ec; color: #03543f; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Factura Procesada con Éxito</h1>
                <p>Automatización de Procesos - SuperDulces BI</p>
            </div>
            <div class="content">
                <p class="welcome">Hola Administradores de SuperDulces,</p>
                <p class="welcome">Les informamos que un nuevo documento PDF ha sido extraído, normalizado e integrado correctamente al flujo analítico del sistema. A continuación se presentan los detalles clave del procesamiento:</p>
                
                <div class="card">
                    <div class="card-title">Métricas de la Operación</div>
                    <div class="info-grid">
                        <div class="info-row">
                            <div class="info-label">ID de Registro:</div>
                            <div class="info-value"><strong>#{invoice_id}</strong></div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Archivo de Origen:</div>
                            <div class="info-value" style="word-break: break-all;">{file_name}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">NIT del Emisor:</div>
                            <div class="info-value">{nit if nit else 'No detectado'}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Ítems Extraídos:</div>
                            <div class="info-value">{total_items} unidades</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Estado:</div>
                            <div class="info-value"><span class="badge">Listo para SysCafé</span></div>
                        </div>
                    </div>
                </div>
                
                <p class="welcome" style="font-size: 14px; color: #718096;">He adjuntado a este mensaje el archivo completo <strong>factura_{invoice_id}.json</strong> estructurado bajo la especificación técnica requerida por el sistema contable.</p>
            </div>
            <div class="footer">
                Este es un mensaje automático generado por el Subsistema de Extracción de Datos de SuperDulces BI.
            </div>
        </div>
    </body>
    </html>
    """
    msg.add_alternative(html_template, subtype='html')

    # 4. Serializar el JSON que está guardado en la DB y adjuntarlo
    try:
        json_string = json.dumps(json_data, indent=4, ensure_ascii=False)
        msg.add_attachment(
            json_string.encode('utf-8'),
            maintype='application',
            subtype='json',
            filename=f'factura_{invoice_id}.json'
        )
    except Exception as je:
        print(f"❌ Error al adjuntar JSON: {je}")
        return

    # 5. Envío TLS/SSL seguro mediante Gmail
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)
            print(f"✅ [ID #{invoice_id}] Correo HTML enviado con éxito a {target_email}")
    except Exception as e:
        print(f"❌ Error técnico SMTP al enviar correo de factura #{invoice_id}: {e}")