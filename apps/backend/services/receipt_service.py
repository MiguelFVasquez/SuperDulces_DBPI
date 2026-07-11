import io
import json
import math
import os
import re
import smtplib
import unicodedata
import logging
import pdfplumber
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.analytics import Product
from models.invoice_extraction import FacturaExtraidaLLM
from email.message import EmailMessage


logger = logging.getLogger(__name__)  # <-- Inicializar logger

# Función auxiliar para limpiar y convertir números con formato colombiano a float
def limpiar_numero_colombiano(val) -> float:
    v = str(val).strip().lower()
    if not v or v in ['nan', 'none', 'null', '']:
        return 0.0
    v = re.sub(r'[^\d,.-]', '', v)
    if not v or v == '-':
        return 0.0
    if ',' in v and '.' in v:
        if v.rfind('.') < v.rfind(','):
            v = v.replace('.', '').replace(',', '.')
        else:
            v = v.replace(',', '')
    elif ',' in v:
        v = v.replace(',', '.')
    elif '.' in v:
        if len(v.split('.')[-1]) == 3:
            v = v.replace('.', '')
    try:
        res = float(v)
        return 0.0 if math.isnan(res) else res
    except ValueError:
        return 0.0


def normalizar_texto(texto: str) -> str:
    """Elimina tildes, saltos de línea y convierte a minúsculas."""
    if not isinstance(texto, str) and pd.isna(texto):
        return ""
    texto = str(texto).strip().replace('\n', ' ')
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8').lower()
    return texto


def extraer_cabecera_pdf(pdf_bytes: bytes) -> dict:
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            if len(pdf.pages) > 0:
                text = pdf.pages[0].extract_text()
    except Exception as e:
        print(f"Error extrayendo texto para cabecera: {e}")

    datos = {
        "numero": "PENDIENTE",
        "fecha": "",
        "fechaven": "",
        "nit_emisor": "",
        "nit_cliente": ""
    }
    if not text:
        return datos

    fechas = re.findall(r'(\d{2}[./-]\d{2}[./-]\d{4})', text)
    if len(fechas) >= 1:
        datos["fecha"] = fechas[0].replace('.', '-').replace('/', '-')
    if len(fechas) >= 2:
        datos["fechaven"] = fechas[1].replace('.', '-').replace('/', '-')

    nit_emisor_match = re.search(r'NIT\.?\s*([0-9]{3}\.?[0-9]{3}\.?[0-9]{3}-[0-9])', text, re.IGNORECASE)
    if nit_emisor_match:
        datos["nit_emisor"] = nit_emisor_match.group(1).replace('.', '')

    nit_cliente_match = re.search(r'(?:ID:|C\.C\.|NIT\.?)[^\d]*([0-9]{8,11})', text, re.IGNORECASE)
    if nit_cliente_match:
        datos["nit_cliente"] = nit_cliente_match.group(1)

    match_factura = re.search(
        r'(?:FACTURA[\w\s]*|NO\.|N°|FOLIO|NUMERO)\s*[:#]?\s*([A-Z0-9]{1,5}[-\s]?\d{3,12})',
        text,
        re.IGNORECASE,
    )
    if match_factura:
        datos["numero"] = match_factura.group(1).replace(" ", "").upper()
    else:
        # Intento 2: Heurística colombiana (números o códigos largos que no sean celulares ni NITs ya encontrados)
        codigos_largos = re.findall(
            r'\b([A-Z]{0,4}[-]?\d{5,15})\b', text, re.IGNORECASE
        )
        for cod in codigos_largos:
            cod_limpio = cod.replace("-", "").upper()
            # Descartar celulares (3xx), o si ya es el NIT del emisor o cliente
            if (
                not cod_limpio.startswith('3')
                and cod_limpio not in datos.values()
                and len(cod_limpio) >= 5
            ):
                datos["numero"] = cod.upper()
                break

    return datos


# --------------Homologación + construcción del JSON (compartida por reglas y LLM)-----------------
def construir_resultado_final(items_crudos: list[dict], db: Session, datos_cabecera: dict) -> dict:
    """
    items_crudos: lista de dicts con claves sku, nombre, cantidad, costo.
    Homologa contra la BD y construye el JSON de SysCafé.
    """
    unique_items_map = {}
    for it in items_crudos:
        ref = it["sku"]
        if ref in unique_items_map:
            unique_items_map[ref]["cantidad"] += it["cantidad"]
            continue

        db_product = db.query(Product).filter(
            (func.lower(Product.name) == func.lower(it["nombre"])) | (Product.sku == ref)
        ).first()

        unique_items_map[ref] = {
            "sku": ref,
            "nombre": db_product.name if db_product else it["nombre"],
            "cantidad": it["cantidad"],
            "costo": it["costo"],
            "homologado": bool(db_product),
        }

    items = list(unique_items_map.values())

    nit_completo = datos_cabecera.get("nit_emisor", "")
    items_syscafe = []
    for item in items:
        vrtotal = item["cantidad"] * item["costo"]
        piva = 19.0
        vriva = vrtotal * (piva / 100)
        items_syscafe.append({
            "plu": item["sku"],
            "detalle": item["nombre"],
            "servicio": "",
            "cant": item["cantidad"],
            "precio": item["costo"],
            "vrunit": item["costo"],
            "vrtotal": vrtotal,
            "piva": piva,
            "vriva": vriva,
            "vrico": 0.0,
        })

    syscafe_json = [{
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
            "ape2": "",
        },
    }]

    return {
        "items": items,
        "resumen": {
            "total_items": len(items),
            "homologados_exitosos": sum(1 for i in items if i["homologado"]),
            "pendientes_revision": sum(1 for i in items if not i["homologado"]),
        },
        "syscafe_json": syscafe_json,
    }


# --------------Camino 1: parser basado en reglas-----------------
def process_receipt_logic(df: pd.DataFrame, db: Session, datos_cabecera: dict):
    cabecera_idx = -1
    for i in range(min(40, len(df))):
        row_str = " ".join([normalizar_texto(val) for val in df.iloc[i]])
        tiene_id = any(p in row_str for p in ["codigo", "cod", "referencia", "ref", "item", "plu", "id", "sku"])
        tiene_desc = any(p in row_str for p in ["descrip", "producto", "detalle", "articulo", "nombre", "concepto"])
        tiene_cant = any(p in row_str for p in ["cant", "unidad", "und", "u/m", "despachada", "unidades", "qty"])
        tiene_precio = any(p in row_str for p in ["precio", "costo", "valor", "unitario", "vr.", "vlr", "val.", "unit"])
        if sum([tiene_id, tiene_desc, tiene_cant, tiene_precio]) >= 3:
            cabecera_idx = i
            break

    if cabecera_idx == -1:
        raise ValueError("No pude identificar la tabla en el PDF. Revisa si los encabezados tienen un formato no estándar.")

    df.columns = [normalizar_texto(c) for c in df.iloc[cabecera_idx]]
    df = df.iloc[cabecera_idx + 1:].reset_index(drop=True)
    df = df.map(lambda x: str(x).strip().replace('\n', ' ') if pd.notnull(x) else x)
    df = df.drop_duplicates().reset_index(drop=True)

    mapeo = {
        "ref": ["codigo", "referencia", "item", "#codigo", "cod.", "cod", "plu", "id", "sku"],
        "desc": ["descripcion", "producto", "detalle", "articulo", "nombre", "bien", "servicio", "desc."],
        "cant": ["cantidad", "cant", "cant.", "unidad", "und", "u/m", "despachada", "unidades", "qty"],
        "costo": ["costo", "precio", "valor unitario", "precio unid", "vr. producto", "vr unitario", "vlr. unit", "val. unitario", "unitario", "p. unitario", "vrunit", "precio/u", "vr. unit"],
    }
    cols_reales = {}
    for clave, sinonimos in mapeo.items():
        for col in df.columns:
            if any(sin in col for sin in sinonimos):
                cols_reales[clave] = col
                break
        if clave not in cols_reales:
            raise ValueError(f"Falta columna obligatoria en la factura para: {clave.upper()}. Columnas detectadas: {list(df.columns)}")

    items_crudos = []
    for _, row in df.iterrows():
        raw_ref = str(row[cols_reales['ref']]).strip()
        ref = raw_ref.split()[-1] if raw_ref else ""
        desc = str(row[cols_reales['desc']]).strip()
        if not ref or not any(char.isdigit() for char in ref):
            continue

        cantidad = limpiar_numero_colombiano(str(row[cols_reales['cant']]))
        costo = limpiar_numero_colombiano(str(row[cols_reales['costo']]))
        if cantidad <= 0:
            continue

        items_crudos.append({"sku": ref, "nombre": desc, "cantidad": cantidad, "costo": costo})

    if not items_crudos:
        raise ValueError("No se encontraron ítems válidos en la tabla detectada.")

    return construir_resultado_final(items_crudos, db, datos_cabecera)


# --------------Camino 2: fallback LLM-----------------
def process_receipt_with_llm(factura_llm: FacturaExtraidaLLM, db: Session, datos_cabecera: dict) -> dict:
    items_crudos = [
        {
            "sku": it.referencia or f"SIN-REF-{i}",
            "nombre": it.descripcion,
            "cantidad": it.cantidad,
            "costo": it.costo_unitario,
        }
        for i, it in enumerate(factura_llm.items)
    ]
    if not items_crudos:
        raise ValueError("El LLM no devolvió ítems válidos.")
    return construir_resultado_final(items_crudos, db, datos_cabecera)


# LÓGICA EN SEGUNDO PLANO: Envío del correo con plantilla HTML y adjunto
def send_html_email_task(invoice_id: int, file_name: str, nit: str, total_items: int, json_data: list):
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    target_email = os.getenv("TARGET_EMAIL")

    if not all([smtp_user, smtp_password, target_email]):
        print("❌ Error SMTP: Faltan variables de entorno (SMTP_USER, SMTP_PASSWORD o TARGET_EMAIL)")
        return

    msg = EmailMessage()
    msg['Subject'] = f'📊 Reporte de Factura Procesada - ID #{invoice_id}'
    msg['From'] = smtp_user
    msg['To'] = target_email

    text_fallback = f"""
    Hola,
    Se ha procesado con éxito la factura ID #{invoice_id}.
    - Archivo original: {file_name}
    - NIT Emisor: {nit}
    - Total de ítems estructurados: {total_items}

    El documento estructurado en formato JSON se encuentra adjunto a este correo.
    """
    msg.set_content(text_fallback)

    html_template = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><style>
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
    </style></head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Factura Procesada con Éxito</h1>
                <p>Automatización de Procesos - SuperDulces BI</p>
            </div>
            <div class="content">
                <p class="welcome">Hola Administradores de SuperDulces,</p>
                <p class="welcome">Les informamos que un nuevo documento PDF ha sido extraído, normalizado e integrado correctamente al flujo analítico del sistema.</p>
                <div class="card">
                    <div class="card-title">Métricas de la Operación</div>
                    <div class="info-grid">
                        <div class="info-row"><div class="info-label">ID de Registro:</div><div class="info-value"><strong>#{invoice_id}</strong></div></div>
                        <div class="info-row"><div class="info-label">Archivo de Origen:</div><div class="info-value" style="word-break: break-all;">{file_name}</div></div>
                        <div class="info-row"><div class="info-label">NIT del Emisor:</div><div class="info-value">{nit if nit else 'No detectado'}</div></div>
                        <div class="info-row"><div class="info-label">Ítems Extraídos:</div><div class="info-value">{total_items} unidades</div></div>
                        <div class="info-row"><div class="info-label">Estado:</div><div class="info-value"><span class="badge">Listo para SysCafé</span></div></div>
                    </div>
                </div>
                <p class="welcome" style="font-size: 14px; color: #718096;">He adjuntado a este mensaje el archivo completo <strong>factura_{invoice_id}.json</strong>.</p>
            </div>
            <div class="footer">Este es un mensaje automático generado por el Subsistema de Extracción de Datos de SuperDulces BI.</div>
        </div>
    </body></html>
    """
    msg.add_alternative(html_template, subtype='html')

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

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15) as smtp:
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)
            logger.info(f"✅ [ID #{invoice_id}] Correo HTML enviado con éxito a {target_email}")    
    except smtplib.SMTPAuthenticationError:
        logger.error(f"❌ Error de Autenticación SMTP en factura #{invoice_id}: Verifica tu contraseña de aplicación de Google.")
    except Exception as e:
        logger.error(f"❌ Error técnico SMTP al enviar correo de factura #{invoice_id}: {e}")