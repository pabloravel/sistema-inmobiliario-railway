#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MÓDULO DE ASPECTOS LEGALES
-------------------------

Este módulo es responsable de detectar y validar los aspectos legales
de las propiedades, como escrituras, créditos, etc.

RESPONSABILIDADES:
1. Detectar aspectos legales en texto
2. Validar documentación legal
3. Mantener catálogo de indicadores
4. Proveer estadísticas de confianza

REGLAS:
1. Validar todos los aspectos detectados
2. NO modificar otros aspectos de la propiedad
3. Mantener registro de decisiones tomadas
4. En caso de duda, marcar como None
"""

import re
import logging
from typing import Dict, Optional, List, Tuple
from decimal import Decimal

# Configuración de logging
logger = logging.getLogger('legal')
logger.setLevel(logging.DEBUG)

# Catálogo de aspectos legales y sus indicadores
LEGAL = {
    "escrituras": {
        "positivos": [
            "con escrituras", "escrituras al dia", "escrituras al día",
            "escrituras en regla", "escrituras publicas", "escrituras públicas",
            "tiene escrituras", "cuenta con escrituras",
            "escrituras listas", "escrituras disponibles"
        ],
        "negativos": [
            "sin escrituras", "no tiene escrituras", "faltan escrituras",
            "en proceso de escrituras", "escrituras en tramite", "escrituras en trámite",
            "en proceso de escrituración", "escrituración en proceso",
            "escrituras en proceso", "tramitando escrituras"
        ]
    },
    
    "cesion_derechos": {
        "indicadores": [
            "cesion de derechos", "cesión de derechos",
            "traspaso de derechos", "venta de derechos",
            "derechos ejidales", "derechos parcelarios"
        ]
    },
    
    "creditos": {
        "generales": [
            "se aceptan creditos", "se aceptan créditos",
            "acepta creditos", "acepta créditos",
            "todos los creditos", "todos los créditos",
            "cualquier tipo de credito", "cualquier tipo de crédito"
        ],
        "tipos": {
            "infonavit": [
                "credito infonavit", "crédito infonavit",
                "acepta infonavit", "se acepta infonavit",
                "infonavit"
            ],
            "fovissste": [
                "credito fovissste", "crédito fovissste",
                "acepta fovissste", "se acepta fovissste",
                "fovissste"
            ],
            "bancario": [
                "credito bancario", "crédito bancario",
                "credito hipotecario", "crédito hipotecario",
                "bancario", "hipotecario", "bancarios"
            ],
            "contado": [
                "de contado", "pago de contado",
                "solo contado", "unicamente contado",
                "exclusivamente contado"
            ]
        }
    }
}

class LegalInvalido(Exception):
    """Excepción para aspectos legales inválidos"""
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

def detectar_escrituras(texto: str) -> Dict:
    """
    Detecta información sobre escrituras.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - valor: bool o None
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
    info = LEGAL["escrituras"]
    
    # Buscar indicadores negativos primero (tienen prioridad)
    for indicador in info["negativos"]:
        if indicador in texto_norm:
            resultado.update({
                "valor": False,
                "confianza": 0.9,
                "evidencia": [f"Indicador negativo encontrado: {indicador}"]
            })
            return resultado
    
    # Buscar indicadores positivos
    for indicador in info["positivos"]:
        if indicador in texto_norm:
            resultado.update({
                "valor": True,
                "confianza": 0.9,
                "evidencia": [f"Indicador positivo encontrado: {indicador}"]
            })
            return resultado
    
    # Casos especiales
    if "en proceso de escrituracion" in texto_norm or "en proceso de escrituración" in texto_norm:
        resultado.update({
            "valor": False,
            "confianza": 0.9,
            "evidencia": ["Escrituras en proceso de trámite"]
        })
        return resultado
    
    # Si se menciona "escritura" o "escrituras" sin contexto claro
    if "escritura" in texto_norm or "escrituras" in texto_norm:
        resultado.update({
            "valor": None,
            "confianza": 0.5,
            "evidencia": ["Mención ambigua de escrituras"]
        })
    
    return resultado

def detectar_cesion_derechos(texto: str) -> Dict:
    """
    Detecta información sobre cesión de derechos.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - valor: bool
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    resultado = {
        "valor": False,
        "confianza": 0.0,
        "evidencia": []
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    info = LEGAL["cesion_derechos"]
    
    # Buscar indicadores
    for indicador in info["indicadores"]:
        if indicador in texto_norm:
            resultado.update({
                "valor": True,
                "confianza": 0.9,
                "evidencia": [f"Indicador encontrado: {indicador}"]
            })
            return resultado
    
    return resultado

def detectar_creditos(texto: str) -> Dict:
    """
    Detecta información sobre créditos aceptados.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con:
        - acepta_creditos: bool
        - tipos_aceptados: List[str]
        - confianza: float (0-1)
        - evidencia: List[str]
    """
    resultado = {
        "acepta_creditos": False,
        "tipos_aceptados": [],
        "confianza": 0.0,
        "evidencia": []
    }
    
    if not texto:
        return resultado
        
    texto_norm = _normalizar_texto(texto)
    info = LEGAL["creditos"]
    
    # Detectar aceptación general de créditos
    for indicador in info["generales"]:
        if indicador in texto_norm:
            resultado.update({
                "acepta_creditos": True,
                "confianza": 0.8,
                "evidencia": [f"Indicador general encontrado: {indicador}"]
            })
            break
    
    # Detectar tipos específicos
    for tipo, indicadores in info["tipos"].items():
        if tipo == "contado":
            continue  # Manejar contado después
            
        for indicador in indicadores:
            if indicador in texto_norm:
                resultado["acepta_creditos"] = True
                if tipo not in resultado["tipos_aceptados"]:
                    resultado["tipos_aceptados"].append(tipo)
                    resultado["evidencia"].append(f"Tipo de crédito detectado: {tipo}")
                    resultado["confianza"] = max(resultado["confianza"], 0.9)
                break
    
    # Detectar si es solo contado
    es_solo_contado = False
    for indicador in info["tipos"]["contado"]:
        if indicador in texto_norm:
            if "solo" in indicador or "unicamente" in indicador or "exclusivamente" in indicador:
                es_solo_contado = True
                break
    
    if es_solo_contado:
        resultado.update({
            "acepta_creditos": False,
            "tipos_aceptados": [],
            "confianza": 0.9,
            "evidencia": ["Solo acepta pago de contado"]
        })
    elif len(resultado["tipos_aceptados"]) > 1:
        # Si se mencionan varios tipos, aumentar la confianza
        resultado["confianza"] = 0.95
        resultado["evidencia"].append(f"Detectados {len(resultado['tipos_aceptados'])} tipos de crédito")
    elif resultado["acepta_creditos"] and not resultado["tipos_aceptados"]:
        # Si se indica aceptación general pero no se especifican tipos
        resultado["tipos_aceptados"] = ["infonavit", "fovissste", "bancario"]
        resultado["evidencia"].append("Se asumen todos los tipos por indicador general")
    
    return resultado

def actualizar_legal(propiedad: Dict) -> Dict:
    """
    Actualiza los aspectos legales en una propiedad.
    Esta es la función principal que otros módulos deben usar.
    
    Args:
        propiedad: Dict con datos de la propiedad
        
    Returns:
        Dict: Propiedad con aspectos legales actualizados
    """
    try:
        # Extraer textos relevantes
        textos = []
        
        # Priorizar título
        if "titulo" in propiedad:
            textos.append(propiedad["titulo"])
        
        # Agregar descripción original
        if "descripcion_original" in propiedad:
            textos.append(propiedad["descripcion_original"])
        
        # Agregar descripción procesada
        if "descripcion" in propiedad:
            textos.append(propiedad["descripcion"])
        
        # Combinar textos
        texto_completo = " ".join(textos)
        
        # Detectar aspectos legales
        info_escrituras = detectar_escrituras(texto_completo)
        info_cesion = detectar_cesion_derechos(texto_completo)
        info_creditos = detectar_creditos(texto_completo)
        
        # Actualizar la propiedad
        if "legal" not in propiedad:
            propiedad["legal"] = {}
            
        propiedad["legal"].update({
            "escrituras": info_escrituras,
            "cesion_derechos": info_cesion,
            "creditos": info_creditos,
            "confianza": max(
                info_escrituras["confianza"],
                info_cesion["confianza"],
                info_creditos["confianza"]
            )
        })
        
        return propiedad
        
    except Exception as e:
        logger.error(f"Error actualizando aspectos legales: {str(e)}")
        return propiedad

def validar_legal(legal: Dict) -> bool:
    """
    Valida si los aspectos legales son válidos y completos.
    
    Args:
        legal: Dict con aspectos legales
        
    Returns:
        bool: True si son válidos
    """
    # Debe tener información sobre escrituras o cesión
    if legal.get("escrituras", {}).get("valor") is None and not legal.get("cesion_derechos", {}).get("valor"):
        return False
    
    # La confianza debe ser razonable
    if legal.get("confianza", 0) < 0.5:
        return False
    
    return True

def obtener_estadisticas(propiedades: List[Dict]) -> Dict:
    """
    Genera estadísticas sobre aspectos legales.
    
    Args:
        propiedades: Lista de propiedades
        
    Returns:
        Dict con estadísticas
    """
    stats = {
        "total": len(propiedades),
        "con_legal_valido": 0,
        "distribucion": {
            "con_escrituras": 0,
            "sin_escrituras": 0,
            "cesion_derechos": 0,
            "acepta_creditos": 0
        },
        "tipos_credito": {
            "infonavit": 0,
            "fovissste": 0,
            "bancario": 0,
            "contado": 0
        },
        "confianza_promedio": 0
    }
    
    confianza_total = 0
    for prop in propiedades:
        legal = prop.get("legal", {})
        
        # Contar aspectos legales válidos
        if validar_legal(legal):
            stats["con_legal_valido"] += 1
        
        # Contar escrituras
        escrituras = legal.get("escrituras", {}).get("valor")
        if escrituras is True:
            stats["distribucion"]["con_escrituras"] += 1
        elif escrituras is False:
            stats["distribucion"]["sin_escrituras"] += 1
        
        # Contar cesión de derechos
        if legal.get("cesion_derechos", {}).get("valor"):
            stats["distribucion"]["cesion_derechos"] += 1
        
        # Contar créditos
        creditos = legal.get("creditos", {})
        if creditos.get("acepta_creditos"):
            stats["distribucion"]["acepta_creditos"] += 1
            
            # Contar tipos de crédito
            for tipo in creditos.get("tipos_aceptados", []):
                stats["tipos_credito"][tipo] = stats["tipos_credito"].get(tipo, 0) + 1
        
        # Acumular confianza
        confianza = legal.get("confianza", 0)
        confianza_total += confianza
    
    # Calcular promedio de confianza
    stats["confianza_promedio"] = confianza_total / len(propiedades) if propiedades else 0
    
    return stats

def analizar_estatus_legal(texto: str) -> Dict:
    """
    Analiza todos los aspectos legales de una propiedad.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Dict con todos los aspectos legales detectados
    """
    resultado = {
        "tiene_escrituras": None,
        "cesion_derechos": False,
        "acepta_creditos": False,
        "creditos_aceptados": [],
        "confianza": 0.0,
        "evidencia": []
    }
    
    # Detectar escrituras
    info_escrituras = detectar_escrituras(texto)
    if info_escrituras["valor"] is not None:
        resultado["tiene_escrituras"] = info_escrituras["valor"]
        resultado["evidencia"].extend(info_escrituras["evidencia"])
        resultado["confianza"] = max(resultado["confianza"], info_escrituras["confianza"])
    elif "en proceso de escrituración" in _normalizar_texto(texto):
        # Caso especial para escrituración en proceso
        resultado["tiene_escrituras"] = False
        resultado["evidencia"].append("Escrituras en proceso de trámite")
        resultado["confianza"] = max(resultado["confianza"], 0.9)
    
    # Detectar cesión de derechos
    info_cesion = detectar_cesion_derechos(texto)
    if info_cesion["valor"]:
        resultado["cesion_derechos"] = True
        resultado["evidencia"].extend(info_cesion["evidencia"])
        resultado["confianza"] = max(resultado["confianza"], info_cesion["confianza"])
    
    # Detectar créditos
    info_creditos = detectar_creditos(texto)
    if info_creditos["acepta_creditos"] or info_creditos["tipos_aceptados"]:
        resultado["acepta_creditos"] = True
        resultado["creditos_aceptados"] = info_creditos["tipos_aceptados"]
        resultado["evidencia"].extend(info_creditos["evidencia"])
        resultado["confianza"] = max(resultado["confianza"], info_creditos["confianza"])
    
    # Si solo acepta contado, marcar como no acepta créditos
    if "contado" in resultado["creditos_aceptados"] and len(resultado["creditos_aceptados"]) == 1:
        resultado["acepta_creditos"] = False
        resultado["creditos_aceptados"] = []
        resultado["evidencia"].append("Solo acepta pago de contado")
    
    return resultado 