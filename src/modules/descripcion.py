#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MÓDULO DE LIMPIEZA DE DESCRIPCIONES
---------------------------------

Este módulo es responsable de limpiar y normalizar las descripciones
de las propiedades.

RESPONSABILIDADES:
1. Limpiar texto de caracteres especiales
2. Normalizar formatos
3. Eliminar información no relevante
4. Estructurar la descripción

REGLAS:
1. NO modificar información importante
2. Mantener registro de cambios
3. Preservar URLs y referencias importantes
4. En caso de duda, preservar el texto original
"""

import re
import logging
from typing import Dict, Optional, List, Tuple

# Configuración de logging
logger = logging.getLogger('descripcion')
logger.setLevel(logging.DEBUG)

def limpiar_descripcion(texto: str) -> Dict:
    """
    Limpia y normaliza una descripción.
    
    Args:
        texto: Texto original de la descripción
        
    Returns:
        Dict con:
        - texto_limpio: str
        - texto_original: str
        - cambios_realizados: List[str]
        - urls_encontradas: List[str]
        - confianza: float
    """
    if not texto:
        return {
            "texto_limpio": "",
            "texto_original": "",
            "cambios_realizados": [],
            "urls_encontradas": [],
            "confianza": 0.0
        }
    
    cambios = []
    urls = []
    
    # Preservar texto original
    texto_original = texto
    texto_limpio = texto
    
    # Extraer URLs antes de limpiar
    patron_urls = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(patron_urls, texto_limpio)
    
    # Normalizar espacios
    texto_prev = texto_limpio
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio)
    if texto_prev != texto_limpio:
        cambios.append("normalización de espacios")
    
    # Eliminar caracteres especiales preservando puntuación importante
    texto_prev = texto_limpio
    texto_limpio = re.sub(r'[^\w\s.,;:¿?¡!()$%#@-]', '', texto_limpio)
    if texto_prev != texto_limpio:
        cambios.append("eliminación de caracteres especiales")
    
    # Normalizar saltos de línea
    texto_prev = texto_limpio
    texto_limpio = texto_limpio.replace('\r\n', '\n').replace('\r', '\n')
    if texto_prev != texto_limpio:
        cambios.append("normalización de saltos de línea")
    
    # Eliminar múltiples saltos de línea
    texto_prev = texto_limpio
    texto_limpio = re.sub(r'\n\s*\n', '\n', texto_limpio)
    if texto_prev != texto_limpio:
        cambios.append("eliminación de saltos de línea múltiples")
    
    # Eliminar espacios al inicio y final
    texto_limpio = texto_limpio.strip()
    
    # Calcular confianza basado en cambios realizados
    confianza = 1.0 - (len(cambios) * 0.1)  # Reduce confianza por cada cambio
    confianza = max(0.1, min(confianza, 1.0))  # Mantener entre 0.1 y 1.0
    
    return {
        "texto_limpio": texto_limpio,
        "texto_original": texto_original,
        "cambios_realizados": cambios,
        "urls_encontradas": urls,
        "confianza": confianza
    }

def estructurar_descripcion(texto: str) -> Dict:
    """
    Estructura una descripción en secciones lógicas.
    
    Args:
        texto: Texto limpio de la descripción
        
    Returns:
        Dict con secciones estructuradas
    """
    secciones = {
        "general": "",
        "caracteristicas": "",
        "ubicacion": "",
        "contacto": "",
        "precio": "",
        "legal": ""
    }
    
    # Implementar lógica de estructuración
    # TODO: Implementar esta función
    
    return secciones 