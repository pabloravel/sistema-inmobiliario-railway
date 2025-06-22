#!/usr/bin/env python3
"""
🚀 MAIN.PY - PUNTO DE ENTRADA PARA RENDER
==========================================
"""

# CORRECCIÓN CRÍTICA APLICADA: Frontend usa imagenFinal para imágenes S3
# Fecha: 22 junio 2025 15:25

import os
import uvicorn

def main():
    """Punto de entrada principal para Render"""
    print("🚀 Iniciando desde main.py para Render...")
    
    # Configuración del puerto para Render
    port = int(os.environ.get("PORT", 10000))
    print(f"📊 Puerto: {port}")
    print("🌐 API lista con endpoint /api/propiedades")
    
    # Importar la app después de configurar el entorno
    from api_render_completa import app
    
    # Ejecutar con configuración de producción
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


# ===== PROXY DE IMÁGENES S3 =====
@app.get("/imagen/{imagen_path:path}")
async def proxy_imagen(imagen_path: str):
    """Proxy para servir imágenes S3 desde el mismo dominio"""
    import httpx
    
    # URL completa de S3
    s3_url = f"https://propiedades-morelos-imagenes.s3.amazonaws.com/{imagen_path}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(s3_url)
            
            if response.status_code == 200:
                return Response(
                    content=response.content,
                    media_type="image/jpeg",
                    headers={
                        "Cache-Control": "public, max-age=3600",
                        "Access-Control-Allow-Origin": "*"
                    }
                )
            else:
                # Imagen placeholder si falla
                placeholder_svg = '<svg width="300" height="200" viewBox="0 0 300 200" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="200" fill="#F3F4F6"/><text x="150" y="100" text-anchor="middle" fill="#9CA3AF" font-family="Arial" font-size="16">Sin Imagen</text></svg>'
                return Response(
                    content=placeholder_svg,
                    media_type="image/svg+xml"
                )
                
    except Exception as e:
        # Imagen placeholder en caso de error
        placeholder_svg = '<svg width="300" height="200" viewBox="0 0 300 200" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="200" fill="#F3F4F6"/><text x="150" y="100" text-anchor="middle" fill="#9CA3AF" font-family="Arial" font-size="16">Error Imagen</text></svg>'
        return Response(
            content=placeholder_svg,
            media_type="image/svg+xml"
        )


if __name__ == "__main__":
    main() 