#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MÓDULO DE EXTRACCIÓN DE CARACTERÍSTICAS
------------------------------------

Este módulo es responsable de extraer y normalizar las características
físicas de las propiedades, como número de recámaras, baños, etc.

RESPONSABILIDADES:
1. Extraer características de texto
2. Validar valores extraídos
3. Mantener catálogo de patrones
4. Proveer estadísticas de confianza

REGLAS:
1. Validar todos los valores extraídos
2. NO modificar otros aspectos de la propiedad
3. Mantener registro de decisiones tomadas
4. En caso de duda, marcar como None
"""

import re
import logging
from typing import Dict, Optional, List, Tuple
from decimal import Decimal

# Configuración de logging
logger = logging.getLogger('caracteristicas')
logger.setLevel(logging.DEBUG)

# Patrones de extracción
PATRONES = {
    "recamaras": [
        r"(\d+)\s*(?:recamaras?|recámaras?|rec\.?|habitaciones?|cuartos?)",
        r"(?:recamaras?|recámaras?|rec\.?|habitaciones?|cuartos?)\s*(\d+)"
    ],
    
    "banos": [
        r"(\d+)(?:\s*y\s*medio|\s*\.5)?\s*(?:baños?|banos?|wc)",
        r"(?:baños?|banos?|wc)\s*(\d+)(?:\s*y\s*medio|\s*\.5)?",
        r"(\d+)\s*(?:baños?|banos?|wc)\s*(?:y\s*medio|completos?)",
        r"baño\s*y\s*medio",
        r"medio\s*baño"
    ],
    
    "estacionamientos": [
        r"(\d+)\s*(?:cajones?|lugares?|estacionamientos?)",
        r"(?:cajon|lugar|estacionamiento)\s*(?:para|de)?\s*(\d+)"
    ],
    
    "superficie": [
        r"(\d+(?:\.\d+)?)\s*(?:m2|m²|metros?(?:\s*cuadrados?)?)",
        r"(?:superficie|terreno|construccion)\s*(?:de)?\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*(?:m2|m²)\s*(?:de\s*)?(?:construccion|construcción)",
        r"(?:construccion|construcción)\s*(?:de)?\s*(\d+(?:\.\d+)?)\s*(?:m2|m²)"
    ],
    
    "niveles": [
        r"(\d+)\s*(?:niveles?|pisos?)",
        r"(?:de)?\s*(\d+)\s*(?:niveles?|pisos?)"
    ]
}

# Indicadores de características
INDICADORES = {
    "planta_alta": [
        "planta alta", "segundo piso", "2do piso"
    ],
    
    "un_nivel": [
        "un nivel", "una planta", "planta baja"
    ],
    
    "recamara_planta_baja": [
        "recamara en planta baja", "recámara en planta baja",
        "habitacion en planta baja", "habitación en planta baja"
    ],
    
    "opcion_crecer": [
        "opcion a crecer", "opción a crecer", "posibilidad de crecer",
        "puede crecer", "oportunidad de crecer"
    ],
    
    "estacionamiento_general": [
        "estacionamiento", "cochera", "garage"
    ]
}

class CaracteristicaInvalida(Exception):
    """Excepción para características inválidas"""
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

def _extraer_numero(texto: str, patrones: List[str], min_val: float, max_val: float) -> Dict:
    """
    Extrae un número usando patrones y lo valida.
    USO INTERNO ÚNICAMENTE.
    
    Args:
        texto: Texto donde buscar
        patrones: Lista de patrones regex
        min_val: Valor mínimo aceptable
        max_val: Valor máximo aceptable
        
    Returns:
        Dict con:
        - valor: float o None
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    resultado = {
        "valor": None,
        "confianza": 0.0,
        "evidencia": []
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    
    for patron in patrones:
        if match := re.search(patron, texto_norm):
            try:
                valor_str = match.group(1).replace(',', '.')
                valor = float(valor_str)
                if min_val <= valor <= max_val:
                    resultado.update({
                        "valor": valor,
                        "confianza": 0.9,
                        "evidencia": [f"Patrón '{patron}' encontrado: {valor}"]
                    })
                    return resultado
                else:
                    resultado["evidencia"].append(
                        f"Valor {valor} fuera de rango [{min_val}-{max_val}]"
                    )
            except ValueError:
                resultado["evidencia"].append(
                    f"No se pudo convertir '{match.group(1)}' a número"
                )
    
    return resultado

def extraer_recamaras(texto: str) -> Dict:
    """
    Extrae información sobre recámaras.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - valor: int o None
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    return _extraer_numero(texto, PATRONES["recamaras"], 1, 10)

def extraer_banos(texto: str) -> Dict:
    """
    Extrae información sobre baños.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - valor: float o None (puede ser decimal para medios baños)
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    resultado = {
        "valor": None,
        "confianza": 0.0,
        "evidencia": []
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    
    # Detectar "baño y medio" explícito
    if "bano y medio" in texto_norm or "baño y medio" in texto_norm:
        resultado.update({
            "valor": 1.5,
            "confianza": 0.9,
            "evidencia": ["Detectado explícitamente 'baño y medio'"]
        })
        return resultado
        
    # Detectar "medio baño" explícito
    if "medio bano" in texto_norm or "medio baño" in texto_norm:
        resultado.update({
            "valor": 0.5,
            "confianza": 0.9,
            "evidencia": ["Detectado explícitamente 'medio baño'"]
        })
        return resultado
    
    # Buscar patrones con decimales
    for patron in PATRONES["banos"]:
        if match := re.search(patron, texto_norm):
            try:
                valor = float(match.group(1))
                if "y medio" in match.group(0) or ".5" in match.group(0):
                    valor += 0.5
                
                if 0.5 <= valor <= 10:
                    resultado.update({
                        "valor": valor,
                        "confianza": 0.9,
                        "evidencia": [f"Patrón '{patron}' encontrado: {valor}"]
                    })
                    return resultado
                else:
                    resultado["evidencia"].append(
                        f"Valor {valor} fuera de rango [0.5-10]"
                    )
            except ValueError:
                resultado["evidencia"].append(
                    f"No se pudo convertir '{match.group(1)}' a número"
                )
    
    return resultado

def extraer_estacionamientos(texto: str) -> Dict:
    """
    Extrae información sobre estacionamientos.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - cantidad: int
        - tipo: str (fijo/general/None)
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    resultado = {
        "cantidad": 0,
        "tipo": None,
        "confianza": 0.0,
        "evidencia": []
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    
    # Buscar cantidad específica
    info_num = _extraer_numero(texto, PATRONES["estacionamientos"], 1, 10)
    if info_num["valor"] is not None:
        resultado.update({
            "cantidad": info_num["valor"],
            "tipo": "fijo",
            "confianza": info_num["confianza"],
            "evidencia": info_num["evidencia"]
        })
        return resultado
    
    # Detectar estacionamiento general
    for indicador in INDICADORES["estacionamiento_general"]:
        if indicador in texto_norm:
            resultado.update({
                "cantidad": 1,
                "tipo": "general",
                "confianza": 0.7,
                "evidencia": [f"Indicador general encontrado: {indicador}"]
            })
            return resultado
    
    return resultado

def extraer_superficie(texto: str) -> Dict:
    """
    Extrae información sobre superficie.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - construccion: float o None
        - terreno: float o None
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    resultado = {
        "construccion": None,
        "terreno": None,
        "confianza": 0.0,
        "evidencia": []
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    
    # Buscar superficie de construcción
    patrones_construccion = [
        r"(\d+(?:\.\d+)?)\s*(?:m2|m²)\s*(?:de\s*)?(?:construccion|construcción)",
        r"(?:construccion|construcción)\s*(?:de)?\s*(\d+(?:\.\d+)?)\s*(?:m2|m²)"
    ]
    
    info_construccion = _extraer_numero(texto, patrones_construccion, 20, 1000)
    if info_construccion["valor"] is not None:
        resultado["construccion"] = float(info_construccion["valor"])
        resultado["confianza"] = max(resultado["confianza"], info_construccion["confianza"])
        resultado["evidencia"].extend(info_construccion["evidencia"])
    
    # Buscar superficie de terreno
    patrones_terreno = [
        r"(\d+(?:\.\d+)?)\s*(?:m2|m²)\s*(?:de\s*)?(?:terreno|lote)",
        r"(?:terreno|lote)\s*(?:de)?\s*(\d+(?:\.\d+)?)\s*(?:m2|m²)"
    ]
    
    info_terreno = _extraer_numero(texto, patrones_terreno, 50, 10000)
    if info_terreno["valor"] is not None:
        resultado["terreno"] = float(info_terreno["valor"])
        resultado["confianza"] = max(resultado["confianza"], info_terreno["confianza"])
        resultado["evidencia"].extend(info_terreno["evidencia"])
    
    # Si no se especifica tipo, asumir construcción
    if not resultado["construccion"] and not resultado["terreno"]:
        info_general = _extraer_numero(texto, PATRONES["superficie"], 20, 10000)
        if info_general["valor"] is not None:
            resultado["construccion"] = float(info_general["valor"])
            resultado["confianza"] = max(resultado["confianza"], info_general["confianza"] * 0.8)
            resultado["evidencia"].extend(["Superficie asumida como construcción"])
            resultado["evidencia"].extend(info_general["evidencia"])
    
    return resultado

def extraer_niveles(texto: str) -> Dict:
    """
    Extrae información sobre niveles/pisos.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - valor: int o None
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    resultado = {
        "valor": None,
        "confianza": 0.0,
        "evidencia": []
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    
    # Buscar número específico de niveles
    info_num = _extraer_numero(texto, PATRONES["niveles"], 1, 10)
    if info_num["valor"] is not None:
        resultado.update(info_num)
        return resultado
    
    # Detectar indicadores de un nivel
    for indicador in INDICADORES["un_nivel"]:
        if indicador in texto_norm:
            resultado.update({
                "valor": 1,
                "confianza": 0.8,
                "evidencia": [f"Indicador de un nivel encontrado: {indicador}"]
            })
            return resultado
    
    return resultado

def extraer_caracteristicas_adicionales(texto: str) -> Dict:
    """
    Extrae características adicionales.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con características adicionales y su confianza
    """
    resultado = {
        "recamara_planta_baja": {
            "valor": False,
            "confianza": 0.0,
            "evidencia": []
        },
        "opcion_crecer": {
            "valor": False,
            "confianza": 0.0,
            "evidencia": []
        }
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    
    # Detectar recámara en planta baja
    for indicador in INDICADORES["recamara_planta_baja"]:
        if indicador in texto_norm:
            resultado["recamara_planta_baja"].update({
                "valor": True,
                "confianza": 0.9,
                "evidencia": [f"Indicador encontrado: {indicador}"]
            })
            break
    
    # Detectar opción a crecer
    for indicador in INDICADORES["opcion_crecer"]:
        if indicador in texto_norm:
            resultado["opcion_crecer"].update({
                "valor": True,
                "confianza": 0.8,
                "evidencia": [f"Indicador encontrado: {indicador}"]
            })
            break
    
    return resultado

def extraer_caracteristicas(texto: str) -> Dict:
    """
    Extrae todas las características de una propiedad.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con todas las características extraídas
    """
    resultado = {}
    
    # Extraer características básicas
    info_recamaras = extraer_recamaras(texto)
    if info_recamaras["valor"] is not None:
        resultado["recamaras"] = info_recamaras["valor"]
        
    info_banos = extraer_banos(texto)
    if info_banos["valor"] is not None:
        resultado["banos"] = info_banos["valor"]
        
    info_estacionamiento = extraer_estacionamientos(texto)
    if info_estacionamiento["cantidad"] > 0:
        resultado["estacionamiento"] = {
            "cantidad": info_estacionamiento["cantidad"],
            "tipo": info_estacionamiento["tipo"]
        }
        
    info_superficie = extraer_superficie(texto)
    if info_superficie["construccion"] is not None:
        resultado["superficie_construida"] = info_superficie["construccion"]
    if info_superficie["terreno"] is not None:
        resultado["superficie_terreno"] = info_superficie["terreno"]
        
    info_niveles = extraer_niveles(texto)
    if info_niveles["valor"] is not None:
        resultado["niveles"] = info_niveles["valor"]
        
    # Extraer características adicionales
    info_adicional = extraer_caracteristicas_adicionales(texto)
    resultado.update(info_adicional)
    
    return resultado

def actualizar_caracteristicas(propiedad: Dict) -> Dict:
    """
    Actualiza las características de una propiedad.
    
    Args:
        propiedad: Dict con datos de la propiedad
        
    Returns:
        Dict con la propiedad actualizada
    """
    try:
        # Extraer texto relevante
        texto = propiedad.get("descripcion", "")
        if not texto:
            logger.warning("Propiedad sin descripción")
            return propiedad
        
        # Extraer características
        caracteristicas = extraer_caracteristicas(texto)
        
        # Validar y actualizar
        if validar_caracteristicas(caracteristicas):
            propiedad["caracteristicas"] = caracteristicas
            propiedad["caracteristicas_validas"] = True
        else:
            propiedad["caracteristicas"] = caracteristicas
            propiedad["caracteristicas_validas"] = False
        
        return propiedad
        
    except Exception as e:
        logger.error(f"Error actualizando características: {e}")
        propiedad["caracteristicas_validas"] = False
        return propiedad

def validar_caracteristicas(caracteristicas: Dict) -> bool:
    """
    Valida que las características extraídas sean coherentes.
    
    Args:
        caracteristicas: Dict con características extraídas
        
    Returns:
        bool: True si las características son válidas
    """
    try:
        # Validar rangos
        if caracteristicas.get("recamaras") is not None:
            if not (1 <= caracteristicas["recamaras"] <= 10):
                return False
                
        if caracteristicas.get("banos") is not None:
            if not (0.5 <= caracteristicas["banos"] <= 10):
                return False
                
        if caracteristicas.get("estacionamientos") is not None:
            if not (0 <= caracteristicas["estacionamientos"] <= 10):
                return False
                
        if caracteristicas.get("superficie") is not None:
            if not (20 <= caracteristicas["superficie"] <= 10000):
                return False
                
        if caracteristicas.get("niveles") is not None:
            if not (1 <= caracteristicas["niveles"] <= 50):
                return False
    
        # Validar coherencia
        if (caracteristicas.get("recamaras") is not None and 
            caracteristicas.get("banos") is not None):
            if caracteristicas["recamaras"] < caracteristicas["banos"]:
                return False
    
        return True
        
    except Exception as e:
        logger.error(f"Error validando características: {e}")
        return False

def obtener_estadisticas(propiedades: List[Dict]) -> Dict:
    """
    Genera estadísticas sobre características.
    
    Args:
        propiedades: Lista de propiedades
        
    Returns:
        Dict con estadísticas
    """
    stats = {
        "total": len(propiedades),
        "con_caracteristicas_validas": 0,
        "distribucion_recamaras": {},
        "distribucion_banos": {},
        "distribucion_estacionamientos": {},
        "con_planta_alta": 0,
        "confianza_promedio": 0
    }
    
    confianza_total = 0
    for prop in propiedades:
        caracteristicas = prop.get("caracteristicas", {})
        
        # Contar características válidas
        if validar_caracteristicas(caracteristicas):
            stats["con_caracteristicas_validas"] += 1
        
        # Contar distribución de recámaras
        recamaras = caracteristicas.get("recamaras", {}).get("valor")
        if recamaras:
            stats["distribucion_recamaras"][recamaras] = (
                stats["distribucion_recamaras"].get(recamaras, 0) + 1
            )
        
        # Contar distribución de baños
        banos = caracteristicas.get("banos", {}).get("valor")
        if banos:
            stats["distribucion_banos"][banos] = (
                stats["distribucion_banos"].get(banos, 0) + 1
            )
        
        # Contar distribución de estacionamientos
        estacionamientos = caracteristicas.get("estacionamientos", {}).get("cantidad")
        if estacionamientos:
            stats["distribucion_estacionamientos"][estacionamientos] = (
                stats["distribucion_estacionamientos"].get(estacionamientos, 0) + 1
            )
        
        # Contar propiedades con planta alta
        if caracteristicas.get("tiene_planta_alta"):
            stats["con_planta_alta"] += 1
        
        # Acumular confianza
        confianza = caracteristicas.get("confianza", 0)
        confianza_total += confianza
    
    # Calcular promedio de confianza
    stats["confianza_promedio"] = confianza_total / len(propiedades) if propiedades else 0
    
    return stats 