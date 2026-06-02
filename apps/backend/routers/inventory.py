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
            Inventory.min_stock,
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
            "total_value": float(row.total_value or 0),
            "min_stock": row.min_stock or 0
        }
        for row in result
    ]


@router.put("/min-stock")
def update_min_stock(sku: str, min_stock: int, db: Session = Depends(get_db)):
    """Actualiza el stock mínimo de un producto específico buscando por SKU."""
    
    # 1. Buscamos el ID del producto usando el SKU
    product = db.query(Product).filter(Product.sku == sku).first()
    if not product:
        return {"error": "Producto no encontrado en la base de datos."}
        
    # 2. Buscamos el inventario asociado
    inventory_item = db.query(Inventory).filter(Inventory.product_id == product.product_id).first()
    
    if not inventory_item:
        return {"error": "Registro de inventario no encontrado para este producto."}
    
    # 3. Actualizamos y guardamos
    inventory_item.min_stock = min_stock
    db.commit()
    
    return {"message": f"Stock mínimo actualizado a {min_stock} para el SKU {sku}."}