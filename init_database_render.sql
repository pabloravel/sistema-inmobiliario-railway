-- SCRIPT DE INICIALIZACIÓN COMPLETA PARA RENDER
-- Crear todas las tablas necesarias

-- 1. Tabla de propiedades
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
    superficie_construida INTEGER,
    superficie_terreno INTEGER,
    amenidades JSONB,
    caracteristicas JSONB,
    imagenes JSONB,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    es_admin BOOLEAN DEFAULT false,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT true
);

-- 3. Tabla de favoritos
CREATE TABLE IF NOT EXISTS favoritos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    propiedad_id VARCHAR(255) REFERENCES propiedades(id) ON DELETE CASCADE,
    fecha_agregado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usuario_id, propiedad_id)
);

-- 4. Crear usuario administrador por defecto
INSERT INTO usuarios (nombre, email, telefono, password_hash, es_admin, activo) 
VALUES (
    'Administrador',
    'admin@propiedades.com',
    '7771234567',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3L.dHxWJKm', -- password: admin123
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- 5. Insertar propiedades de ejemplo
INSERT INTO propiedades (id, titulo, descripcion, precio, ciudad, tipo_operacion, tipo_propiedad, direccion, estado, imagen, recamaras, banos, estacionamientos, superficie_construida, activo) VALUES
('prop-001', 'Casa en Cuernavaca Centro', 'Hermosa casa colonial en el corazón de Cuernavaca', 2500000.00, 'Cuernavaca', 'Venta', 'Casa', 'Centro de Cuernavaca', 'Morelos', 'casa-cuernavaca-001.jpg', 3, 2, 2, 180, true),
('prop-002', 'Departamento en Temixco', 'Moderno departamento con vista panorámica', 1800000.00, 'Temixco', 'Venta', 'Departamento', 'Temixco Norte', 'Morelos', 'depto-temixco-001.jpg', 2, 2, 1, 120, true),
('prop-003', 'Casa en Jiutepec', 'Casa familiar con jardín y alberca', 3200000.00, 'Jiutepec', 'Venta', 'Casa', 'Jiutepec Centro', 'Morelos', 'casa-jiutepec-001.jpg', 4, 3, 2, 250, true),
('prop-004', 'Terreno en Tepoztlán', 'Terreno con vista a los cerros', 800000.00, 'Tepoztlán', 'Venta', 'Terreno', 'Tepoztlán', 'Morelos', 'terreno-tepoztlan-001.jpg', 0, 0, 0, 500, true),
('prop-005', 'Casa en Yautepec', 'Casa de una planta con patio amplio', 1500000.00, 'Yautepec', 'Venta', 'Casa', 'Yautepec Centro', 'Morelos', 'casa-yautepec-001.jpg', 3, 2, 1, 150, true);

-- 6. Crear índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_propiedades_ciudad ON propiedades(ciudad);
CREATE INDEX IF NOT EXISTS idx_propiedades_tipo_operacion ON propiedades(tipo_operacion);
CREATE INDEX IF NOT EXISTS idx_propiedades_precio ON propiedades(precio);
CREATE INDEX IF NOT EXISTS idx_propiedades_activo ON propiedades(activo);

-- 7. Verificar que todo se creó correctamente
SELECT 'Tablas creadas exitosamente' as status;
SELECT COUNT(*) as total_propiedades FROM propiedades;
SELECT COUNT(*) as total_usuarios FROM usuarios;
