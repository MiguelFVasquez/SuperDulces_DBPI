import io
import math
import re
import pdfplumber
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.analytics import Product 

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


# --------------Función principal que procesa el DataFrame y hace la homologación
def process_receipt_logic(df: pd.DataFrame, db: Session):
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
        
        # Filtro 1: IGNORAR BASURA SIN NÚMEROS.
        # Los SKU reales de Colombina y otros proveedores tienen dígitos.
        # Esto mata instantáneamente las frases del pie de página que se colaban.
        if not ref or not any(char.isdigit() for char in ref): 
            continue

        raw_row_data = str(row[cols_reales['costo']])
        partes = raw_row_data.split()
        
        # Filtro 2: EL ESCUDO DE ESTRUCTURA.
        # Una fila real de productos tiene [Cantidad, Precio, VrBruto...].
        # Si solo tiene 1 elemento, es un subtotal o un número suelto del pie de página.
        if len(partes) < 2:
            continue
        
        # Ahora sí, extraemos seguros de que hay datos suficientes
        cantidad = limpiar_numero_colombiano(partes[0])
        costo = limpiar_numero_colombiano(partes[1])
        
        if cantidad <= 0: 
            continue 

        # Lógica de consolidación
        if ref in unique_items_map:
            unique_items_map[ref]['cantidad'] += cantidad
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
    return {
        "items": items,
        "resumen": {
            "total_items": len(items),
            "homologados_exitosos": sum(1 for i in items if i["homologado"]),
            "pendientes_revision": sum(1 for i in items if not i["homologado"])
        }
    }