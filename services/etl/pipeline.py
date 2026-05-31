from pathlib import Path
from parsers.csv_parser import parse_csv
from transformers.sales_transformer import transform_sales
from transformers.articles_transformer import transform_articles
from loaders.postgres_loader import get_db_connection, load_sales, load_articles
from dotenv import load_dotenv  

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(dotenv_path=BASE_DIR / ".env")

# Rutas a los archivos
SALES_CSV_FILE = BASE_DIR / "storage/raw/csv/202605.csv"
ARTICLES_CSV_FILE = BASE_DIR / "storage/raw/csv/ARTICULO.csv"

def run_pipeline():
    print("🚀 Iniciando ETL SuperDulces BI")

    # Verificación de archivos
    if not SALES_CSV_FILE.exists():
        print(f"❌ Archivo de ventas no encontrado: {SALES_CSV_FILE}")
        return
    if not ARTICLES_CSV_FILE.exists():
        print(f"❌ Archivo de artículos no encontrado: {ARTICLES_CSV_FILE}")
        return

    try:
        # Abrimos la conexión una sola vez para todo el proceso
        conn = get_db_connection()

        # =========================
        # FASE 1: MAESTRO DE ARTÍCULOS
        # =========================
        print("\n📦 [1/2] PROCESANDO MAESTRO DE ARTÍCULOS (Inventario y Costos)...")
        print(" 📥 Extrayendo CSV...")
        raw_articles = parse_csv(ARTICLES_CSV_FILE)
        
        print(" ✨ Transformando datos...")
        articles = transform_articles(raw_articles)
        print(f" ✅ Artículos listos para cargar: {len(articles)}")

        if articles:
            print(" 💾 Cargando a PostgreSQL...")
            load_articles(conn, articles)

        # =========================
        # FASE 2: TRANSACCIONES DE VENTAS
        # =========================
        print("\n🛒 [2/2] PROCESANDO TRANSACCIONES DE VENTAS...")
        print(" 📥 Extrayendo CSV...")
        raw_sales = parse_csv(SALES_CSV_FILE)
        
        print(" ✨ Transformando ventas...")
        sales = transform_sales(raw_sales)
        print(f" ✅ Ventas válidas: {len(sales)}")

        if sales:
            print(" 💾 Cargando a PostgreSQL...")
            load_sales(conn, sales)

        # Confirmamos la transacción completa
        conn.commit()
        conn.close()
        print("\n🎉 ETL finalizado correctamente en la base de datos analítica")

    except Exception as e:
        print(f"\n💥 Error ETL: {e}")
        # Aseguramos hacer rollback y cerrar la conexión en caso de error
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    run_pipeline()