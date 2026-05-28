from pathlib import Path
from parsers.csv_parser import parse_csv
from transformers.sales_transformer import transform_sales
from loaders.postgres_loader import get_db_connection, load_sales
from dotenv import load_dotenv  

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(dotenv_path=BASE_DIR / ".env")

CSV_FILE = BASE_DIR / "storage/raw/csv/202605.csv"

def run_pipeline():
    print("🚀 Iniciando ETL SuperDulces BI")

    if not CSV_FILE.exists():
        print(f"❌ Archivo no encontrado: {CSV_FILE}")
        return

    try:
        # =========================
        # EXTRACT
        # =========================
        print("📥 Extrayendo CSV...")
        raw_rows = parse_csv(CSV_FILE)
        print(f"✅ Filas extraídas: {len(raw_rows)}")

        # =========================
        # TRANSFORM
        # =========================
        print("✨ Transformando ventas...")
        sales = transform_sales(raw_rows)
        print(f"✅ Ventas válidas: {len(sales)}")

        if not sales:
            print("⚠️ No se encontraron registros de ventas válidos para cargar.")
            return

        # =========================
        # LOAD
        # =========================
        print("📦 Cargando PostgreSQL...")
        conn = get_db_connection()
        
        # load_sales ahora se encarga de la secuencia relacional completa
        load_sales(conn, sales)

        conn.commit()
        conn.close()
        print("🎉 ETL finalizado correctamente en la base de datos analítica")

    except Exception as e:
        print(f"💥 Error ETL: {e}")

if __name__ == "__main__":
    run_pipeline()