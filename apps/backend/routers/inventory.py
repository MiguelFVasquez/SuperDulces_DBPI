from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from config.database import get_db
from models.analytics import Product, Inventory

router = APIRouter(prefix="/inventory", tags=["Inventario"])

@router.get("/")
def get_inventory_status(limit: int = 100, db: Session = Depends(get_db)):
    """Retorna el estado actual del inventario cruzando productos con su stock."""
    result = (
        db.query(
            Product.sku,
            Product.name,
            Product.unit_cost,
            Inventory.current_stock,
            # Calculamos el valor inmovilizado en bodega (stock * costo)
            (Inventory.current_stock * Product.unit_cost).label("total_value")
        )
        .join(Inventory, Product.product_id == Inventory.product_id)
        # Ordenar por los productos que tienen más capital inmovilizado
        .order_by((Inventory.current_stock * Product.unit_cost).desc())
        .limit(limit)
        .all()
    )
    
    # Formatear la salida para el frontend
    return [
        {
            "sku": row.sku,
            "name": row.name,
            "unit_cost": float(row.unit_cost or 0),
            "current_stock": row.current_stock,
            "total_value": float(row.total_value or 0)
        }
        for row in result
    ]