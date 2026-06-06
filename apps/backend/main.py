import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import receipts
from routers import inventory
from routers import metrics


# Configurar rutas y entorno de forma absoluta y limpia
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")



app = FastAPI(
    title=os.getenv("PROJECT_NAME", "SuperDulces BI API"),
    version="1.0.0",
    description="API Analítica para Dashboard de Inteligencia de Negocio"
)

origins = [
    "https://super-dulces-dbpi.vercel.app",  # La URL de tu Vercel
    "http://localhost:5173",                 # Para que sigas probando en local
]

# Configuración de CORS para intercomunicación con React (Vite / Next)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción puedes cambiarlo por tu host específico (ej: http://localhost:5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar las rutas analíticas
app.include_router(metrics.router) # Ruta de las metricas 
app.include_router(inventory.router) # Ruta de inventario
app.include_router(receipts.router) # Ruta de automatización de facturas
@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Bienvenido al Backend de SuperDulces BI",
        "database_connected_to": os.getenv("DB_NAME")
    }