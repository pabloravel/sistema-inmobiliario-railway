# Sistema Inmobiliario Morelos

Sistema web para la gestión y visualización de propiedades inmobiliarias en el estado de Morelos, México.

## 🏠 Características

- **5,434 propiedades** en base de datos PostgreSQL
- **Búsqueda avanzada** con filtros múltiples
- **API REST** con FastAPI
- **Frontend responsive** con diseño moderno
- **Imágenes optimizadas** con carga dinámica
- **Paginación eficiente** (60 propiedades por página)

## 🚀 Tecnologías

- **Backend**: Python, FastAPI, PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript
- **Base de datos**: PostgreSQL con índices optimizados
- **Deployment**: Railway

## 📊 Estadísticas

- **Total propiedades**: 5,434
- **Ciudades**: 11 municipios de Morelos
- **Tipos de propiedad**: Casa, Departamento, Terreno, Local
- **Operaciones**: Venta, Renta
- **Rendimiento**: < 50ms por consulta

## 🌐 URLs

- **API**: `/docs` - Documentación interactiva
- **Frontend**: `/frontend_desarrollo_postgresql_v2_con_diseno_original.html`

## 🔧 Instalación Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env

# Ejecutar API
uvicorn api_colaborativa:app --reload

# Servir frontend
python -m http.server 8080
```

## 📝 API Endpoints

- `GET /propiedades` - Listar propiedades con filtros
- `GET /propiedades/{id}` - Obtener propiedad específica
- `GET /estadisticas` - Estadísticas del sistema
- `GET /ciudades` - Lista de ciudades disponibles

## 🏆 Estado del Sistema

✅ **Sistema 100% funcional**  
✅ **Base de datos optimizada**  
✅ **API documentada**  
✅ **Frontend responsive**  
✅ **Deployment automatizado**

---

**Última actualización**: 19 de junio 2025 - Sistema Railway optimizado # Forzar nuevo deployment Railway - Thu Jun 19 17:00:17 CST 2025
# Railway deployment fix - Thu Jun 19 17:01:17 CST 2025
# Forzar redeploy
# Force redeploy Fri Jun 20 09:40:58 CST 2025
# Added PORT variable Fri Jun 20 09:42:53 CST 2025
# PORT variable added Fri Jun 20 09:47:29 CST 2025
# Final deployment Fri Jun 20 09:51:08 CST 2025
