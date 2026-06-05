-- 002_add_invoice_history.sql
CREATE TABLE IF NOT EXISTS invoice_history (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    json_data JSON NOT NULL -- SQLAlchemy maneja el JSON automáticamente
);