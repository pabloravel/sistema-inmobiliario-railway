#!/usr/bin/env python3
"""
API COMPLETA PARA RENDER - CON TODAS LAS FUNCIONALIDADES
=======================================================

Esta API incluye:
✅ Endpoint /api/propiedades (compatible con frontend)
✅ Endpoint /estadisticas (ya funciona)
✅ Conexión PostgreSQL a Render
✅ CORS habilitado
✅ Configuración para puerto variable de Render
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from datetime import datetime
import time
import os

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la aplicación
app = FastAPI(
    title="API Inmobiliaria Render",
    description="Sistema inmobiliario completo para Render",
    version="1.0.0 - RENDER COMPLETO"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de base de datos para Render
DATABASE_URL = os.getenv('DATABASE_URL', 
    'postgresql://propiedades_db_user:UT9bFWvDMydVGtBj2evsNlB2xYO9fzbC@dpg-d1aothp5pdvs73d4kahg-a.oregon-postgres.render.com/propiedades_db')

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        if DATABASE_URL.startswith('postgresql://'):
            # Conexión directa con URL
            conn = psycopg2.connect(DATABASE_URL)
        else:
            # Configuración manual (fallback)
            conn = psycopg2.connect(
                host='dpg-d1aothp5pdvs73d4kahg-a.oregon-postgres.render.com',
                database='propiedades_db',
                user='propiedades_db_user',
                password='UT9bFWvDMydVGtBj2evsNlB2xYO9fzbC',
                port=5432
            )
        return conn
    except Exception as e:
        logger.error(f"Error conectando a BD: {e}")
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")

def ejecutar_consulta(query: str, params=None, fetchall=True):
    """Ejecutar consulta y retornar resultados con tiempo"""
    start_time = time.time()
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params or ())
        
        if fetchall:
            result = cursor.fetchall()
        else:
            result = cursor.fetchone()
            
        conn.close()
        elapsed_time = (time.time() - start_time) * 1000
        return result, elapsed_time
    except Exception as e:
        logger.error(f"Error en consulta: {e}")
        raise HTTPException(status_code=500, detail=f"Error en consulta: {str(e)}")

# =====================================================
# MODELOS PYDANTIC
# =====================================================

class PropiedadResumen(BaseModel):
    id: str
    titulo: str
    descripcion: Optional[str]
    precio: Optional[float]
    ciudad: str
    tipo_operacion: str
    tipo_propiedad: Optional[str]
    imagen_url: Optional[str]
    direccion: Optional[str]
    estado: Optional[str]
    link: Optional[str]
    recamaras: Optional[int]
    banos: Optional[int]
    estacionamientos: Optional[int]
    superficie_m2: Optional[int]

class RespuestaPaginada(BaseModel):
    propiedades: List[PropiedadResumen]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int
    tiempo_consulta_ms: float

class Estadisticas(BaseModel):
    total_propiedades: int
    con_precio: int
    precio_promedio: float
    precio_minimo: float
    precio_maximo: float
    tipos_operacion: Dict[str, int]
    tiempo_consulta_ms: float

# =====================================================
# FUNCIONES AUXILIARES
# =====================================================

def generar_url_imagen(nombre_imagen: str) -> str:
    """Generar URL completa para imagen de AWS S3"""
    if not nombre_imagen or nombre_imagen == 'null' or 'imagen_no_disponible' in nombre_imagen:
        return "https://via.placeholder.com/300x200?text=Sin+Imagen"
    
    # Si ya es URL completa de S3, devolverla
    if nombre_imagen.startswith('http') and 's3.amazonaws.com' in nombre_imagen:
        return nombre_imagen
    
    # Si es URL completa pero no S3, usar placeholder
    if nombre_imagen.startswith('http'):
        return "https://via.placeholder.com/300x200?text=Sin+Imagen"
    
    # Para nombres locales, convertir a URL S3
    # Formato esperado: cuernavaca-2025-06-09-1234567890.jpg
    if '-' in nombre_imagen and '2025-' in nombre_imagen:
        partes = nombre_imagen.split('-')
        if len(partes) >= 4:
            try:
                # Extraer fecha del nombre: ciudad-2025-06-09-id.jpg
                fecha = f"{partes[1]}-{partes[2]}-{partes[3]}"
                return f"https://propiedades-morelos-imagenes.s3.amazonaws.com/{fecha}/{nombre_imagen}"
            except:
                pass
    
    # Si no se puede procesar, usar placeholder
    return "https://via.placeholder.com/300x200?text=Sin+Imagen"

# =====================================================
# ENDPOINTS PRINCIPALES
# =====================================================

@app.get("/")
def root():
    return {"mensaje": "API Inmobiliaria Render", "version": "1.0.0", "propiedades": True}

@app.get("/health")
def health_check():
    return {"status": "ok", "database": "connected", "render": True}

@app.get("/estadisticas", response_model=Estadisticas)
async def obtener_estadisticas():
    """Obtener estadísticas generales del sistema"""
    
    # Consulta de estadísticas
    query_stats = """
    SELECT 
        COUNT(*) as total_propiedades,
        COUNT(CASE WHEN precio > 0 THEN 1 END) as con_precio,
        COALESCE(AVG(CASE WHEN precio > 0 THEN precio END), 0) as precio_promedio,
        COALESCE(MIN(CASE WHEN precio > 0 THEN precio END), 0) as precio_minimo,
        COALESCE(MAX(CASE WHEN precio > 0 THEN precio END), 0) as precio_maximo
    FROM propiedades 
    WHERE activo = true
    """
    
    # Consulta tipos de operación
    query_tipos = """
    SELECT tipo_operacion, COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true
    GROUP BY tipo_operacion
    ORDER BY cantidad DESC
    """
    
    stats, tiempo_ms1 = ejecutar_consulta(query_stats, fetchall=False)
    tipos, tiempo_ms2 = ejecutar_consulta(query_tipos, fetchall=True)
    
    # Procesar tipos de operación
    tipos_dict = {}
    for tipo in tipos:
        tipos_dict[tipo['tipo_operacion']] = tipo['cantidad']
    
    return Estadisticas(
        total_propiedades=stats['total_propiedades'],
        con_precio=stats['con_precio'],
        precio_promedio=float(stats['precio_promedio']) if stats['precio_promedio'] else 0,
        precio_minimo=float(stats['precio_minimo']) if stats['precio_minimo'] else 0,
        precio_maximo=float(stats['precio_maximo']) if stats['precio_maximo'] else 0,
        tipos_operacion=tipos_dict,
        tiempo_consulta_ms=tiempo_ms1 + tiempo_ms2
    )

@app.get("/propiedades", response_model=RespuestaPaginada)
async def listar_propiedades(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(60, ge=1, le=100, description="Propiedades por página"),
    operaciones: Optional[str] = Query(None, description="Filtrar por tipos de operación (separados por coma)"),
    ciudades: Optional[str] = Query(None, description="Filtrar por ciudades (separadas por coma)"),
    tipos: Optional[str] = Query(None, description="Filtrar por tipos de propiedad (separados por coma)"),
    precio_min: Optional[float] = Query(1, description="Precio mínimo"),
    precio_max: Optional[float] = Query(None, description="Precio máximo"),
    q: Optional[str] = Query(None, description="Búsqueda por texto"),
):
    """Listar propiedades con filtros y paginación"""
    
    # Construir WHERE clause
    where_conditions = ["activo = true"]
    params = []
    
    # Filtro de precio mínimo por defecto
    if precio_min and precio_min > 0:
        where_conditions.append("precio >= %s")
        params.append(precio_min)
    
    if precio_max:
        where_conditions.append("precio <= %s")
        params.append(precio_max)
    
    if operaciones:
        ops_list = [op.strip() for op in operaciones.split(',')]
        placeholders = ','.join(['%s'] * len(ops_list))
        where_conditions.append(f"tipo_operacion IN ({placeholders})")
        params.extend(ops_list)
    
    if ciudades:
        ciudades_list = [c.strip() for c in ciudades.split(',')]
        placeholders = ','.join(['%s'] * len(ciudades_list))
        where_conditions.append(f"ciudad IN ({placeholders})")
        params.extend(ciudades_list)
    
    if tipos:
        tipos_list = [t.strip() for t in tipos.split(',')]
        placeholders = ','.join(['%s'] * len(tipos_list))
        where_conditions.append(f"tipo_propiedad IN ({placeholders})")
        params.extend(tipos_list)
    
    if q:
        where_conditions.append("(titulo ILIKE %s OR descripcion ILIKE %s OR ciudad ILIKE %s)")
        search_term = f"%{q}%"
        params.extend([search_term, search_term, search_term])
    
    where_clause = " AND ".join(where_conditions)
    
    # Consulta principal con paginación
    offset = (pagina - 1) * por_pagina
    
    query_propiedades = f"""
    SELECT 
        id, titulo, descripcion, precio, ciudad, tipo_operacion, tipo_propiedad,
        direccion, estado, link, imagen,
        recamaras, banos, estacionamientos, superficie_m2
    FROM propiedades 
    WHERE {where_clause}
    ORDER BY 
        CASE WHEN precio > 0 THEN 0 ELSE 1 END,
        precio DESC NULLS LAST,
        created_at DESC
    LIMIT %s OFFSET %s
    """
    
    query_total = f"SELECT COUNT(*) as total FROM propiedades WHERE {where_clause}"
    
    # Ejecutar consultas
    propiedades_data, tiempo_ms1 = ejecutar_consulta(query_propiedades, params + [por_pagina, offset])
    total_data, tiempo_ms2 = ejecutar_consulta(query_total, params, fetchall=False)
    
    total = total_data['total']
    total_paginas = (total + por_pagina - 1) // por_pagina
    
    # Procesar propiedades
    propiedades = []
    for prop in propiedades_data:
        prop_dict = dict(prop)
        
        # Generar URL de imagen
        if prop_dict.get('imagen'):
            prop_dict['imagen_url'] = generar_url_imagen(prop_dict['imagen'])
        else:
            prop_dict['imagen_url'] = generar_url_imagen('')
        
        # Convertir Decimal a float
        if prop_dict.get('precio'):
            prop_dict['precio'] = float(prop_dict['precio'])
        
        propiedades.append(PropiedadResumen(**prop_dict))
    
    return RespuestaPaginada(
        propiedades=propiedades,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=total_paginas,
        tiempo_consulta_ms=tiempo_ms1 + tiempo_ms2
    )

# =====================================================
# ENDPOINT COMPATIBILIDAD FRONTEND
# =====================================================

@app.get("/api/propiedades", response_model=RespuestaPaginada)
async def api_propiedades_compatibilidad(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(60, ge=1, le=100),
    operaciones: Optional[str] = Query(None),
    ciudades: Optional[str] = Query(None),
    tipos: Optional[str] = Query(None),
    precio_min: Optional[float] = Query(1),
    precio_max: Optional[float] = Query(None),
    q: Optional[str] = Query(None),
):
    """Endpoint de compatibilidad con frontend actual - REDIRIGE A PRINCIPAL"""
    return await listar_propiedades(
        pagina=pagina,
        por_pagina=por_pagina,
        operaciones=operaciones,
        ciudades=ciudades,
        tipos=tipos,
        precio_min=precio_min,
        precio_max=precio_max,
        q=q
    )

# =====================================================
# INICIAR APLICACIÓN
# =====================================================

if __name__ == "__main__":
    import uvicorn
    
    # Puerto de Render o puerto local
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🚀 Iniciando aplicación en Render...")
    print(f"📊 Puerto: {port}")
    print(f"🌐 Host: {host}")
    
    uvicorn.run(app, host=host, port=port) 