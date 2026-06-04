from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from services.receipt_service import process_receipt_logic
from services.receipt_service import extraer_cabecera_pdf
from utils.pdf_parser import extraer_con_camelot 
from config.database import get_db
from models.analytics import Product

router = APIRouter(prefix="/receipts", tags=["Automatización"])

@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        df = extraer_con_camelot(contents) # Delegado a un utils

        # Extraemos datos de cabecera con pdfplumber + regex, también delegado a un servicio específico
        datos_cabecera = extraer_cabecera_pdf(contents)
        
        # Invocamos el servicio
        result = process_receipt_logic(df, db)
        return result
        
    except ValueError as ve:
        # Errores de lógica de negocio (ej: no encontró columna) -> 400
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Errores inesperados -> 500
        print(f"Error técnico: {e}")
        raise HTTPException(status_code=500, detail="Error interno procesando el archivo")