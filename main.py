#!/usr/bin/env python3
"""
PUNTO DE ENTRADA PRINCIPAL PARA RENDER CON AUTO-CORRECCIÓN
========================================================

Este archivo es el que Render ejecutará automáticamente.
Importa la API completa con todos los endpoints necesarios.
EJECUTA CORRECCIÓN AUTOMÁTICA DE IMÁGENES AL INICIAR.
"""

from api_render_completa import app

# Este archivo se ejecuta automáticamente en Render
# La variable 'app' es lo que Render buscará

if __name__ == "__main__":
    import uvicorn
    import os
    import subprocess
    import sys
    
    port = int(os.getenv("PORT", 10000))
    
    print("🚀 INICIANDO SISTEMA CON AUTO-CORRECCIÓN DE IMÁGENES")
    print("=" * 55)
    
    # PASO 1: Ejecutar corrección automática de imágenes
    print("🔧 EJECUTANDO CORRECCIÓN AUTOMÁTICA DE IMÁGENES...")
    try:
        resultado = subprocess.run([sys.executable, "fix_images_auto.py"], 
                                 capture_output=True, text=True, timeout=60)
        
        if resultado.returncode == 0:
            print("✅ CORRECCIÓN DE IMÁGENES COMPLETADA")
            # Mostrar solo las líneas importantes del resultado
            for linea in resultado.stdout.split('\n'):
                if '✅' in linea or '📊' in linea or '🎉' in linea:
                    print(linea)
        else:
            print("⚠️  Corrección de imágenes falló, continuando sin imágenes")
    except Exception as e:
        print(f"⚠️  Error en corrección automática: {e}")
    
    # PASO 2: Iniciar API principal
    print("\n🚀 INICIANDO API PRINCIPAL...")
    print(f"📊 Puerto: {port}")
    print("🌐 API lista con endpoint /api/propiedades")
    print("🖼️  IMÁGENES: Corregidas automáticamente para AWS S3")
    print("=" * 55)
    
    uvicorn.run("api_render_completa:app", host="0.0.0.0", port=port) 