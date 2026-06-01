import io
import pandas as pd
import pdfplumber
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from config.database import get_db
from models.analytics import Product

router = APIRouter(prefix="/receipts", tags=["Automatización de Facturas"])

def extraer_tabla_pdf(pdf_bytes: bytes) -> pd.DataFrame:
    """
    Lee un PDF en memoria, extrae las tablas de todas las páginas
    y las unifica en un solo DataFrame de Pandas.
    """
    all_rows = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            # extract_tables busca estructuras de grilla en el PDF
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Limpiamos saltos de línea extraños dentro de las celdas
                    cleaned_row = [str(cell).strip().replace('\n', ' ') if cell else "" for cell in row]
                    # Descartamos filas completamente vacías
                    if any(cleaned_row):
                        all_rows.append(cleaned_row)

    if not all_rows:
        raise ValueError("No se detectaron tablas estructuradas en el PDF.")

    # Asumimos que la primera fila encontrada contiene los encabezados
    headers = [str(h).lower().strip() for h in all_rows[0]]
    data = all_rows[1:]
    
    return pd.DataFrame(data, columns=headers)

@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Recibe un archivo Excel/CSV/PDF del proveedor, extrae los items y los homologa
    contra la tabla maestra de productos de SysCafe.
    """
    # 1. Validar el formato
    valid_extensions = ('.xlsx', '.csv', '.pdf')
    if not file.filename.lower().endswith(valid_extensions):
        raise HTTPException( 
            status_code=400, 
            detail=f"Formato no soportado. Usa {valid_extensions}"
        )
    
    contents = await file.read()
    
    # 2. Cargar en un DataFrame de Pandas según la extensión
    try:
        filename_lower = file.filename.lower()
        if filename_lower.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename_lower.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(contents))
        elif filename_lower.endswith('.pdf'):
            df = extraer_tabla_pdf(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo el archivo: {str(e)}")

    # Normalizar nombres de columnas
    df.columns = [str(col).strip().lower() for col in df.columns]
    
    # Validar que existan las columnas mínimas (hacemos un best-effort)
    expected_cols = {"referencia", "descripcion", "cantidad", "costo", "iva"}
    
    # Comprobación flexible: vemos si las columnas requeridas están en el dataframe
    missing_cols = expected_cols - set(df.columns)
    if missing_cols:
        raise HTTPException(
            status_code=400, 
            detail=f"El archivo no tiene el formato esperado. Faltan las columnas: {missing_cols}. Columnas detectadas: {list(df.columns)}"
        )

    processed_items = []
    
    # 3. Lógica de Homologación
    for _, row in df.iterrows():
        # Saltamos filas donde la referencia o descripción estén vacías o sean NaN
        if pd.isna(row['referencia']) or pd.isna(row['descripcion']):
            continue
            
        proveedor_ref = str(row['referencia']).strip()
        descripcion = str(row['descripcion']).strip()
        
        # Limpieza de valores numéricos que puedan venir como strings desde el PDF (ej. "$ 1.500,00")
        try:
            cantidad = float(str(row['cantidad']).replace(',', ''))
            costo = float(str(row['costo']).replace('$', '').replace(',', ''))
            iva = float(str(row['iva']).replace('%', '').replace(',', ''))
        except ValueError:
            # Si no se puede convertir a número, saltamos la fila (puede ser un subtotal)
            continue
        
        db_product = db.query(Product).filter(
            (func.lower(Product.name) == func.lower(descripcion)) | 
            (Product.sku == proveedor_ref)
        ).first()

        syscafe_sku = db_product.sku if db_product else "PENDIENTE"
        nombre_oficial = db_product.name if db_product else descripcion

        processed_items.append({
            "referencia_proveedor": proveedor_ref,
            "referencia_syscafe": syscafe_sku,
            "nombre": nombre_oficial,
            "cantidad": cantidad,
            "costo_unitario": costo,
            "iva": iva,
            "homologado": bool(db_product)
        })

    if not processed_items:
         raise HTTPException(status_code=400, detail="No se pudieron extraer items válidos del documento.")

    return {
        "filename": file.filename,
        "items": processed_items,
        "resumen": {
            "total_items": len(processed_items),
            "homologados_exitosos": sum(1 for i in processed_items if i["homologado"]),
            "pendientes_revision": sum(1 for i in processed_items if not i["homologado"])
        }
    }