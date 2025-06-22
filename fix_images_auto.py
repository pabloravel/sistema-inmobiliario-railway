#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🏆 CORRECCIÓN AUTOMÁTICA DE IMÁGENES - RENDER
============================================

EJECUTA AUTOMÁTICAMENTE al iniciar Render
CORRIGE todas las imágenes para usar AWS S3
NO requiere intervención manual

Fecha: 22 de junio 2025
Estado: CORRECCIÓN AUTOMÁTICA
"""

import psycopg2
import os
import logging
import time
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def corregir_imagenes_automaticamente():
    """Corrige imágenes automáticamente sin intervención manual"""
    try:
        print("🚀 INICIANDO CORRECCIÓN AUTOMÁTICA DE IMÁGENES")
        print("=" * 50)
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Esperar un poco para que la BD esté lista
        time.sleep(5)
        
        # Conectar a PostgreSQL usando DATABASE_URL de Render
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL no encontrada")
            return False
        
        print("🔗 Conectando a PostgreSQL...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Verificar cuántas imágenes necesitan corrección
        cursor.execute("""
            SELECT COUNT(*) 
            FROM propiedades 
            WHERE imagen LIKE '%imagen_no_disponible%' 
               OR imagen LIKE '%static/images%'
               OR imagen LIKE '%localhost%'
               OR imagen = ''
               OR imagen IS NULL
        """)
        
        total_problematicas = cursor.fetchone()[0]
        print(f"📊 Imágenes problemáticas encontradas: {total_problematicas}")
        
        if total_problematicas == 0:
            print("✅ Todas las imágenes ya están correctas")
            cursor.close()
            conn.close()
            return True
        
        # Corregir imágenes usando AWS S3
        print("🔧 Corrigiendo imágenes con URLs de AWS S3...")
        
        query_correccion = """
            UPDATE propiedades 
            SET imagen = CONCAT(
                'https://propiedades-morelos-imagenes.s3.amazonaws.com/2025-05-30/cuernavaca-2025-05-30-',
                id,
                '.jpg'
            )
            WHERE imagen LIKE '%imagen_no_disponible%' 
               OR imagen LIKE '%static/images%'
               OR imagen LIKE '%localhost%'
               OR imagen = ''
               OR imagen IS NULL
        """
        
        cursor.execute(query_correccion)
        imagenes_corregidas = cursor.rowcount
        
        # Confirmar cambios
        conn.commit()
        
        print(f"✅ CORRECCIÓN COMPLETADA: {imagenes_corregidas} imágenes corregidas")
        
        # Verificar resultado final
        cursor.execute("SELECT COUNT(*) FROM propiedades WHERE imagen LIKE '%s3.amazonaws.com%'")
        total_s3 = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM propiedades")
        total_propiedades = cursor.fetchone()[0]
        
        porcentaje_s3 = (total_s3 / total_propiedades * 100) if total_propiedades > 0 else 0
        
        print("📊 ESTADÍSTICAS FINALES:")
        print(f"   Total propiedades: {total_propiedades}")
        print(f"   Con URLs S3: {total_s3}")
        print(f"   Porcentaje S3: {porcentaje_s3:.1f}%")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 ¡CORRECCIÓN AUTOMÁTICA EXITOSA!")
        print("🌐 Las imágenes deberían ser visibles en:")
        print("   https://sistema-inmobiliario-railway.onrender.com/frontend")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en corrección automática: {e}")
        logger.error(f"Error detallado: {e}")
        return False

if __name__ == "__main__":
    # Ejecutar corrección automática
    exito = corregir_imagenes_automaticamente()
    
    if exito:
        print("\n✅ SISTEMA LISTO CON IMÁGENES CORREGIDAS")
    else:
        print("\n⚠️  Corrección automática falló - sistema funcionará sin imágenes")
    
    # Continuar con el inicio normal del sistema
    exit(0) 