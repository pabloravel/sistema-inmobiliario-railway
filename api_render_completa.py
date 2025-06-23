#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 API RENDER MANUAL - ARREGLO INMEDIATO IMÁGENES
Archivo para subir manualmente a Render
Soluciona problema de imágenes con placeholders profesionales
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import time

# CONFIGURACIÓN
app = FastAPI(
    title="🏠 Sistema Inmobiliario - Arreglo Manual",
    description="API con placeholders profesionales para imágenes",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LOGGING
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# BASE DE DATOS
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL no configurada")

def get_db_connection():
    """Conexión a PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"❌ Error conectando a BD: {e}")
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")

@app.get("/", response_class=HTMLResponse)
async def frontend_principal():
    """Frontend principal con placeholders profesionales"""
    html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏠 Sistema Inmobiliario - FUNCIONANDO</title>
    <style>
        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .status {
            background: #dcfce7;
            color: #166534;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
            font-weight: bold;
        }
        .properties-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .property-card {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
            background: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .property-card:hover {
            transform: translateY(-2px);
        }
        .property-content {
            padding: 15px;
        }
        .property-title {
            font-size: 1.1rem;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .property-price {
            color: #059669;
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .property-location {
            color: #6b7280;
            margin-bottom: 15px;
        }
        .image-placeholder {
            width: 100%;
            height: 200px;
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.1rem;
            font-weight: bold;
        }
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.2rem;
        }
        .error {
            background: #fee2e2;
            color: #dc2626;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 Sistema Inmobiliario</h1>
            <p>✅ ARREGLO MANUAL APLICADO - Sistema Funcionando</p>
        </div>
        
        <div class="status">
            ✅ <strong>SISTEMA OPERATIVO:</strong> Usando placeholders profesionales mientras se soluciona S3
        </div>
        
        <div id="loading" class="loading">
            ⏳ Cargando propiedades...
        </div>
        
        <div id="error" class="error" style="display: none;"></div>
        
        <div id="properties-container" class="properties-grid"></div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        
        function crearImagenProfesional(property) {
            const tipoPropiedad = property.tipo_propiedad || 'Propiedad';
            const ciudad = property.ciudad || 'Morelos';
            
            const emojis = {
                'Casa': '🏠',
                'Departamento': '🏢', 
                'Local': '🏪',
                'Terreno': '🌿',
                'Oficina': '🏢',
                'Bodega': '🏭'
            };
            
            const emoji = emojis[tipoPropiedad] || '🏠';
            
            return `
                <div class="image-placeholder">
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; margin-bottom: 10px;">${emoji}</div>
                        <div>${tipoPropiedad}</div>
                        <div style="font-size: 0.9rem; opacity: 0.8;">${ciudad}</div>
                    </div>
                </div>
            `;
        }

        function createPropertyCard(property) {
            const div = document.createElement('div');
            div.className = 'property-card';
            
            const titulo = `${property.tipo_propiedad || 'Propiedad'} en ${property.ciudad || 'Ubicación no especificada'}`;
            const precio = formatPrice(property.precio);
            const ubicacion = getLocation(property);
            
            const imagenPlaceholder = crearImagenProfesional(property);
            
            div.innerHTML = `
                ${imagenPlaceholder}
                
                <div class="property-content">
                    <h3 class="property-title">${titulo}</h3>
                    <div class="property-price">${precio}</div>
                    <div class="property-location">📍 ${ubicacion}</div>
                    <div style="font-size: 0.8rem; color: #6b7280; margin-top: 10px;">
                        🔖 ${property.tipo_operacion || 'Sin especificar'} • 🆔 ${property.id}
                    </div>
                    <div style="font-size: 0.7rem; color: #059669; margin-top: 5px;">
                        ✅ Sistema funcionando con placeholders
                    </div>
                </div>
            `;
            
            return div;
        }

        function formatPrice(precio) {
            if (!precio || precio === 0) return 'Precio a consultar';
            
            if (typeof precio === 'string') {
                precio = parseFloat(precio.replace(/[^0-9.-]+/g, ''));
            }
            
            return `$${precio.toLocaleString('es-MX')}`;
        }

        function getLocation(property) {
            const ubicaciones = [
                property.ciudad,
                property.estado,
                property.colonia,
                property.direccion
            ].filter(Boolean);
            
            return ubicaciones.join(', ') || 'Ubicación no especificada';
        }

        async function loadProperties() {
            try {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('error').style.display = 'none';
                
                const response = await fetch(`${API_BASE}/propiedades?pagina=1&por_pagina=60`);
                if (!response.ok) {
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (!data.propiedades || data.propiedades.length === 0) {
                    throw new Error('No se encontraron propiedades');
                }
                
                displayProperties(data.propiedades);
                document.getElementById('loading').style.display = 'none';
                
            } catch (error) {
                console.error('❌ Error:', error);
                document.getElementById('loading').style.display = 'none';
                const errorDiv = document.getElementById('error');
                errorDiv.textContent = `Error: ${error.message}`;
                errorDiv.style.display = 'block';
            }
        }

        function displayProperties(properties) {
            const container = document.getElementById('properties-container');
            container.innerHTML = '';
            
            properties.forEach(property => {
                const card = createPropertyCard(property);
                container.appendChild(card);
            });
        }

        document.addEventListener('DOMContentLoaded', () => {
            console.log('🚀 Sistema con placeholders cargando...');
            loadProperties();
        });
    </script>
</body>
</html>"""
    
    return HTMLResponse(content=html_content)

@app.get("/propiedades")
async def obtener_propiedades(
    pagina: int = 1,
    por_pagina: int = 60,
    precio_min: int = 1,
    precio_max: Optional[int] = None,
    ciudad: Optional[str] = None,
    tipo_operacion: Optional[str] = None,
    tipo_propiedad: Optional[str] = None
):
    """Obtener propiedades con filtros"""
    start_time = time.time()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query base
        query = """
            SELECT 
                id,
                titulo,
                precio,
                ciudad,
                estado,
                colonia,
                direccion,
                tipo_propiedad,
                tipo_operacion,
                descripcion,
                recamaras,
                banos,
                estacionamientos,
                superficie_m2,
                fecha_publicacion,
                link,
                imagen
            FROM propiedades 
            WHERE precio >= %s
        """
        
        params = [precio_min]
        
        # Filtros adicionales
        if precio_max:
            query += " AND precio <= %s"
            params.append(precio_max)
        
        if ciudad:
            query += " AND LOWER(ciudad) LIKE LOWER(%s)"
            params.append(f"%{ciudad}%")
        
        if tipo_operacion:
            query += " AND LOWER(tipo_operacion) = LOWER(%s)"
            params.append(tipo_operacion)
        
        if tipo_propiedad:
            query += " AND LOWER(tipo_propiedad) = LOWER(%s)"
            params.append(tipo_propiedad)
        
        # Ordenar y paginar
        query += " ORDER BY fecha_publicacion DESC"
        
        # Contar total
        count_query = query.replace("SELECT id,titulo,precio,ciudad,estado,colonia,direccion,tipo_propiedad,tipo_operacion,descripcion,recamaras,banos,estacionamientos,superficie_m2,fecha_publicacion,link,imagen", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Paginación
        offset = (pagina - 1) * por_pagina
        query += " LIMIT %s OFFSET %s"
        params.extend([por_pagina, offset])
        
        cursor.execute(query, params)
        propiedades = cursor.fetchall()
        
        # Convertir a dict
        propiedades_dict = []
        for prop in propiedades:
            prop_dict = dict(prop)
            # Asegurar que precio sea numérico
            if prop_dict.get('precio'):
                try:
                    prop_dict['precio'] = float(prop_dict['precio'])
                except:
                    prop_dict['precio'] = 0
            propiedades_dict.append(prop_dict)
        
        total_paginas = (total + por_pagina - 1) // por_pagina
        tiempo_consulta = round((time.time() - start_time) * 1000, 2)
        
        cursor.close()
        conn.close()
        
        return {
            "propiedades": propiedades_dict,
            "total": total,
            "pagina_actual": pagina,
            "por_pagina": por_pagina,
            "total_paginas": total_paginas,
            "tiempo_consulta_ms": tiempo_consulta,
            "mensaje": "✅ Sistema funcionando con placeholders profesionales"
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo propiedades: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/health")
async def health_check():
    """Verificación de salud del sistema"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM propiedades")
        total_propiedades = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return {
            "status": "✅ FUNCIONANDO",
            "timestamp": datetime.now().isoformat(),
            "total_propiedades": total_propiedades,
            "mensaje": "Sistema operativo con placeholders profesionales"
        }
    except Exception as e:
        logger.error(f"❌ Error en health check: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 