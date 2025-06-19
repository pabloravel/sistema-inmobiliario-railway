#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de procesamiento de tipo de propiedad.
"""

import logging
from typing import Dict

# Configuración de logging
logger = logging.getLogger('tipo_propiedad')
logger.setLevel(logging.DEBUG)

def actualizar_tipo_propiedad(propiedad: Dict) -> Dict:
    """
    Actualiza el tipo de propiedad.
    
    Args:
        propiedad: Diccionario con los datos de la propiedad
        
    Returns:
        Dict: Propiedad con el tipo de propiedad actualizado
    """
    if not isinstance(propiedad, dict):
        return propiedad
        
    if "propiedad" not in propiedad:
        return propiedad

    # Obtener el tipo de propiedad
    tipo_prop = propiedad["propiedad"].get("tipo_propiedad", "").lower()
    
    # Tipos válidos
    tipos_validos = [
        "casa", "departamento", "terreno", "local", "oficina",
        "bodega", "edificio", "cabaña", "lote", "ejidal"
    ]
    
    # Si es un tipo válido, dejarlo así
    if tipo_prop in tipos_validos:
        propiedad["propiedad"]["tipo_propiedad"] = tipo_prop
    else:
        # Si no es un tipo válido, marcar como desconocido
        propiedad["propiedad"]["tipo_propiedad"] = "desconocido"
        
    return propiedad 