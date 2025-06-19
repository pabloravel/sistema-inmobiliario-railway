#!/usr/bin/env python3
"""
API REST OPTIMIZADA PARA POSTGRESQL - VERSIÓN CORREGIDA
=====================================================

CORRECCIONES APLICADAS:
- ✅ Rutas de imágenes con carpetas de fecha
- ✅ Filtros de ciudades limpios (solo ciudades reales)
- ✅ Filtros funcionales que actualizan resultados
- ✅ Consultas optimizadas
"""

from fastapi import FastAPI, HTTPException, Query, Depends, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
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
    title="API Inmobiliaria Colaborativa",
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

# Configuración de base de datos
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
    'Yautepec', 'Cuautla', 'Ayala', 'Tepoztlán', 'Huitzilac', 'Tetela del Volcán',
    'Tlaltizapán', 'Tlaquiltenango', 'Jojutla', 'Puente de Ixtla', 'Zacatepec',
    'Axochiapan', 'Jantetelco', 'Jonacatepec', 'Ocuituco', 'Temoac', 'Tetecala',
    'Mazatepec', 'Miacatlán', 'Coatlán del Río', 'Tlalnepantla', 'Totolapan',
    'Atlatlahucan', 'Yecapixtla', 'Amacuzac', 'Tres de Mayo'
}

# =====================================================
# MODELOS PYDANTIC
# =====================================================

class UsuarioRegistro(BaseModel):
    nombre: str
    email: EmailStr
    telefono: str
    password: str

class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

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
    imagenes: Optional[List[str]]  # ✅ CORREGIDO: List[str] para compatibilidad con BD
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
    email: EmailStr

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

# =====================================================
# FUNCIONES AUXILIARES
# =====================================================

def hash_password(password: str) -> str:
    """Hashea una contraseña"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verifica una contraseña"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    """Crea un token JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Obtiene el usuario actual del token (opcional)"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
    except jwt.PyJWTError:
        return None
    
    # Obtener usuario de la base de datos
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s AND activo = TRUE", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user is None:
        return None
    
    return Usuario(**user)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene el usuario actual del token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Obtener usuario de la base de datos
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s AND activo = TRUE", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    return Usuario(**user)

def get_admin_user(current_user: Usuario = Depends(get_current_user)):
    """Verifica que el usuario sea administrador"""
    if not current_user.es_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requieren permisos de administrador")
    return current_user

def limpiar_ciudad(ciudad: str) -> Optional[str]:
    """Limpia y valida nombres de ciudades"""
    if not ciudad:
        return None
    
    ciudad_limpia = ciudad.strip()
    
    # Buscar ciudad válida en el texto
    for ciudad_valida in CIUDADES_MORELOS:
        if ciudad_valida.lower() in ciudad_limpia.lower():
            return ciudad_valida
    
    # Si no encuentra una ciudad válida, devolver None
    return None

def generar_url_imagen(nombre_imagen: str) -> str:
    """Genera URL completa de imagen con carpeta de fecha y fallback"""
    if not nombre_imagen:
        return "https://via.placeholder.com/400x300/e2e8f0/64748b?text=Sin+Imagen"
    
    # Si ya tiene la ruta completa, devolverla tal como está
    if nombre_imagen.startswith('resultados/'):
        return nombre_imagen
    
    # Extraer fecha del nombre de archivo
    # Formato: cuernavaca-2025-06-09-123456.jpg
    match = re.search(r'(\d{4}-\d{2}-\d{2})', nombre_imagen)
    if match:
        fecha = match.group(1)
        return f"resultados/{fecha}/{nombre_imagen}"
    
    # Fallback para imágenes sin fecha - intentar con diferentes rutas
    rutas_posibles = [
        f"resultados/2025-05-30/{nombre_imagen}",  # Ruta más común
        f"resultados/{nombre_imagen}",              # Ruta directa
        f"resultados/2025-06-06/{nombre_imagen}",   # Otras fechas posibles
        f"resultados/2025-06-08/{nombre_imagen}",
        f"resultados/2025-06-09/{nombre_imagen}"
    ]
    
    # Devolver la primera ruta (más probable)
    return rutas_posibles[0]

# Conexión a base de datos
def get_db_connection():
    """Obtiene conexión a PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Error conectando a BD: {e}")
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")

def ejecutar_consulta(query: str, params: tuple = None, fetchall: bool = True):
    """Ejecuta consulta con medición de tiempo"""
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
        
        cursor.close()
        conn.close()
        
        tiempo_ms = (time.time() - inicio) * 1000
        logger.info(f"Consulta ejecutada en {tiempo_ms:.2f}ms")
        
        return resultado, tiempo_ms
        
    except Exception as e:
        logger.error(f"Error en consulta: {e}")
        raise HTTPException(status_code=500, detail=f"Error en consulta: {str(e)}")

# ENDPOINTS PRINCIPALES

@app.get("/", response_model=Dict)
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "mensaje": "🏡 API Inmobiliaria Colaborativa",
        "version": "3.0.0",
        "estado": "activo",
        "funcionalidades": [
            "Sistema de usuarios y autenticación",
            "Propiedades con favoritos",
            "Sistema colaborativo",
            "Panel de administración",
            "Mensajes WhatsApp personalizados"
        ],
        "endpoints_principales": {
            "propiedades": "/propiedades",
            "registro": "/registro",
            "login": "/login",
            "favoritos": "/favoritos",
            "admin": "/admin",
            "whatsapp": "/whatsapp"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/propiedades", response_model=RespuestaPaginada)
async def listar_propiedades(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(60, ge=1, le=500, description="Propiedades por página"),
    ciudad: Optional[List[str]] = Query(None, description="Filtrar por ciudades"),
    tipo_operacion: Optional[List[str]] = Query(None, description="Filtrar por tipos de operación"),
    tipo_propiedad: Optional[List[str]] = Query(None, description="Filtrar por tipos de propiedad"),
    precio_min: Optional[float] = Query(1, description="Precio mínimo (por defecto 1 para mostrar solo propiedades con precio)"),
    precio_max: Optional[float] = Query(None, description="Precio máximo"),
    recamaras: Optional[List[int]] = Query(None, description="Números de recámaras"),
    banos: Optional[List[int]] = Query(None, description="Números de baños"),
    estacionamientos: Optional[List[int]] = Query(None, description="Números de estacionamientos"),
    superficie_min: Optional[int] = Query(None, description="Superficie mínima en m²"),
    superficie_max: Optional[int] = Query(None, description="Superficie máxima en m²"),
    amenidad: Optional[List[str]] = Query(None, description="Filtrar por amenidades"),
    documentacion: Optional[List[str]] = Query(None, description="Filtrar por documentación"),
    caracteristicas_adicionales: Optional[List[str]] = Query(None, description="Filtrar por características adicionales"),
    q: Optional[str] = Query(None, description="Búsqueda de texto"),
    orden: Optional[str] = Query("created_at", description="Campo para ordenar"),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """
    Lista propiedades con paginación y filtros FUNCIONALES
    
    MEJORAS:
    - ✅ Filtros que SÍ funcionan
    - ✅ Imágenes con rutas correctas
    - ✅ Ciudades limpias
    - ✅ Filtro precio mínimo por defecto para mostrar solo propiedades con precio
    """
    
    # Construir WHERE clause - SOLO activo = true por defecto + precio > 0
    where_conditions = ["activo = true"]
    params = []
    
    # FILTRO DE BÚSQUEDA DE TEXTO
    if q:
        where_conditions.append("(titulo ILIKE %s OR descripcion ILIKE %s OR direccion ILIKE %s)")
        search_term = f"%{q}%"
        params.extend([search_term, search_term, search_term])
    
    # FILTROS DE CIUDAD - Múltiples ciudades
    if ciudad and len(ciudad) > 0:
        ciudades_limpias = [limpiar_ciudad(c) for c in ciudad if limpiar_ciudad(c)]
        if ciudades_limpias:
            placeholders = ",".join(["%s"] * len(ciudades_limpias))
            where_conditions.append(f"ciudad IN ({placeholders})")
            params.extend(ciudades_limpias)
    
    # FILTROS DE TIPO DE OPERACIÓN - Múltiples
    if tipo_operacion and len(tipo_operacion) > 0:
        placeholders = ",".join(["%s"] * len(tipo_operacion))
        where_conditions.append(f"tipo_operacion IN ({placeholders})")
        params.extend(tipo_operacion)
    
    # FILTROS DE TIPO DE PROPIEDAD - Múltiples
    if tipo_propiedad and len(tipo_propiedad) > 0:
        placeholders = ",".join(["%s"] * len(tipo_propiedad))
        where_conditions.append(f"tipo_propiedad IN ({placeholders})")
        params.extend(tipo_propiedad)
    
    # FILTROS DE PRECIO - APLICAR PRECIO MÍNIMO POR DEFECTO
    if precio_min is not None:
        where_conditions.append("precio >= %s")
        params.append(precio_min)
    
    if precio_max is not None:
        where_conditions.append("precio <= %s")
        params.append(precio_max)
    
    # FILTROS DE CARACTERÍSTICAS - Múltiples valores
    if recamaras and len(recamaras) > 0:
        # Manejar "5+" como >= 5
        recamaras_conditions = []
        for rec in recamaras:
            if rec >= 5:
                recamaras_conditions.append("recamaras >= %s")
                params.append(5)
            else:
                recamaras_conditions.append("recamaras = %s")
                params.append(rec)
        if recamaras_conditions:
            where_conditions.append(f"({' OR '.join(recamaras_conditions)})")
    
    if banos and len(banos) > 0:
        # Manejar "4+" como >= 4
        banos_conditions = []
        for ban in banos:
            if ban >= 4:
                banos_conditions.append("banos >= %s")
                params.append(4)
            else:
                banos_conditions.append("banos = %s")
                params.append(ban)
        if banos_conditions:
            where_conditions.append(f"({' OR '.join(banos_conditions)})")
    
    if estacionamientos and len(estacionamientos) > 0:
        # Manejar "3+" como >= 3
        est_conditions = []
        for est in estacionamientos:
            if est >= 3:
                est_conditions.append("estacionamientos >= %s")
                params.append(3)
            else:
                est_conditions.append("estacionamientos = %s")
                params.append(est)
        if est_conditions:
            where_conditions.append(f"({' OR '.join(est_conditions)})")
    
    if superficie_min is not None:
        where_conditions.append("superficie_construida >= %s")
        params.append(superficie_min)
    
    if superficie_max is not None:
        where_conditions.append("superficie_construida <= %s")
        params.append(superficie_max)
    
    # FILTROS DE AMENIDADES
    if amenidad and len(amenidad) > 0:
        amenidad_conditions = []
        for am in amenidad:
            if am == 'alberca':
                amenidad_conditions.append("(amenidades->>'alberca')::boolean = true")
            elif am == 'jardin':
                amenidad_conditions.append("(amenidades->>'jardin')::boolean = true")
            elif am == 'seguridad':
                amenidad_conditions.append("(amenidades->>'seguridad')::boolean = true")
            elif am == 'terraza':
                amenidad_conditions.append("(amenidades->>'terraza')::boolean = true")
            elif am == 'estacionamiento':
                amenidad_conditions.append("(amenidades->>'estacionamiento')::boolean = true")
            elif am == 'cisterna':
                amenidad_conditions.append("(amenidades->>'cisterna')::boolean = true")
            elif am == 'jacuzzi':
                amenidad_conditions.append("(amenidades->>'jacuzzi')::boolean = true")
        if amenidad_conditions:
            where_conditions.append(f"({' OR '.join(amenidad_conditions)})")
    
    # FILTROS DE DOCUMENTACIÓN
    if documentacion and len(documentacion) > 0:
        doc_conditions = []
        for doc in documentacion:
            if doc in ['escrituras', 'Escrituras']:
                doc_conditions.append("(LOWER(titulo) LIKE '%%escrituras%%' OR LOWER(descripcion) LIKE '%%escrituras%%')")
            elif doc in ['cesion', 'Cesión']:
                doc_conditions.append("(LOWER(titulo) LIKE '%%cesión%%' OR LOWER(descripcion) LIKE '%%cesión%%' OR LOWER(titulo) LIKE '%%cesion%%' OR LOWER(descripcion) LIKE '%%cesion%%')")
        if doc_conditions:
            where_conditions.append(f"({' OR '.join(doc_conditions)})")
    
    # FILTROS DE CARACTERÍSTICAS ADICIONALES
    if caracteristicas_adicionales and len(caracteristicas_adicionales) > 0:
        caracteristicas_adicionales_conditions = []
        for ca in caracteristicas_adicionales:
            if ca == 'Casa de un nivel':
                caracteristicas_adicionales_conditions.append("(LOWER(titulo) LIKE '%%un nivel%%' OR LOWER(descripcion) LIKE '%%un nivel%%')")
            elif ca == 'Recámara en planta baja':
                caracteristicas_adicionales_conditions.append("(LOWER(titulo) LIKE '%%recámara en planta baja%%' OR LOWER(descripcion) LIKE '%%recámara en planta baja%%')")
            elif ca == 'Cochera techada':
                caracteristicas_adicionales_conditions.append("(LOWER(titulo) LIKE '%%cochera techada%%' OR LOWER(descripcion) LIKE '%%cochera techada%%')")
            elif ca == 'Área de servicio':
                caracteristicas_adicionales_conditions.append("(LOWER(titulo) LIKE '%%área de servicio%%' OR LOWER(descripcion) LIKE '%%área de servicio%%')")
        if caracteristicas_adicionales_conditions:
            where_conditions.append(f"({' OR '.join(caracteristicas_adicionales_conditions)})")
    
    where_clause = " AND ".join(where_conditions)
    
    # Validar campo de orden
    campos_validos = ['created_at', 'precio', 'titulo', 'recamaras', 'banos', 'estacionamientos', 'superficie_construida']
    if orden not in campos_validos:
        orden = 'created_at'
    
    # Contar total de registros
    count_query = f"SELECT COUNT(*) FROM propiedades WHERE {where_clause}"
    total_result, _ = ejecutar_consulta(count_query, tuple(params), fetchall=False)
    total = total_result['count']
    
    # Calcular offset
    offset = (pagina - 1) * por_pagina
    
    # Consulta principal con paginación - RUTAS DE IMÁGENES CORREGIDAS
    main_query = f"""
    SELECT 
        id, titulo, descripcion, precio, ciudad, tipo_operacion, tipo_propiedad,
        CASE 
            WHEN imagenes IS NOT NULL AND jsonb_array_length(imagenes) > 0 
            THEN imagenes->>0 
            ELSE NULL 
        END as imagen_url,
        direccion, estado, url_original as link,
        recamaras, banos, estacionamientos, superficie_construida as superficie_m2,
        amenidades, caracteristicas
    FROM propiedades 
    WHERE {where_clause}
    ORDER BY 
        CASE 
            WHEN '{orden}' = 'precio' AND (precio IS NULL OR precio = 0) THEN 1 
            ELSE 0 
        END,
        CASE 
            WHEN imagenes IS NOT NULL AND jsonb_array_length(imagenes) > 0 THEN 0
            ELSE 1 
        END,
        {orden} {'ASC' if orden == 'precio' else 'DESC'} NULLS LAST,
        created_at DESC
    LIMIT %s OFFSET %s
    """
    
    params.extend([por_pagina, offset])
    propiedades_result, tiempo_ms = ejecutar_consulta(main_query, tuple(params))
    
    # Convertir a modelos Pydantic y CORREGIR RUTAS DE IMÁGENES
    propiedades = []
    for prop in propiedades_result:
        prop_dict = dict(prop)
        
        # CORREGIR RUTA DE IMAGEN
        if prop_dict.get('imagen_url'):
            prop_dict['imagen_url'] = generar_url_imagen(prop_dict['imagen_url'])
        
        # Procesar amenidades y características JSONB
        for field in ['amenidades', 'caracteristicas']:
            if prop_dict.get(field):
                if isinstance(prop_dict[field], str):
                    try:
                        prop_dict[field] = json.loads(prop_dict[field])
                    except:
                        prop_dict[field] = {}
        
        propiedades.append(PropiedadResumen(**prop_dict))
    
    # Calcular metadatos de paginación
    total_paginas = (total + por_pagina - 1) // por_pagina
    
    return RespuestaPaginada(
        propiedades=propiedades,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=total_paginas,
        tiempo_consulta_ms=tiempo_ms
    )

@app.get("/propiedades/{propiedad_id}", response_model=PropiedadCompleta)
async def obtener_propiedad(propiedad_id: str):
    """
    Obtiene una propiedad específica por ID
    """
    
    query = """
    SELECT 
        id, titulo, descripcion, precio, ciudad, tipo_operacion, tipo_propiedad,
        direccion, estado, url_original as link,
        recamaras, banos, estacionamientos, superficie_construida as superficie_m2,
        amenidades, caracteristicas, imagenes, created_at,
        CASE 
            WHEN imagenes IS NOT NULL AND jsonb_array_length(imagenes) > 0 
            THEN imagenes->>0 
            ELSE NULL 
        END as imagen_url
    FROM propiedades 
    WHERE id = %s AND activo = true
    """
    
    resultado, tiempo_ms = ejecutar_consulta(query, (propiedad_id,), fetchall=False)
    
    if not resultado:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    
    # Convertir JSONB a dict y CORREGIR IMAGEN
    propiedad_dict = dict(resultado)
    
    # CORREGIR RUTA DE IMAGEN
    if propiedad_dict.get('imagen_url'):
        propiedad_dict['imagen_url'] = generar_url_imagen(propiedad_dict['imagen_url'])
    
    # Procesar JSONB fields
    for field in ['amenidades', 'caracteristicas', 'imagenes']:
        if propiedad_dict.get(field):
            if isinstance(propiedad_dict[field], str):
                try:
                    propiedad_dict[field] = json.loads(propiedad_dict[field])
                except:
                    propiedad_dict[field] = {}
    
    return PropiedadCompleta(**propiedad_dict)

@app.get("/buscar", response_model=RespuestaPaginada)
async def buscar_propiedades(
    q: str = Query(..., description="Término de búsqueda"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(12, ge=1, le=50)
):
    """
    Búsqueda de texto completo en título y descripción
    """
    
    # Consulta con búsqueda de texto completo mejorada
    search_query = """
    SELECT 
        id, titulo, descripcion, precio, ciudad, tipo_operacion, tipo_propiedad,
        CASE 
            WHEN imagenes IS NOT NULL AND jsonb_array_length(imagenes) > 0 
            THEN imagenes->>0 
            ELSE NULL 
        END as imagen_url,
        direccion, estado, url_original as link, 
        recamaras, banos, estacionamientos, superficie_construida as superficie_m2,
        amenidades, caracteristicas,
        ts_rank(to_tsvector('spanish', titulo || ' ' || COALESCE(descripcion, '') || ' ' || COALESCE(direccion, '') || ' ' || COALESCE(ciudad, '')), 
                plainto_tsquery('spanish', %s)) as relevancia
    FROM propiedades 
    WHERE activo = true 
    AND (
        to_tsvector('spanish', titulo || ' ' || COALESCE(descripcion, '') || ' ' || COALESCE(direccion, '') || ' ' || COALESCE(ciudad, '')) 
        @@ plainto_tsquery('spanish', %s)
        OR titulo ILIKE %s
        OR descripcion ILIKE %s
        OR direccion ILIKE %s
        OR ciudad ILIKE %s
    )
    ORDER BY relevancia DESC, 
             CASE WHEN precio IS NOT NULL THEN 0 ELSE 1 END,
             created_at DESC
    LIMIT %s OFFSET %s
    """
    
    # Contar resultados de búsqueda
    count_query = """
    SELECT COUNT(*) FROM propiedades 
    WHERE activo = true 
    AND (
        to_tsvector('spanish', titulo || ' ' || COALESCE(descripcion, '') || ' ' || COALESCE(direccion, '') || ' ' || COALESCE(ciudad, '')) 
        @@ plainto_tsquery('spanish', %s)
        OR titulo ILIKE %s
        OR descripcion ILIKE %s
        OR direccion ILIKE %s
        OR ciudad ILIKE %s
    )
    """
    
    search_term = f"%{q}%"
    search_params = (q, q, search_term, search_term, search_term, search_term)
    
    # Ejecutar conteo
    total_result, _ = ejecutar_consulta(count_query, search_params, fetchall=False)
    total = total_result['count']
    
    # Calcular offset
    offset = (pagina - 1) * por_pagina
    
    # Ejecutar búsqueda principal
    main_params = search_params + (por_pagina, offset)
    propiedades_result, tiempo_ms = ejecutar_consulta(search_query, main_params)
    
    # Procesar resultados
    propiedades = []
    for prop in propiedades_result:
        prop_dict = dict(prop)
        # Remover campo de relevancia para el modelo
        prop_dict.pop('relevancia', None)
        
        # CORREGIR RUTA DE IMAGEN
        if prop_dict.get('imagen_url'):
            prop_dict['imagen_url'] = generar_url_imagen(prop_dict['imagen_url'])
        
        # Procesar JSONB
        for field in ['amenidades', 'caracteristicas']:
            if prop_dict.get(field):
                if isinstance(prop_dict[field], str):
                    try:
                        prop_dict[field] = json.loads(prop_dict[field])
                    except:
                        prop_dict[field] = {}
        
        propiedades.append(PropiedadResumen(**prop_dict))
    
    # Calcular metadatos de paginación
    total_paginas = (total + por_pagina - 1) // por_pagina
    
    return RespuestaPaginada(
        propiedades=propiedades,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=total_paginas,
        tiempo_consulta_ms=tiempo_ms
    )

@app.get("/estadisticas")
async def obtener_estadisticas():
    """
    Estadísticas generales con FILTROS LIMPIOS
    """
    
    query = """
    SELECT 
        COUNT(*) as total_propiedades,
        COUNT(CASE WHEN precio IS NOT NULL THEN 1 END) as con_precio,
        COALESCE(AVG(precio), 0) as precio_promedio,
        COALESCE(MIN(precio), 0) as precio_minimo,
        COALESCE(MAX(precio), 0) as precio_maximo
    FROM propiedades 
    WHERE activo = true
    """
    
    # Estadísticas por tipo de operación
    tipos_query = """
    SELECT tipo_operacion, COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true AND tipo_operacion IS NOT NULL
    GROUP BY tipo_operacion
    ORDER BY cantidad DESC
    """
    
    # CIUDADES - Todas las ciudades válidas que existen en la BD
    ciudades_query = """
    SELECT ciudad, COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND ciudad IS NOT NULL 
    AND ciudad != ''
    AND ciudad NOT LIKE '%Chats%'
    AND ciudad NOT LIKE '%Notificaciones%'  
    GROUP BY ciudad
    ORDER BY cantidad DESC
    """
    
    # Estadísticas por tipo de propiedad
    tipos_prop_query = """
    SELECT tipo_propiedad, COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true AND tipo_propiedad IS NOT NULL
    GROUP BY tipo_propiedad
    ORDER BY cantidad DESC
    """
    
    # Estadísticas por recámaras (solo valores razonables)
    recamaras_query = """
    SELECT recamaras, COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true AND recamaras IS NOT NULL AND recamaras BETWEEN 1 AND 10
    GROUP BY recamaras
    ORDER BY recamaras
    """
    
    # Estadísticas por baños (solo valores razonables)
    banos_query = """
    SELECT banos, COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true AND banos IS NOT NULL AND banos BETWEEN 1 AND 10
    GROUP BY banos
    ORDER BY banos
    """
    
    # Estadísticas por estacionamientos (solo valores razonables)
    estacionamientos_query = """
    SELECT estacionamientos, COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true AND estacionamientos IS NOT NULL AND estacionamientos BETWEEN 1 AND 20
    GROUP BY estacionamientos
    ORDER BY estacionamientos
    """
    
    # Amenidades desde columna amenidades JSONB
    amenidades_query = """
    SELECT 
        'Alberca' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'alberca')::boolean = true
    
    UNION ALL
    
    SELECT 
        'Jardín' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'jardin')::boolean = true
    
    UNION ALL
    
    SELECT 
        'Seguridad' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'seguridad')::boolean = true
    
    UNION ALL
    
    SELECT 
        'Terraza' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'terraza')::boolean = true
    
    UNION ALL
    
    SELECT 
        'Estacionamiento' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'estacionamiento')::boolean = true
    
    UNION ALL
    
    SELECT 
        'Cisterna' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'cisterna')::boolean = true
    
    UNION ALL
    
    SELECT 
        'Jacuzzi' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'jacuzzi')::boolean = true
    """

    # Estadísticas de documentación (basadas en texto)
    documentacion_query = """
    SELECT 
        'Escrituras' as tipo_doc, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (LOWER(titulo) LIKE '%escrituras%' OR LOWER(descripcion) LIKE '%escrituras%')
    
    UNION ALL
    
    SELECT 
        'Cesión' as tipo_doc, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (LOWER(titulo) LIKE '%cesión%' OR LOWER(descripcion) LIKE '%cesión%' OR LOWER(titulo) LIKE '%cesion%' OR LOWER(descripcion) LIKE '%cesion%')
    """
    
    # Estadísticas de características adicionales (basadas en texto)
    caracteristicas_adicionales_query = """
    SELECT 
        'Casa de un nivel' as caracteristica, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (
        LOWER(titulo) LIKE '%un nivel%' OR 
        LOWER(descripcion) LIKE '%un nivel%' OR
        LOWER(titulo) LIKE '%1 nivel%' OR 
        LOWER(descripcion) LIKE '%1 nivel%'
    )
    
    UNION ALL
    
    SELECT 
        'Recámara en planta baja' as caracteristica, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (
        LOWER(titulo) LIKE '%recámara en planta baja%' OR 
        LOWER(descripcion) LIKE '%recámara en planta baja%' OR
        LOWER(titulo) LIKE '%recamara en planta baja%' OR 
        LOWER(descripcion) LIKE '%recamara en planta baja%' OR
        LOWER(titulo) LIKE '%planta baja%' OR 
        LOWER(descripcion) LIKE '%planta baja%'
    )
    
    UNION ALL
    
    SELECT 
        'Cochera techada' as caracteristica, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (
        LOWER(titulo) LIKE '%cochera techada%' OR 
        LOWER(descripcion) LIKE '%cochera techada%' OR
        LOWER(titulo) LIKE '%garage techado%' OR 
        LOWER(descripcion) LIKE '%garage techado%'
    )
    
    UNION ALL
    
    SELECT 
        'Área de servicio' as caracteristica, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (
        LOWER(titulo) LIKE '%área de servicio%' OR 
        LOWER(descripcion) LIKE '%área de servicio%' OR
        LOWER(titulo) LIKE '%area de servicio%' OR 
        LOWER(descripcion) LIKE '%area de servicio%'
    )
    """
    
    # Ejecutar consultas
    stats_result, tiempo_ms1 = ejecutar_consulta(query, fetchall=False)
    tipos_result, tiempo_ms2 = ejecutar_consulta(tipos_query)
    ciudades_result, tiempo_ms3 = ejecutar_consulta(ciudades_query)
    tipos_prop_result, tiempo_ms4 = ejecutar_consulta(tipos_prop_query)
    recamaras_result, tiempo_ms5 = ejecutar_consulta(recamaras_query)
    banos_result, tiempo_ms6 = ejecutar_consulta(banos_query)
    estacionamientos_result, tiempo_ms7 = ejecutar_consulta(estacionamientos_query)
    amenidades_result, tiempo_ms8 = ejecutar_consulta(amenidades_query)
    documentacion_result, tiempo_ms9 = ejecutar_consulta(documentacion_query)
    caracteristicas_adicionales_result, tiempo_ms10 = ejecutar_consulta(caracteristicas_adicionales_query)
    
    # Procesar resultados
    stats = dict(stats_result)
    tipos_operacion = {row['tipo_operacion']: row['cantidad'] for row in tipos_result}
    ciudades = {row['ciudad']: row['cantidad'] for row in ciudades_result}
    tipos_propiedad = {row['tipo_propiedad']: row['cantidad'] for row in tipos_prop_result}
    
    # Formatear características numéricas
    caracteristicas = {}
    for row in recamaras_result:
        if row['recamaras']:
            key = f"{row['recamaras']} Recámara{'s' if row['recamaras'] > 1 else ''}"
            caracteristicas[key] = row['cantidad']
    
    for row in banos_result:
        if row['banos']:
            key = f"{row['banos']} Baño{'s' if row['banos'] > 1 else ''}"
            caracteristicas[key] = row['cantidad']
    
    for row in estacionamientos_result:
        if row['estacionamientos']:
            key = f"{row['estacionamientos']} Estacionamiento{'s' if row['estacionamientos'] > 1 else ''}"
            caracteristicas[key] = row['cantidad']
    
    # Procesar amenidades (solo incluir si tienen más de 0)
    amenidades = {row['amenidad']: row['cantidad'] for row in amenidades_result if row['amenidad'] and row['cantidad'] > 0}
    
    # Procesar documentación
    documentacion = {row['tipo_doc']: row['cantidad'] for row in documentacion_result if row['tipo_doc'] and row['cantidad'] > 0}
    
    # Procesar características adicionales
    caracteristicas_adicionales = {row['caracteristica']: row['cantidad'] for row in caracteristicas_adicionales_result if row['caracteristica'] and row['cantidad'] > 0}
    
    tiempo_total = tiempo_ms1 + tiempo_ms2 + tiempo_ms3 + tiempo_ms4 + tiempo_ms5 + tiempo_ms6 + tiempo_ms7 + tiempo_ms8 + tiempo_ms9 + tiempo_ms10
    
    return {
        'total': stats['total_propiedades'],
        'total_propiedades': stats['total_propiedades'],
        'con_precio': stats['con_precio'],
        'precio_promedio': float(stats['precio_promedio']),
        'precio_minimo': float(stats['precio_minimo']),
        'precio_maximo': float(stats['precio_maximo']),
        'por_tipo_operacion': tipos_operacion,
        'tipos_operacion': tipos_operacion,
        'ciudades': ciudades,  # Agregar ciudades al nivel principal
        'tiempo_consulta_ms': tiempo_total,
        # Estructura de filtros LIMPIOS para el frontend
        'filtros': {
            'operaciones': tipos_operacion,
            'ciudades': ciudades,
            'tipos': tipos_propiedad,
            'amenidades': amenidades,
            'caracteristicas': caracteristicas,
            'documentacion': documentacion,
            'caracteristicas_adicionales': caracteristicas_adicionales
        }
    }

# =====================================================
# ENDPOINTS DE AUTENTICACIÓN
# =====================================================

@app.post("/registro", response_model=Token)
async def registrar_usuario(usuario: UsuarioRegistro):
    """Registra un nuevo usuario"""
    try:
        # Verificar si el email ya existe
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (usuario.email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        
        # Crear usuario
        password_hash = hash_password(usuario.password)
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, telefono, password_hash)
            VALUES (%s, %s, %s, %s) RETURNING id, nombre, email, telefono, es_admin, fecha_registro, activo
        """, (usuario.nombre, usuario.email, usuario.telefono, password_hash))
        
        user_data = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        # Crear token
        access_token = create_access_token(data={"sub": user_data[0]})
        
        usuario_obj = Usuario(
            id=user_data[0],
            nombre=user_data[1],
            email=user_data[2],
            telefono=user_data[3],
            es_admin=user_data[4],
            fecha_registro=user_data[5],
            activo=user_data[6]
        )
        
        return Token(access_token=access_token, token_type="bearer", usuario=usuario_obj)
        
    except Exception as e:
        logger.error(f"Error en registro: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/login", response_model=Token)
async def login_usuario(usuario: UsuarioLogin):
    """Inicia sesión de usuario"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, email, telefono, password_hash, es_admin, fecha_registro, activo FROM usuarios WHERE email = %s AND activo = TRUE", (usuario.email,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user_data or not verify_password(usuario.password, user_data[4]):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        # Crear token
        access_token = create_access_token(data={"sub": user_data[0]})
        
        usuario_obj = Usuario(
            id=user_data[0],
            nombre=user_data[1],
            email=user_data[2],
            telefono=user_data[3],
            es_admin=user_data[5],
            fecha_registro=user_data[6],
            activo=user_data[7]
        )
        
        return Token(access_token=access_token, token_type="bearer", usuario=usuario_obj)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/perfil", response_model=Usuario)
async def obtener_perfil(current_user: Usuario = Depends(get_current_user)):
    """Obtiene el perfil del usuario actual"""
    return current_user

# =====================================================
# ENDPOINTS DE FAVORITOS
# =====================================================

@app.post("/favoritos/{propiedad_id}")
async def agregar_favorito(propiedad_id: str, current_user: Usuario = Depends(get_current_user)):
    """Agrega una propiedad a favoritos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si ya existe
        cursor.execute("SELECT id FROM favoritos WHERE usuario_id = %s AND propiedad_id = %s", 
                      (current_user.id, int(propiedad_id)))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return {"mensaje": "Ya está en favoritos", "es_favorito": True}
        
        # Agregar a favoritos
        cursor.execute("INSERT INTO favoritos (usuario_id, propiedad_id) VALUES (%s, %s)",
                      (current_user.id, int(propiedad_id)))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"mensaje": "Agregado a favoritos", "es_favorito": True}
        
    except Exception as e:
        logger.error(f"Error agregando favorito: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.delete("/favoritos/{propiedad_id}")
async def quitar_favorito(propiedad_id: str, current_user: Usuario = Depends(get_current_user)):
    """Quita una propiedad de favoritos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM favoritos WHERE usuario_id = %s AND propiedad_id = %s",
                      (current_user.id, int(propiedad_id)))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"mensaje": "Quitado de favoritos", "es_favorito": False}
        
    except Exception as e:
        logger.error(f"Error quitando favorito: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/mis-favoritos", response_model=RespuestaPaginada)
async def obtener_favoritos(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene los favoritos del usuario con información completa"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener total de favoritos
        cursor.execute("""
            SELECT COUNT(*) FROM favoritos WHERE usuario_id = %s
        """, (current_user.id,))
        total = cursor.fetchone()[0]
        
        # Calcular offset
        offset = (pagina - 1) * por_pagina
        
        # Obtener favoritos con información completa de propiedades
        cursor.execute("""
            SELECT p.*, f.fecha_agregado,
                   cp.nombre as contacto_nombre, cp.telefono as contacto_telefono
            FROM favoritos f
            JOIN propiedades p ON f.propiedad_id = p.id
            LEFT JOIN contactos_propiedades cp ON (cp.propiedad_id = p.id AND cp.usuario_id = %s)
            WHERE f.usuario_id = %s
            ORDER BY f.fecha_agregado DESC
            LIMIT %s OFFSET %s
        """, (current_user.id, current_user.id, por_pagina, offset))
        
        favoritos = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Formatear propiedades
        propiedades = []
        for fav in favoritos:
            propiedad_data = {
                "id": fav[0],
                "titulo": fav[1] or "Sin título",
                "descripcion": fav[2],
                "precio": fav[3],
                "ciudad": fav[4] or "Sin ciudad",
                "tipo_operacion": fav[5] or "Sin especificar",
                "tipo_propiedad": fav[6],
                "imagen_url": generar_url_imagen(fav[7]) if fav[7] else None,
                "direccion": fav[8],
                "estado": fav[9],
                "link": fav[10],
                "recamaras": fav[11],
                "banos": fav[12],
                "estacionamientos": fav[13],
                "superficie_m2": fav[14],
                "amenidades": fav[15] if fav[15] else {},
                "caracteristicas": fav[16] if fav[16] else {},
                "es_favorito": True,
                "fecha_favorito": fav[17],
                "contacto": {
                    "nombre": fav[18],
                    "telefono": fav[19]
                } if fav[18] or fav[19] else None
            }
            propiedades.append(PropiedadResumen(**propiedad_data))
        
        total_paginas = (total + por_pagina - 1) // por_pagina
        
        return RespuestaPaginada(
            propiedades=propiedades,
            total=total,
            pagina=pagina,
            por_pagina=por_pagina,
            total_paginas=total_paginas,
            tiempo_consulta_ms=0.0
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo favoritos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Endpoint para administradores para eliminar usuarios
@app.delete("/admin/usuarios/{usuario_id}")
async def eliminar_usuario_admin(
    usuario_id: int,
    admin_user: Usuario = Depends(get_admin_user)
):
    """Permite a un admin eliminar un usuario"""
    try:
        if usuario_id == admin_user.id:
            raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Desactivar usuario en lugar de eliminar
        cursor.execute("""
            UPDATE usuarios SET activo = false WHERE id = %s
        """, (usuario_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"mensaje": "Usuario desactivado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando usuario: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/admin/usuarios")
async def listar_usuarios_admin(admin_user: Usuario = Depends(get_admin_user)):
    """Lista todos los usuarios para administración"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nombre, email, telefono, es_admin, fecha_registro, activo
            FROM usuarios
            ORDER BY fecha_registro DESC
        """)
        
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {
            "usuarios": [
                {
                    "id": usuario[0],
                    "nombre": usuario[1],
                    "email": usuario[2],
                    "telefono": usuario[3],
                    "es_admin": usuario[4],
                    "fecha_registro": usuario[5],
                    "activo": usuario[6]
                }
                for usuario in usuarios
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listando usuarios: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# =====================================================
# ENDPOINTS DE PROPIEDADES COLABORATIVAS
# =====================================================

@app.post("/propiedades-colaborativas")
async def crear_propiedad_colaborativa(
    propiedad: PropiedadColaborativa,
    current_user: Usuario = Depends(get_current_user)
):
    """Permite a usuarios registrados agregar propiedades"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO propiedades_colaborativas 
            (usuario_id, titulo, descripcion, precio, tipo_propiedad, tipo_operacion,
             ciudad, estado, direccion, recamaras, banos, estacionamientos,
             metros_construccion, metros_terreno, telefono_contacto, email_contacto)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            current_user.id, propiedad.titulo, propiedad.descripcion, propiedad.precio,
            propiedad.tipo_propiedad, propiedad.tipo_operacion, propiedad.ciudad,
            propiedad.estado, propiedad.direccion, propiedad.recamaras, propiedad.banos,
            propiedad.estacionamientos, propiedad.metros_construccion, propiedad.metros_terreno,
            propiedad.telefono_contacto, propiedad.email_contacto
        ))
        
        propiedad_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "mensaje": "Propiedad agregada exitosamente",
            "id": propiedad_id,
            "estado": "pendiente_aprobacion"
        }
        
    except Exception as e:
        logger.error(f"Error creando propiedad colaborativa: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# =====================================================
# ENDPOINTS DE WHATSAPP
# =====================================================

@app.post("/whatsapp/mensaje")
async def generar_mensaje_whatsapp(
    mensaje: MensajeWhatsApp,
    current_user: Usuario = Depends(get_current_user)
):
    """Genera mensaje personalizado de WhatsApp"""
    try:
        # Obtener información de la propiedad
        query = """
            SELECT titulo, precio, ciudad, tipo_operacion, tipo_propiedad, direccion, url_original as link
            FROM propiedades
            WHERE id = %s AND activo = true
        """
        
        propiedad_raw, _ = ejecutar_consulta(query, (int(mensaje.propiedad_id),), fetchall=False)
        
        if not propiedad_raw:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada")
        
        # Generar mensaje personalizado
        if mensaje.mensaje_personalizado:
            mensaje_final = mensaje.mensaje_personalizado
        else:
            # Mensaje por defecto con datos del usuario
            precio_texto = f"${propiedad_raw['precio']:,.0f}" if propiedad_raw['precio'] else "Precio a consultar"
            
            mensaje_final = f"""¡Hola! Me interesa esta propiedad:

🏠 *{propiedad_raw['titulo']}*
💰 {precio_texto}
📍 {propiedad_raw['ciudad']}, {propiedad_raw['direccion'] or 'Ubicación disponible'}
🏷️ {propiedad_raw['tipo_operacion']} - {propiedad_raw['tipo_propiedad']}

Mi información de contacto:
👤 Nombre: {current_user.nombre}
📱 Teléfono: {current_user.telefono}
📧 Email: {current_user.email}

¿Podrías proporcionarme más información?

Gracias."""
        
        # Generar URL de WhatsApp
        numero_limpio = re.sub(r'[^\d]', '', mensaje.numero_destino)
        if numero_limpio.startswith('52'):
            numero_limpio = numero_limpio[2:]  # Quitar código de país si ya está
        
        numero_whatsapp = f"52{numero_limpio}"
        mensaje_encoded = mensaje_final.replace('\n', '%0A').replace(' ', '%20')
        
        url_whatsapp = f"https://wa.me/{numero_whatsapp}?text={mensaje_encoded}"
        
        return {
            "url_whatsapp": url_whatsapp,
            "mensaje": mensaje_final,
            "numero_destino": numero_whatsapp,
            "propiedad": {
                "id": mensaje.propiedad_id,
                "titulo": propiedad_raw['titulo'],
                "precio": propiedad_raw['precio']
            }
        }
        
    except Exception as e:
        logger.error(f"Error generando mensaje WhatsApp: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/salud")
async def verificar_salud():
    """
    Verifica el estado del sistema y la base de datos
    """
    try:
        # Probar conexión a BD
        query = "SELECT COUNT(*) as total FROM propiedades WHERE activo = true"
        resultado, tiempo_ms = ejecutar_consulta(query, fetchall=False)
        
        return {
            "estado": "saludable",
            "version": "2.4.0 - TODOS LOS FILTROS FUNCIONALES",
            "base_datos": "conectada",
            "total_propiedades": resultado['total'],
            "tiempo_respuesta_ms": tiempo_ms,
            "correcciones": [
                "✅ Filtros de Operación corregidos (tipo_operacion)",
                "✅ Filtros de Amenidades funcionando",
                "✅ Características separadas (Recámaras, Baños, Estacionamientos)",
                "✅ CSS de checkboxes mejorado para alineación",
                "✅ Filtros de documentación implementados",
                "✅ Función de imagen mejorada con fallback",
                "✅ Rutas de imágenes corregidas",
                "✅ Filtros de ciudades limpios", 
                "✅ Consultas optimizadas"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "estado": "error",
                "base_datos": "desconectada",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# Endpoint adicional para compatibilidad con frontend actual
@app.get("/api/propiedades")
async def api_propiedades_compatibilidad():
    """Endpoint de compatibilidad con frontend actual"""
    # Redirigir a endpoint principal con parámetros por defecto
    return await listar_propiedades(pagina=1, por_pagina=12)

def generar_token_recuperacion() -> str:
    """Genera un token único para recuperación de contraseña"""
    return secrets.token_urlsafe(32)

def enviar_email_recuperacion(email: str, token: str):
    """Simula el envío de email de recuperación"""
    # Aquí implementarías el envío real de email
    logger.info(f"Email de recuperación enviado a {email} con token {token}")
    return True

@app.post("/recuperar-password")
async def solicitar_recuperacion_password(datos: RecuperarPassword):
    """Solicita recuperación de contraseña"""
    try:
        # Verificar si el usuario existe
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nombre FROM usuarios WHERE email = %s AND activo = true
        """, (datos.email,))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            # Por seguridad, no revelamos si el email existe
            return {"mensaje": "Si el email existe, recibirás instrucciones de recuperación"}
        
        # Generar token de recuperación
        token = generar_token_recuperacion()
        expiracion = datetime.utcnow() + timedelta(hours=1)  # Token válido por 1 hora
        
        # Guardar token en la base de datos
        cursor.execute("""
            INSERT INTO tokens_recuperacion (usuario_id, token, expiracion)
            VALUES (%s, %s, %s)
            ON CONFLICT (usuario_id) 
            DO UPDATE SET token = %s, expiracion = %s, usado = false
        """, (usuario[0], token, expiracion, token, expiracion))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Enviar email (simulado)
        enviar_email_recuperacion(datos.email, token)
        
        return {"mensaje": "Si el email existe, recibirás instrucciones de recuperación"}
        
    except Exception as e:
        logger.error(f"Error en recuperación de contraseña: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/cambiar-password")
async def cambiar_password(datos: CambiarPassword):
    """Cambia la contraseña usando token de recuperación"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar token
        cursor.execute("""
            SELECT tr.usuario_id, u.email 
            FROM tokens_recuperacion tr
            JOIN usuarios u ON tr.usuario_id = u.id
            WHERE tr.token = %s 
            AND tr.expiracion > %s 
            AND tr.usado = false
        """, (datos.token, datetime.utcnow()))
        
        resultado = cursor.fetchone()
        
        if not resultado:
            raise HTTPException(status_code=400, detail="Token inválido o expirado")
        
        usuario_id, email = resultado
        
        # Actualizar contraseña
        nueva_password_hash = hash_password(datos.nueva_password)
        
        cursor.execute("""
            UPDATE usuarios SET password_hash = %s WHERE id = %s
        """, (nueva_password_hash, usuario_id))
        
        # Marcar token como usado
        cursor.execute("""
            UPDATE tokens_recuperacion SET usado = true WHERE token = %s
        """, (datos.token,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"mensaje": "Contraseña actualizada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cambiando contraseña: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/contactos/{propiedad_id}")
async def agregar_contacto_propiedad(
    propiedad_id: str, 
    contacto: ContactoPropiedad,
    current_user: Usuario = Depends(get_current_user)
):
    """Agrega información de contacto a una propiedad"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO contactos_propiedades 
            (usuario_id, propiedad_id, nombre, telefono, email, notas)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (usuario_id, propiedad_id)
            DO UPDATE SET 
                nombre = %s, telefono = %s, email = %s, notas = %s,
                fecha_actualizacion = CURRENT_TIMESTAMP
            RETURNING id
        """, (
            current_user.id, propiedad_id, contacto.nombre, 
            contacto.telefono, contacto.email, contacto.notas,
            contacto.nombre, contacto.telefono, contacto.email, contacto.notas
        ))
        
        contacto_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"mensaje": "Contacto guardado exitosamente", "id": contacto_id}
        
    except Exception as e:
        logger.error(f"Error agregando contacto: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/contactos/{propiedad_id}")
async def obtener_contacto_propiedad(
    propiedad_id: str,
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene información de contacto de una propiedad"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT nombre, telefono, email, notas, fecha_creacion, fecha_actualizacion
            FROM contactos_propiedades
            WHERE usuario_id = %s AND propiedad_id = %s
        """, (current_user.id, propiedad_id))
        
        contacto = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not contacto:
            return None
            
        return {
            "nombre": contacto[0],
            "telefono": contacto[1],
            "email": contacto[2],
            "notas": contacto[3],
            "fecha_creacion": contacto[4],
            "fecha_actualizacion": contacto[5]
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo contacto: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/carpetas")
async def crear_carpeta_colaborativa(
    carpeta: CarpetaColaborativa,
    current_user: Usuario = Depends(get_current_user)
):
    """Crea una nueva carpeta colaborativa"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO carpetas_colaborativas (usuario_id, nombre, descripcion, es_publica)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (current_user.id, carpeta.nombre, carpeta.descripcion, carpeta.es_publica))
        
        carpeta_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"mensaje": "Carpeta creada exitosamente", "id": carpeta_id}
        
    except Exception as e:
        logger.error(f"Error creando carpeta: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/mis-carpetas")
async def obtener_mis_carpetas(current_user: Usuario = Depends(get_current_user)):
    """Obtiene las carpetas del usuario"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.id, c.nombre, c.descripcion, c.es_publica, c.fecha_creacion,
                   COUNT(cp.propiedad_id) as total_propiedades
            FROM carpetas_colaborativas c
            LEFT JOIN carpetas_propiedades cp ON c.id = cp.carpeta_id
            WHERE c.usuario_id = %s AND c.activa = true
            GROUP BY c.id, c.nombre, c.descripcion, c.es_publica, c.fecha_creacion
            ORDER BY c.fecha_creacion DESC
        """, (current_user.id,))
        
        carpetas = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {
            "carpetas": [
                {
                    "id": carpeta[0],
                    "nombre": carpeta[1],
                    "descripcion": carpeta[2],
                    "es_publica": carpeta[3],
                    "fecha_creacion": carpeta[4],
                    "total_propiedades": carpeta[5]
                }
                for carpeta in carpetas
            ]
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo carpetas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/carpetas/{carpeta_id}/propiedades/{propiedad_id}")
async def agregar_propiedad_a_carpeta(
    carpeta_id: int,
    propiedad_id: str,
    current_user: Usuario = Depends(get_current_user)
):
    """Agrega una propiedad a una carpeta"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que la carpeta pertenece al usuario
        cursor.execute("""
            SELECT id FROM carpetas_colaborativas 
            WHERE id = %s AND usuario_id = %s AND activa = true
        """, (carpeta_id, current_user.id))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Carpeta no encontrada")
        
        # Agregar propiedad a la carpeta
        cursor.execute("""
            INSERT INTO carpetas_propiedades (carpeta_id, propiedad_id)
            VALUES (%s, %s)
            ON CONFLICT (carpeta_id, propiedad_id) DO NOTHING
        """, (carpeta_id, propiedad_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"mensaje": "Propiedad agregada a la carpeta exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error agregando propiedad a carpeta: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Iniciando API PostgreSQL CORREGIDA v2.2")
    logger.info("📊 Base de datos: PostgreSQL")
    logger.info("⚡ Velocidad esperada: 10-100ms por consulta")
    logger.info("✅ CORRECCIONES APLICADAS:")
    logger.info("   - Rutas de imágenes con carpetas de fecha")
    logger.info("   - Filtros de ciudades limpios (solo Morelos)")
    logger.info("   - Filtros funcionales que actualizan resultados")
    logger.info("   - Consultas optimizadas")
    logger.info("🌐 Servidor: http://localhost:8000")
    logger.info("📚 Documentación: http://localhost:8000/docs")
    
    uvicorn.run(
        "api_postgresql:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 