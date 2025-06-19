FROM python:3.12-slim

# Metadatos
LABEL maintainer="Facebook Scraper Team"
LABEL version="1.0"
LABEL description="Facebook Property Scraper API Server"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production
ENV PORT=8000

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p /app && \
    chown -R app:app /app

# Cambiar a usuario no-root
USER app
WORKDIR /app

# Copiar requirements e instalar dependencias Python
COPY --chown=app:app requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY --chown=app:app . .

# Crear directorios necesarios
RUN mkdir -p resultados/{imagenes,json,html} \
             logs \
             cache_ia \
             datos/raw

# Hacer ejecutables los scripts
RUN chmod +x *.sh 2>/dev/null || true

# Verificar instalación
RUN python3 -c "import flask, requests, selenium; print('Dependencies OK')"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Exponer puerto
EXPOSE ${PORT}

# Comando de inicio - usar uvicorn con FastAPI
CMD ["sh", "-c", "uvicorn api_colaborativa:app --host 0.0.0.0 --port $PORT"]
