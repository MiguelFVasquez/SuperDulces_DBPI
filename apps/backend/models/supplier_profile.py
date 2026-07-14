from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from config.database import Base

class SupplierProfile(Base):
    __tablename__ = "supplier_profiles"

    id = Column(Integer, primary_key=True)
    nit_emisor = Column(String(20), unique=True, nullable=False, index=True)
    nombre_proveedor = Column(String(255), nullable=True)
    mapeo_columnas = Column(JSONB, nullable=False)
    veces_usado = Column(Integer, nullable=False, default=1)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())