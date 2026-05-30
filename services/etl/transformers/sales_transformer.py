from decimal import Decimal

INVALID_DETAIL_PATTERNS = [
    "FRA DE VNTA",
    "IVA",
    "TRASLADO",
    "TRAS",
    "DESCUENTO",
    "COMPRAS",
    "DEVOLUCION",
]

def is_real_product(row: dict) -> bool:
    detail = row.get("DETALLE", "").upper()

    if not detail:
        return False

    if any(pattern in detail for pattern in INVALID_DETAIL_PATTERNS):
        return False

    if not row.get("ARTRELA"):
        return False

    try:
        # Convertimos y aseguramos que tras el abs() sea mayor a cero
        quantity = abs(float(row.get("ARTCANT", 0)))
        return quantity > 0
    except:
        return False


def transform_sales(rows: list[dict]) -> list[dict]:
    transformed = []
    seen = set()

    for row in rows:

        if not is_real_product(row):
            continue

        invoice_id = row.get("DOCRELA")
        product_code = row.get("ARTRELA")
        product_name = row.get("DETALLE")

        try:
            # syscafe exporta ARTCANT en negativo para salidas, aplicamos abs()
            # y casteamos a int para cumplir con el tipo INT de PostgreSQL
            quantity = int(abs(float(row.get("ARTCANT", 0))))
            revenue = float(row.get("CREDITO", 0))
        except (ValueError, TypeError):
            continue

        # Huella para detectar filas duplicadas basadas en los campos clave
        fingerprint = (
            invoice_id,
            product_code,
            quantity,
            revenue
        )

        if fingerprint in seen:
            continue

        seen.add(fingerprint)

        transformed_row = {
            "invoice_id": invoice_id,
            "invoice_number": row.get("NUMERO"),
            "document_type": row.get("TIPO"),
            "product_code": product_code,
            "product_name": product_name,
            "quantity": quantity,
            "revenue": revenue,
            "customer_id": row.get("TERCERO"),
            "item": row.get("ITEM"),
        }

        transformed.append(transformed_row)

    return transformed