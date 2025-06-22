#!/usr/bin/env python3
"""
API REST COMPLETA PARA RENDER - VERSIÓN FINAL
==============================================

Sistema inmobiliario completo con:
- ✅ Manejo de propiedades
- ✅ Subida y servicio de imágenes
- ✅ Sistema de usuarios
- ✅ Configuración para Render
- ✅ Sin dependencias problemáticas
"""

from fastapi import FastAPI, HTTPException, Query, Depends, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
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
import urllib.parse as urlparse

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la aplicación
app = FastAPI(
    title="API Inmobiliaria Completa para Render",
    description="Sistema inmobiliario completo con manejo de imágenes",
    version="4.0.0 - RENDER COMPLETO"
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
SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_super_segura_para_render_2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 días

# Configuración de base de datos para Render
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    url = urlparse.urlparse(DATABASE_URL)
    DB_CONFIG = {
        'host': url.hostname,
        'database': url.path[1:],
        'user': url.username,
        'password': url.password,
        'port': url.port or 5432
    }
else:
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'propiedades_db'),
        'user': os.getenv('DB_USER', 'pabloravel'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': int(os.getenv('DB_PORT', 5432))
    }

# Seguridad
security = HTTPBearer(auto_error=False)

# Ciudades válidas de Morelos
CIUDADES_MORELOS = {
    'Cuernavaca', 'Jiutepec', 'Temixco', 'Emiliano Zapata', 'Xochitepec',
    'Yautepec', 'Cuautla', 'Ayala', 'Tepoztlán', 'Huitzilac', 'Tetela del Volcán'
}

# =====================================================
# CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS PARA IMÁGENES
# =====================================================

# Crear directorio para imágenes si no existe
IMAGENES_DIR = Path("static/imagenes")
IMAGENES_DIR.mkdir(parents=True, exist_ok=True)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# =====================================================
# VALIDADORES Y UTILIDADES
# =====================================================

def validar_email(email: str) -> bool:
    """Validador de email simple sin dependencias externas"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def hash_password(password: str) -> str:
    """Hash de contraseña"""
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

def get_db_connection():
    """Conexión a base de datos"""
    return psycopg2.connect(**DB_CONFIG)

def generar_url_imagen(nombre_imagen: str) -> str:
    """Generar URL completa para imagen"""
    if not nombre_imagen:
        return None
    
    # Si ya es una URL completa, devolverla tal como está
    if nombre_imagen.startswith('http') or nombre_imagen.startswith('/static'):
        return nombre_imagen
    
    # Si es un nombre de archivo con formato fecha, generar ruta
    if '-2025-' in nombre_imagen:
        fecha_match = re.search(r'2025-\d{2}-\d{2}', nombre_imagen)
        if fecha_match:
            fecha = fecha_match.group()
            return f"/static/imagenes/{fecha}/{nombre_imagen}"
    
    # URL por defecto
    return f"/static/imagenes/{nombre_imagen}"

# =====================================================
# MODELOS PYDANTIC
# =====================================================

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

class UsuarioRegistro(BaseModel):
    nombre: str
    email: str = Field(..., description="Email del usuario")
    telefono: str
    password: str

class UsuarioLogin(BaseModel):
    email: str = Field(..., description="Email del usuario")
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

# =====================================================
# FUNCIONES DE AUTENTICACIÓN
# =====================================================

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

# =====================================================
# ENDPOINTS PARA MANEJO DE IMÁGENES
# =====================================================

@app.post("/subir-imagen")
async def subir_imagen(
    imagen: UploadFile = File(...),
    carpeta: str = Form(...)
):
    """Endpoint para recibir imágenes y guardarlas en Render"""
    try:
        # Crear carpeta si no existe
        carpeta_destino = IMAGENES_DIR / carpeta
        carpeta_destino.mkdir(parents=True, exist_ok=True)
        
        # Guardar imagen
        ruta_imagen = carpeta_destino / imagen.filename
        
        with open(ruta_imagen, "wb") as f:
            contenido = await imagen.read()
            f.write(contenido)
        
        # URL pública de la imagen
        url_publica = f"/static/imagenes/{carpeta}/{imagen.filename}"
        
        logger.info(f"Imagen subida exitosamente: {url_publica}")
        
        return {
            "success": True,
            "url": url_publica,
            "mensaje": f"Imagen {imagen.filename} subida exitosamente"
        }
        
    except Exception as e:
        logger.error(f"Error subiendo imagen: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/imagen/{carpeta}/{nombre_imagen}")
async def servir_imagen(carpeta: str, nombre_imagen: str):
    """Servir imágenes directamente"""
    try:
        ruta_imagen = IMAGENES_DIR / carpeta / nombre_imagen
        if ruta_imagen.exists():
            return FileResponse(ruta_imagen)
        else:
            raise HTTPException(status_code=404, detail="Imagen no encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sirviendo imagen: {str(e)}")

# =====================================================
# ENDPOINTS PRINCIPALES
# =====================================================

@app.get("/")
def root():
    """Endpoint raíz para Render"""
    return {"status": "running", "service": "propiedades-api", "version": "4.0"}

@app.get("/health")
def health_check():
    """Health check para Render"""
    return {"status": "healthy", "service": "propiedades-api", "version": "4.0"}

@app.get("/salud")
def salud_check():
    """Health check en español"""
    return {"status": "ok", "mensaje": "Sistema funcionando correctamente"}

@app.get("/ping")
def ping():
    """Ping simple"""
    return "pong"

@app.get("/propiedades", response_model=RespuestaPaginada)
async def listar_propiedades(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(60, ge=1, le=500, description="Propiedades por página"),
    precio_min: Optional[float] = Query(1, description="Precio mínimo")
):
    """Listar propiedades con filtros básicos"""
    inicio = time.time()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Consulta base con filtro de precio mínimo
        query_base = """
            SELECT 
                id, titulo, descripcion, precio, ciudad, tipo_operacion, 
                tipo_propiedad, imagen, direccion, estado, link, 
                recamaras, banos, estacionamientos, superficie_m2,
                amenidades, caracteristicas, created_at
            FROM propiedades 
            WHERE activo = true AND precio >= %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        
        query_count = "SELECT COUNT(*) FROM propiedades WHERE activo = true AND precio >= %s"
        
        offset = (pagina - 1) * por_pagina
        
        # Contar total
        cursor.execute(query_count, (precio_min,))
        total = cursor.fetchone()['count']
        
        # Obtener propiedades
        cursor.execute(query_base, (precio_min, por_pagina, offset))
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
            
            prop_dict['es_favorito'] = False
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
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                id, titulo, precio, ciudad, tipo_operacion, tipo_propiedad,
                descripcion, link, imagen, direccion, estado, recamaras, banos,
                estacionamientos, superficie_m2, amenidades, caracteristicas,
                imagenes, created_at
            FROM propiedades 
            WHERE id = %s AND activo = true
        """, (propiedad_id,))
        
        propiedad = cursor.fetchone()
        conn.close()
        
        if not propiedad:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada")
        
        prop_dict = dict(propiedad)
        
        # Generar URL de imagen
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
        
        conn.close()
        
        tipos_operacion = {item['tipo_operacion']: item['cantidad'] for item in tipos_operacion_data}
        
        tiempo_ms = (time.time() - inicio) * 1000
        
        return Estadisticas(
            total_propiedades=total_propiedades,
            con_precio=con_precio,
            precio_promedio=float(precios['promedio'] or 0),
            precio_minimo=float(precios['minimo'] or 0),
            precio_maximo=float(precios['maximo'] or 0),
            tipos_operacion=tipos_operacion,
            tiempo_consulta_ms=tiempo_ms
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")

# =====================================================
# ENDPOINTS DE USUARIO
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
            raise HTTPException(status_code=400, detail="El usuario ya existe")
        
        # Hash de la contraseña
        hashed_password = hash_password(usuario.password)
        
        # Insertar usuario
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, telefono, password_hash, es_admin, activo, fecha_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (usuario.nombre, usuario.email, usuario.telefono, hashed_password, False, True, datetime.utcnow()))
        
        new_user = cursor.fetchone()
        conn.commit()
        conn.close()
        
        # Crear token
        access_token = create_access_token(data={"sub": usuario.email})
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            usuario=Usuario(**new_user)
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
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM usuarios WHERE email = %s AND activo = true", (usuario.email,))
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data or not verify_password(usuario.password, user_data['password_hash']):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        # Crear token
        access_token = create_access_token(data={"sub": usuario.email})
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            usuario=Usuario(**user_data)
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
# STARTUP
# =====================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port) 