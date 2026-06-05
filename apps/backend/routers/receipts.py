import json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Response
from sqlalchemy.orm import Session
from models.history import InvoiceHistory
from services.receipt_service import process_receipt_logic
from services.receipt_service import extraer_cabecera_pdf
from utils.pdf_parser import extraer_con_camelot 
from config.database import get_db


router = APIRouter(prefix="/receipts", tags=["Automatización"])

@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        df = extraer_con_camelot(contents)

        # 1. Sacamos la cabecera 
        datos_cabecera = extraer_cabecera_pdf(contents)
        
        # 2. Se lo pasamos al servicio
        result = process_receipt_logic(df, db, datos_cabecera)
        result["filename"] = file.filename
        
        # GUARDAR EN DB
        nuevo_historial = InvoiceHistory(
            file_name=file.filename,
            nit=datos_cabecera.get("nit_emisor"),
            total_items=result["resumen"]["total_items"],
            json_data=result["syscafe_json"]
        )
        db.add(nuevo_historial)
        db.commit()

        return result
    
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error técnico: {e}")
        raise HTTPException(status_code=500, detail="Error interno procesando el archivo")
    

# Endpoint para obtener el historial de facturas procesadas
@router.get("/history")
async def get_history(db: Session = Depends(get_db)):
    # Traemos todo el historial, ordenado del más reciente al más antiguo
    history = db.query(InvoiceHistory).order_by(InvoiceHistory.created_at.desc()).all()
    
    # Retornamos una lista simplificada
    return [
        {
            "id": h.id,
            "file_name": h.file_name,
            "created_at": h.created_at,
            "nit": h.nit,
            "total_items": h.total_items
        }
        for h in history
    ]


@router.get("/download-receipt/{invoice_id}")
async def download_json(invoice_id: int, db: Session = Depends(get_db)): 
    record = db.query(InvoiceHistory).filter(InvoiceHistory.id == invoice_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Serializar correctamente a JSON válido
    # ensure_ascii=False permite que las tildes y caracteres especiales se vean bien
    json_content = json.dumps(record.json_data, indent=4, ensure_ascii=False)
    
    return Response(
        content=json_content, 
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=factura_{record.id}.json"}
    )



@router.get("/download-receipt-txt/{invoice_id}")
async def download_txt(invoice_id: int, db: Session = Depends(get_db)):
    # 1. Buscamos el registro en la base de datos
    record = db.query(InvoiceHistory).filter(InvoiceHistory.id == invoice_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # 2. Extraemos los items del JSON guardado.
    # Recordar que json_data es una lista con 1 diccionario adentro: [{ "tipo": "FV2", ..., "items": [...] }]
    try:
        factura_data = record.json_data[0] 
        items = factura_data.get("items", [])
    except (IndexError, AttributeError):
        raise HTTPException(status_code=500, detail="Formato de datos corrupto en la base de datos")

    # 3. Construimos el contenido del TXT
    lineas = ["referencia,nombre,cantidad,precio"]
    for item in items:
        # Formateamos los números para quitar decimales si son ceros, tal como lo querías
        cant = int(item['cant']) if item['cant'] % 1 == 0 else item['cant']
        precio = int(item['precio']) if item['precio'] % 1 == 0 else item['precio']
        nombre = item.get("nombre", "")
        nombre_seguro = f'"{nombre}"'
        
        lineas.append(f"{item['referencia']},{nombre_seguro},{cant},{precio}")
    
    txt_content = "\n".join(lineas)
    
    # 4. Retornamos el archivo de texto plano
    return Response(
        content=txt_content, 
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=factura_{record.id}.txt"}
    )