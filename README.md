# 🏠 Sistema Inmobiliario - Railway Deployment

Sistema inmobiliario con **5,434 propiedades** en Morelos, México. Plataforma colaborativa con gestión de usuarios, favoritos y contactos.

## 🚀 Características

- **5,434 propiedades** verificadas en Morelos
- **Sistema colaborativo** con usuarios y favoritos
- **API REST** con FastAPI y PostgreSQL
- **Frontend responsive** con diseño moderno
- **Gestión de contactos** para cada propiedad
- **Filtros avanzados** por ciudad, tipo, precio
- **Búsqueda inteligente** por texto e ID

## 📊 Estadísticas

- **Propiedades**: 5,434 total
- **Con precios válidos**: 2,560+ (47.1%+)
- **Ciudades**: 11 principales de Morelos
- **Tipos**: Casa, Departamento, Terreno, Local
- **Operaciones**: Venta, Renta, Desconocido

## 🛠️ Tecnologías

- **Backend**: Python 3.9, FastAPI, SQLAlchemy
- **Base de datos**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript
- **Deployment**: Railway
- **Autenticación**: JWT

## 🌐 URLs

- **API**: https://tu-app.railway.app
- **Frontend**: https://tu-app.railway.app/frontend_desarrollo_postgresql_v2_con_diseno_original.html
- **Sistema Colaborativo**: https://tu-app.railway.app/frontend_colaborativo.html
- **Documentación**: https://tu-app.railway.app/docs

## 🔧 Variables de Entorno

Configurar en Railway:

```
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=tu-clave-secreta-jwt
ENVIRONMENT=production
```

## 📁 Estructura

```
├── api_colaborativa.py                 # API principal
├── frontend_colaborativo.html          # Frontend colaborativo
├── frontend_desarrollo_postgresql_v2_con_diseno_original.html  # Frontend principal
├── src/modules/                        # Módulos de procesamiento
├── requirements.txt                    # Dependencias Python
├── Procfile                           # Configuración Railway
└── railway.json                       # Configuración Railway
```

## 🚀 Deployment en Railway

1. **Conectar repositorio** a Railway
2. **Configurar variables** de entorno
3. **Railway automáticamente**:
   - Instala dependencias
   - Configura PostgreSQL
   - Despliega la aplicación

## 📱 Funcionalidades

### Sistema Principal
- Búsqueda y filtros avanzados
- Visualización de propiedades
- Paginación optimizada (60 por página)
- Imágenes de alta calidad

### Sistema Colaborativo
- Registro y login de usuarios
- Gestión de favoritos
- Contactos por propiedad
- Panel de administración

## 🔒 Seguridad

- Autenticación JWT
- Validación de datos con Pydantic
- Sanitización de consultas SQL
- Variables de entorno seguras

## 📈 Rendimiento

- **API**: 5-40ms por consulta
- **Base de datos**: PostgreSQL optimizada
- **Frontend**: Carga asíncrona
- **Imágenes**: Optimizadas y comprimidas

---

**Desarrollado por Pablo Ravel** - Sistema Inmobiliario Morelos 2025 
# Railway deployment fix - Wed Jun 19 2025
