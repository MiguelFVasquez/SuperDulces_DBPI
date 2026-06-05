# 1. Usar una imagen oficial de Python ligera
FROM python:3.11-slim

# 2. Instalar Ghostscript y la dependencia gráfica actualizada (libgl1)
RUN apt-get update && apt-get install -y \
    ghostscript \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# 3. Crear el directorio de trabajo
WORKDIR /app

# 4. Copiar los requerimientos e instalarlos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto del código del backend
COPY . .

# 6. Comando para arrancar FastAPI, usando el puerto dinámico de Render
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}