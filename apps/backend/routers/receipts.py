import json
import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Response, BackgroundTasks
from sqlalchemy.orm import Session
from models.history import InvoiceHistory
from services.receipt_service import (
    process_receipt_logic,
    process_receipt_with_llm,
    extraer_cabecera_pdf,
    send_html_email_task,
)
from utils.pdf_parser import extraer_con_pymupdf_tables, extraer_texto_para_llm
from config.database import get_db
from services.llm_extraction_service import extraer_factura_con_llm

router = APIRouter(prefix="/receipts", tags=["Automatización"])
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        datos_cabecera = extraer_cabecera_pdf(contents)

        # CAMINO 1: parser geométrico basado en reglas (rápido, gratis)
        try:
            df = extraer_con_pymupdf_tables(contents)
            result = process_receipt_logic(df, db, datos_cabecera)
            logger.info(f"'{file.filename}' procesada con parser de reglas")
        except ValueError as e_reglas:
            # CAMINO 2 (fallback): LLM Haiku 4.5
            logger.warning(f"Parser de reglas falló en '{file.filename}' ({e_reglas}), usando fallback LLM")
            texto_llm = extraer_texto_para_llm(contents)
            factura_llm = extraer_factura_con_llm(texto_llm)  # puede lanzar ValueError
            result = process_receipt_with_llm(factura_llm, db, datos_cabecera)
            logger.info(f"'{file.filename}' procesada con fallback LLM")

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
        db.refresh(nuevo_historial)

        result["invoice_id"] = nuevo_historial.id  # útil para que el frontend luego dispare /send-email
        return result

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error técnico procesando '{file.filename}': {e}")
        raise HTTPException(status_code=500, detail="Error interno procesando el archivo")


# Endpoint para obtener el historial de facturas procesadas
@router.get("/history")
async def get_history(db: Session = Depends(get_db)):
    history = db.query(InvoiceHistory).order_by(InvoiceHistory.created_at.desc()).all()
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

    json_content = json.dumps(record.json_data, indent=4, ensure_ascii=False)
    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=factura_{record.id}.json"}
    )


@router.get("/download-receipt-txt/{invoice_id}")
async def download_txt(invoice_id: int, db: Session = Depends(get_db)):
    record = db.query(InvoiceHistory).filter(InvoiceHistory.id == invoice_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    try:
        factura_data = record.json_data[0]
        items = factura_data.get("items", [])
    except (IndexError, AttributeError):
        raise HTTPException(status_code=500, detail="Formato de datos corrupto en la base de datos")

    lineas = ["referencia,nombre,cantidad,precio"]
    for item in items:
        cant = int(item['cant']) if item['cant'] % 1 == 0 else item['cant']
        precio = int(item['precio']) if item['precio'] % 1 == 0 else item['precio']
        nombre = item.get("nombre", "")
        nombre_seguro = f'"{nombre}"'
        lineas.append(f"{item['referencia']},{nombre_seguro},{cant},{precio}")

    txt_content = "\n".join(lineas)
    return Response(
        content=txt_content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=factura_{record.id}.txt"}
    )


# --- Disparar el envío de correo desde el Frontend ---
@router.post("/send-email/{invoice_id}")
async def trigger_invoice_email(invoice_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    record = db.query(InvoiceHistory).filter(InvoiceHistory.id == invoice_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="El registro de factura solicitado no existe.")

    background_tasks.add_task(
        send_html_email_task,
        record.id,
        record.file_name,
        record.nit,
        record.total_items,
        record.json_data
    )

    return {"status": "success", "message": f"El envío del correo para la factura #{invoice_id} ha sido encolado con éxito."}