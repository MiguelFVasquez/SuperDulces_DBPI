from fastapi import FastAPI
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../.env")

app = FastAPI(title=os.getenv("PROJECT_NAME", "BI API"))

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Bienvenido al Backend de SuperDulces BI",
        "database_connected_to": os.getenv("DB_NAME")
    }