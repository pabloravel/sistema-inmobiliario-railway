#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de procesamiento de tipo de operación.
Detecta y corrige tipos de operación basándose en descripción y precio.
"""

import logging
import re
from typing import Dict, Tuple

# Configuración de logging
logger = logging.getLogger('tipo_operacion')
logger.setLevel(logging.INFO)  # Cambiar a INFO para reducir spam

# Patrones para detección de tipo de operación
PATRONES_RENTA = [
    r'\brenta\b', r'\brento\b', r'\balquilo\b', r'\balquiler\b',
    r'\bse renta\b', r'\bpara renta\b', r'\ben renta\b',
    r'\bmensual\b', r'\bmes\b.*\$', r'\$/mes\b',
    r'\barrendo\b', r'\barrendamiento\b'
]

PATRONES_VENTA = [
    r'\bventa\b', r'\bvendo\b', r'\bse vende\b', r'\bpara venta\b',
    r'\ben venta\b', r'\bcontado\b', r'\bfinanciamiento\b',
    r'\bcredito\b.*\bventa\b', r'\bventa.*\bcredito\b'
]

# Umbral de precio para clasificación automática
UMBRAL_PRECIO_VENTA = 300000  # Si precio > $300,000 y no especifica = venta

def detectar_tipo_por_descripcion(descripcion: str) -> Tuple[str, float]:
    """
    Detecta el tipo de operación basándose en la descripción.
    
    Args:
        descripcion: Texto de la descripción de la propiedad
        
    Returns:
        Tuple[str, float]: (tipo_detectado, confianza)
    """
    if not descripcion:
        return "desconocido", 0.0
    
    desc_lower = descripcion.lower()
    
    # Contar coincidencias de renta
    coincidencias_renta = 0
    for patron in PATRONES_RENTA:
        if re.search(patron, desc_lower):
            coincidencias_renta += 1
    
    # Contar coincidencias de venta
    coincidencias_venta = 0
    for patron in PATRONES_VENTA:
        if re.search(patron, desc_lower):
            coincidencias_venta += 1
    
    # Determinar tipo y confianza
    if coincidencias_renta > coincidencias_venta:
        confianza = min(0.9, 0.6 + (coincidencias_renta * 0.1))
        return "renta", confianza
    elif coincidencias_venta > coincidencias_renta:
        confianza = min(0.9, 0.6 + (coincidencias_venta * 0.1))
        return "venta", confianza
    elif coincidencias_renta == coincidencias_venta and coincidencias_renta > 0:
        # Empate, buscar patrones más específicos
        if re.search(r'\$.*mes\b|\bmensual\b', desc_lower):
            return "renta", 0.7
        elif re.search(r'\bcontado\b|\bfinanciamiento\b', desc_lower):
            return "venta", 0.7
        else:
            return "desconocido", 0.3
    else:
        return "desconocido", 0.0

def clasificar_por_precio(precio: float) -> str:
    """
    Clasifica el tipo de operación basándose en el precio.
    
    REGLA CORREGIDA:
    - Si precio > $300,000 SIN indicios en descripción = "venta"
    - Si precio ≤ $300,000 SIN indicios en descripción = "desconocido"
    
    Args:
        precio: Precio de la propiedad
        
    Returns:
        str: Tipo de operación sugerido
    """
    if precio > UMBRAL_PRECIO_VENTA:
        return "venta"
    else:
        return "desconocido"  # CORREGIDO: ya no asume "renta" automáticamente

def extraer_precio_numerico(precio_raw) -> float:
    """
    Extrae el valor numérico del precio desde diferentes formatos.
    
    Args:
        precio_raw: Precio en formato string, dict o numérico
        
    Returns:
        float: Valor numérico del precio
    """
    if precio_raw is None:
        return 0.0
    elif isinstance(precio_raw, (int, float)):
        return float(precio_raw)
    elif isinstance(precio_raw, str):
        if not precio_raw.strip():
            return 0.0
        # Limpiar string y extraer número
        precio_limpio = precio_raw.replace('$', '').replace(',', '').replace('.', '').replace('𝟲', '6').replace('𝟵', '9').replace('𝟴', '8').replace('𝟬', '0')
        match = re.search(r'\d+', precio_limpio)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return 0.0
    elif isinstance(precio_raw, dict):
        valor = precio_raw.get('valor', 0)
        if valor is None:
            return 0.0
        return float(valor)
    
    return 0.0

def actualizar_tipo_operacion(propiedad: Dict) -> Dict:
    """
    Actualiza el tipo de operación de una propiedad usando lógica avanzada.
    
    Args:
        propiedad: Diccionario con los datos de la propiedad
        
    Returns:
        Dict: Propiedad con el tipo de operación actualizado
    """
    if not isinstance(propiedad, dict):
        return propiedad
    
    # Obtener datos desde la estructura real de propiedades_estructuradas.json
    tipo_actual = propiedad.get("tipo_operacion", "").lower()
    descripcion = propiedad.get("datos_originales", {}).get("descripcion", "")
    precio_str = propiedad.get("datos_originales", {}).get("precio", "")
    
    # Extraer precio numérico
    precio = extraer_precio_numerico(precio_str)
    
    # Si ya tiene tipo válido, verificar consistencia
    if tipo_actual in ["venta", "renta"]:
        # Verificar consistencia con descripción
        tipo_detectado, confianza = detectar_tipo_por_descripcion(descripcion)
        
        if tipo_detectado != "desconocido":
            if tipo_detectado == tipo_actual:
                # Consistente
                logger.debug(f"Tipo consistente: {tipo_actual} (precio: ${precio:,.0f})")
                return propiedad
            else:
                # Inconsistente, priorizar descripción si confianza es alta
                if confianza >= 0.7:
                    logger.info(f"Corrigiendo tipo: {tipo_actual} -> {tipo_detectado} (precio: ${precio:,.0f})")
                    propiedad["tipo_operacion"] = tipo_detectado.title()
                    return propiedad
        
        logger.debug(f"Tipo mantenido: {tipo_actual} (precio: ${precio:,.0f})")
        return propiedad
    
    # Si no tiene tipo válido, detectar
    tipo_detectado, confianza_desc = detectar_tipo_por_descripcion(descripcion)
    
    if tipo_detectado != "desconocido" and confianza_desc >= 0.6:
        # Detección confiable por descripción
        nuevo_tipo = tipo_detectado
        metodo = "descripcion"
        logger.info(f"Tipo detectado por descripción: {nuevo_tipo} (confianza: {confianza_desc:.2f}, precio: ${precio:,.0f})")
    elif precio > 0:
        # Usar precio para clasificar
        nuevo_tipo = clasificar_por_precio(precio)
        metodo = "precio"
        
        # Si había detección parcial por descripción, combinar
        if tipo_detectado != "desconocido":
            if tipo_detectado == nuevo_tipo:
                logger.info(f"Tipo confirmado por precio y descripción: {nuevo_tipo} (precio: ${precio:,.0f})")
            else:
                # Conflicto entre descripción y precio, priorizar descripción
                if confianza_desc >= 0.4:
                    nuevo_tipo = tipo_detectado
                    metodo = "descripcion_vs_precio"
                    logger.info(f"Tipo por descripción vs precio: {nuevo_tipo} (desc: {tipo_detectado}, precio sugiere: {clasificar_por_precio(precio)})")
                else:
                    logger.info(f"Tipo por precio: {nuevo_tipo} (descripción incierta, precio: ${precio:,.0f})")
        else:
            logger.info(f"Tipo por precio: {nuevo_tipo} (precio: ${precio:,.0f})")
    else:
        # No se puede determinar
        nuevo_tipo = "desconocido"
        metodo = "sin_datos"
        logger.debug(f"Tipo no determinable: sin datos suficientes")
    
    # Actualizar tipo de operación
    propiedad["tipo_operacion"] = nuevo_tipo.title()
    
    return propiedad

def corregir_tipos_masivo(propiedades: list) -> dict:
    """
    Corrige tipos de operación de forma masiva.
    
    Args:
        propiedades: Lista de propiedades a corregir
        
    Returns:
        dict: Estadísticas de corrección
    """
    estadisticas = {
        "total_procesadas": 0,
        "correcciones": 0,
        "tipos_antes": {},
        "tipos_despues": {},
        "metodos_deteccion": {}
    }
    
    for propiedad in propiedades:
        # Contar tipo antes
        tipo_antes = propiedad.get("tipo_operacion", "desconocido").lower()
        estadisticas["tipos_antes"][tipo_antes] = estadisticas["tipos_antes"].get(tipo_antes, 0) + 1
        
        # Aplicar corrección
        propiedad_corregida = actualizar_tipo_operacion(propiedad)
        
        # Contar tipo después
        tipo_despues = propiedad_corregida.get("tipo_operacion", "desconocido").lower()
        estadisticas["tipos_despues"][tipo_despues] = estadisticas["tipos_despues"].get(tipo_despues, 0) + 1
        
        # Contar corrección si cambió
        if tipo_antes != tipo_despues:
            estadisticas["correcciones"] += 1
        
        estadisticas["total_procesadas"] += 1
    
    return estadisticas

if __name__ == "__main__":
    # Pruebas del módulo
    print("🧪 Probando módulo tipo_operacion...")
    
    # Casos de prueba con estructura real
    casos_prueba = [
        {
            "tipo_operacion": "",
            "datos_originales": {
                "descripcion": "Casa en renta, 3 recámaras, $15,000 mensuales",
                "precio": "$15000"
            }
        },
        {
            "tipo_operacion": "",
            "datos_originales": {
                "descripcion": "Se vende casa en Cuernavaca, precio $2,500,000",
                "precio": "$2500000"
            }
        },
        {
            "tipo_operacion": "",
            "datos_originales": {
                "descripcion": "Hermosa propiedad, excelente ubicación",
                "precio": "$450000"
            }
        },
        {
            "tipo_operacion": "",
            "datos_originales": {
                "descripcion": "Departamento céntrico, muy bien ubicado",
                "precio": "$1200000"
            }
        }
    ]
    
    for i, caso in enumerate(casos_prueba, 1):
        print(f"\n--- Caso {i} ---")
        resultado = actualizar_tipo_operacion(caso.copy())
        print(f"Descripción: {caso['datos_originales']['descripcion'][:50]}...")
        print(f"Precio: {caso['datos_originales']['precio']}")
        print(f"Resultado: {resultado['tipo_operacion']}") 
        Tuple[str, float]: (tipo_detectado, confianza)
    """
    if not descripcion:
        return "desconocido", 0.0
    
    desc_lower = descripcion.lower()
    
    # Contar coincidencias de renta
    coincidencias_renta = 0
    for patron in PATRONES_RENTA:
        if re.search(patron, desc_lower):
            coincidencias_renta += 1
    
    # Contar coincidencias de venta
    coincidencias_venta = 0
    for patron in PATRONES_VENTA:
        if re.search(patron, desc_lower):
            coincidencias_venta += 1
    
    # Determinar tipo y confianza
    if coincidencias_renta > coincidencias_venta:
        confianza = min(0.9, 0.6 + (coincidencias_renta * 0.1))
        return "renta", confianza
    elif coincidencias_venta > coincidencias_renta:
        confianza = min(0.9, 0.6 + (coincidencias_venta * 0.1))
        return "venta", confianza
    elif coincidencias_renta == coincidencias_venta and coincidencias_renta > 0:
        # Empate, buscar patrones más específicos
        if re.search(r'\$.*mes\b|\bmensual\b', desc_lower):
            return "renta", 0.7
        elif re.search(r'\bcontado\b|\bfinanciamiento\b', desc_lower):
            return "venta", 0.7
        else:
            return "desconocido", 0.3
    else:
        return "desconocido", 0.0

def clasificar_por_precio(precio: float) -> str:
    """
    Clasifica el tipo de operación basándose en el precio.
    
    REGLA CORREGIDA:
    - Si precio > $300,000 SIN indicios en descripción = "venta"
    - Si precio ≤ $300,000 SIN indicios en descripción = "desconocido"
    
    Args:
        precio: Precio de la propiedad
        
    Returns:
        str: Tipo de operación sugerido
    """
    if precio > UMBRAL_PRECIO_VENTA:
        return "venta"
    else:
        return "desconocido"  # CORREGIDO: ya no asume "renta" automáticamente

def extraer_precio_numerico(precio_raw) -> float:
    """
    Extrae el valor numérico del precio desde diferentes formatos.
    
    Args:
        precio_raw: Precio en formato string, dict o numérico
        
    Returns:
        float: Valor numérico del precio
    """
    if precio_raw is None:
        return 0.0
    elif isinstance(precio_raw, (int, float)):
        return float(precio_raw)
    elif isinstance(precio_raw, str):
        if not precio_raw.strip():
            return 0.0
        # Limpiar string y extraer número
        precio_limpio = precio_raw.replace('$', '').replace(',', '').replace('.', '').replace('𝟲', '6').replace('𝟵', '9').replace('𝟴', '8').replace('𝟬', '0')
        match = re.search(r'\d+', precio_limpio)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return 0.0
    elif isinstance(precio_raw, dict):
        valor = precio_raw.get('valor', 0)
        if valor is None:
            return 0.0
        return float(valor)
    
    return 0.0

def actualizar_tipo_operacion(propiedad: Dict) -> Dict:
    """
    Actualiza el tipo de operación de una propiedad usando lógica avanzada.
    
    Args:
        propiedad: Diccionario con los datos de la propiedad
        
    Returns:
        Dict: Propiedad con el tipo de operación actualizado
    """
    if not isinstance(propiedad, dict):
        return propiedad
    
    # Obtener datos desde la estructura real de propiedades_estructuradas.json
    tipo_actual = propiedad.get("tipo_operacion", "").lower()
    descripcion = propiedad.get("datos_originales", {}).get("descripcion", "")
    precio_str = propiedad.get("datos_originales", {}).get("precio", "")
    
    # Extraer precio numérico
    precio = extraer_precio_numerico(precio_str)
    
    # Si ya tiene tipo válido, verificar consistencia
    if tipo_actual in ["venta", "renta"]:
        # Verificar consistencia con descripción
        tipo_detectado, confianza = detectar_tipo_por_descripcion(descripcion)
        
        if tipo_detectado != "desconocido":
            if tipo_detectado == tipo_actual:
                # Consistente
                logger.debug(f"Tipo consistente: {tipo_actual} (precio: ${precio:,.0f})")
                return propiedad
            else:
                # Inconsistente, priorizar descripción si confianza es alta
                if confianza >= 0.7:
                    logger.info(f"Corrigiendo tipo: {tipo_actual} -> {tipo_detectado} (precio: ${precio:,.0f})")
                    propiedad["tipo_operacion"] = tipo_detectado.title()
                    return propiedad
        
        logger.debug(f"Tipo mantenido: {tipo_actual} (precio: ${precio:,.0f})")
        return propiedad
    
    # Si no tiene tipo válido, detectar
    tipo_detectado, confianza_desc = detectar_tipo_por_descripcion(descripcion)
    
    if tipo_detectado != "desconocido" and confianza_desc >= 0.6:
        # Detección confiable por descripción
        nuevo_tipo = tipo_detectado
        metodo = "descripcion"
        logger.info(f"Tipo detectado por descripción: {nuevo_tipo} (confianza: {confianza_desc:.2f}, precio: ${precio:,.0f})")
    elif precio > 0:
        # Usar precio para clasificar
        nuevo_tipo = clasificar_por_precio(precio)
        metodo = "precio"
        
        # Si había detección parcial por descripción, combinar
        if tipo_detectado != "desconocido":
            if tipo_detectado == nuevo_tipo:
                logger.info(f"Tipo confirmado por precio y descripción: {nuevo_tipo} (precio: ${precio:,.0f})")
            else:
                # Conflicto entre descripción y precio, priorizar descripción
                if confianza_desc >= 0.4:
                    nuevo_tipo = tipo_detectado
                    metodo = "descripcion_vs_precio"
                    logger.info(f"Tipo por descripción vs precio: {nuevo_tipo} (desc: {tipo_detectado}, precio sugiere: {clasificar_por_precio(precio)})")
                else:
                    logger.info(f"Tipo por precio: {nuevo_tipo} (descripción incierta, precio: ${precio:,.0f})")
        else:
            logger.info(f"Tipo por precio: {nuevo_tipo} (precio: ${precio:,.0f})")
    else:
        # No se puede determinar
        nuevo_tipo = "desconocido"
        metodo = "sin_datos"
        logger.debug(f"Tipo no determinable: sin datos suficientes")
    
    # Actualizar tipo de operación
    propiedad["tipo_operacion"] = nuevo_tipo.title()
    
    return propiedad

def corregir_tipos_masivo(propiedades: list) -> dict:
    """
    Corrige tipos de operación de forma masiva.
    
    Args:
        propiedades: Lista de propiedades a corregir
        
    Returns:
        dict: Estadísticas de corrección
    """
    estadisticas = {
        "total_procesadas": 0,
        "correcciones": 0,
        "tipos_antes": {},
        "tipos_despues": {},
        "metodos_deteccion": {}
    }
    
    for propiedad in propiedades:
        # Contar tipo antes
        tipo_antes = propiedad.get("tipo_operacion", "desconocido").lower()
        estadisticas["tipos_antes"][tipo_antes] = estadisticas["tipos_antes"].get(tipo_antes, 0) + 1
        
        # Aplicar corrección
        propiedad_corregida = actualizar_tipo_operacion(propiedad)
        
        # Contar tipo después
        tipo_despues = propiedad_corregida.get("tipo_operacion", "desconocido").lower()
        estadisticas["tipos_despues"][tipo_despues] = estadisticas["tipos_despues"].get(tipo_despues, 0) + 1
        
        # Contar corrección si cambió
        if tipo_antes != tipo_despues:
            estadisticas["correcciones"] += 1
        
        estadisticas["total_procesadas"] += 1
    
    return estadisticas

if __name__ == "__main__":
    # Pruebas del módulo
    print("🧪 Probando módulo tipo_operacion...")
    
    # Casos de prueba con estructura real
    casos_prueba = [
        {
            "tipo_operacion": "",
            "datos_originales": {
                "descripcion": "Casa en renta, 3 recámaras, $15,000 mensuales",
                "precio": "$15000"
            }
        },
        {
            "tipo_operacion": "",
            "datos_originales": {
                "descripcion": "Se vende casa en Cuernavaca, precio $2,500,000",
                "precio": "$2500000"
            }
        },
        {
            "tipo_operacion": "",
            "datos_originales": {
                "descripcion": "Hermosa propiedad, excelente ubicación",
                "precio": "$450000"
            }
        },
        {
            "tipo_operacion": "",
            "datos_originales": {
                "descripcion": "Departamento céntrico, muy bien ubicado",
                "precio": "$1200000"
            }
        }
    ]
    
    for i, caso in enumerate(casos_prueba, 1):
        print(f"\n--- Caso {i} ---")
        resultado = actualizar_tipo_operacion(caso.copy())
        print(f"Descripción: {caso['datos_originales']['descripcion'][:50]}...")
        print(f"Precio: {caso['datos_originales']['precio']}")
        print(f"Resultado: {resultado['tipo_operacion']}") 