from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from config.database import Base
import datetime
#modelos para las tablas de productos, clientes, facturas y ventas, con relaciones adecuadas para análisis posteriores.
class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    unit_cost = Column(Numeric(12, 2), default=0.00)

class Inventory(Base):
    __tablename__ = "inventory"
    product_id = Column(Integer, ForeignKey("products.product_id"), primary_key=True)
    current_stock = Column(Integer, nullable=False, default=0)
    min_stock = Column(Integer, default=0)
    last_movement_date = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True, index=True)
    document_number = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)

class Invoice(Base):
    __tablename__ = "invoices"
    invoice_id = Column(String(50), primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    issue_date = Column(DateTime, default=datetime.datetime.utcnow)
    total_amount = Column(Numeric(12, 2), nullable=False)

class Sale(Base):
    __tablename__ = "sales"
    sale_id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(String(50), ForeignKey("invoices.invoice_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    revenue = Column(Numeric(12, 2), nullable=False)