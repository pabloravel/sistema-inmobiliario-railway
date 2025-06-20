FROM python:3.12-slim

# Variables de entorno críticas para Railway
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código y script de inicio
COPY . .
RUN chmod +x start.sh

# Exponer puerto
EXPOSE 8080

# Usar script de inicio
CMD ["./start.sh"] 