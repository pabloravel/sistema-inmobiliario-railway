#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MÓDULO DE NORMALIZACIÓN DE PRECIOS
---------------------------------

Este módulo normaliza el formato de los precios que vienen de Facebook.
No realiza validaciones ni extracciones de texto, ya que Facebook
ya valida los precios antes de mostrarlos.
"""

import re
import logging
from typing import Dict, Optional, Union
from decimal import Decimal, InvalidOperation

# Configuración de logging
logger = logging.getLogger('precio')
logger.setLevel(logging.DEBUG)

def normalizar_precio(precio: Union[str, float, int]) -> Dict:
    """
    Normaliza el formato de un precio que viene de Facebook.
    
    Args:
        precio: Precio en formato string, float o int
        
    Returns:
        Dict con:
        - valor: float
        - moneda: str ('MXN')
        - texto_original: str
    """
    resultado = {
        "valor": None,
        "moneda": "MXN",
        "texto_original": str(precio) if precio is not None else ""
    }
    
    if precio is None:
        return resultado
        
    try:
        if isinstance(precio, str):
            # Limpiar el string de símbolos no numéricos excepto punto y coma
            valor = re.sub(r'[^\d.,]', '', precio)
            
            # Si está vacío después de limpiar, retornar None
            if not valor:
                return resultado
                
            # Manejar diferentes formatos de número
            if ',' in valor and '.' in valor:
                # Si hay ambos separadores, determinar cuál es el decimal
                if valor.find(',') < valor.find('.'):
                    # Formato: 1,234,567.89 -> 1234567.89
                    valor = valor.replace(',', '')
                else:
                    # Formato: 1.234.567,89 -> 1234567.89
                    valor = valor.replace('.', '').replace(',', '.')
            elif ',' in valor:
                # Si solo hay coma, verificar si es decimal o separador de miles
                partes = valor.split(',')
                if len(partes) == 2 and len(partes[1]) <= 2:
                    # Formato: 1234567,89 -> 1234567.89
                    valor = valor.replace(',', '.')
                else:
                    # Formato: 1,234,567 -> 1234567
                    valor = valor.replace(',', '')
            elif '.' in valor:
                # Si solo hay punto, verificar si es separador de miles o decimal
                partes = valor.split('.')
                if len(partes) == 2 and len(partes[1]) <= 2:
                    # Formato: 1234567.89 -> 1234567.89
                    pass
                else:
                    # Formato: 1.234.567 -> 1234567
                    valor = valor.replace('.', '')
            
            # Convertir a float
            resultado["valor"] = float(valor)
        else:
            # Si ya es número, convertirlo a float
            resultado["valor"] = float(precio)
            
    except (ValueError, TypeError, InvalidOperation):
        pass
    
    return resultado

def formatear_precio(precio: Union[Dict, float, int, str]) -> str:
    """
    Formatea un precio para mostrar.
    
    Args:
        precio: Precio en cualquier formato soportado
        
    Returns:
        str: Precio formateado como "$X,XXX,XXX"
    """
    if isinstance(precio, dict):
        valor = precio.get("valor")
    else:
        valor = precio
        
    if valor is None:
        return ""
        
    try:
        valor = float(valor)
        return f"${valor:,.2f}"
    except (ValueError, TypeError):
        return str(precio)

def actualizar_precio_propiedad(propiedad: Dict) -> Dict:
    """
    Actualiza el campo de precio de una propiedad.
    
    Args:
        propiedad: Diccionario con los datos de la propiedad
        
    Returns:
        Dict: Propiedad con el precio actualizado
    """
    if not isinstance(propiedad, dict):
        return propiedad
        
    # Si no hay campo precio, retornar la propiedad sin cambios
    if "precio" not in propiedad:
        return propiedad
        
    # Normalizar el precio
    precio_normalizado = normalizar_precio(propiedad["precio"])
        
    # Actualizar la propiedad
    propiedad["precio"] = precio_normalizado
    
    return propiedad 