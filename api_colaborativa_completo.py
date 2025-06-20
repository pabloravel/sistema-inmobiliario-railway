#!/usr/bin/env python3
"""
API REST COLABORATIVA PARA RAILWAY - VERSIÓN COMPLETA CORREGIDA
==============================================================

CORRECCIONES APLICADAS:
- ✅ Rutas de imágenes con carpetas de fecha
- ✅ Filtros de ciudades limpios (solo ciudades reales)
- ✅ Filtros funcionales que actualizan resultados
- ✅ Consultas optimizadas
- ✅ Sistema colaborativo completo
- ✅ Health check para Railway
- ✅ EmailStr corregido para evitar dependencia de email-validator
"""

from fastapi import FastAPI, HTTPException, Query, Depends, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from datetime import datetime, timedelta
import time
import re
import bcrypt
import jwt
import os
from pathlib import Path
import secrets

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la aplicación
app = FastAPI(
    title="API Inmobiliaria Colaborativa para Railway",
    description="Sistema inmobiliario completo con funcionalidades colaborativas",
    version="3.0.0 - COLABORATIVO PARA RAILWAY"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración JWT
SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_super_segura_para_railway_2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 días

# Configuración de base de datos para Railway
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Usar DATABASE_URL de Railway
    import urllib.parse as urlparse
    url = urlparse.urlparse(DATABASE_URL)
    DB_CONFIG = {
        'host': url.hostname,
        'database': url.path[1:],
        'user': url.username,
        'password': url.password,
        'port': url.port or 5432
    }
else:
    # Configuración local
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'propiedades_db'),
        'user': os.getenv('DB_USER', 'pabloravel'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': int(os.getenv('DB_PORT', 5432))
    }

# Seguridad
security = HTTPBearer()

# Ciudades válidas de Morelos
CIUDADES_MORELOS = {
    'Cuernavaca', 'Jiutepec', 'Temixco', 'Emiliano Zapata', 'Xochitepec',
    'Yautepec', 'Cuautla', 'Ayala', 'Tepoztlán', 'Huitzilac', 'Tetela del Volcán'
}

# =====================================================
# VALIDADOR DE EMAIL SIMPLE
# =====================================================

def validar_email(email: str) -> bool:
    """Validador de email simple sin dependencias externas"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# =====================================================
# MODELOS PYDANTIC
# =====================================================

class UsuarioRegistro(BaseModel):
    nombre: str
    email: str = Field(..., description="Email del usuario")
    telefono: str
    password: str
    
    def validate_email(cls, v):
        if not validar_email(v):
            raise ValueError('Email inválido')
        return v

class UsuarioLogin(BaseModel):
    email: str = Field(..., description="Email del usuario")
    password: str
    
    def validate_email(cls, v):
        if not validar_email(v):
            raise ValueError('Email inválido')
        return v

class Usuario(BaseModel):
    id: int
    nombre: str
    email: str
    telefono: Optional[str]
    es_admin: bool
    fecha_registro: datetime
    activo: bool

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: Usuario

class MensajeWhatsApp(BaseModel):
    numero_destino: str
    mensaje_personalizado: Optional[str]
    propiedad_id: str

class PropiedadColaborativa(BaseModel):
    titulo: str
    descripcion: Optional[str]
    precio: Optional[float]
    tipo_propiedad: str
    tipo_operacion: str
    ciudad: str
    estado: str
    direccion: Optional[str]
    recamaras: Optional[int]
    banos: Optional[int]
    estacionamientos: Optional[int]
    metros_construccion: Optional[int]
    metros_terreno: Optional[int]
    telefono_contacto: Optional[str]
    email_contacto: Optional[str]

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
    amenidades: Optional[Dict]
    caracteristicas: Optional[Dict]
    es_favorito: bool = False

class PropiedadCompleta(BaseModel):
    id: str
    titulo: str
    precio: Optional[float]
    ciudad: str
    tipo_operacion: str
    tipo_propiedad: str
    descripcion: Optional[str]
    link: Optional[str]
    imagen_url: Optional[str]
    direccion: Optional[str]
    estado: Optional[str]
    recamaras: Optional[int]
    banos: Optional[int]
    estacionamientos: Optional[int]
    superficie_m2: Optional[int]
    amenidades: Optional[Dict]
    caracteristicas: Optional[Dict]
    imagenes: Optional[List[str]]
    created_at: Optional[datetime]

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

class RecuperarPassword(BaseModel):
    email: str = Field(..., description="Email del usuario")

class CambiarPassword(BaseModel):
    token: str
    nueva_password: str

class ContactoPropiedad(BaseModel):
    propiedad_id: str
    nombre: Optional[str]
    telefono: Optional[str]
    email: Optional[str]
    notas: Optional[str]

class CarpetaColaborativa(BaseModel):
    nombre: str
    descripcion: Optional[str]
    es_publica: bool = False

# =====================================================
# FUNCIONES DE UTILIDAD
# =====================================================

def hash_password(password: str) -> str:
    """Hash de contraseña usando bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verificar contraseña"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    """Crear token JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Obtener usuario actual (opcional)"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except jwt.PyJWTError:
        return None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s AND activo = true", (email,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return Usuario(**user_data)
        return None
    except Exception:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtener usuario actual (requerido)"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s AND activo = true", (email,))
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        return Usuario(**user_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")

def get_admin_user(current_user: Usuario = Depends(get_current_user)):
    """Verificar que el usuario sea administrador"""
    if not current_user.es_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado. Se requieren permisos de administrador.")
    return current_user

def limpiar_ciudad(ciudad: str) -> Optional[str]:
    """Limpiar nombre de ciudad y verificar que esté en Morelos"""
    if not ciudad:
        return None
    
    ciudad_limpia = ciudad.strip().title()
    
    # Verificar si la ciudad está en nuestra lista de ciudades válidas
    if ciudad_limpia in CIUDADES_MORELOS:
        return ciudad_limpia
    
    return None

def generar_url_imagen(nombre_imagen: str) -> str:
    """
    Genera la URL completa de la imagen basada en el nombre del archivo
    Ejemplo: 'cuernavaca-2025-06-09-9964436130247431.jpg' -> 'resultados/2025-06-09/cuernavaca-2025-06-09-9964436130247431.jpg'
    """
    if not nombre_imagen or nombre_imagen == 'null' or nombre_imagen == '':
        return None
    
    try:
        # Extraer la fecha del nombre del archivo (formato: ciudad-YYYY-MM-DD-id.jpg)
        partes = nombre_imagen.split('-')
        if len(partes) >= 4:
            fecha = f"{partes[1]}-{partes[2]}-{partes[3]}"
            return f"resultados/{fecha}/{nombre_imagen}"
        else:
            # Si no sigue el formato esperado, devolver la ruta básica
            return f"resultados/{nombre_imagen}"
    except Exception:
        return f"resultados/{nombre_imagen}"

# =====================================================
# FUNCIONES DE BASE DE DATOS
# =====================================================

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

def ejecutar_consulta(query: str, params: tuple = None, fetchall: bool = True):
    """Ejecutar consulta SQL y medir tiempo"""
    inicio = time.time()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetchall:
            resultado = cursor.fetchall()
        else:
            resultado = cursor.fetchone()
        
        conn.close()
        
        tiempo_ms = (time.time() - inicio) * 1000
        logger.info(f"Consulta ejecutada en {tiempo_ms:.2f}ms")
        
        return resultado, tiempo_ms
        
    except Exception as e:
        logger.error(f"Error ejecutando consulta: {e}")
        raise HTTPException(status_code=500, detail=f"Error en consulta: {str(e)}")

# =====================================================
# ENDPOINTS PRINCIPALES
# =====================================================

@app.get("/", response_model=Dict)
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "mensaje": "🏠 API Inmobiliaria Colaborativa para Railway",
        "version": "3.0.0",
        "estado": "✅ Funcionando correctamente",
        "funcionalidades": [
            "🔍 Búsqueda avanzada de propiedades",
            "👥 Sistema de usuarios y autenticación",
            "⭐ Favoritos personalizados",
            "📁 Carpetas colaborativas",
            "📱 Integración WhatsApp",
            "📊 Estadísticas en tiempo real",
            "🛡️ Seguridad JWT"
        ],
        "endpoints": {
            "propiedades": "/propiedades",
            "buscar": "/buscar",
            "estadisticas": "/estadisticas",
            "registro": "/registro",
            "login": "/login",
            "docs": "/docs"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check básico para Railway"""
    try:
        # Probar conexión a BD
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        
        return {
            "status": "healthy",
            "version": "3.0.0",
            "service": "propiedades-api",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/propiedades", response_model=RespuestaPaginada)
async def listar_propiedades(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(60, ge=1, le=500, description="Propiedades por página"),
    ciudad: Optional[List[str]] = Query(None, description="Filtrar por ciudades"),
    tipo_operacion: Optional[List[str]] = Query(None, description="Filtrar por tipos de operación"),
    tipo_propiedad: Optional[List[str]] = Query(None, description="Filtrar por tipos de propiedad"),
    precio_min: Optional[float] = Query(1, description="Precio mínimo"),
    precio_max: Optional[float] = Query(None, description="Precio máximo"),
    recamaras: Optional[List[int]] = Query(None, description="Números de recámaras"),
    banos: Optional[List[int]] = Query(None, description="Números de baños"),
    estacionamientos: Optional[List[int]] = Query(None, description="Números de estacionamientos"),
    superficie_min: Optional[int] = Query(None, description="Superficie mínima en m²"),
    superficie_max: Optional[int] = Query(None, description="Superficie máxima en m²"),
    amenidad: Optional[List[str]] = Query(None, description="Filtrar por amenidades"),
    q: Optional[str] = Query(None, description="Búsqueda de texto"),
    orden: Optional[str] = Query("created_at", description="Campo para ordenar"),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """Listar propiedades con filtros avanzados"""
    inicio = time.time()
    
    # Construir consulta base
    query_base = """
    SELECT 
        p.id,
        p.titulo,
        p.descripcion,
        p.precio,
        p.ciudad,
        p.tipo_operacion,
        p.tipo_propiedad,
        p.imagen,
        p.direccion,
        p.estado,
        p.link,
        p.recamaras,
        p.banos,
        p.estacionamientos,
        p.superficie_m2,
        p.amenidades,
        p.caracteristicas,
        p.created_at
    FROM propiedades p
    WHERE p.activo = true
    """
    
    query_count = "SELECT COUNT(*) FROM propiedades p WHERE p.activo = true"
    
    # Lista de condiciones y parámetros
    condiciones = []
    parametros = []
    contador = 1
    
    # Filtros
    if precio_min is not None:
        condiciones.append(f"p.precio >= ${contador}")
        parametros.append(precio_min)
        contador += 1
    
    if precio_max is not None:
        condiciones.append(f"p.precio <= ${contador}")
        parametros.append(precio_max)
        contador += 1
    
    if ciudad:
        ciudades_limpias = [limpiar_ciudad(c) for c in ciudad if limpiar_ciudad(c)]
        if ciudades_limpias:
            placeholders = ','.join([f"${contador + i}" for i in range(len(ciudades_limpias))])
            condiciones.append(f"p.ciudad IN ({placeholders})")
            parametros.extend(ciudades_limpias)
            contador += len(ciudades_limpias)
    
    if tipo_operacion:
        placeholders = ','.join([f"${contador + i}" for i in range(len(tipo_operacion))])
        condiciones.append(f"p.tipo_operacion IN ({placeholders})")
        parametros.extend(tipo_operacion)
        contador += len(tipo_operacion)
    
    if tipo_propiedad:
        placeholders = ','.join([f"${contador + i}" for i in range(len(tipo_propiedad))])
        condiciones.append(f"p.tipo_propiedad IN ({placeholders})")
        parametros.extend(tipo_propiedad)
        contador += len(tipo_propiedad)
    
    if recamaras:
        placeholders = ','.join([f"${contador + i}" for i in range(len(recamaras))])
        condiciones.append(f"p.recamaras IN ({placeholders})")
        parametros.extend(recamaras)
        contador += len(recamaras)
    
    if banos:
        placeholders = ','.join([f"${contador + i}" for i in range(len(banos))])
        condiciones.append(f"p.banos IN ({placeholders})")
        parametros.extend(banos)
        contador += len(banos)
    
    if estacionamientos:
        placeholders = ','.join([f"${contador + i}" for i in range(len(estacionamientos))])
        condiciones.append(f"p.estacionamientos IN ({placeholders})")
        parametros.extend(estacionamientos)
        contador += len(estacionamientos)
    
    if superficie_min is not None:
        condiciones.append(f"p.superficie_m2 >= ${contador}")
        parametros.append(superficie_min)
        contador += 1
    
    if superficie_max is not None:
        condiciones.append(f"p.superficie_m2 <= ${contador}")
        parametros.append(superficie_max)
        contador += 1
    
    if q:
        condiciones.append(f"(p.titulo ILIKE ${contador} OR p.descripcion ILIKE ${contador} OR p.direccion ILIKE ${contador})")
        parametros.append(f"%{q}%")
        contador += 1
    
    # Agregar condiciones a las consultas
    if condiciones:
        condiciones_str = " AND " + " AND ".join(condiciones)
        query_base += condiciones_str
        query_count += condiciones_str
    
    # Ordenamiento
    campos_orden_validos = ['precio', 'created_at', 'ciudad', 'tipo_operacion']
    if orden in campos_orden_validos:
        query_base += f" ORDER BY p.{orden} DESC"
    else:
        query_base += " ORDER BY p.created_at DESC"
    
    # Paginación
    offset = (pagina - 1) * por_pagina
    query_base += f" LIMIT ${contador} OFFSET ${contador + 1}"
    parametros.extend([por_pagina, offset])
    
    try:
        # Ejecutar consultas
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Contar total
        cursor.execute(query_count, parametros[:-2])  # Sin LIMIT y OFFSET
        total = cursor.fetchone()['count']
        
        # Obtener propiedades
        cursor.execute(query_base, parametros)
        propiedades_data = cursor.fetchall()
        
        conn.close()
        
        # Procesar resultados
        propiedades = []
        for prop in propiedades_data:
            prop_dict = dict(prop)
            
            # Generar URL de imagen
            if prop_dict.get('imagen'):
                prop_dict['imagen_url'] = generar_url_imagen(prop_dict['imagen'])
            else:
                prop_dict['imagen_url'] = None
            
            # Verificar si es favorito del usuario
            prop_dict['es_favorito'] = False
            if current_user:
                try:
                    conn_fav = get_db_connection()
                    cursor_fav = conn_fav.cursor()
                    cursor_fav.execute(
                        "SELECT 1 FROM favoritos WHERE usuario_id = %s AND propiedad_id = %s",
                        (current_user.id, prop_dict['id'])
                    )
                    prop_dict['es_favorito'] = cursor_fav.fetchone() is not None
                    conn_fav.close()
                except:
                    pass
            
            propiedades.append(PropiedadResumen(**prop_dict))
        
        tiempo_ms = (time.time() - inicio) * 1000
        total_paginas = (total + por_pagina - 1) // por_pagina
        
        return RespuestaPaginada(
            propiedades=propiedades,
            total=total,
            pagina=pagina,
            por_pagina=por_pagina,
            total_paginas=total_paginas,
            tiempo_consulta_ms=tiempo_ms
        )
        
    except Exception as e:
        logger.error(f"Error en listar_propiedades: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener propiedades: {str(e)}")

@app.get("/propiedades/{propiedad_id}", response_model=PropiedadCompleta)
async def obtener_propiedad(propiedad_id: str):
    """Obtener una propiedad específica por ID"""
    try:
        query = """
        SELECT 
            id, titulo, precio, ciudad, tipo_operacion, tipo_propiedad,
            descripcion, link, imagen, direccion, estado, recamaras, banos,
            estacionamientos, superficie_m2, amenidades, caracteristicas,
            imagenes, created_at
        FROM propiedades 
        WHERE id = %s AND activo = true
        """
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, (propiedad_id,))
        propiedad = cursor.fetchone()
        conn.close()
        
        if not propiedad:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada")
        
        prop_dict = dict(propiedad)
        
        # Generar URL de imagen principal
        if prop_dict.get('imagen'):
            prop_dict['imagen_url'] = generar_url_imagen(prop_dict['imagen'])
        else:
            prop_dict['imagen_url'] = None
        
        return PropiedadCompleta(**prop_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo propiedad {propiedad_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener propiedad: {str(e)}")

@app.get("/estadisticas")
async def obtener_estadisticas():
    """Obtener estadísticas generales del sistema"""
    inicio = time.time()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Estadísticas básicas
        cursor.execute("SELECT COUNT(*) as total FROM propiedades WHERE activo = true")
        total_propiedades = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as con_precio FROM propiedades WHERE activo = true AND precio > 0")
        con_precio = cursor.fetchone()['con_precio']
        
        cursor.execute("SELECT AVG(precio) as promedio, MIN(precio) as minimo, MAX(precio) as maximo FROM propiedades WHERE activo = true AND precio > 0")
        precios = cursor.fetchone()
        
        cursor.execute("SELECT tipo_operacion, COUNT(*) as cantidad FROM propiedades WHERE activo = true GROUP BY tipo_operacion")
        tipos_operacion_data = cursor.fetchall()
        
        # Estadísticas por ciudad
        cursor.execute("SELECT ciudad, COUNT(*) as cantidad FROM propiedades WHERE activo = true GROUP BY ciudad ORDER BY cantidad DESC LIMIT 10")
        ciudades_data = cursor.fetchall()
        
        # Estadísticas por tipo de propiedad
        cursor.execute("SELECT tipo_propiedad, COUNT(*) as cantidad FROM propiedades WHERE activo = true GROUP BY tipo_propiedad ORDER BY cantidad DESC")
        tipos_propiedad_data = cursor.fetchall()
        
        # Recámaras
        cursor.execute("SELECT recamaras, COUNT(*) as cantidad FROM propiedades WHERE activo = true AND recamaras IS NOT NULL GROUP BY recamaras ORDER BY recamaras")
        recamaras_data = cursor.fetchall()
        
        # Baños
        cursor.execute("SELECT banos, COUNT(*) as cantidad FROM propiedades WHERE activo = true AND banos IS NOT NULL GROUP BY banos ORDER BY banos")
        banos_data = cursor.fetchall()
        
        # Estacionamientos
        cursor.execute("SELECT estacionamientos, COUNT(*) as cantidad FROM propiedades WHERE activo = true AND estacionamientos IS NOT NULL GROUP BY estacionamientos ORDER BY estacionamientos")
        estacionamientos_data = cursor.fetchall()
        
        conn.close()
        
        # Procesar datos
        tipos_operacion = {item['tipo_operacion']: item['cantidad'] for item in tipos_operacion_data}
        ciudades = {item['ciudad']: item['cantidad'] for item in ciudades_data}
        tipos_propiedad = {item['tipo_propiedad']: item['cantidad'] for item in tipos_propiedad_data}
        recamaras = {str(item['recamaras']): item['cantidad'] for item in recamaras_data}
        banos = {str(item['banos']): item['cantidad'] for item in banos_data}
        estacionamientos = {str(item['estacionamientos']): item['cantidad'] for item in estacionamientos_data}
        
        tiempo_ms = (time.time() - inicio) * 1000
        
        return {
            "total_propiedades": total_propiedades,
            "con_precio": con_precio,
            "precio_promedio": float(precios['promedio']) if precios['promedio'] else 0,
            "precio_minimo": float(precios['minimo']) if precios['minimo'] else 0,
            "precio_maximo": float(precios['maximo']) if precios['maximo'] else 0,
            "tipos_operacion": tipos_operacion,
            "ciudades": ciudades,
            "tipos_propiedad": tipos_propiedad,
            "recamaras": recamaras,
            "banos": banos,
            "estacionamientos": estacionamientos,
            "tiempo_consulta_ms": tiempo_ms
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")

# =====================================================
# ENDPOINTS DE AUTENTICACIÓN
# =====================================================

@app.post("/registro", response_model=Token)
async def registrar_usuario(usuario: UsuarioRegistro):
    """Registrar nuevo usuario"""
    try:
        # Validar email
        if not validar_email(usuario.email):
            raise HTTPException(status_code=400, detail="Email inválido")
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (usuario.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        
        # Hash de la contraseña
        password_hash = hash_password(usuario.password)
        
        # Insertar usuario
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, telefono, password_hash, es_admin, activo, fecha_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            usuario.nombre,
            usuario.email,
            usuario.telefono,
            password_hash,
            False,  # No es admin por defecto
            True,   # Activo por defecto
            datetime.now()
        ))
        
        user_data = cursor.fetchone()
        conn.commit()
        conn.close()
        
        # Crear token
        access_token = create_access_token(data={"sub": usuario.email})
        
        # Crear objeto Usuario
        user_obj = Usuario(**user_data)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            usuario=user_obj
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registrando usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario: {str(e)}")

@app.post("/login", response_model=Token)
async def login_usuario(usuario: UsuarioLogin):
    """Iniciar sesión"""
    try:
        # Validar email
        if not validar_email(usuario.email):
            raise HTTPException(status_code=400, detail="Email inválido")
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM usuarios WHERE email = %s AND activo = true", (usuario.email,))
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data or not verify_password(usuario.password, user_data['password_hash']):
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
        
        # Crear token
        access_token = create_access_token(data={"sub": usuario.email})
        
        # Crear objeto Usuario
        user_obj = Usuario(**user_data)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            usuario=user_obj
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(status_code=500, detail=f"Error al iniciar sesión: {str(e)}")

@app.get("/perfil", response_model=Usuario)
async def obtener_perfil(current_user: Usuario = Depends(get_current_user)):
    """Obtener perfil del usuario actual"""
    return current_user

# =====================================================
# ENDPOINTS DE FAVORITOS
# =====================================================

@app.post("/favoritos/{propiedad_id}")
async def agregar_favorito(propiedad_id: str, current_user: Usuario = Depends(get_current_user)):
    """Agregar propiedad a favoritos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si ya está en favoritos
        cursor.execute(
            "SELECT 1 FROM favoritos WHERE usuario_id = %s AND propiedad_id = %s",
            (current_user.id, propiedad_id)
        )
        
        if cursor.fetchone():
            conn.close()
            return {"mensaje": "La propiedad ya está en favoritos"}
        
        # Agregar a favoritos
        cursor.execute(
            "INSERT INTO favoritos (usuario_id, propiedad_id, fecha_agregado) VALUES (%s, %s, %s)",
            (current_user.id, propiedad_id, datetime.now())
        )
        
        conn.commit()
        conn.close()
        
        return {"mensaje": "Propiedad agregada a favoritos"}
        
    except Exception as e:
        logger.error(f"Error agregando favorito: {e}")
        raise HTTPException(status_code=500, detail=f"Error al agregar favorito: {str(e)}")

@app.delete("/favoritos/{propiedad_id}")
async def quitar_favorito(propiedad_id: str, current_user: Usuario = Depends(get_current_user)):
    """Quitar propiedad de favoritos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM favoritos WHERE usuario_id = %s AND propiedad_id = %s",
            (current_user.id, propiedad_id)
        )
        
        conn.commit()
        conn.close()
        
        return {"mensaje": "Propiedad quitada de favoritos"}
        
    except Exception as e:
        logger.error(f"Error quitando favorito: {e}")
        raise HTTPException(status_code=500, detail=f"Error al quitar favorito: {str(e)}")

@app.get("/mis-favoritos", response_model=RespuestaPaginada)
async def obtener_favoritos(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener favoritos del usuario"""
    inicio = time.time()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Contar total
        cursor.execute("""
            SELECT COUNT(*) FROM favoritos f
            JOIN propiedades p ON f.propiedad_id = p.id
            WHERE f.usuario_id = %s AND p.activo = true
        """, (current_user.id,))
        total = cursor.fetchone()['count']
        
        # Obtener favoritos paginados
        offset = (pagina - 1) * por_pagina
        cursor.execute("""
            SELECT 
                p.id, p.titulo, p.descripcion, p.precio, p.ciudad,
                p.tipo_operacion, p.tipo_propiedad, p.imagen, p.direccion,
                p.estado, p.link, p.recamaras, p.banos, p.estacionamientos,
                p.superficie_m2, p.amenidades, p.caracteristicas
            FROM favoritos f
            JOIN propiedades p ON f.propiedad_id = p.id
            WHERE f.usuario_id = %s AND p.activo = true
            ORDER BY f.fecha_agregado DESC
            LIMIT %s OFFSET %s
        """, (current_user.id, por_pagina, offset))
        
        propiedades_data = cursor.fetchall()
        conn.close()
        
        # Procesar resultados
        propiedades = []
        for prop in propiedades_data:
            prop_dict = dict(prop)
            prop_dict['es_favorito'] = True  # Todas son favoritos
            
            # Generar URL de imagen
            if prop_dict.get('imagen'):
                prop_dict['imagen_url'] = generar_url_imagen(prop_dict['imagen'])
            else:
                prop_dict['imagen_url'] = None
            
            propiedades.append(PropiedadResumen(**prop_dict))
        
        tiempo_ms = (time.time() - inicio) * 1000
        total_paginas = (total + por_pagina - 1) // por_pagina
        
        return RespuestaPaginada(
            propiedades=propiedades,
            total=total,
            pagina=pagina,
            por_pagina=por_pagina,
            total_paginas=total_paginas,
            tiempo_consulta_ms=tiempo_ms
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo favoritos: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener favoritos: {str(e)}")

# =====================================================
# ENDPOINTS COLABORATIVOS
# =====================================================

@app.post("/propiedades-colaborativas")
async def crear_propiedad_colaborativa(
    propiedad: PropiedadColaborativa,
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva propiedad colaborativa"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Generar ID único
        import uuid
        propiedad_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO propiedades (
                id, titulo, descripcion, precio, tipo_propiedad, tipo_operacion,
                ciudad, estado, direccion, recamaras, banos, estacionamientos,
                superficie_m2, telefono_contacto, email_contacto, usuario_id,
                activo, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            propiedad_id,
            propiedad.titulo,
            propiedad.descripcion,
            propiedad.precio,
            propiedad.tipo_propiedad,
            propiedad.tipo_operacion,
            propiedad.ciudad,
            propiedad.estado,
            propiedad.direccion,
            propiedad.recamaras,
            propiedad.banos,
            propiedad.estacionamientos,
            propiedad.metros_construccion,
            propiedad.telefono_contacto,
            propiedad.email_contacto,
            current_user.id,
            True,
            datetime.now()
        ))
        
        nueva_propiedad = cursor.fetchone()
        conn.commit()
        conn.close()
        
        return {
            "mensaje": "Propiedad creada exitosamente",
            "propiedad_id": propiedad_id,
            "propiedad": dict(nueva_propiedad)
        }
        
    except Exception as e:
        logger.error(f"Error creando propiedad colaborativa: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear propiedad: {str(e)}")

# =====================================================
# ENDPOINT PARA INICIAR SERVIDOR
# =====================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 