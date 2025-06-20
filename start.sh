#!/bin/bash

echo "🚀 Iniciando API Inmobiliaria en Railway..."
echo "Puerto: $PORT"
echo "Comando: gunicorn api_colaborativa:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT"

# Ejecutar la aplicación
exec gunicorn api_colaborativa:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT 