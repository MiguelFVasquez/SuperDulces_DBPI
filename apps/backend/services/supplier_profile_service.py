import logging
import pandas as pd
from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from models.supplier_profile import SupplierProfile
from services.receipt_service import normalizar_texto, limpiar_numero_colombiano, construir_resultado_final

logger = logging.getLogger(__name__)
UMBRAL_SIMILITUD = 90  

def buscar_perfil(nit_emisor: str, db: Session) -> SupplierProfile | None:
    """
    Busca si ya existe un mapeo de columnas guardado para este proveedor.
    Devuelve None si no hay NIT o no se encuentra perfil.
    """
    if not nit_emisor:
        return None
    return db.query(SupplierProfile).filter(SupplierProfile.nit_emisor == nit_emisor).first()


def guardar_o_actualizar_perfil(
    nit_emisor: str, nombre_proveedor: str, mapeo: dict, db: Session
) -> SupplierProfile:
    """
    Crea un perfil nuevo o actualiza el mapeo de uno existente (por ejemplo,
    si el proveedor cambió ligeramente su formato y el usuario tuvo que
    remapear columnas).
    """
    perfil = buscar_perfil(nit_emisor, db)
    if perfil:
        perfil.mapeo_columnas = mapeo
        perfil.veces_usado += 1
        if nombre_proveedor:
            perfil.nombre_proveedor = nombre_proveedor
        logger.info(f"Perfil actualizado para NIT {nit_emisor} (uso #{perfil.veces_usado})")
    else:
        perfil = SupplierProfile(
            nit_emisor=nit_emisor,
            nombre_proveedor=nombre_proveedor or None,
            mapeo_columnas=mapeo,
        )
        db.add(perfil)
        logger.info(f"Perfil nuevo creado para NIT {nit_emisor}")

    db.commit()
    db.refresh(perfil)
    return perfil


def _encontrar_fila_encabezado(df: pd.DataFrame, mapeo: dict) -> int:
    """
    Busca la fila del DataFrame que coincide con los nombres de columna
    guardados en el perfil, tolerando variaciones triviales de formato
    (espacios extra, puntuación, tildes ya resueltas por normalizar_texto)
    pero NO sinónimos distintos — para eso está el flujo de remapeo manual.
    """
    valores_esperados = list(mapeo.values())

    for i in range(min(40, len(df))):
        valores_fila = [normalizar_texto(val) for val in df.iloc[i] if str(val).strip()]
        if not valores_fila:
            continue

        # Cada valor esperado debe tener AL MENOS una celda en la fila
        # con similitud >= umbral
        coincidencias = 0
        for esperado in valores_esperados:
            mejor_score = max(
                (fuzz.ratio(esperado, celda) for celda in valores_fila),
                default=0,
            )
            if mejor_score >= UMBRAL_SIMILITUD:
                coincidencias += 1

        if coincidencias == len(valores_esperados):
            return i

    return -1


def procesar_con_perfil(df: pd.DataFrame, perfil: SupplierProfile, datos_cabecera: dict, db: Session) -> dict:
    """
    Procesa una factura usando el mapeo de columnas ya conocido para este
    proveedor, sin pasar por detección genérica de encabezados ni el LLM.

    Lanza ValueError si el layout cambió tanto que el mapeo guardado ya no aplica
    (esto hace que el caller pueda decidir caer a reglas genéricas o LLM como respaldo).
    """
    mapeo = perfil.mapeo_columnas

    cabecera_idx = _encontrar_fila_encabezado(df, mapeo)
    if cabecera_idx == -1:
        raise ValueError(
            f"El mapeo guardado para el proveedor NIT {perfil.nit_emisor} ya no coincide "
            f"con el formato de esta factura. Puede que el proveedor haya cambiado su layout."
        )

    df.columns = [normalizar_texto(c) for c in df.iloc[cabecera_idx]]
    df = df.iloc[cabecera_idx + 1:].reset_index(drop=True)
    df = df.map(lambda x: str(x).strip().replace('\n', ' ') if pd.notnull(x) else x)
    df = df.drop_duplicates().reset_index(drop=True)

    # Verificamos que las columnas mapeadas realmente existan tras normalizar
    for clave, nombre_columna in mapeo.items():
        if nombre_columna not in df.columns:
            raise ValueError(
                f"La columna '{nombre_columna}' (mapeada para '{clave}') ya no existe en esta factura. "
                f"Columnas encontradas: {list(df.columns)}"
            )

    items_crudos = []
    for _, row in df.iterrows():
        raw_ref = str(row[mapeo["ref"]]).strip()
        ref = raw_ref.split()[-1] if raw_ref else ""
        if not ref or not any(char.isdigit() for char in ref):
            continue

        desc = str(row[mapeo["desc"]]).strip()
        cantidad = limpiar_numero_colombiano(str(row[mapeo["cant"]]))
        costo = limpiar_numero_colombiano(str(row[mapeo["costo"]]))

        if cantidad <= 0:
            continue

        items_crudos.append({"sku": ref, "nombre": desc, "cantidad": cantidad, "costo": costo})

    if not items_crudos:
        raise ValueError(
            f"El mapeo del proveedor NIT {perfil.nit_emisor} no produjo ítems válidos en esta factura."
        )

    return construir_resultado_final(items_crudos, db, datos_cabecera)