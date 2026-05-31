import psycopg2
import os

# Función para obtener la conexión a la base de datos PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )

# Carga de productos respetando la relación con facturas
def load_products(cursor, sales):
    products = {}
    for sale in sales:
        sku = sale["product_code"]
        if sku not in products:
            products[sku] = sale["product_name"]

    for sku, name in products.items():
        cursor.execute("""
            INSERT INTO products (sku, name)
            VALUES (%s, %s)
            ON CONFLICT (sku) DO NOTHING
        """, (sku, name))

# Carga de clientes respetando la relación con facturas
def load_customers(cursor, sales):
    customers = set()
    for sale in sales:
        customers.add(sale["customer_id"])

    for document in customers:
        cursor.execute("""
            INSERT INTO customers (document_number, name)
            VALUES (%s, %s)
            ON CONFLICT (document_number) DO NOTHING
        """, (document, "CLIENTE GENERAL"))

# Carga de facturas respetando la relación con clientes
def load_invoices(cursor, sales):
    invoices = {}
    for sale in sales:
        invoice_id = sale["invoice_id"]
        if invoice_id not in invoices:
            invoices[invoice_id] = {
                "invoice_number": sale["invoice_number"],
                "customer_document": sale["customer_id"],
                "total_amount": 0.0,
            }
        invoices[invoice_id]["total_amount"] += sale["revenue"]

    for invoice_id, invoice_data in invoices.items():
        cursor.execute("""
            SELECT customer_id FROM customers WHERE document_number = %s
        """, (invoice_data["customer_document"],))
        
        customer = cursor.fetchone()
        if not customer:
            continue
        customer_id = customer[0]

        cursor.execute("""
            INSERT INTO invoices (invoice_id, customer_id, issue_date, total_amount)
            VALUES (%s, %s, NOW(), %s)
            ON CONFLICT (invoice_id) DO NOTHING
        """, (invoice_id, customer_id, invoice_data["total_amount"]))


# Orquestador maestro de inserciones relacionales
def load_sales(conn, sales):
    """Orquestador maestro de inserciones relacionales."""
    cursor = conn.cursor()

    # Ejecutar cargas respetando las llaves foráneas
    print("   ↳ Cargando productos...")
    load_products(cursor, sales)
    
    print("   ↳ Cargando clientes...")
    load_customers(cursor, sales)
    
    print("   ↳ Cargando encabezados de facturas...")
    load_invoices(cursor, sales)

    print("   ↳ Cargando detalle de transacciones de ventas...")
    for sale in sales:
        cursor.execute("""
            SELECT product_id FROM products WHERE sku = %s
        """, (sale["product_code"],))
        
        product = cursor.fetchone()
        if not product:
            continue
        product_id = product[0]

        quantity = sale["quantity"]
        unit_price = sale["revenue"] / quantity if quantity > 0 else 0.0

        cursor.execute("""
            INSERT INTO sales (invoice_id, product_id, quantity, unit_price, revenue)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            sale["invoice_id"],
            product_id,
            quantity,
            unit_price,
            sale["revenue"]
        ))

    cursor.close()

# Carga del maestro de artículos respetando la relación con inventario
def load_articles(conn, articles):
    """
    Carga el maestro de artículos actualizando costo en products 
    y el stock en inventory.
    """
    cursor = conn.cursor()
    
    for art in articles:
        # 1. Upsert en products (Insertar o Actualizar costo y nombre)
        cursor.execute("""
            INSERT INTO products (sku, name, unit_cost)
            VALUES (%s, %s, %s)
            ON CONFLICT (sku) DO UPDATE
            SET name = EXCLUDED.name,
                unit_cost = EXCLUDED.unit_cost
            RETURNING product_id
        """, (art["sku"], art["name"], art["unit_cost"]))
        
        result = cursor.fetchone()
        
        # Fallback por si DO UPDATE no retorna el ID en algunas versiones de psycopg2
        if not result:
            cursor.execute("SELECT product_id FROM products WHERE sku = %s", (art["sku"],))
            result = cursor.fetchone()
            
        if result:
            product_id = result[0]
            
            # 2. Upsert en inventory (Actualiza el stock actual)
            cursor.execute("""
                INSERT INTO inventory (product_id, current_stock, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (product_id) DO UPDATE
                SET current_stock = EXCLUDED.current_stock,
                    updated_at = NOW()
            """, (product_id, art["current_stock"]))

    cursor.close()