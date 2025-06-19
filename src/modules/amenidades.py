"""
Módulo para detectar y validar amenidades de propiedades.
"""
from typing import Dict, List, Optional, Tuple
import re
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes y patrones
AMENIDADES = {
    "alberca": {
        "indicadores": [
            "alberca", "piscina", "pool", "chapoteadero", "alberquita",
            "splash", "jacuzzi", "hidromasaje"
        ],
        "tipos": {
            "techada": ["techada", "cubierta", "climatizada", "temperada"],
            "exterior": ["exterior", "descubierta", "jardin"],
            "infinita": ["infinita", "infinity", "desbordante"],
            "olimpica": ["olimpica", "semi olimpica", "semiolimpica"]
        }
    },
    "jardin": {
        "indicadores": [
            "jardin", "area verde", "pasto", "cesped", "plantas", 
            "arboles", "vegetacion", "paisajismo"
        ],
        "tipos": {
            "amplio": ["amplio", "grande", "extenso", "espacioso"],
            "pequeno": ["pequeno", "chico", "reducido"],
            "zen": ["zen", "japones", "oriental", "meditacion"],
            "tropical": ["tropical", "exotico", "palmeras"]
        },
        "patrones_medida": [
            r"jardin de (\d+)m2",
            r"jardin de (\d+) metros",
            r"area verde de (\d+)m2",
            r"(\d+)m2 de jardin",
            r"(\d+) metros de jardin"
        ]
    },
    "estacionamiento": {
        "indicadores": [
            "estacionamiento", "cochera", "garage", "parking",
            "espacio para auto", "lugar de auto"
        ],
        "tipos": {
            "techado": [
                "techado", "cubierto", "cerrado", "protegido"
            ],
            "subterraneo": [
                "subterraneo", "sotano", "bajo nivel"
            ],
            "multiple": [
                "multiple", "varios", "doble", "triple"
            ]
        },
        "patrones_cantidad": [
            r"(\d+) autos",
            r"(\d+) coches",
            r"(\d+) lugares",
            r"(\d+) cajones",
            r"para (\d+) autos"
        ]
    },
    "areas_comunes": {
        "indicadores": [
            "areas comunes", "amenidades", "instalaciones",
            "espacios compartidos", "servicios comunes"
        ],
        "tipos": {
            "salon": [
                "salon", "sala", "eventos", "fiestas", 
                "usos multiples", "reuniones"
            ],
            "gimnasio": [
                "gimnasio", "gym", "ejercicio", "pesas",
                "aparatos", "fitness"
            ],
            "juegos": [
                "juegos infantiles", "playground", "area infantil",
                "parque infantil", "juegos niños"
            ],
            "terraza": [
                "terraza", "roof garden", "sky deck", "mirador",
                "vista panoramica"
            ],
            "business": [
                "business center", "centro negocios", "coworking",
                "sala juntas", "oficinas"
            ]
        }
    },
    "asador": {
        "indicadores": [
            "asador", "parrilla", "bbq", "barbecue", "grill",
            "area bbq", "zona asador"
        ],
        "tipos": {
            "gas": ["gas", "linea gas"],
            "carbon": ["carbon", "leña"],
            "electrico": ["electrico"]
        }
    }
}

class AmenidadInvalida(Exception):
    """Excepción para amenidades inválidas"""
    pass

def _normalizar_texto(texto: str) -> str:
    """
    Normaliza el texto para búsqueda de patrones.
    
    Args:
        texto: Texto a normalizar
        
    Returns:
        Texto normalizado
    """
    if not texto:
        return ""
        
    # Convertir a minúsculas
    texto = texto.lower()
    
    # Eliminar acentos
    texto = texto.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    
    # Eliminar caracteres especiales
    texto = re.sub(r'[^\w\s]', ' ', texto)
    
    # Normalizar espacios
    texto = ' '.join(texto.split())
    
    return texto

def _detectar_tipos(texto: str, tipos: Dict[str, List[str]]) -> List[Tuple[str, float]]:
    """
    Detecta tipos específicos en el texto.
    
    Args:
        texto: Texto normalizado
        tipos: Diccionario de tipos y sus indicadores
        
    Returns:
        Lista de tuplas (tipo, confianza)
    """
    resultados = []
    
    for tipo, indicadores in tipos.items():
        for indicador in indicadores:
            if indicador in texto:
                resultados.append((tipo, 0.9))
                break
                
    return resultados

def _extraer_medida(texto: str, patrones: List[str]) -> Optional[int]:
    """
    Extrae medidas numéricas usando patrones.
    
    Args:
        texto: Texto normalizado
        patrones: Lista de patrones regex
        
    Returns:
        Valor numérico o None
    """
    for patron in patrones:
        if match := re.search(patron, texto):
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    return None

def extraer_alberca(texto: str) -> Dict:
    """
    Extrae información sobre alberca.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - presente: bool
        - tipos: List[str]
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    resultado = {
        "presente": False,
        "tipos": [],
        "confianza": 0.0,
        "evidencia": []
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    info = AMENIDADES["alberca"]
    
    # Detectar presencia
    for indicador in info["indicadores"]:
        if indicador in texto_norm:
            resultado["presente"] = True
            resultado["confianza"] = 0.9
            resultado["evidencia"].append(f"Indicador encontrado: {indicador}")
            break
        
    if resultado["presente"]:
        # Detectar tipos
        tipos_detectados = _detectar_tipos(texto_norm, info["tipos"])
        for tipo, conf in tipos_detectados:
            resultado["tipos"].append(tipo)
            resultado["evidencia"].append(f"Tipo detectado: {tipo}")
            resultado["confianza"] = max(resultado["confianza"], conf)
                
    return resultado

def extraer_jardin(texto: str) -> Dict:
    """
    Extrae información sobre jardín.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - presente: bool
        - tipos: List[str]
        - metros: Optional[int]
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    resultado = {
        "presente": False,
        "tipos": [],
        "metros": None,
        "confianza": 0.0,
        "evidencia": []
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    info = AMENIDADES["jardin"]
    
    # Detectar presencia
    for indicador in info["indicadores"]:
        if indicador in texto_norm:
            resultado["presente"] = True
            resultado["confianza"] = 0.9
            resultado["evidencia"].append(f"Indicador encontrado: {indicador}")
            break
        
    if resultado["presente"]:
        # Detectar tipos
        tipos_detectados = _detectar_tipos(texto_norm, info["tipos"])
        for tipo, conf in tipos_detectados:
            resultado["tipos"].append(tipo)
            resultado["evidencia"].append(f"Tipo detectado: {tipo}")
            resultado["confianza"] = max(resultado["confianza"], conf)
        
        # Detectar metros cuadrados
        if metros := _extraer_medida(texto_norm, info["patrones_medida"]):
            resultado["metros"] = metros
            resultado["evidencia"].append(f"Metros detectados: {metros}m2")
            resultado["confianza"] = 0.95
                
    return resultado

def extraer_estacionamiento(texto: str) -> Dict:
    """
    Extrae información sobre estacionamiento.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - cantidad: int
        - tipo: str (techado/subterraneo/multiple/normal)
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    resultado = {
        "cantidad": 0,
        "tipo": "normal",
        "confianza": 0.0,
        "evidencia": []
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    info = AMENIDADES["estacionamiento"]
    
    # Detectar presencia y tipo
    for tipo, indicadores in info["tipos"].items():
        for indicador in indicadores:
            if indicador in texto_norm:
                resultado["tipo"] = tipo
                resultado["confianza"] = 0.9
                resultado["evidencia"].append(f"Tipo detectado: {tipo}")
                break
    
    # Detectar número de lugares
    if lugares := _extraer_medida(texto_norm, info["patrones_cantidad"]):
        resultado["cantidad"] = lugares
        resultado["evidencia"].append(f"Lugares detectados: {lugares}")
        resultado["confianza"] = 0.95
    else:
        # Si no hay número específico pero hay indicador, asumir 1
        for indicador in info["indicadores"]:
            if indicador in texto_norm:
                resultado["cantidad"] = 1
                resultado["evidencia"].append(f"Indicador general encontrado: {indicador}")
                resultado["confianza"] = 0.7
                break
                
    return resultado

def extraer_areas_comunes(texto: str) -> Dict:
    """
    Extrae información sobre áreas comunes.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - presente: bool
        - tipos: List[str]
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    resultado = {
        "presente": False,
        "tipos": [],
        "confianza": 0.0,
        "evidencia": []
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    info = AMENIDADES["areas_comunes"]
    
    # Detectar tipos específicos primero
    for tipo, indicadores in info["tipos"].items():
        for indicador in indicadores:
            if indicador in texto_norm:
                resultado["presente"] = True
                if tipo not in resultado["tipos"]:
                    resultado["tipos"].append(tipo)
                    resultado["evidencia"].append(f"Tipo detectado: {tipo}")
                    resultado["confianza"] = max(resultado["confianza"], 0.9)
    
    # Si no se detectaron tipos específicos, buscar indicadores generales
    if not resultado["presente"]:
        for indicador in info["indicadores"]:
            if indicador in texto_norm:
                resultado["presente"] = True
                resultado["confianza"] = 0.7
                resultado["evidencia"].append(f"Indicador general encontrado: {indicador}")
                break
    
    return resultado

def extraer_asador(texto: str) -> Dict:
    """
    Extrae información sobre asador.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - presente: bool
        - tipos: List[str]
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    resultado = {
        "presente": False,
        "tipos": [],
        "confianza": 0.0,
        "evidencia": []
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    info = AMENIDADES["asador"]
    
    # Detectar presencia
    for indicador in info["indicadores"]:
        if indicador in texto_norm:
            resultado["presente"] = True
            resultado["confianza"] = 0.9
            resultado["evidencia"].append(f"Indicador encontrado: {indicador}")
            break
            
    if resultado["presente"]:
        # Detectar tipos
        tipos_detectados = _detectar_tipos(texto_norm, info["tipos"])
        for tipo, conf in tipos_detectados:
            resultado["tipos"].append(tipo)
            resultado["evidencia"].append(f"Tipo detectado: {tipo}")
            resultado["confianza"] = max(resultado["confianza"], conf)
                
    return resultado

def actualizar_amenidades(propiedad: Dict) -> Dict:
    """
    Actualiza las amenidades de una propiedad.
    
    Args:
        propiedad: Diccionario de propiedad
        
    Returns:
        Diccionario con amenidades actualizadas
    """
    texto = propiedad.get("descripcion_original", "")
    
    amenidades = {
        "alberca": {
            "presente": False,
            "tipo": None,
            "detalles": []
        },
        "jardin": {
            "presente": False,
            "tipo": None,
            "detalles": []
        },
        "estacionamiento": {
            "presente": False,
            "tipo": None,
            "techado": False,
            "detalles": []
        },
        "areas_comunes": {
            "presentes": False,
            "tipos": [],
            "detalles": []
        },
        "deportivas": {
            "presentes": False,
            "tipos": [],
            "detalles": []
        },
        "adicionales": []
    }
    
    # Extraer cada tipo de amenidad
    alberca = extraer_alberca(texto)
    if alberca["presente"]:
        amenidades["alberca"]["presente"] = True
        if alberca["tipos"]:
            amenidades["alberca"]["tipo"] = alberca["tipos"][0]
        amenidades["alberca"]["detalles"] = alberca["evidencia"]
            
    jardin = extraer_jardin(texto)
    if jardin["presente"]:
        amenidades["jardin"]["presente"] = True
        if jardin["tipos"]:
            amenidades["jardin"]["tipo"] = jardin["tipos"][0]
        amenidades["jardin"]["detalles"] = jardin["evidencia"]
            
    estacionamiento = extraer_estacionamiento(texto)
    if estacionamiento["cantidad"] > 0:
        amenidades["estacionamiento"]["presente"] = True
        amenidades["estacionamiento"]["tipo"] = estacionamiento["tipo"]
        amenidades["estacionamiento"]["techado"] = estacionamiento["tipo"] == "techado"
        amenidades["estacionamiento"]["detalles"] = estacionamiento["evidencia"]
            
    areas = extraer_areas_comunes(texto)
    if areas["presente"]:
        amenidades["areas_comunes"]["presentes"] = True
        amenidades["areas_comunes"]["tipos"] = areas["tipos"]
        amenidades["areas_comunes"]["detalles"] = areas["evidencia"]
            
    asador = extraer_asador(texto)
    if asador["presente"]:
        amenidades["adicionales"].append("asador")
        if asador["tipos"]:
            amenidades["adicionales"].extend(asador["tipos"])
            
    return amenidades

def validar_amenidades(amenidades: Dict) -> bool:
    """
    Valida que un diccionario de amenidades tenga la estructura correcta.
    
    Args:
        amenidades: Diccionario de amenidades
        
    Returns:
        True si es válido, False si no
    """
    try:
        # Validar estructura básica
        campos_requeridos = [
            "alberca", "jardin", "estacionamiento",
            "areas_comunes", "deportivas", "adicionales"
        ]
        
        for campo in campos_requeridos:
            if campo not in amenidades:
                raise AmenidadInvalida(f"Falta campo requerido: {campo}")
                
        # Validar alberca
        alberca = amenidades["alberca"]
        if not isinstance(alberca, dict):
            raise AmenidadInvalida("alberca debe ser un diccionario")
            
        if not all(k in alberca for k in ["presente", "tipo", "detalles"]):
            raise AmenidadInvalida("alberca: faltan campos requeridos")
            
        # Validar jardin
        jardin = amenidades["jardin"]
        if not isinstance(jardin, dict):
            raise AmenidadInvalida("jardin debe ser un diccionario")
            
        if not all(k in jardin for k in ["presente", "tipo", "detalles"]):
            raise AmenidadInvalida("jardin: faltan campos requeridos")
            
        # Validar estacionamiento
        estacionamiento = amenidades["estacionamiento"]
        if not isinstance(estacionamiento, dict):
            raise AmenidadInvalida("estacionamiento debe ser un diccionario")
            
        if not all(k in estacionamiento for k in ["presente", "tipo", "techado", "detalles"]):
            raise AmenidadInvalida("estacionamiento: faltan campos requeridos")
            
        # Validar areas_comunes
        areas = amenidades["areas_comunes"]
        if not isinstance(areas, dict):
            raise AmenidadInvalida("areas_comunes debe ser un diccionario")
            
        if not all(k in areas for k in ["presentes", "tipos", "detalles"]):
            raise AmenidadInvalida("areas_comunes: faltan campos requeridos")
            
        # Validar deportivas
        deportivas = amenidades["deportivas"]
        if not isinstance(deportivas, dict):
            raise AmenidadInvalida("deportivas debe ser un diccionario")
            
        if not all(k in deportivas for k in ["presentes", "tipos", "detalles"]):
            raise AmenidadInvalida("deportivas: faltan campos requeridos")
            
        # Validar adicionales
        if not isinstance(amenidades["adicionales"], list):
            raise AmenidadInvalida("adicionales debe ser una lista")
            
        return True
        
    except Exception as e:
        logger.error(f"Error validando amenidades: {str(e)}")
        return False

def obtener_estadisticas(propiedades: List[Dict]) -> Dict:
    """
    Obtiene estadísticas sobre amenidades en un conjunto de propiedades.
    
    Args:
        propiedades: Lista de propiedades
        
    Returns:
        Dict con estadísticas
    """
    stats = {
        "total_propiedades": len(propiedades),
        "alberca": {
            "total": 0,
            "tipos": {}
        },
        "jardin": {
            "total": 0,
            "tipos": {}
        },
        "estacionamiento": {
            "total": 0,
            "tipos": {},
            "techado": 0
        },
        "areas_comunes": {
            "total": 0,
            "tipos": {}
        },
        "deportivas": {
            "total": 0,
            "tipos": {}
        },
        "adicionales": {}
    }
    
    for prop in propiedades:
        if "amenidades" not in prop:
            continue
            
        amenidades = prop["amenidades"]
        
        # Alberca
        if amenidades["alberca"]["presente"]:
            stats["alberca"]["total"] += 1
            tipo = amenidades["alberca"]["tipo"]
            if tipo:
                stats["alberca"]["tipos"][tipo] = stats["alberca"]["tipos"].get(tipo, 0) + 1
                
        # Jardín
        if amenidades["jardin"]["presente"]:
            stats["jardin"]["total"] += 1
            tipo = amenidades["jardin"]["tipo"]
            if tipo:
                stats["jardin"]["tipos"][tipo] = stats["jardin"]["tipos"].get(tipo, 0) + 1
                
        # Estacionamiento
        if amenidades["estacionamiento"]["presente"]:
            stats["estacionamiento"]["total"] += 1
            tipo = amenidades["estacionamiento"]["tipo"]
            if tipo:
                stats["estacionamiento"]["tipos"][tipo] = stats["estacionamiento"]["tipos"].get(tipo, 0) + 1
            if amenidades["estacionamiento"]["techado"]:
                stats["estacionamiento"]["techado"] += 1
                
        # Áreas comunes
        if amenidades["areas_comunes"]["presentes"]:
            stats["areas_comunes"]["total"] += 1
            for tipo in amenidades["areas_comunes"]["tipos"]:
                stats["areas_comunes"]["tipos"][tipo] = stats["areas_comunes"]["tipos"].get(tipo, 0) + 1
                
        # Deportivas
        if amenidades["deportivas"]["presentes"]:
            stats["deportivas"]["total"] += 1
            for tipo in amenidades["deportivas"]["tipos"]:
                stats["deportivas"]["tipos"][tipo] = stats["deportivas"]["tipos"].get(tipo, 0) + 1
                
        # Adicionales
        for adicional in amenidades["adicionales"]:
            stats["adicionales"][adicional] = stats["adicionales"].get(adicional, 0) + 1
            
    return stats

def detectar_amenidades(texto: str) -> Dict:
    """
    Detecta todas las amenidades presentes en un texto.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con todas las amenidades detectadas
    """
    propiedad = {"descripcion_original": texto}
    return actualizar_amenidades(propiedad) 