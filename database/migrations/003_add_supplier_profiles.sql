-- ============================================
-- Migración 003: Perfiles de proveedor
-- Guarda el mapeo de columnas aprendido por NIT,
-- para saltarse la detección genérica en facturas recurrentes.
-- ============================================

CREATE TABLE IF NOT EXISTS supplier_profiles (
    id SERIAL PRIMARY KEY,
    nit_emisor VARCHAR(20) UNIQUE NOT NULL,
    nombre_proveedor VARCHAR(255),
    mapeo_columnas JSONB NOT NULL,
    veces_usado INTEGER NOT NULL DEFAULT 1,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_supplier_profiles_nit ON supplier_profiles(nit_emisor);

-- Trigger para mantener actualizado_en sincronizado en cada UPDATE
CREATE OR REPLACE FUNCTION set_actualizado_en()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_supplier_profiles_actualizado_en ON supplier_profiles;

CREATE TRIGGER trg_supplier_profiles_actualizado_en
BEFORE UPDATE ON supplier_profiles
FOR EACH ROW
EXECUTE FUNCTION set_actualizado_en();