from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, Date
from config.database import get_db
from models.analytics import Sale, Product, Invoice

router = APIRouter(prefix="/metrics", tags=["Métricas Analíticas"])# Rutas para métricas analíticas clave: productos top/menos vendidos, resumen de ventas, ingresos totales, ticket promedio y evolución temporal de ventas.
# Cada endpoint realiza consultas agregadas a la base de datos utilizando SQLAlchemy para obtener insights relevantes para el dashboard de BI.

# Endpoint para obtener los productos con mayores ingresos acumulados
@router.get("/top-products")
def get_top_products(limit: int = 5, db: Session = Depends(get_db)):
    """Los productos con mayores ingresos acumulados."""
    result = (
        db.query(
            Product.sku,
            Product.name,
            func.sum(Sale.quantity).label("total_qty"),
            func.sum(Sale.revenue).label("total_revenue"),
            # Calculamos el costo total multiplicando cantidad vendida por costo unitario
            func.sum(Sale.quantity * Product.unit_cost).label("total_cost")
        )
        .join(Sale, Product.product_id == Sale.product_id)
        .group_by(Product.product_id, Product.sku, Product.name)
        .order_by(func.sum(Sale.revenue).desc())
        .limit(limit)
        .all()
    )
    response = []
    for row in result:
        rev = float(row.total_revenue or 0)
        cost = float(row.total_cost or 0)
        profit = rev - cost
        margin = (profit / rev * 100) if rev > 0 else 0
        
        response.append({
            "sku": row.sku,
            "name": row.name,
            "total_qty": row.total_qty,
            "total_revenue": rev,
            "total_cost": cost,
            "total_profit": profit,
            "margin_percentage": round(margin, 2)
        })
        
    return response

# Endpoint para obtener los productos con menores ingresos acumuladoss
@router.get("/least-products")
def get_least_products(limit: int = 5, db: Session = Depends(get_db)):
    """Los productos menos vendidos o con menor impacto en ingresos."""
    result = (
        db.query(
            Product.sku,
            Product.name,
            func.sum(Sale.quantity).label("total_qty"),
            func.sum(Sale.revenue).label("total_revenue"),
            func.sum(Sale.quantity * Product.unit_cost).label("total_cost")
        )
        .join(Sale, Product.product_id == Sale.product_id)
        .group_by(Product.product_id, Product.sku, Product.name)
        .order_by(func.sum(Sale.revenue).asc())
        .limit(limit)
        .all()
    )
    response = []
    for row in result:
        rev = float(row.total_revenue or 0)
        cost = float(row.total_cost or 0)
        profit = rev - cost
        margin = (profit / rev * 100) if rev > 0 else 0
        
        response.append({
            "sku": row.sku,
            "name": row.name,
            "total_qty": row.total_qty,
            "total_revenue": rev,
            "total_cost": cost,
            "total_profit": profit,
            "margin_percentage": round(margin, 2)
        })
        
    return response

# Endpoint para obtener un resumen transaccional de ventas
@router.get("/sales")
def get_sales_summary(db: Session = Depends(get_db)):
    """Resumen transaccional: Número total de registros de venta y unidades totales vendidas."""
    summary = db.query(
        func.count(Sale.sale_id).label("total_transactions"),
        func.sum(Sale.quantity).label("total_units_sold")
    ).first()
    return dict(summary._mapping) if summary else {"total_transactions": 0, "total_units_sold": 0}

# Endpoint para obtener el monto bruto total recaudado en el periodo|
@router.get("/revenue")
def get_total_revenue(db: Session = Depends(get_db)):
    """Monto bruto total recaudado en el periodo."""
    total = db.query(func.sum(Sale.revenue)).scalar()
    return {"total_revenue": float(total) if total else 0.0}

# Endpoint para obtener el valor promedio de una factura (Ticket Promedio)
@router.get("/ticket-average")
def get_ticket_average(db: Session = Depends(get_db)):
    """Valor promedio de una factura (Ticket Promedio)."""
    avg_ticket = db.query(func.avg(Invoice.total_amount)).scalar()
    return {"ticket_average": float(avg_ticket) if avg_ticket else 0.0}

# Endpoint para obtener la evolución temporal de ventas diarias
@router.get("/sales-by-date")
def get_sales_by_date(db: Session = Depends(get_db)):
    """Evolución temporal de ventas diarias (ideal para gráficos de líneas)."""
    result = (
        db.query(
            func.cast(Invoice.issue_date, Date).label("date"),
            func.sum(Invoice.total_amount).label("revenue"),
            func.count(Invoice.invoice_id).label("invoice_count")
        )
        .group_by(func.cast(Invoice.issue_date, Date))
        .order_by(func.cast(Invoice.issue_date, Date).asc())
        .all()
    )
    return [
        {
            "date": str(row._mapping["date"]),
            "revenue": float(row._mapping["revenue"]),
            "invoice_count": row._mapping["invoice_count"]
        }
        for row in result
    ]