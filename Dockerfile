FROM python:3.12-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p resultados logs cache_ia datos

# Verificar instalación crítica
RUN python3 -c "import fastapi, uvicorn, gunicorn; print('✅ Dependencies OK')"

# Exponer puerto
EXPOSE ${PORT}

# Comando de inicio - usar gunicorn con workers uvicorn
CMD ["sh", "-c", "gunicorn api_colaborativa:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT"] 