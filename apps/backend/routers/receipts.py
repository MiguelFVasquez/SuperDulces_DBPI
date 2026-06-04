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
        df = extraer_con_camelot(contents)

        # 1. Sacamos la cabecera 
        datos_cabecera = extraer_cabecera_pdf(contents)
        
        # 2. Se lo pasamos al servicio
        result = process_receipt_logic(df, db, datos_cabecera)
        result["filename"] = file.filename
        
        return result
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error técnico: {e}")
        raise HTTPException(status_code=500, detail="Error interno procesando el archivo")