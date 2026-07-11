# 1. Usar una imagen oficial de Python ligera
FROM python:3.11-slim

# 2. Crear el directorio de trabajo
WORKDIR /app

# 3. Copiar y compilar requerimientos (Asegurarnos de que pip esté actualizado)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Copiar el resto del código del backend
COPY . .

# 5. Variable de entorno para evitar que Python genere archivos .pyc en el contenedor
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 6. Comando para arrancar FastAPI, usando el puerto dinámico de Render
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}