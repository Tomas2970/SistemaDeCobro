-- =====================================
-- DATOS DE PRUEBA COMPLETOS
-- Sistema de Cobro - Supermercado Don Atilio
-- =====================================

USE supermercado_don_atilio;

-- Limpiar datos existentes (opcional - comentar si no quieres borrar)
-- SET FOREIGN_KEY_CHECKS = 0;
-- TRUNCATE TABLE DetalleVenta;
-- TRUNCATE TABLE Venta;
-- TRUNCATE TABLE DetalleCompra;
-- TRUNCATE TABLE Compra;
-- TRUNCATE TABLE Pago;
-- TRUNCATE TABLE AuditoriaInventario;
-- TRUNCATE TABLE Inventario;
-- TRUNCATE TABLE Producto;
-- TRUNCATE TABLE CuentaCorriente;
-- TRUNCATE TABLE Cliente;
-- TRUNCATE TABLE Proveedor;
-- TRUNCATE TABLE Usuario;
-- SET FOREIGN_KEY_CHECKS = 1;

-- =====================================
-- USUARIOS (contraseña: admin123 para todos)
-- =====================================
-- Hash bcrypt de 'admin123': $2b$12$LQv3c1yqBqR...
-- NOTA: Estos usuarios deben crearse con la función Python insertar_usuario()
-- porque las contraseñas deben hashearse con bcrypt

-- Insertar usuarios manualmente si ya tienes el hash
-- O mejor, usar el script crear_usuarios.py que generaremos después

-- =====================================
-- CLIENTES
-- =====================================
INSERT INTO Cliente (nombre, direccion, telefono, email) VALUES
('Juan Pérez', 'Av. San Martín 123', '3815551234', 'juan.perez@email.com'),
('María González', 'Calle Belgrano 456', '3815555678', 'maria.gonzalez@email.com'),
('Carlos Rodríguez', 'Pasaje Los Alamos 789', '3815559012', 'carlos.rodriguez@email.com'),
('Ana Martínez', 'Av. Mate de Luna 321', '3815553456', 'ana.martinez@email.com'),
('Pedro Sánchez', 'Calle 25 de Mayo 654', '3815557890', 'pedro.sanchez@email.com'),
('Laura Fernández', 'Barrio Los Pocitos 987', '3815552345', NULL),
('Roberto Díaz', 'Villa Urquiza 147', '3815556789', 'roberto.diaz@email.com'),
('Silvia Castro', 'Av. Aconquija 258', '3815550123', NULL),
('Jorge López', 'Calle Junín 369', '3815554567', 'jorge.lopez@email.com'),
('Claudia Romero', 'Barrio Jardín 741', '3815558901', 'claudia.romero@email.com');

-- =====================================
-- CUENTAS CORRIENTES
-- =====================================
INSERT INTO CuentaCorriente (id_cliente, saldo, limite_credito) VALUES
(1, 0, 50000),      -- Juan Pérez
(3, -15000, 30000), -- Carlos Rodríguez (debe $15,000)
(5, -8000, 20000),  -- Pedro Sánchez (debe $8,000)
(7, 0, 40000),      -- Roberto Díaz
(9, -5000, 25000);  -- Jorge López (debe $5,000)

-- =====================================
-- PRODUCTOS
-- =====================================
-- Bebidas
INSERT INTO Producto (nombre, descripcion, precio, codigo_barras, id_categoria) VALUES
('Coca Cola 2.25L', 'Gaseosa sabor cola', 1500.00, '7790001234567', 1),
('Sprite 2.25L', 'Gaseosa sabor lima-limón', 1450.00, '7790001234574', 1),
('Fanta 2.25L', 'Gaseosa sabor naranja', 1450.00, '7790001234581', 1),
('Agua Mineral 2L', 'Agua sin gas', 800.00, '7790001234598', 1),
('Cerveza Quilmes 1L', 'Cerveza rubia', 2200.00, '7790001234604', 1),
('Jugo Baggio 1L', 'Jugo de naranja', 950.00, '7790001234611', 1),

-- Almacén
('Yerba Mate La Merced 1kg', 'Yerba con palo', 3500.00, '7790002234567', 2),
('Azúcar Ledesma 1kg', 'Azúcar blanca', 1200.00, '7790002234574', 2),
('Arroz Gallo 1kg', 'Arroz largo fino', 1400.00, '7790002234581', 2),
('Fideos Matarazzo 500g', 'Fideos secos', 850.00, '7790002234598', 2),
('Aceite Cocinero 900ml', 'Aceite de girasol', 1800.00, '7790002234604', 2),
('Sal Celusal 500g', 'Sal fina', 600.00, '7790002234611', 2),
('Café La Virginia 250g', 'Café molido', 2800.00, '7790002234628', 2),
('Galletitas Oreo 118g', 'Galletitas de chocolate', 1350.00, '7790002234635', 2),

-- Lácteos
('Leche La Serenísima 1L', 'Leche entera', 950.00, '7790003234567', 3),
('Queso Cremoso 500g', 'Queso untable', 2200.00, '7790003234574', 3),
('Yogur Sancor 190g', 'Yogur frutilla', 680.00, '7790003234581', 3),
('Manteca La Serenísima 200g', 'Manteca con sal', 1450.00, '7790003234598', 3),

-- Carnes
('Carne Molida 1kg', 'Carne vacuna', 5500.00, '7790004234567', 4),
('Pollo Entero 1kg', 'Pollo fresco', 3200.00, '7790004234574', 4),
('Salchichas Vienna 500g', 'Salchichas de cerdo', 2400.00, '7790004234581', 4),

-- Limpieza
('Detergente Magistral 500ml', 'Limón', 1200.00, '7790005234567', 5),
('Lavandina Ayudín 1L', 'Clásica', 950.00, '7790005234574', 5),
('Jabón en Polvo Skip 800g', 'Para ropa', 2800.00, '7790005234581', 5),
('Papel Higiénico Elite x4', 'Doble hoja', 1650.00, '7790005234598', 5),

-- Panadería
('Pan Francés unidad', 'Pan blanco', 450.00, '7790006234567', 6),
('Facturas x6', 'Medialunas y vigilantes', 2200.00, '7790006234574', 6),
('Pan de Molde Bimbo', 'Pan lactal', 1850.00, '7790006234581', 6);

-- =====================================
-- INVENTARIO
-- =====================================
INSERT INTO Inventario (id_producto, cantidad, stock_minimo, stock_maximo) VALUES
-- Bebidas
(1, 45, 10, 100),   -- Coca Cola
(2, 38, 10, 100),   -- Sprite
(3, 42, 10, 100),   -- Fanta
(4, 60, 15, 150),   -- Agua
(5, 25, 8, 80),     -- Cerveza
(6, 30, 10, 100),   -- Jugo

-- Almacén
(7, 8, 15, 80),     -- Yerba (STOCK BAJO!)
(8, 55, 20, 120),   -- Azúcar
(9, 48, 20, 120),   -- Arroz
(10, 75, 30, 150),  -- Fideos
(11, 32, 12, 80),   -- Aceite
(12, 90, 40, 200),  -- Sal
(13, 15, 10, 60),   -- Café
(14, 6, 15, 100),   -- Galletitas (STOCK BAJO!)

-- Lácteos
(15, 80, 30, 150),  -- Leche
(16, 22, 10, 60),   -- Queso
(17, 45, 20, 120),  -- Yogur
(18, 28, 12, 80),   -- Manteca

-- Carnes
(19, 12, 8, 50),    -- Carne Molida
(20, 18, 10, 60),   -- Pollo
(21, 25, 15, 80),   -- Salchichas

-- Limpieza
(22, 40, 15, 100),  -- Detergente
(23, 55, 20, 120),  -- Lavandina
(24, 18, 10, 80),   -- Jabón
(25, 5, 20, 100),   -- Papel Higiénico (STOCK BAJO!)

-- Panadería
(26, 120, 50, 200), -- Pan Francés
(27, 35, 15, 100),  -- Facturas
(28, 28, 12, 80);   -- Pan de Molde

-- =====================================
-- PROVEEDORES
-- =====================================
INSERT INTO Proveedor (nombre, direccion, telefono, email, contacto) VALUES
('Distribuidora Norte', 'Parque Industrial', '3814441234', 'ventas@disnorte.com', 'Roberto Gómez'),
('Mayorista Central', 'Av. Circunvalación 1500', '3814445678', 'pedidos@mayorista.com', 'Laura Martínez'),
('Frigorífico San Miguel', 'Ruta 9 Km 8', '3814449012', 'contacto@frigosm.com', 'Carlos Ruiz'),
('Lácteos del Valle', 'Tafí Viejo', '3814443456', 'info@lacvalle.com', 'Ana Torres');

-- =====================================
-- COMPRAS
-- =====================================
INSERT INTO Compra (id_proveedor, id_usuario, fecha, numero_factura, estado) VALUES
(1, 1, '2025-10-01 09:00:00', 'A-0001-00012345', 'recibida'),
(2, 1, '2025-10-05 10:30:00', 'B-0002-00067890', 'recibida'),
(3, 1, '2025-10-08 14:00:00', 'A-0003-00023456', 'recibida');

-- Detalles de compras
INSERT INTO DetalleCompra (id_compra, id_producto, cantidad, precio_unitario) VALUES
-- Compra 1: Bebidas
(1, 1, 50, 1200.00),  -- Coca Cola
(1, 2, 40, 1150.00),  -- Sprite
(1, 3, 45, 1150.00),  -- Fanta
(1, 4, 60, 600.00),   -- Agua

-- Compra 2: Almacén
(2, 7, 30, 2800.00),  -- Yerba
(2, 8, 60, 950.00),   -- Azúcar
(2, 9, 50, 1100.00),  -- Arroz
(2, 11, 40, 1400.00), -- Aceite

-- Compra 3: Carnes
(3, 19, 20, 4500.00), -- Carne Molida
(3, 20, 25, 2600.00), -- Pollo
(3, 21, 30, 1900.00); -- Salchichas

-- =====================================
-- VENTAS
-- =====================================
-- Nota: Los usuarios deben ser creados primero con Python
-- Asumiendo que el admin tiene id_usuario = 1

-- Venta 1: Cliente 1 (efectivo)
INSERT INTO Venta (id_usuario, id_cliente, fecha, tipo_pago, estado) 
VALUES (1, 1, '2025-10-10 10:15:00', 'efectivo', 'completada');

INSERT INTO DetalleVenta (id_venta, id_producto, cantidad, precio_unitario) VALUES
(1, 1, 2, 1500.00),  -- Coca Cola x2
(1, 7, 1, 3500.00),  -- Yerba x1
(1, 15, 3, 950.00);  -- Leche x3

-- Venta 2: Cliente 2 (tarjeta)
INSERT INTO Venta (id_usuario, id_cliente, fecha, tipo_pago, estado) 
VALUES (1, 2, '2025-10-10 11:30:00', 'tarjeta', 'completada');

INSERT INTO DetalleVenta (id_venta, id_producto, cantidad, precio_unitario) VALUES
(2, 19, 2, 5500.00),  -- Carne x2
(2, 26, 5, 450.00),   -- Pan x5
(2, 4, 2, 800.00);    -- Agua x2

-- Venta 3: Cliente 3 (cuenta corriente - generará deuda)
INSERT INTO Venta (id_usuario, id_cliente, fecha, tipo_pago, estado) 
VALUES (1, 3, '2025-10-11 09:00:00', 'cuenta_corriente', 'completada');

INSERT INTO DetalleVenta (id_venta, id_producto, cantidad, precio_unitario) VALUES
(3, 7, 2, 3500.00),   -- Yerba x2
(3, 8, 2, 1200.00),   -- Azúcar x2
(3, 11, 1, 1800.00),  -- Aceite x1
(3, 22, 2, 1200.00);  -- Detergente x2

-- Venta 4: Cliente 4 (efectivo)
INSERT INTO Venta (id_usuario, id_cliente, fecha, tipo_pago, estado) 
VALUES (1, 4, '2025-10-11 15:45:00', 'efectivo', 'completada');

INSERT INTO DetalleVenta (id_venta, id_producto, cantidad, precio_unitario) VALUES
(4, 5, 4, 2200.00),   -- Cerveza x4
(4, 14, 3, 1350.00),  -- Galletitas x3
(4, 27, 1, 2200.00);  -- Facturas x1

-- Venta 5: Cliente 5 (cuenta corriente)
INSERT INTO Venta (id_usuario, id_cliente, fecha, tipo_pago, estado) 
VALUES (1, 5, '2025-10-12 12:00:00', 'cuenta_corriente', 'completada');

INSERT INTO DetalleVenta (id_venta, id_producto, cantidad, precio_unitario) VALUES
(5, 1, 3, 1500.00),   -- Coca Cola x3
(5, 26, 10, 450.00),  -- Pan x10
(5, 15, 4, 950.00);   -- Leche x4

-- =====================================
-- PAGOS
-- =====================================
-- Pago parcial de Carlos Rodríguez
INSERT INTO Pago (id_cuenta, monto, metodo, referencia, id_usuario) VALUES
(2, 5000.00, 'efectivo', NULL, 1);

-- Pago total de Pedro Sánchez
INSERT INTO Pago (id_cuenta, monto, metodo, referencia, id_usuario) VALUES
(3, 8000.00, 'transferencia', 'TRANS20251012001', 1);

-- Pago parcial de Jorge López
INSERT INTO Pago (id_cuenta, monto, metodo, referencia, id_usuario) VALUES
(5, 2500.00, 'efectivo', NULL, 1);

-- =====================================
-- RESUMEN DE DATOS INSERTADOS
-- =====================================
SELECT 'Datos de prueba insertados correctamente' as mensaje;

SELECT 
    (SELECT COUNT(*) FROM Cliente) as clientes,
    (SELECT COUNT(*) FROM Producto) as productos,
    (SELECT COUNT(*) FROM Inventario) as items_inventario,
    (SELECT COUNT(*) FROM Venta) as ventas,
    (SELECT COUNT(*) FROM DetalleVenta) as detalles_venta,
    (SELECT COUNT(*) FROM Proveedor) as proveedores,
    (SELECT COUNT(*) FROM Compra) as compras,
    (SELECT COUNT(*) FROM CuentaCorriente) as cuentas_corrientes,
    (SELECT COUNT(*) FROM Pago) as pagos;

-- =====================================
-- VERIFICACIONES
-- =====================================
-- Productos con stock bajo
SELECT 'PRODUCTOS CON STOCK BAJO:' as alerta;
SELECT * FROM vista_stock_bajo;

-- Clientes con deuda
SELECT 'CLIENTES CON DEUDA:' as alerta;
SELECT * FROM vista_clientes_deuda;

-- Ventas del día
SELECT 'VENTAS RECIENTES:' as info;
SELECT * FROM vista_ventas_diarias LIMIT 5;