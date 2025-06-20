#!/bin/bash

echo "🚀 Iniciando aplicación en Railway..."
echo "📊 Puerto: ${PORT:-8080}"
echo "🌐 Host: 0.0.0.0"

# Verificar que el archivo existe
if [ ! -f "api_colaborativa.py" ]; then
    echo "❌ Error: api_colaborativa.py no encontrado"
    exit 1
fi

# Iniciar con gunicorn (más estable para producción)
exec gunicorn api_colaborativa:app \
    -w 1 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8080} \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    --log-level info 