FROM python:3.12-slim

# Variables críticas para Railway
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Comando optimizado para Railway (usando sh -c para manejo correcto del puerto)
CMD ["sh", "-c", "gunicorn api_colaborativa:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8080} --timeout 300"] 