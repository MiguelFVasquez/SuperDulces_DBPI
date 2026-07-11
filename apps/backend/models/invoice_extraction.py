from pydantic import BaseModel, field_validator
from typing import Optional

class ItemFacturaLLM(BaseModel):
    referencia: Optional[str] = None
    descripcion: str
    cantidad: float          # <-- Quitamos Field(gt=0) del esquema
    costo_unitario: float    # <-- Quitamos Field(ge=0) del esquema

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("la descripción no puede estar vacía")
        return v.strip()

    @field_validator("cantidad")
    @classmethod
    def cantidad_positiva(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("la cantidad debe ser mayor a 0")
        return v

    @field_validator("costo_unitario")
    @classmethod
    def costo_no_negativo(cls, v: float) -> float:
        if v < 0:
            raise ValueError("el costo unitario no puede ser negativo")
        return v


class FacturaExtraidaLLM(BaseModel):
    proveedor: Optional[str] = None
    numero_factura: Optional[str] = None
    items: list[ItemFacturaLLM]  # <-- Quitamos Field(min_length=1) del esquema

    @field_validator("items")
    @classmethod
    def items_no_vacios(cls, v: list) -> list:
        if not v or len(v) == 0:
            raise ValueError("debe haber al menos un ítem extraído en la factura")
        return v