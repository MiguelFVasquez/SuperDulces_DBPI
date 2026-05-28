-- 1. Tabla de Productos
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE,
    name VARCHAR(255) NOT NULL, -- Ej: 'PAPAS CHIPS *45GR'
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Clientes
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    document_number VARCHAR(50) UNIQUE, -- NIT o Cédula
    name VARCHAR(255) NOT NULL,
    customer_type VARCHAR(50) -- Régimen común, simplificado, etc.
);

-- 3. Tabla de Facturas (Encabezados)
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id VARCHAR(50) PRIMARY KEY, -- Ej: 'FP60000143637'
    customer_id INT REFERENCES customers(customer_id),
    issue_date TIMESTAMP NOT NULL,
    total_iva NUMERIC(12, 2) DEFAULT 0.00,
    total_amount NUMERIC(12, 2) NOT NULL,
    pos_box VARCHAR(50), -- Caja POS de origen
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabla de Ventas (Detalle de Factura / Transacciones)
CREATE TABLE IF NOT EXISTS sales (
    sale_id SERIAL PRIMARY KEY,
    invoice_id VARCHAR(50) REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    product_id INT REFERENCES products(product_id),
    quantity INT NOT NULL, -- Ej: 12
    unit_price NUMERIC(12, 2) NOT NULL,
    revenue NUMERIC(12, 2) NOT NULL, -- Ej: 38330.88 (quantity * unit_price libre de ciertos impuestos o total)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tabla de Inventario (Estado Analítico)
CREATE TABLE IF NOT EXISTS inventory (
    product_id INT PRIMARY KEY REFERENCES products(product_id) ON DELETE CASCADE,
    current_stock INT NOT NULL DEFAULT 0,
    min_stock INT DEFAULT 0,
    last_movement_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);