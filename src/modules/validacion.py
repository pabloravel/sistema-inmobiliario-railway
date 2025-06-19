#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de validación de propiedades inmobiliarias.
Solo valida campos requeridos básicos.
"""

from typing import Dict, List, Tuple

def validar_propiedad_completa(propiedad: Dict) -> Tuple[bool, List[str]]:
    """
    Valida los campos básicos requeridos de una propiedad.
    
    Args:
        propiedad: Diccionario con los datos de la propiedad
        
    Returns:
        Tuple[bool, List[str]]: (es_valida, lista_errores)
    """
    errores = []
    
    # Validar campos requeridos básicos
    campos_requeridos = [
        ("titulo", "Título no encontrado"),
        ("descripcion", "Descripción no encontrada"),
        ("link", "Link no encontrado")
    ]
    
    for campo, mensaje in campos_requeridos:
        if not propiedad.get(campo):
            errores.append(mensaje)
    
        # Validar tipo de operación
    tipo_op = propiedad.get("tipo_operacion")
        if not tipo_op:
        # Intentar extraer de la descripción
        descripcion = propiedad.get("descripcion", "")
        if "venta" in descripcion.lower():
            tipo_op = "venta"
        elif "renta" in descripcion.lower():
            tipo_op = "renta"
        else:
            errores.append("Tipo de operación no especificado")
            
        # Validar tipo de propiedad
    tipo_prop = propiedad.get("tipo_propiedad")
        if not tipo_prop:
        # Intentar extraer de la descripción
        descripcion = propiedad.get("descripcion", "")
        if "casa" in descripcion.lower():
            tipo_prop = "casa"
        elif "departamento" in descripcion.lower():
            tipo_prop = "departamento"
        elif "terreno" in descripcion.lower():
            tipo_prop = "terreno"
        else:
            # No es un error crítico si no se puede determinar
            pass
            
        # Validar precio
    precio = propiedad.get("precio")
        if not precio:
        # Intentar extraer de la descripción
        import re
        descripcion = propiedad.get("descripcion", "")
        precio_match = re.search(r'\$[\d,]+', descripcion)
        if not precio_match:
            errores.append("Precio no especificado")
    
    return len(errores) == 0, errores 

# Palabras clave que indican que ES una propiedad inmobiliaria
PALABRAS_INMOBILIARIAS: List[str] = [
    "casa", "depto", "departamento", "terreno", "propiedad",
    "inmueble", "edificio", "local", "oficina", "bodega",
    "renta", "venta", "alquiler", "inmobiliaria", "bienes raices",
    "m2", "metros", "recamara", "habitacion", "baño",
    "cocina", "sala", "comedor", "jardin", "alberca",
    "estacionamiento", "garage", "cochera", "residencial",
    "condominio", "fraccionamiento", "privada", "hogar",
    "cabaña", "cabana", "lote", "construccion", "obra negra",
    "cisterna", "fosa", "septica", "escrituras", "ejidal",
    "cesion", "derechos", "constancia"
]

# Palabras clave que indican ubicación
PALABRAS_UBICACION: List[str] = [
    "cuernavaca", "morelos", "jiutepec", "temixco", "zapata",
    "yautepec", "tepoztlan", "huitzilac", "tres marias",
    "teopanzolco", "ahuatepec", "lomas", "zona norte",
    "colonia", "fraccionamiento"
]

def es_publicacion_no_inmobiliaria(texto: str) -> bool:
    """
    Detecta si una publicación NO es sobre propiedades inmobiliarias.
    
    Args:
        texto (str): Texto de la publicación a analizar
        
    Returns:
        bool: True si la publicación NO es inmobiliaria, False si SÍ es inmobiliaria
        
    Examples:
        >>> es_publicacion_no_inmobiliaria("Vendo casa en Cuernavaca")
        False
        >>> es_publicacion_no_inmobiliaria("Vendo mi coche")
        True
    """
    if not texto:
        return True
        
    texto_lower = texto.lower()
    
    # Contar palabras clave
    contador_inmobiliarias = sum(1 for palabra in PALABRAS_INMOBILIARIAS if palabra in texto_lower)
    contador_ubicacion = sum(1 for palabra in PALABRAS_UBICACION if palabra in texto_lower)
    
    # Si tiene al menos una palabra inmobiliaria y una de ubicación, es válida
    if contador_inmobiliarias >= 1 and contador_ubicacion >= 1:
        return False
        
    # Si tiene al menos 2 palabras inmobiliarias, es válida
    if contador_inmobiliarias >= 2:
        return False
        
    # Si menciona metros cuadrados o dimensiones, es válida
    if re.search(r'\d+\s*(?:m2|mts?2|metros?(?:\s+cuadrados?)?)', texto_lower):
        return False
        
    return True 