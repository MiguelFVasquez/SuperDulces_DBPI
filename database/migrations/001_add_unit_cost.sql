# This migration adds a new column 'unit_cost' to the 'products' table.
ALTER TABLE products ADD COLUMN unit_cost NUMERIC(12, 2) DEFAULT 0.00;