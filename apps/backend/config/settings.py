from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings

# ── Cálculo Dinámico de la Ruta Raíz ──
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    anthropic_api_key: str
    llm_model_fallback: str = "claude-haiku-4-5-20251001"
    llm_max_tokens: int = 2048
    llm_timeout_seconds: int = 30

    class Config:
        # Le pasamos la ruta absoluta exacta del .env global
        env_file = str(ENV_PATH)
        env_file_encoding = "utf-8"
        
        # PRO-TIP: Como tu .env es global, seguro tendrá variables del Frontend (VITE_...) 
        # o de Docker. Esto evita que Pydantic lance un error si ve variables que no están aquí definidas:
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()