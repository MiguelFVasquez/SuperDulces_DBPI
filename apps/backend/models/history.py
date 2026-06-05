from sqlalchemy import Column, Integer, String, DateTime, JSON, Float
from sqlalchemy.sql import func
from config.database import Base 

class InvoiceHistory(Base):
    __tablename__ = "invoice_history"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    nit = Column(String, nullable=True)
    total_items = Column(Integer, default=0)
    json_data = Column(JSON, nullable=False) # Aquí guardamos todo el JSON
    created_at = Column(DateTime, default=func.now())