-- =====================================
-- CREACIÓN DE BASE DE DATOS
-- =====================================
CREATE DATABASE IF NOT EXISTS supermercado_don_atilio 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE supermercado_don_atilio;

-- =====================================
-- TABLAS DE SEGURIDAD
-- =====================================
CREATE TABLE Rol (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(200),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE Usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    contraseña VARCHAR(255) NOT NULL,  -- Aumentado para bcrypt hash
    id_rol INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,  -- Para soft delete
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP NULL,
    FOREIGN KEY (id_rol) REFERENCES Rol(id_rol) ON UPDATE CASCADE,
    INDEX idx_usuario_nombre (nombre),
    INDEX idx_usuario_activo (activo)
) ENGINE=InnoDB;

-- =====================================
-- TABLAS DE CLIENTES Y CUENTA CORRIENTE
-- =====================================
CREATE TABLE Cliente (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(200),
    telefono VARCHAR(20),
    email VARCHAR(255) UNIQUE,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (email IS NULL OR email LIKE '%@%.%'),  -- Validación básica de email
    INDEX idx_cliente_nombre (nombre),
    INDEX idx_cliente_email (email),
    INDEX idx_cliente_activo (activo)
) ENGINE=InnoDB;

CREATE TABLE CuentaCorriente (
    id_cuenta INT AUTO_INCREMENT PRIMARY KEY,
    saldo DECIMAL(10,2) DEFAULT 0.00,
    limite_credito DECIMAL(10,2) DEFAULT 0.00,
    id_cliente INT UNIQUE NOT NULL,
    fecha_apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CHECK (saldo >= -limite_credito),  -- El saldo no puede exceder el límite de crédito negativo
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente) ON DELETE CASCADE,
    INDEX idx_cuenta_saldo (saldo)
) ENGINE=InnoDB;

CREATE TABLE Pago (
    id_pago INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    monto DECIMAL(10,2) NOT NULL,
    metodo VARCHAR(50) NOT NULL,
    referencia VARCHAR(100),  -- Número de referencia/transacción
    id_cuenta INT NOT NULL,
    id_usuario INT,  -- Usuario que registró el pago
    CHECK (monto > 0),
    CHECK (metodo IN ('efectivo', 'tarjeta_debito', 'tarjeta_credito', 'transferencia', 'cheque')),
    FOREIGN KEY (id_cuenta) REFERENCES CuentaCorriente(id_cuenta) ON DELETE RESTRICT,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE SET NULL,
    INDEX idx_pago_fecha (fecha),
    INDEX idx_pago_cuenta (id_cuenta)
) ENGINE=InnoDB;

-- =====================================
-- TABLAS DE PRODUCTOS E INVENTARIO
-- =====================================
CREATE TABLE Categoria (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(200),
    activa BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_categoria_nombre (nombre),
    INDEX idx_categoria_activa (activa)
) ENGINE=InnoDB;

CREATE TABLE Producto (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) NOT NULL,
    codigo_barras VARCHAR(50) UNIQUE,
    id_categoria INT,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (precio > 0),
    FOREIGN KEY (id_categoria) REFERENCES Categoria(id_categoria) ON UPDATE CASCADE,
    INDEX idx_producto_nombre (nombre),
    INDEX idx_producto_codigo (codigo_barras),
    INDEX idx_producto_categoria (id_categoria),
    INDEX idx_producto_activo (activo)
) ENGINE=InnoDB;

CREATE TABLE Inventario (
    id_inventario INT AUTO_INCREMENT PRIMARY KEY,
    cantidad INT NOT NULL DEFAULT 0,
    stock_minimo INT NOT NULL DEFAULT 5,
    stock_maximo INT DEFAULT 100,
    id_producto INT UNIQUE NOT NULL,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CHECK (cantidad >= 0),
    CHECK (stock_minimo >= 0),
    CHECK (stock_maximo > stock_minimo),
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto) ON DELETE CASCADE,
    INDEX idx_inventario_cantidad (cantidad),
    INDEX idx_inventario_alerta (cantidad, stock_minimo)
) ENGINE=InnoDB;

-- =====================================
-- TABLAS DE PROVEEDORES Y COMPRAS
-- =====================================
CREATE TABLE Proveedor (
    id_proveedor INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(200),
    telefono VARCHAR(20),
    email VARCHAR(255) UNIQUE,
    contacto VARCHAR(100),
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (email IS NULL OR email LIKE '%@%.%'),
    INDEX idx_proveedor_nombre (nombre),
    INDEX idx_proveedor_activo (activo)
) ENGINE=InnoDB;

CREATE TABLE Compra (
    id_compra INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(10,2) DEFAULT 0.00,  -- Calculado con trigger
    id_usuario INT,
    id_proveedor INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'pendiente',
    numero_factura VARCHAR(50),
    CHECK (total >= 0),
    CHECK (estado IN ('pendiente', 'recibida', 'cancelada')),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE SET NULL,
    FOREIGN KEY (id_proveedor) REFERENCES Proveedor(id_proveedor) ON DELETE RESTRICT,
    INDEX idx_compra_fecha (fecha),
    INDEX idx_compra_proveedor (id_proveedor),
    INDEX idx_compra_estado (estado)
) ENGINE=InnoDB;

CREATE TABLE DetalleCompra (
    id_detalle_compra INT AUTO_INCREMENT PRIMARY KEY,
    id_compra INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,
    CHECK (cantidad > 0),
    CHECK (precio_unitario > 0),
    FOREIGN KEY (id_compra) REFERENCES Compra(id_compra) ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto) ON DELETE RESTRICT,
    INDEX idx_detalle_compra_compra (id_compra),
    INDEX idx_detalle_compra_producto (id_producto)
) ENGINE=InnoDB;

-- =====================================
-- TABLAS DE VENTAS
-- =====================================
CREATE TABLE Venta (
    id_venta INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(10,2) DEFAULT 0.00,  -- Calculado con trigger
    id_usuario INT,
    id_cliente INT,
    estado VARCHAR(20) DEFAULT 'completada',
    tipo_pago VARCHAR(20) DEFAULT 'efectivo',
    CHECK (total >= 0),
    CHECK (estado IN ('completada', 'cancelada', 'pendiente')),
    CHECK (tipo_pago IN ('efectivo', 'tarjeta', 'cuenta_corriente', 'transferencia')),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE SET NULL,
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente) ON DELETE RESTRICT,
    INDEX idx_venta_fecha (fecha),
    INDEX idx_venta_cliente (id_cliente),
    INDEX idx_venta_usuario (id_usuario),
    INDEX idx_venta_estado (estado)
) ENGINE=InnoDB;

CREATE TABLE DetalleVenta (
    id_detalle_venta INT AUTO_INCREMENT PRIMARY KEY,
    id_venta INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,
    CHECK (cantidad > 0),
    CHECK (precio_unitario > 0),
    FOREIGN KEY (id_venta) REFERENCES Venta(id_venta) ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto) ON DELETE RESTRICT,
    INDEX idx_detalle_venta_venta (id_venta),
    INDEX idx_detalle_venta_producto (id_producto)
) ENGINE=InnoDB;

-- =====================================
-- TABLA DE AUDITORÍA (OPCIONAL)
-- =====================================
CREATE TABLE AuditoriaInventario (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    id_producto INT NOT NULL,
    cantidad_anterior INT NOT NULL,
    cantidad_nueva INT NOT NULL,
    tipo_movimiento VARCHAR(50) NOT NULL,  -- 'venta', 'compra', 'ajuste', 'devolución'
    id_referencia INT,  -- ID de la venta/compra relacionada
    id_usuario INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observaciones TEXT,
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE SET NULL,
    INDEX idx_auditoria_producto (id_producto),
    INDEX idx_auditoria_fecha (fecha),
    INDEX idx_auditoria_tipo (tipo_movimiento)
) ENGINE=InnoDB;

-- =====================================
-- TRIGGERS
-- =====================================

-- Trigger para actualizar total de venta
DELIMITER $$
CREATE TRIGGER actualizar_total_venta
AFTER INSERT ON DetalleVenta
FOR EACH ROW
BEGIN
    UPDATE Venta 
    SET total = (
        SELECT SUM(subtotal) 
        FROM DetalleVenta 
        WHERE id_venta = NEW.id_venta
    )
    WHERE id_venta = NEW.id_venta;
END$$

-- Trigger para actualizar total de compra
CREATE TRIGGER actualizar_total_compra
AFTER INSERT ON DetalleCompra
FOR EACH ROW
BEGIN
    UPDATE Compra 
    SET total = (
        SELECT SUM(subtotal) 
        FROM DetalleCompra 
        WHERE id_compra = NEW.id_compra
    )
    WHERE id_compra = NEW.id_compra;
END$$

-- Trigger para auditoría de inventario en ventas
CREATE TRIGGER auditoria_venta_inventario
AFTER INSERT ON DetalleVenta
FOR EACH ROW
BEGIN
    DECLARE cantidad_anterior INT;
    
    SELECT cantidad INTO cantidad_anterior 
    FROM Inventario 
    WHERE id_producto = NEW.id_producto;
    
    INSERT INTO AuditoriaInventario 
    (id_producto, cantidad_anterior, cantidad_nueva, tipo_movimiento, id_referencia)
    VALUES 
    (NEW.id_producto, cantidad_anterior, cantidad_anterior - NEW.cantidad, 'venta', NEW.id_venta);
END$$

-- Trigger para actualizar cuenta corriente automáticamente
CREATE TRIGGER actualizar_cuenta_corriente_venta
AFTER UPDATE ON Venta
FOR EACH ROW
BEGIN
    -- Solo si es venta a cuenta corriente y tiene cliente
    IF NEW.tipo_pago = 'cuenta_corriente' AND NEW.id_cliente IS NOT NULL THEN
        -- Si el total cambió, ajustar la diferencia
        IF NEW.total != OLD.total THEN
            UPDATE CuentaCorriente 
            SET saldo = saldo - (NEW.total - OLD.total)
            WHERE id_cliente = NEW.id_cliente;
        END IF;
    END IF;
END$$

DELIMITER ;

-- =====================================
-- DATOS INICIALES
-- =====================================

-- Roles básicos
INSERT INTO Rol (nombre, descripcion) VALUES 
('admin', 'Administrador del sistema con todos los permisos'),
('vendedor', 'Usuario que puede realizar ventas'),
('supervisor', 'Usuario que puede gestionar inventario y ver reportes');

-- Categorías de ejemplo
INSERT INTO Categoria (nombre, descripcion) VALUES 
('Bebidas', 'Bebidas alcohólicas y no alcohólicas'),
('Almacén', 'Productos de almacén y despensa'),
('Lácteos', 'Productos lácteos y derivados'),
('Carnes', 'Carnes y embutidos'),
('Limpieza', 'Productos de limpieza e higiene'),
('Panadería', 'Productos de panadería y pastelería');

-- =====================================
-- VISTAS ÚTILES
-- =====================================

-- Vista de productos con stock bajo
CREATE VIEW vista_stock_bajo AS
SELECT 
    p.id_producto,
    p.nombre,
    p.precio,
    c.nombre as categoria,
    i.cantidad,
    i.stock_minimo,
    (i.stock_minimo - i.cantidad) as unidades_faltantes
FROM Producto p
JOIN Inventario i ON p.id_producto = i.id_producto
JOIN Categoria c ON p.id_categoria = c.id_categoria
WHERE i.cantidad <= i.stock_minimo
ORDER BY i.cantidad ASC;

-- Vista de ventas por día
CREATE VIEW vista_ventas_diarias AS
SELECT 
    DATE(v.fecha) as fecha,
    COUNT(v.id_venta) as total_ventas,
    SUM(v.total) as monto_total,
    AVG(v.total) as promedio_venta
FROM Venta v
WHERE v.estado = 'completada'
GROUP BY DATE(v.fecha)
ORDER BY fecha DESC;

-- Vista de productos más vendidos
CREATE VIEW vista_productos_mas_vendidos AS
SELECT 
    p.id_producto,
    p.nombre,
    p.precio,
    c.nombre as categoria,
    SUM(dv.cantidad) as total_vendido,
    SUM(dv.subtotal) as ingresos_generados
FROM Producto p
JOIN DetalleVenta dv ON p.id_producto = dv.id_producto
JOIN Venta v ON dv.id_venta = v.id_venta
JOIN Categoria c ON p.id_categoria = c.id_categoria
WHERE v.estado = 'completada'
GROUP BY p.id_producto
ORDER BY total_vendido DESC;

-- Vista de clientes con deuda
CREATE VIEW vista_clientes_deuda AS
SELECT 
    c.id_cliente,
    c.nombre,
    c.telefono,
    c.email,
    cc.saldo,
    cc.limite_credito,
    (cc.limite_credito + cc.saldo) as credito_disponible
FROM Cliente c
JOIN CuentaCorriente cc ON c.id_cliente = cc.id_cliente
WHERE cc.saldo < 0
ORDER BY cc.saldo ASC;

-- =====================================
-- PROCEDIMIENTOS ALMACENADOS
-- =====================================

DELIMITER $$

-- Procedimiento para crear inventario automáticamente al insertar producto
CREATE PROCEDURE crear_producto_con_inventario(
    IN p_nombre VARCHAR(100),
    IN p_precio DECIMAL(10,2),
    IN p_id_categoria INT,
    IN p_stock_inicial INT,
    IN p_stock_minimo INT
)
BEGIN
    DECLARE nuevo_id_producto INT;
    
    START TRANSACTION;
    
    -- Insertar producto
    INSERT INTO Producto (nombre, precio, id_categoria)
    VALUES (p_nombre, p_precio, p_id_categoria);
    
    SET nuevo_id_producto = LAST_INSERT_ID();
    
    -- Crear registro de inventario
    INSERT INTO Inventario (id_producto, cantidad, stock_minimo)
    VALUES (nuevo_id_producto, p_stock_inicial, p_stock_minimo);
    
    COMMIT;
    
    SELECT nuevo_id_producto as id_producto_creado;
END$

-- Procedimiento para procesar venta completa
CREATE PROCEDURE procesar_venta(
    IN p_id_usuario INT,
    IN p_id_cliente INT,
    IN p_tipo_pago VARCHAR(20)
)
BEGIN
    DECLARE nuevo_id_venta INT;
    
    START TRANSACTION;
    
    -- Crear venta
    INSERT INTO Venta (id_usuario, id_cliente, tipo_pago)
    VALUES (p_id_usuario, p_id_cliente, p_tipo_pago);
    
    SET nuevo_id_venta = LAST_INSERT_ID();
    
    COMMIT;
    
    SELECT nuevo_id_venta as id_venta_creada;
END$

-- Procedimiento para registrar pago y actualizar cuenta corriente
CREATE PROCEDURE registrar_pago_cuenta(
    IN p_id_cuenta INT,
    IN p_monto DECIMAL(10,2),
    IN p_metodo VARCHAR(50),
    IN p_id_usuario INT,
    IN p_referencia VARCHAR(100)
)
BEGIN
    START TRANSACTION;
    
    -- Validar que el monto sea positivo
    IF p_monto <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'El monto debe ser mayor a 0';
    END IF;
    
    -- Registrar pago
    INSERT INTO Pago (id_cuenta, monto, metodo, id_usuario, referencia)
    VALUES (p_id_cuenta, p_monto, p_metodo, p_id_usuario, p_referencia);
    
    -- Actualizar saldo de cuenta corriente
    UPDATE CuentaCorriente
    SET saldo = saldo + p_monto
    WHERE id_cuenta = p_id_cuenta;
    
    COMMIT;
    
    SELECT 'Pago registrado exitosamente' as mensaje;
END$

DELIMITER ;

-- =====================================
-- ÍNDICES COMPUESTOS ADICIONALES
-- =====================================

-- Para búsquedas de ventas por fecha y cliente
CREATE INDEX idx_venta_fecha_cliente ON Venta(fecha, id_cliente);

-- Para reportes de productos por categoría
CREATE INDEX idx_producto_categoria_activo ON Producto(id_categoria, activo);

-- Para auditoría de inventario
CREATE INDEX idx_auditoria_producto_fecha ON AuditoriaInventario(id_producto, fecha);










