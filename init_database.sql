-- Script de inicialización de base de datos para Render
-- Ejecutar después de crear la base de datos PostgreSQL

-- Tabla de propiedades principal
CREATE TABLE IF NOT EXISTS propiedades (
    id VARCHAR(255) PRIMARY KEY,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    precio DECIMAL(15,2),
    ciudad VARCHAR(100),
    tipo_operacion VARCHAR(50),
    tipo_propiedad VARCHAR(100),
    direccion TEXT,
    estado VARCHAR(100),
    link TEXT,
    imagen TEXT,
    recamaras INTEGER,
    banos INTEGER,
    estacionamientos INTEGER,
    superficie_m2 INTEGER,
    amenidades JSONB,
    caracteristicas JSONB,
    imagenes JSONB,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    es_admin BOOLEAN DEFAULT false,
    activo BOOLEAN DEFAULT true,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de favoritos
CREATE TABLE IF NOT EXISTS favoritos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    propiedad_id VARCHAR(255) REFERENCES propiedades(id) ON DELETE CASCADE,
    fecha_agregado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usuario_id, propiedad_id)
);

-- Índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_propiedades_ciudad ON propiedades(ciudad);
CREATE INDEX IF NOT EXISTS idx_propiedades_tipo_operacion ON propiedades(tipo_operacion);
CREATE INDEX IF NOT EXISTS idx_propiedades_precio ON propiedades(precio);
CREATE INDEX IF NOT EXISTS idx_propiedades_activo ON propiedades(activo);

-- Crear usuario administrador por defecto
INSERT INTO usuarios (nombre, email, telefono, password_hash, es_admin, activo)
VALUES (
    'Administrador',
    'admin@propiedades.com',
    '777-123-4567',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeOjQOBaOjDQOVpim',
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- Datos de prueba
INSERT INTO propiedades (id, titulo, descripcion, precio, ciudad, tipo_operacion, tipo_propiedad, activo)
VALUES 
('test-1', 'Casa en Cuernavaca', 'Hermosa casa con jardín', 2500000, 'Cuernavaca', 'Venta', 'Casa', true),
('test-2', 'Departamento en Jiutepec', 'Depto moderno céntrico', 1800000, 'Jiutepec', 'Venta', 'Departamento', true),
('test-3', 'Casa en renta Temixco', 'Casa amueblada', 15000, 'Temixco', 'Renta', 'Casa', true)
ON CONFLICT (id) DO NOTHING;

SELECT 'Base de datos inicializada correctamente' as status;
