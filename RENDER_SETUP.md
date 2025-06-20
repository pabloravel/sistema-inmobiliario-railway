# 🚀 Configuración PostgreSQL en Render

## 📋 PROBLEMA ACTUAL
Tu aplicación funciona pero `/propiedades` falla porque **NO TIENE BASE DE DATOS**.

- ✅ App: https://sistema-inmobiliario-railway.onrender.com
- ✅ Salud: https://sistema-inmobiliario-railway.onrender.com/salud  
- ❌ Propiedades: https://sistema-inmobiliario-railway.onrender.com/propiedades

## 🔧 SOLUCIÓN RÁPIDA

### 1. Crear PostgreSQL en Render
1. Dashboard → "New +" → "PostgreSQL"
2. Name: `propiedades-db`
3. Plan: Free
4. Create Database

### 2. Agregar DATABASE_URL
1. Ve a tu Web Service
2. Settings → Environment Variables
3. Agregar: `DATABASE_URL` = (la URL que te dio Render)

### 3. Inicializar BD
1. PostgreSQL service → Connect → PSQL
2. Ejecutar contenido de `init_database.sql`

### 4. ¡Listo!
Tu API funcionará completamente con datos de prueba.

## 🔑 CREDENCIALES
- Email: admin@propiedades.com  
- Password: admin123
