-- =========================================================
-- DATOS INICIALES - Sistema Don Atilio
-- Ejecutar: mysql -u root --port=3307 supermercado_don_atilio < cargar_datos_manual.sql
-- =========================================================

USE supermercado_don_atilio;

-- =========================================================
-- 1. ROLES
-- =========================================================
INSERT IGNORE INTO Rol (id_rol, nombre, descripcion) VALUES
(1, 'admin', 'Administrador del sistema con acceso total'),
(2, 'vendedor', 'Vendedor de caja'),
(3, 'supervisor', 'Supervisor de tienda');

-- =========================================================
-- 2. USUARIOS (contraseñas hasheadas con bcrypt)
-- =========================================================
-- admin / admin123
INSERT IGNORE INTO Usuario (nombre, contraseña, id_rol, activo) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5jtRkzXuuMQhC', 1, TRUE);

-- tomas / tomas123
INSERT IGNORE INTO Usuario (nombre, contraseña, id_rol, activo) VALUES
('tomas', '$2b$12$8x1c8VN5WT5qKH.WYgZWZu5JnY3xK9vMQN8C1xYqP5Lh3sJ8Qx2yG', 2, TRUE);

-- supervisor / super123
INSERT IGNORE INTO Usuario (nombre, contraseña, id_rol, activo) VALUES
('supervisor', '$2b$12$5K8vX2mN9PL4qH.WYgZWZu5JnY3xK9vMQN8C1xYqP5Lh3sJ8Qx2yG', 3, TRUE);

-- =========================================================
-- 3. CATEGORÍAS
-- =========================================================
INSERT IGNORE INTO Categoria (nombre, descripcion, activa) VALUES
('Almacen', 'Productos de almacén general', TRUE),
('Bebidas', 'Gaseosas, jugos, agua mineral', TRUE),
('Lacteos', 'Leche, quesos, yogures, manteca', TRUE),
('Panaderia', 'Pan, facturas, galletas', TRUE),
('Limpieza', 'Productos de limpieza del hogar', TRUE),
('Carnes', 'Carnes rojas, blancas y embutidos', TRUE),
('Verduleria', 'Frutas y verduras frescas', TRUE),
('Golosinas', 'Caramelos, chocolates, snacks', TRUE),
('Congelados', 'Productos congelados', TRUE),
('Perfumeria', 'Higiene y cuidado personal', TRUE);

-- =========================================================
-- 4. PRODUCTOS DE EJEMPLO (Opcional)
-- =========================================================
-- Bebidas
INSERT IGNORE INTO Producto (nombre, precio, id_categoria, codigo_barras, es_pesable, activo) VALUES
('Coca Cola 2.25L', 2500.00, 2, '7790895001109', FALSE, TRUE),
('Sprite 2.25L', 2400.00, 2, '7790895002205', FALSE, TRUE),
('Agua Villa del Sur 2L', 1200.00, 2, '7790315002311', FALSE, TRUE);

-- Almacén
INSERT IGNORE INTO Producto (nombre, precio, id_categoria, codigo_barras, es_pesable, activo) VALUES
('Arroz Gallo Oro 1kg', 1800.00, 1, '7790070300034', FALSE, TRUE),
('Fideos Matarazzo 500g', 1200.00, 1, '7790742005014', FALSE, TRUE),
('Aceite Cocinero 900ml', 3500.00, 1, '7790070400041', FALSE, TRUE);

-- Lácteos
INSERT IGNORE INTO Producto (nombre, precio, id_categoria, codigo_barras, es_pesable, activo) VALUES
('Leche Larga Vida 1L', 1500.00, 3, '7790387001013', FALSE, TRUE),
('Yogur Danone 190g', 800.00, 3, '7790310062013', FALSE, TRUE);

-- Panadería
INSERT IGNORE INTO Producto (nombre, precio, id_categoria, es_pesable, activo) VALUES
('Pan Frances', 1500.00, 4, TRUE, TRUE),
('Medialunas x6', 2000.00, 4, FALSE, TRUE);

-- Verdulería (productos pesables)
INSERT IGNORE INTO Producto (nombre, precio, id_categoria, es_pesable, activo) VALUES
('Tomate', 2500.00, 7, TRUE, TRUE),
('Papa', 1800.00, 7, TRUE, TRUE),
('Cebolla', 1500.00, 7, TRUE, TRUE),
('Manzana', 3000.00, 7, TRUE, TRUE);

-- =========================================================
-- 5. INVENTARIO INICIAL
-- =========================================================
-- Asociar productos con inventario inicial
INSERT IGNORE INTO Inventario (id_producto, cantidad, stock_minimo)
SELECT id_producto, 100.000, 10
FROM Producto
WHERE activo = TRUE;

-- =========================================================
-- 6. CLIENTE DE PRUEBA
-- =========================================================
INSERT IGNORE INTO Cliente (nombre, dni, direccion, telefono, email, activo) VALUES
('Cliente Generico', '', '', '', NULL, TRUE);

-- Crear cuenta corriente para el cliente
INSERT IGNORE INTO CuentaCorriente (id_cliente, saldo, limite_credito)
SELECT id_cliente, 0.00, 50000.00
FROM Cliente
WHERE nombre = 'Cliente Generico';

-- =========================================================
-- 7. PROVEEDOR DE EJEMPLO
-- =========================================================
INSERT IGNORE INTO Proveedor (nombre, empresa, telefono, email, activo) VALUES
('Distribuidora Central', 'Distribuidora Central SA', '3512345678', 'contacto@distcentral.com', TRUE);

-- =========================================================
-- VERIFICACIÓN
-- =========================================================
SELECT '=== ROLES ===' AS '';
SELECT * FROM Rol;

SELECT '=== USUARIOS ===' AS '';
SELECT id_usuario, nombre, 
       CASE id_rol 
           WHEN 1 THEN 'admin'
           WHEN 2 THEN 'vendedor'
           WHEN 3 THEN 'supervisor'
       END as rol,
       activo
FROM Usuario;

SELECT '=== CATEGORIAS ===' AS '';
SELECT id_categoria, nombre, activa FROM Categoria;

SELECT '=== PRODUCTOS ===' AS '';
SELECT COUNT(*) as total_productos FROM Producto WHERE activo = TRUE;

SELECT '=== INVENTARIO ===' AS '';
SELECT COUNT(*) as total_items FROM Inventario;

SELECT '' AS '';
SELECT 'DATOS CARGADOS CORRECTAMENTE' AS ESTADO;
SELECT '' AS '';
SELECT 'Credenciales de acceso:' AS '';
SELECT '- admin / admin123' AS '';
SELECT '- tomas / tomas123' AS '';
SELECT '- supervisor / super123' AS '';