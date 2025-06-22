#!/usr/bin/env python3
"""
🚀 MAIN.PY - PUNTO DE ENTRADA PARA RENDER
==========================================
"""

# CORRECCIÓN CRÍTICA APLICADA: Frontend usa proxy para imágenes S3
# Fecha: 22 junio 2025 22:15

import os
import uvicorn

def main():
    """Punto de entrada principal para Render"""
    print("🚀 Iniciando desde main.py para Render...")
    
    # Configuración del puerto para Render
    port = int(os.environ.get("PORT", 10000))
    print(f"📊 Puerto: {port}")
    print("🌐 API lista con endpoint /api/propiedades")
    print("🖼️ Proxy de imágenes S3 activado")
    
    # Importar la app después de configurar el entorno
    from api_render_completa import app
    
    # Ejecutar con configuración de producción
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main() 