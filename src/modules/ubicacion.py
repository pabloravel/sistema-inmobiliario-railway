#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MÓDULO DE PROCESAMIENTO DE UBICACIONES
------------------------------------

Este módulo es responsable de extraer y normalizar información de ubicación
de las propiedades, incluyendo ciudad, colonia, calle y referencias.

RESPONSABILIDADES:
1. Extraer ubicaciones de texto
2. Normalizar nombres de ubicaciones
3. Validar ubicaciones contra catálogos
4. Mantener catálogos de ubicaciones conocidas
5. Proveer estadísticas de confianza
6. Corregir ciudades en PostgreSQL

REGLAS:
1. Mantener catálogos actualizados
2. NO modificar otros aspectos de la propiedad
3. Mantener registro de decisiones tomadas
4. En caso de duda, marcar como NO_ENCONTRADO
"""

import re
import json
import logging
from typing import Dict, Optional, List, Tuple
from pathlib import Path
from decimal import Decimal

# Configuración de logging
logger = logging.getLogger('ubicacion')
logger.setLevel(logging.DEBUG)

# Constantes y configuración

# Ciudades principales de México
CIUDADES_MEXICO = [
    # Morelos
    "Cuernavaca", "Jiutepec", "Temixco", "Emiliano Zapata", "Xochitepec", 
    "Tepoztlán", "Yautepec", "Cuautla", "Jojutla", "Zacatepec",
    
    # Ciudad de México y área metropolitana
    "Ciudad de México", "CDMX", "México", "Distrito Federal", "DF",
    "Naucalpan", "Tlalnepantla", "Ecatepec", "Nezahualcóyotl", "Tlalpan",
    "Coyoacán", "Benito Juárez", "Miguel Hidalgo", "Cuauhtémoc", "Iztapalapa",
    "Xochimilco", "Tláhuac", "Milpa Alta", "Cuajimalpa", "Álvaro Obregón",
    "Azcapotzalco", "Gustavo A. Madero", "Iztacalco", "Magdalena Contreras",
    "Venustiano Carranza",
    
    # Estado de México
    "Toluca", "Metepec", "Lerma", "Atizapán", "Cuautitlán", "Texcoco",
    "Chalco", "Valle de Chalco", "Chimalhuacán", "La Paz", "Ixtapaluca",
    "Tecámac", "Coacalco", "Tultitlán", "Huixquilucan", "Satélite",
    
    # Jalisco
    "Guadalajara", "Zapopan", "Tlaquepaque", "Tonalá", "Tlajomulco",
    "Puerto Vallarta", "Chapala", "Ajijic",
    
    # Nuevo León
    "Monterrey", "San Pedro Garza García", "Santa Catarina", "Guadalupe",
    "Apodaca", "General Escobedo", "San Nicolás de los Garza",
    
    # Quintana Roo
    "Cancún", "Playa del Carmen", "Cozumel", "Tulum", "Chetumal",
    "Isla Mujeres", "Puerto Morelos", "Akumal", "Bacalar",
    
    # Yucatán
    "Mérida", "Valladolid", "Progreso", "Uman", "Kanasín",
    
    # Puebla
    "Puebla", "Cholula", "San Pedro Cholula", "San Andrés Cholula",
    "Atlixco", "Tehuacán", "Amozoc",
    
    # Querétaro
    "Querétaro", "Santiago de Querétaro", "El Marqués", "Corregidora",
    
    # Guanajuato
    "León", "Guanajuato", "Irapuato", "Celaya", "Salamanca", "San Miguel de Allende",
    
    # Veracruz
    "Veracruz", "Xalapa", "Coatzacoalcos", "Córdoba", "Orizaba", "Poza Rica",
    
    # Baja California
    "Tijuana", "Mexicali", "Ensenada", "Tecate", "Playas de Rosarito",
    
    # Baja California Sur
    "La Paz", "Los Cabos", "Cabo San Lucas", "San José del Cabo", "Loreto",
    
    # Sonora
    "Hermosillo", "Ciudad Obregón", "Nogales", "Navojoa", "Guaymas",
    
    # Chihuahua
    "Chihuahua", "Ciudad Juárez", "Delicias", "Parral", "Cuauhtémoc",
    
    # Coahuila
    "Saltillo", "Torreón", "Monclova", "Piedras Negras", "Acuña",
    
    # Tamaulipas
    "Tampico", "Reynosa", "Matamoros", "Nuevo Laredo", "Ciudad Victoria",
    
    # Sinaloa
    "Culiacán", "Mazatlán", "Los Mochis", "Guasave", "Navolato",
    
    # Michoacán
    "Morelia", "Uruapan", "Zamora", "Lázaro Cárdenas", "Pátzcuaro",
    
    # Oaxaca
    "Oaxaca", "Salina Cruz", "Tuxtepec", "Juchitán", "Puerto Escondido",
    
    # Chiapas
    "Tuxtla Gutiérrez", "San Cristóbal de las Casas", "Tapachula", "Comitán",
    
    # Guerrero
    "Acapulco", "Chilpancingo", "Iguala", "Taxco", "Zihuatanejo", "Ixtapa",
    
    # Hidalgo
    "Pachuca", "Tulancingo", "Tizayuca", "Huejutla",
    
    # Tlaxcala
    "Tlaxcala", "Apizaco", "Huamantla",
    
    # Aguascalientes
    "Aguascalientes", "Jesús María", "Calvillo",
    
    # Colima
    "Colima", "Manzanillo", "Tecomán", "Villa de Álvarez",
    
    # Durango
    "Durango", "Gómez Palacio", "Lerdo", "Santiago Papasquiaro",
    
    # Nayarit
    "Tepic", "Bahía de Banderas", "Puerto Vallarta", "Compostela",
    
    # San Luis Potosí
    "San Luis Potosí", "Soledad de Graciano Sánchez", "Ciudad Valles",
    
    # Zacatecas
    "Zacatecas", "Fresnillo", "Guadalupe", "Jerez",
    
    # Campeche
    "Campeche", "Ciudad del Carmen", "Champotón",
    
    # Tabasco
    "Villahermosa", "Cárdenas", "Comalcalco", "Huimanguillo"
]

# Cargar catálogos
def cargar_catalogos() -> Dict:
    """
    Carga los catálogos de ubicaciones conocidas.
    """
    try:
        catalogs_path = Path(__file__).parent.parent.parent / 'known_locations.json'
        with open(catalogs_path) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando catálogos: {str(e)}")
        return {
            "ciudades": {},
            "colonias": {},
            "calles": {},
            "referencias": {}
        }

# Cargar catálogos al inicio
CATALOGOS = cargar_catalogos()

class UbicacionInvalida(Exception):
    """Excepción para ubicaciones inválidas"""
    pass

def _normalizar_texto(texto: str) -> str:
    """
    Normaliza texto para análisis.
    USO INTERNO ÚNICAMENTE.
    """
    if not texto:
        return ""
    
    # Convertir a minúsculas y eliminar espacios extras
    texto = texto.lower().strip()
    texto = re.sub(r'\s+', ' ', texto)
    
    # Normalizar caracteres especiales
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u', 'ñ': 'n', 'à': 'a', 'è': 'e', 'ì': 'i',
        'ò': 'o', 'ù': 'u'
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    
    return texto

def _extraer_texto_seguro(valor) -> Optional[str]:
    """
    Extrae texto de forma segura de cualquier tipo de valor.
    USO INTERNO ÚNICAMENTE.
    """
    try:
        if valor is None:
            return None
        
        if isinstance(valor, str):
            return valor.strip() if valor.strip() else None
        
        if isinstance(valor, (int, float, Decimal)):
            return str(valor)
        
        if isinstance(valor, dict):
            # Si es un dict, buscar campos comunes de texto
            campos_texto = ['texto', 'descripcion', 'titulo', 'contenido', 'value']
            for campo in campos_texto:
                if campo in valor and valor[campo]:
                    return str(valor[campo])
            return None
        
        if isinstance(valor, list):
            # Si es una lista, unir elementos de texto
            textos = []
            for item in valor:
                texto = _extraer_texto_seguro(item)
                if texto:
                    textos.append(texto)
            return " ".join(textos) if textos else None
        
        # Para otros tipos, convertir a string
        return str(valor)
        
    except Exception as e:
        logger.debug(f"Error extrayendo texto de {type(valor)}: {str(e)}")
        return None

def extraer_ciudad(texto: str) -> Dict[str, any]:
    """
    Extrae información de ciudad del texto proporcionado.
    Busca ciudades de Morelos en el texto usando patrones específicos.
    FILTROS ANTI-BASURA IMPLEMENTADOS.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con ciudad, confianza y detalles
    """
    if not texto:
        return {"ciudad": None, "confianza": 0.0, "metodo": "texto_vacio"}
    
    texto_limpio = texto.upper().strip()
    
    # FILTROS ANTI-BASURA - Rechazar textos que NO son ciudades
    textos_basura = [
        'PUBLICADO', 'HACE', 'HACE UN', 'HACE UNA', 'HACE DOS', 'HACE TRES',
        'RENTO', 'RENTA', 'VENTA', 'VENDO', 'SE VENDE', 'SE RENTA',
        'CASA EN VENTA', 'CASA EN RENTA', 'DEPA', 'DEPARTAMENTO',
        'COL', 'COLONIA', 'FRACCIONAMIENTO', 'FRACC',
        'BOULEVARD', 'BLVD', 'AVENIDA', 'AV', 'CALLE', 'C.',
        'TERRENO', 'LOTE', 'PREDIO', 'EDIFICIO', 'OFICINA',
        'LOCAL', 'COMERCIAL', 'RESIDENCIAL', 'PRIVADA',
        'CAMINO', 'CARRETERA', 'CARR', 'KM', 'KILÓMETRO',
        'NORTE', 'SUR', 'ESTE', 'OESTE', 'PONIENTE', 'ORIENTE',
        'CENTRO', 'PLAZA', 'PASEO', 'CERRADA', 'CALZADA',
        'RETORNO', 'CIRCUITO', 'ANDADOR', 'PROLONGACIÓN',
        'NINGUNO', 'NO DISPONIBLE', 'N/A', 'SIN ESPECIFICAR'
    ]
    
    # Si el texto es solo basura, rechazarlo inmediatamente
    if any(basura == texto_limpio for basura in textos_basura):
        return {"ciudad": None, "confianza": 0.0, "metodo": "texto_basura_rechazado"}
    
    # Si el texto contiene más del 70% de palabras basura, rechazarlo
    palabras = texto_limpio.split()
    palabras_basura_encontradas = sum(1 for palabra in palabras if any(basura in palabra for basura in textos_basura))
    if len(palabras) > 0 and (palabras_basura_encontradas / len(palabras)) > 0.7:
        return {"ciudad": None, "confianza": 0.0, "metodo": "mayoria_basura_rechazado"}
    
    # Lista de ciudades de Morelos con variaciones
    ciudades_morelos = {
        'CUERNAVACA': ['CUERNAVACA', 'CUERNAVACA MORELOS', 'CENTRO CUERNAVACA', 'OCOTEPEC'],
        'JIUTEPEC': ['JIUTEPEC', 'JIUTEPEC MORELOS', 'COL. EL PORVENIR JIUTEPEC'],
        'TEMIXCO': ['TEMIXCO', 'TEMIXCO MORELOS'],
        'EMILIANO ZAPATA': ['EMILIANO ZAPATA', 'ZAPATA', 'EMILIANO ZAPATA MORELOS'],
        'XOCHITEPEC': ['XOCHITEPEC', 'XOCHITEPEC MORELOS'],
        'YAUTEPEC': ['YAUTEPEC', 'YAUTEPEC MORELOS'],
        'CUAUTLA': ['CUAUTLA', 'CUAUTLA MORELOS'],
        'TEPOZTLAN': ['TEPOZTLAN', 'TEPOZTLÁN', 'TEPOZTLAN MORELOS'],
        'HUITZILAC': ['HUITZILAC', 'HUITZILAC MORELOS'],
        'TRES MARIAS': ['TRES MARIAS', '3 MARIAS', 'TRES MARÍAS'],
        'TLALTIZAPAN': ['TLALTIZAPAN', 'TLALTIZAPÁN'],
        'ZACATEPEC': ['ZACATEPEC', 'ZACATEPEC MORELOS'],
        'AYALA': ['AYALA', 'AYALA MORELOS']
    }
    
    # Buscar cada ciudad y sus variaciones
    for ciudad_oficial, variaciones in ciudades_morelos.items():
        for variacion in variaciones:
            if variacion in texto_limpio:
                # Verificar que no sea una coincidencia accidental con basura
                # Por ejemplo, "CUERNAVACA" en "RENTA CASA EN CUERNAVACA NORTE"
                palabras_texto = texto_limpio.split()
                ciudad_encontrada_limpia = False
                
                # Verificar si la ciudad aparece como palabra completa o en contexto válido
                if variacion in palabras_texto:
                    ciudad_encontrada_limpia = True
                elif any(f"{variacion} " in texto_limpio, f" {variacion}" in texto_limpio, 
                        f"{variacion}," in texto_limpio, f"{variacion}." in texto_limpio):
                    ciudad_encontrada_limpia = True
                
                if ciudad_encontrada_limpia:
                    # Calcular confianza basada en contexto
                    confianza = 0.8
                    
                    # Aumentar confianza si aparece con "MORELOS"
                    if 'MORELOS' in texto_limpio:
                        confianza = 0.95
                    
                    # Aumentar confianza si aparece en contexto de ubicación válido
                    contextos_ubicacion = ['UBICACIÓN', 'UBICADA EN', 'MUNICIPIO', 'ESTADO']
                    for contexto in contextos_ubicacion:
                        if contexto in texto_limpio:
                            confianza = min(0.99, confianza + 0.1)
                            break
                    
                    return {
                        "ciudad": ciudad_oficial.title(),
                        "confianza": confianza,
                        "metodo": f"patron_directo_{variacion}",
                        "texto_encontrado": variacion
                    }
    
    return {
        "ciudad": None,
        "confianza": 0.0,
        "metodo": "no_encontrado"
    }

def determinar_estado_por_ciudad(ciudad: str) -> str:
    """Determina el estado basado en la ciudad"""
    mapeo_estados = {
        # Morelos
        "Cuernavaca": "Morelos", "Jiutepec": "Morelos", "Temixco": "Morelos",
        "Emiliano Zapata": "Morelos", "Xochitepec": "Morelos", "Tepoztlán": "Morelos",
        "Yautepec": "Morelos", "Cuautla": "Morelos", "Jojutla": "Morelos", "Zacatepec": "Morelos",
        
        # Ciudad de México
        "Ciudad de México": "Ciudad de México", "CDMX": "Ciudad de México", 
        "México": "Ciudad de México", "Distrito Federal": "Ciudad de México",
        "Tlalpan": "Ciudad de México", "Coyoacán": "Ciudad de México",
        "Benito Juárez": "Ciudad de México", "Miguel Hidalgo": "Ciudad de México",
        "Cuauhtémoc": "Ciudad de México", "Iztapalapa": "Ciudad de México",
        
        # Estado de México
        "Toluca": "Estado de México", "Metepec": "Estado de México", 
        "Naucalpan": "Estado de México", "Tlalnepantla": "Estado de México",
        "Ecatepec": "Estado de México", "Nezahualcóyotl": "Estado de México",
        
        # Jalisco
        "Guadalajara": "Jalisco", "Zapopan": "Jalisco", "Puerto Vallarta": "Jalisco",
        "Tlaquepaque": "Jalisco", "Tonalá": "Jalisco",
        
        # Nuevo León
        "Monterrey": "Nuevo León", "San Pedro Garza García": "Nuevo León",
        "Santa Catarina": "Nuevo León", "Guadalupe": "Nuevo León",
        
        # Quintana Roo
        "Cancún": "Quintana Roo", "Playa del Carmen": "Quintana Roo",
        "Cozumel": "Quintana Roo", "Tulum": "Quintana Roo",
        
        # Yucatán
        "Mérida": "Yucatán", "Valladolid": "Yucatán", "Progreso": "Yucatán",
        
        # Puebla
        "Puebla": "Puebla", "Cholula": "Puebla", "San Pedro Cholula": "Puebla",
        
        # Querétaro
        "Querétaro": "Querétaro", "Santiago de Querétaro": "Querétaro",
        
        # Guanajuato
        "León": "Guanajuato", "Guanajuato": "Guanajuato", "Irapuato": "Guanajuato",
        "Celaya": "Guanajuato", "Salamanca": "Guanajuato", "San Miguel de Allende": "Guanajuato",
        
        # Agregar más según necesidad...
    }
    
    return mapeo_estados.get(ciudad, "México")

def extraer_colonia(texto: str) -> Dict:
    """
    Extrae información de colonia del texto.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - colonia: str o None
        - tipo: str (colonia, fraccionamiento, unidad habitacional, etc.)
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    resultado = {
        "colonia": None,
        "tipo": "colonia",
        "confianza": 0.0,
        "evidencia": []
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    
    # Patrones para diferentes tipos de asentamientos
    patrones = [
        (r'colonia\s+([a-z\s]+?)(?:\s|,|$)', "colonia", 0.9),
        (r'col\.?\s+([a-z\s]+?)(?:\s|,|$)', "colonia", 0.85),
        (r'fraccionamiento\s+([a-z\s]+?)(?:\s|,|$)', "fraccionamiento", 0.9),
        (r'fracc\.?\s+([a-z\s]+?)(?:\s|,|$)', "fraccionamiento", 0.85),
        (r'unidad\s+habitacional\s+([a-z\s]+?)(?:\s|,|$)', "unidad habitacional", 0.9),
        (r'u\.?\s?h\.?\s+([a-z\s]+?)(?:\s|,|$)', "unidad habitacional", 0.8),
        (r'residencial\s+([a-z\s]+?)(?:\s|,|$)', "residencial", 0.9),
        (r'condominio\s+([a-z\s]+?)(?:\s|,|$)', "condominio", 0.9),
        (r'privada\s+([a-z\s]+?)(?:\s|,|$)', "privada", 0.85),
        (r'barrio\s+([a-z\s]+?)(?:\s|,|$)', "barrio", 0.8)
    ]
    
    for patron, tipo, confianza_base in patrones:
        if match := re.search(patron, texto_norm):
            colonia = match.group(1).strip()
            # Limpiar la colonia de palabras comunes al final
            colonia = re.sub(r'\s+(centro|norte|sur|este|oeste|poniente|oriente)$', '', colonia)
            
            if len(colonia) > 2:  # Evitar colonias muy cortas
                resultado.update({
                    "colonia": colonia.title(),
                    "tipo": tipo,
                    "confianza": confianza_base,
                    "evidencia": [f"{tipo.title()} encontrada: {colonia}"]
                })
                return resultado
    
    return resultado

def extraer_calle(texto: str) -> Dict:
    """
    Extrae información de calle del texto.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - calle: str o None
        - numero: str o None
        - referencias: List[str]
        - confianza: float (0-1)
    """
    resultado = {
        "calle": None,
        "numero": None,
        "referencias": [],
        "confianza": 0.0
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    
    # Patrones para calles
    patrones_calle = [
        r'calle\s+([a-z0-9\s]+)',
        r'av(?:enida)?\.?\s+([a-z0-9\s]+)',
        r'blvd?\.?\s+([a-z0-9\s]+)',
        r'boulevard\s+([a-z0-9\s]+)',
        r'calz(?:ada)?\.?\s+([a-z0-9\s]+)'
    ]
    
    # Buscar calle
    for patron in patrones_calle:
        if match := re.search(patron, texto_norm):
            calle = match.group(1).strip()
            # Limpiar número y referencias
            calle = re.sub(r'\s+#?\d+\s*$', '', calle)
            calle = re.sub(r'\s+(?:cerca|junto|frente|atras|detras|esquina|entre)\s+.*$', '', calle)
            
            resultado.update({
                "calle": calle.title(),
                "confianza": 0.8
            })
            break
    
    # Buscar número
    if match := re.search(r'#?\s*(\d+(?:-\w+)?)', texto_norm):
        resultado["numero"] = match.group(1)
        resultado["confianza"] = min(resultado["confianza"] + 0.1, 1.0)
    
    # Buscar referencias
    referencias = []
    patrones_ref = [
        r'cerca\s+(?:de\s+)?(.+?)(?:\.|$)',
        r'junto\s+(?:a\s+)?(.+?)(?:\.|$)',
        r'frente\s+(?:a\s+)?(.+?)(?:\.|$)',
        r'entre\s+(.+?)\s+y\s+(.+?)(?:\.|$)'
    ]
    
    for patron in patrones_ref:
        if match := re.search(patron, texto_norm):
            grupos = match.groups()
            for ref in grupos:
                if ref and len(ref) > 3:  # Ignorar referencias muy cortas
                    referencias.append(ref.strip().title())
    
    if referencias:
        resultado["referencias"] = referencias
        resultado["confianza"] = min(resultado["confianza"] + 0.1, 1.0)
    
    return resultado

def actualizar_ubicacion(propiedad: Dict) -> Dict:
    """
    Actualiza la información de ubicación en una propiedad.
    Esta es la función principal que otros módulos deben usar.
    
    Args:
        propiedad: Dict con datos de la propiedad
        
    Returns:
        Dict: Propiedad con ubicación actualizada
    """
    try:
        # Extraer textos relevantes
        textos = []
        
        # Priorizar ubicación específica si existe
        if "ubicacion" in propiedad:
            texto_ubicacion = _extraer_texto_seguro(propiedad["ubicacion"])
            if texto_ubicacion:
                textos.append(texto_ubicacion)
        
        # Agregar descripción original
        if "descripcion_original" in propiedad:
            textos.append(propiedad["descripcion_original"])
        
        # Agregar título
        if "titulo" in propiedad:
            textos.append(propiedad["titulo"])
        
        # Combinar textos
        texto_completo = " ".join(textos)
        
        # Extraer información
        info_ciudad = extraer_ciudad(texto_completo)
        info_colonia = extraer_colonia(texto_completo)
        info_calle = extraer_calle(texto_completo)
        
        # Actualizar la propiedad
        if "propiedad" not in propiedad:
            propiedad["propiedad"] = {}
            
        propiedad["propiedad"]["ubicacion"] = {
            "ciudad": info_ciudad["ciudad"],
            "estado": info_ciudad["estado"],
            "colonia": info_colonia["colonia"],
            "tipo_colonia": info_colonia["tipo"],
            "calle": info_calle["calle"],
            "numero": info_calle["numero"],
            "referencias": info_calle["referencias"],
            "confianza": max(
                info_ciudad["confianza"],
                info_colonia["confianza"],
                info_calle["confianza"]
            ),
            "evidencia": {
                "ciudad": info_ciudad["evidencia"],
                "colonia": info_colonia["evidencia"]
            }
        }
        
        return propiedad
        
    except Exception as e:
        logger.error(f"Error actualizando ubicación: {str(e)}")
        return propiedad

def corregir_ciudades_desde_json() -> Dict:
    """
    Corrige las ciudades en PostgreSQL leyendo directamente del archivo JSON principal.
    Utiliza los datos de ubicación en datos_originales.ubicacion.
    
    Returns:
        Dict con estadísticas de la corrección
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        import json
        
        # Configuración de base de datos
        DB_CONFIG = {
            'host': 'localhost',
            'database': 'propiedades_db',
            'user': 'pabloravel',
            'port': 5432
        }
        
        logger.info("🔄 Iniciando corrección de ciudades desde archivo JSON...")
        
        # Cargar datos del archivo JSON principal
        with open('resultados/propiedades_estructuradas.json', 'r') as f:
            propiedades_json = json.load(f)
        
        logger.info(f"📊 Cargadas {len(propiedades_json)} propiedades del JSON")
        
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Estadísticas
        stats = {
            "total_analizadas": 0,
            "ciudades_corregidas": 0,
            "colonias_corregidas": 0,
            "ciudades_encontradas": {},
            "colonias_encontradas": {},
            "errores": 0
        }
        
        # Procesar cada propiedad del JSON
        for prop_json in propiedades_json:
            try:
                # Obtener ID de la propiedad
                prop_id = prop_json.get('datos_originales', {}).get('id')
                if not prop_id:
                    continue
                
                # Buscar datos de ubicación en el JSON
                ubicacion_data = prop_json.get('datos_originales', {}).get('ubicacion')
                if not ubicacion_data or not isinstance(ubicacion_data, dict):
                    continue
                
                stats["total_analizadas"] += 1
                
                # Extraer ciudad y colonia del JSON
                ciudad_json = ubicacion_data.get('ciudad', '').strip()
                direccion_completa = ubicacion_data.get('direccion_completa', '').strip()
                
                # Validar ciudad
                if ciudad_json and ciudad_json != '':
                    # Normalizar nombres de ciudades conocidas
                    ciudades_normalizadas = {
                        'Tres de Mayo': 'Emiliano Zapata',  # Tres de Mayo es parte de Emiliano Zapata
                        'Burgos': 'Temixco',  # Burgos es una colonia de Temixco
                        'Jiutepec': 'Jiutepec',
                        'Emiliano Zapata': 'Emiliano Zapata',
                        'Cuernavaca': 'Cuernavaca',
                        'Temixco': 'Temixco',
                        'Xochitepec': 'Xochitepec',
                        'Yautepec': 'Yautepec',
                        'Cuautla': 'Cuautla',
                        'Tepoztlán': 'Tepoztlán',
                        'Huitzilac': 'Huitzilac',
                        'Tlaltizapán': 'Tlaltizapán',
                        'Zacatepec': 'Zacatepec'
                    }
                    
                    ciudad_normalizada = ciudades_normalizadas.get(ciudad_json, ciudad_json)
                    
                    # Verificar si la propiedad existe en la base de datos
                    cursor.execute("SELECT id, ciudad, colonia FROM propiedades WHERE id = %s", (prop_id,))
                    prop_bd = cursor.fetchone()
                    
                    if prop_bd:
                        # Actualizar ciudad si es diferente
                        if prop_bd['ciudad'] != ciudad_normalizada:
                            cursor.execute(
                                "UPDATE propiedades SET ciudad = %s WHERE id = %s",
                                (ciudad_normalizada, prop_id)
                            )
                            stats["ciudades_corregidas"] += 1
                            stats["ciudades_encontradas"][ciudad_normalizada] = stats["ciudades_encontradas"].get(ciudad_normalizada, 0) + 1
                            logger.info(f"✅ Ciudad {prop_id}: {prop_bd['ciudad']} → {ciudad_normalizada}")
                        
                        # Extraer colonia de la dirección completa
                        if direccion_completa:
                            info_colonia = extraer_colonia(direccion_completa)
                            colonia_extraida = info_colonia.get('colonia')
                            
                            if colonia_extraida and colonia_extraida.strip() != '':
                                # Actualizar colonia si es diferente o está vacía
                                if not prop_bd['colonia'] or prop_bd['colonia'] != colonia_extraida:
                                    cursor.execute(
                                        "UPDATE propiedades SET colonia = %s WHERE id = %s",
                                        (colonia_extraida, prop_id)
                                    )
                                    stats["colonias_corregidas"] += 1
                                    stats["colonias_encontradas"][colonia_extraida] = stats["colonias_encontradas"].get(colonia_extraida, 0) + 1
                                    logger.info(f"✅ Colonia {prop_id}: {prop_bd['colonia']} → {colonia_extraida}")
                
            except Exception as e:
                stats["errores"] += 1
                logger.error(f"❌ Error procesando propiedad {prop_id}: {str(e)}")
                continue
        
        # Confirmar cambios
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"🎉 Corrección desde JSON completada:")
        logger.info(f"   • Propiedades analizadas: {stats['total_analizadas']}")
        logger.info(f"   • Ciudades corregidas: {stats['ciudades_corregidas']}")
        logger.info(f"   • Colonias corregidas: {stats['colonias_corregidas']}")
        logger.info(f"   • Errores: {stats['errores']}")
        logger.info(f"   • Ciudades encontradas: {stats['ciudades_encontradas']}")
        logger.info(f"   • Colonias encontradas: {stats['colonias_encontradas']}")
        
        return stats
        
    except Exception as e:
        logger.error(f"💥 Error en corrección desde JSON: {str(e)}")
        return {
            "error": str(e),
            "total_analizadas": 0,
            "ciudades_corregidas": 0,
            "errores": 1
        }

def validar_ubicacion(ubicacion: Dict) -> bool:
    """
    Valida si una ubicación es válida y completa.
    
    Args:
        ubicacion: Dict con datos de ubicación
        
    Returns:
        bool: True si la ubicación es válida
    """
    # Debe tener al menos ciudad
    if not ubicacion.get("ciudad"):
        return False
    
    # La confianza debe ser razonable
    if ubicacion.get("confianza", 0) < 0.5:
        return False
    
    return True

def obtener_estadisticas(propiedades: List[Dict]) -> Dict:
    """
    Genera estadísticas sobre ubicaciones.
    
    Args:
        propiedades: Lista de propiedades
        
    Returns:
        Dict con estadísticas
    """
    stats = {
        "total": len(propiedades),
        "con_ubicacion_valida": 0,
        "por_ciudad": {},
        "por_tipo_colonia": {},
        "confianza_promedio": 0
    }
    
    confianza_total = 0
    for prop in propiedades:
        ubicacion = prop.get("propiedad", {}).get("ubicacion", {})
        
        # Contar ubicaciones válidas
        if validar_ubicacion(ubicacion):
            stats["con_ubicacion_valida"] += 1
        
        # Contar por ciudad
        ciudad = ubicacion.get("ciudad")
        if ciudad:
            stats["por_ciudad"][ciudad] = stats["por_ciudad"].get(ciudad, 0) + 1
        
        # Contar por tipo de colonia
        tipo = ubicacion.get("tipo_colonia")
        if tipo:
            stats["por_tipo_colonia"][tipo] = stats["por_tipo_colonia"].get(tipo, 0) + 1
        
        # Acumular confianza
        confianza = ubicacion.get("confianza", 0)
        confianza_total += confianza
    
    # Calcular promedio de confianza
    stats["confianza_promedio"] = confianza_total / len(propiedades) if propiedades else 0
    
    return stats