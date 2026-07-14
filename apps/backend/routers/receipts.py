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
    construir_resultado_final,
    normalizar_texto,
    limpiar_numero_colombiano,
)
from services.supplier_profile_service import (
    buscar_perfil,
    guardar_o_actualizar_perfil,
    procesar_con_perfil,
)
from utils.pdf_parser import extraer_con_pymupdf_tables, extraer_texto_para_llm, extraer_tabla_cruda
from config.database import get_db
from services.llm_extraction_service import extraer_factura_con_llm

router = APIRouter(prefix="/receipts", tags=["Automatización"])
logger = logging.getLogger(__name__)


def _guardar_historial(result: dict, datos_cabecera: dict, filename: str, db: Session) -> dict:
    """Guarda el resultado procesado en InvoiceHistory. Compartido por los tres flujos de éxito."""
    result["filename"] = filename
    nuevo_historial = InvoiceHistory(
        file_name=filename,
        nit=datos_cabecera.get("nit_emisor"),
        total_items=result["resumen"]["total_items"],
        json_data=result["syscafe_json"],
    )
    db.add(nuevo_historial)
    db.commit()
    db.refresh(nuevo_historial)
    result["invoice_id"] = nuevo_historial.id
    return result


@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        datos_cabecera = extraer_cabecera_pdf(contents)
        nit = datos_cabecera.get("nit_emisor")

        # CAMINO 0: ¿ya conocemos este proveedor?
        perfil = buscar_perfil(nit, db) if nit else None
        if perfil:
            try:
                df = extraer_con_pymupdf_tables(contents)
                result = procesar_con_perfil(df, perfil, datos_cabecera, db)
                logger.info(f"'{file.filename}' procesada con perfil guardado (NIT {nit})")
                return _guardar_historial(result, datos_cabecera, file.filename, db)
            except ValueError as e_perfil:
                logger.warning(f"Perfil de NIT {nit} ya no coincide ({e_perfil}), probando caminos genéricos")

        # CAMINO 1: reglas genéricas
        try:
            df = extraer_con_pymupdf_tables(contents)
            result = process_receipt_logic(df, db, datos_cabecera)
            logger.info(f"'{file.filename}' procesada con parser de reglas")
            return _guardar_historial(result, datos_cabecera, file.filename, db)
        except ValueError as e_reglas:
            logger.warning(f"Parser de reglas falló en '{file.filename}' ({e_reglas}), probando LLM")

        # CAMINO 2: LLM (fallback)
        try:
            texto_llm = extraer_texto_para_llm(contents)
            factura_llm = extraer_factura_con_llm(texto_llm)
            result = process_receipt_with_llm(factura_llm, db, datos_cabecera)
            logger.info(f"'{file.filename}' procesada con fallback LLM")
            return _guardar_historial(result, datos_cabecera, file.filename, db)
        except ValueError as e_llm:
            logger.warning(f"Fallback LLM falló en '{file.filename}' ({e_llm}), pidiendo mapeo manual")

        # CAMINO 3: mapeo manual (último recurso)
        tabla_cruda = extraer_tabla_cruda(contents)  # puede lanzar ValueError, lo atrapa el except general
        return {
            "requiere_mapeo_manual": True,
            "nit_emisor": nit,
            "datos_cabecera": datos_cabecera,
            "tabla_cruda": tabla_cruda,
            "filename": file.filename,
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error técnico procesando '{file.filename}': {e}")
        raise HTTPException(status_code=500, detail="Error interno procesando el archivo")


@router.post("/confirm-mapping")
async def confirm_mapping(payload: dict, db: Session = Depends(get_db)):
    """
    Recibe el mapeo que el usuario definió manualmente en el frontend,
    guarda el perfil del proveedor para futuras facturas, y procesa
    esta factura con ese mapeo.

    payload esperado:
    {
        "nit_emisor": str,
        "nombre_proveedor": str (opcional),
        "mapeo": {"ref": "cod producto", "desc": "descripcion", "cant": "cantidad", "costo": "vr unitario"},
        "tabla_cruda": [[...], [...]],   # tal como se devolvió en /upload
        "datos_cabecera": {...},          # tal como se devolvió en /upload
        "filename": str
    }
    """
    try:
        nit_emisor = payload.get("nit_emisor")
        mapeo = payload.get("mapeo")
        tabla_cruda = payload.get("tabla_cruda")
        datos_cabecera = payload.get("datos_cabecera", {})
        filename = payload.get("filename", "factura_mapeada.pdf")

        if not nit_emisor:
            raise ValueError("No se pudo identificar el NIT del proveedor para guardar el perfil.")
        if not mapeo or not all(k in mapeo for k in ("ref", "desc", "cant", "costo")):
            raise ValueError("El mapeo debe incluir las 4 columnas: ref, desc, cant, costo.")
        if not tabla_cruda or len(tabla_cruda) < 2:
            raise ValueError("No se recibió una tabla válida para procesar.")

        # La primera fila de tabla_cruda es el encabezado (nombres de columna literales del PDF)
        encabezados = [normalizar_texto(c) for c in tabla_cruda[0]]
        filas_datos = tabla_cruda[1:]

        # Ubicamos el índice de cada columna mapeada dentro del encabezado real
        indices = {}
        for clave, nombre_columna in mapeo.items():
            nombre_normalizado = normalizar_texto(nombre_columna)
            if nombre_normalizado not in encabezados:
                raise ValueError(f"La columna '{nombre_columna}' no se encontró en el encabezado de la tabla.")
            indices[clave] = encabezados.index(nombre_normalizado)

        items_crudos = []
        for fila in filas_datos:
            raw_ref = str(fila[indices["ref"]]).strip()
            ref = raw_ref.split()[-1] if raw_ref else ""
            if not ref or not any(c.isdigit() for c in ref):
                continue

            desc = str(fila[indices["desc"]]).strip()
            cantidad = limpiar_numero_colombiano(str(fila[indices["cant"]]))
            costo = limpiar_numero_colombiano(str(fila[indices["costo"]]))
            if cantidad <= 0:
                continue

            items_crudos.append({"sku": ref, "nombre": desc, "cantidad": cantidad, "costo": costo})

        if not items_crudos:
            raise ValueError("El mapeo indicado no produjo ítems válidos en esta factura.")

        # Guardamos el perfil para que la próxima factura de este proveedor entre por CAMINO 0
        mapeo_para_guardar = {
            clave: encabezados[idx] for clave, idx in indices.items()
        }
        guardar_o_actualizar_perfil(
            nit_emisor, payload.get("nombre_proveedor", ""), mapeo_para_guardar, db
        )

        result = construir_resultado_final(items_crudos, db, datos_cabecera)
        logger.info(f"'{filename}' procesada con mapeo manual, perfil guardado para NIT {nit_emisor}")
        return _guardar_historial(result, datos_cabecera, filename, db)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error técnico en confirm-mapping: {e}")
        raise HTTPException(status_code=500, detail="Error interno procesando el mapeo manual")


# ---- Tus endpoints existentes, sin cambios ----

@router.get("/history")
async def get_history(db: Session = Depends(get_db)):
    history = db.query(InvoiceHistory).order_by(InvoiceHistory.created_at.desc()).all()
    return [
        {"id": h.id, "file_name": h.file_name, "created_at": h.created_at, "nit": h.nit, "total_items": h.total_items}
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
        nombre_seguro = f'"{item.get("nombre", "")}"'
        lineas.append(f"{item['referencia']},{nombre_seguro},{cant},{precio}")

    txt_content = "\n".join(lineas)
    return Response(
        content=txt_content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=factura_{record.id}.txt"}
    )


@router.post("/send-email/{invoice_id}")
async def trigger_invoice_email(invoice_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    record = db.query(InvoiceHistory).filter(InvoiceHistory.id == invoice_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="El registro de factura solicitado no existe.")
    background_tasks.add_task(
        send_html_email_task, record.id, record.file_name, record.nit, record.total_items, record.json_data
    )
    return {"status": "success", "message": f"El envío del correo para la factura #{invoice_id} ha sido encolado con éxito."}