# transformers/articles_transformer.py

def transform_articles(rows: list[dict]) -> list[dict]:
    transformed = []
    
    for row in rows:
        sku = row.get("REFERENCIA")
        
        # Ignorar si no hay SKU (filas corruptas o vacías)
        if not sku:
            continue

        name = row.get("DETALLE", "SIN NOMBRE").strip()

        try:
            # Syscafe a veces exporta números con espacios o vacíos
            cost = float(row.get("COSTO", 0) or 0)
            stock = int(float(row.get("SALDO", 0) or 0))
        except (ValueError, TypeError):
            cost = 0.0
            stock = 0

        transformed.append({
            "sku": sku.strip(),
            "name": name,
            "unit_cost": cost,
            "current_stock": stock
        })

    return transformed