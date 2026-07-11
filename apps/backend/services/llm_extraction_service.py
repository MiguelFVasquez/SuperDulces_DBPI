import logging
import anthropic
from config.settings import get_settings
from models.invoice_extraction import FacturaExtraidaLLM
from pydantic import ValidationError

logger = logging.getLogger(__name__)

TOOL_SCHEMA = {
    "name": "extraer_items_factura",
    "description": "Extrae los ítems de una factura de proveedor de dulcería en formato estandarizado",
    "input_schema": {
        "type": "object",
        "properties": {
            "proveedor": {"type": "string"},
            "numero_factura": {"type": "string"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "referencia": {"type": "string"},
                        "descripcion": {"type": "string"},
                        "cantidad": {"type": "number"},
                        "costo_unitario": {"type": "number"},
                    },
                    "required": ["descripcion", "cantidad", "costo_unitario"],
                },
            },
        },
        "required": ["items"],
    },
}

PROMPT_SISTEMA = """Eres un asistente especializado en extraer datos de facturas de \
proveedores de una dulcería en Colombia. Los proveedores usan nombres de columnas \
distintos (Código/Referencia/Item/PLU, Descripción/Producto/Detalle, \
Cantidad/Unidad despachada/U-M, Costo/Precio Unitario/Valor Neto, etc). \
Identifica la tabla de ítems y estandarízala en el formato pedido, sin importar \
el layout original. Si un ítem no tiene referencia/código visible, omite ese campo. \
Ignora filas de totales, subtotales, IVA o notas. Nunca inventes cantidades o precios \
que no aparezcan explícitamente en el texto."""


def extraer_factura_con_llm(texto_factura: str) -> FacturaExtraidaLLM:
    settings = get_settings()
    client = anthropic.Anthropic(
        api_key=settings.anthropic_api_key,
        timeout=settings.llm_timeout_seconds,
    )

    logger.info(f"Usando modelo LLM: '{settings.llm_model_fallback}'")

    try:
        response = client.messages.create(
            model=settings.llm_model_fallback,
            max_tokens=settings.llm_max_tokens,
            system=PROMPT_SISTEMA,
            tools=[TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": "extraer_items_factura"},
            messages=[{"role": "user", "content": texto_factura}],
        )
    except anthropic.APIError as e:
        logger.error(f"Error llamando a la API de Anthropic: {e}")
        raise ValueError("No se pudo procesar la factura con el servicio de IA (fallback).")

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_use is None:
        raise ValueError("El modelo no devolvió una extracción estructurada.")

    try:
        return FacturaExtraidaLLM.model_validate(tool_use.input)
    except ValidationError as e:
        logger.error(f"Respuesta del LLM no pasó validación: {e}")
        raise ValueError("La extracción de la IA no cumplió el formato esperado.")