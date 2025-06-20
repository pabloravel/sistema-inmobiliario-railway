FROM python:3.12-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production
ENV PORT=5001

# Directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

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

# Comando para ejecutar la aplicación
CMD gunicorn api_colaborativa:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 300 