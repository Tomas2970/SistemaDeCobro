-- =========================================================
-- Supermercado Don Atilio - Esquema DEFINITIVO
-- Versión: 3.1 - INTEGRACIÓN id_session EN Venta
-- =========================================================

CREATE DATABASE IF NOT EXISTS supermercado_don_atilio
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE supermercado_don_atilio;

-- =========================================================
-- 1) Seguridad / Usuarios / Roles
-- =========================================================
CREATE TABLE IF NOT EXISTS Rol (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(200),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    contraseña VARCHAR(255) NOT NULL,
    id_rol INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP NULL,
    CONSTRAINT fk_usuario_rol
        FOREIGN KEY (id_rol) REFERENCES Rol(id_rol)
        ON UPDATE CASCADE,
    INDEX idx_usuario_nombre (nombre),
    INDEX idx_usuario_activo (activo)
) ENGINE=InnoDB;

-- =========================================================
-- 2) Clientes / Cuenta Corriente / Pagos
-- =========================================================
CREATE TABLE IF NOT EXISTS Cliente (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    dni VARCHAR(8) NULL UNIQUE,
    cuit VARCHAR(11) NULL UNIQUE,
    direccion VARCHAR(200),
    telefono VARCHAR(20),
    email VARCHAR(255) UNIQUE,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (email IS NULL OR email LIKE '%@%.%'),
    INDEX idx_cliente_nombre (nombre),
    INDEX idx_cliente_dni (dni),
    INDEX idx_cliente_activo (activo)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS CuentaCorriente (
    id_cuenta INT AUTO_INCREMENT PRIMARY KEY,
    saldo DECIMAL(10,2) DEFAULT 0.00,
    limite_credito DECIMAL(10,2) DEFAULT 0.00,
    id_cliente INT UNIQUE NOT NULL,
    fecha_apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CHECK (saldo >= -limite_credito),
    CONSTRAINT fk_cc_cliente
        FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
        ON DELETE CASCADE,
    INDEX idx_cuenta_saldo (saldo)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Pago (
    id_pago INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    monto DECIMAL(10,2) NOT NULL,
    metodo VARCHAR(50) NOT NULL,
    referencia VARCHAR(100),
    id_cuenta INT NOT NULL,
    id_usuario INT,
    CHECK (monto > 0),
    CHECK (metodo IN ('efectivo','tarjeta_debito','tarjeta_credito','transferencia','cheque')),
    CONSTRAINT fk_pago_cuenta
        FOREIGN KEY (id_cuenta) REFERENCES CuentaCorriente(id_cuenta)
        ON DELETE RESTRICT,
    CONSTRAINT fk_pago_usuario
        FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
        ON DELETE SET NULL,
    INDEX idx_pago_fecha (fecha),
    INDEX idx_pago_cuenta (id_cuenta)
) ENGINE=InnoDB;

-- =========================================================
-- 3) Productos / Categorías / Inventario
-- =========================================================
CREATE TABLE IF NOT EXISTS Categoria (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(200),
    activa BOOLEAN DEFAULT TRUE,
    margen_ganancia DECIMAL(5,2) DEFAULT 30.00,
    es_pesable_default BOOLEAN DEFAULT FALSE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_categoria_nombre (nombre),
    INDEX idx_categoria_activa (activa)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Producto (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) NOT NULL,
    es_pesable BOOLEAN NOT NULL DEFAULT FALSE,
    codigo_barras VARCHAR(32) NULL,
    id_categoria INT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (precio > 0),
    CONSTRAINT fk_producto_categoria
        FOREIGN KEY (id_categoria) REFERENCES Categoria(id_categoria)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT ux_producto_codigo_barras UNIQUE (codigo_barras),
    INDEX idx_producto_nombre (nombre),
    INDEX idx_producto_categoria (id_categoria),
    INDEX idx_producto_activo (activo)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Inventario (
    id_inventario INT AUTO_INCREMENT PRIMARY KEY,
    cantidad DECIMAL(10, 3) NOT NULL DEFAULT 0.000,
    stock_minimo INT NOT NULL DEFAULT 5,
    stock_maximo INT DEFAULT 100,
    id_producto INT NOT NULL UNIQUE,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CHECK (cantidad >= 0),
    CHECK (stock_minimo >= 0),
    CHECK (stock_maximo > stock_minimo),
    CONSTRAINT fk_inventario_producto
        FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
        ON DELETE CASCADE,
    INDEX idx_inventario_cantidad (cantidad),
    INDEX idx_inventario_alerta (cantidad, stock_minimo)
) ENGINE=InnoDB;

-- =========================================================
-- 4) Proveedores / Compras / Pagos Proveedor
-- =========================================================
CREATE TABLE IF NOT EXISTS Proveedor (
    id_proveedor INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    empresa VARCHAR(200) NOT NULL,
    dni VARCHAR(8) NULL UNIQUE,
    cuit VARCHAR(11) NOT NULL,
    direccion VARCHAR(200),
    telefono VARCHAR(20),
    email VARCHAR(255) UNIQUE,
    saldo DECIMAL(10,2) DEFAULT 0.00,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (email IS NULL OR email LIKE '%@%.%'),
    INDEX idx_proveedor_nombre (nombre),
    INDEX idx_proveedor_activo (activo)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Compra (
    id_compra INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(10,2) DEFAULT 0.00,
    id_usuario INT,
    id_proveedor INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'pendiente',
    numero_factura VARCHAR(50),
    medio_pago VARCHAR(50) DEFAULT 'efectivo',
    CHECK (total >= 0),
    CHECK (estado IN ('pendiente','recibida','cancelada')),
    CHECK (medio_pago IN ('efectivo','transferencia','cuenta_corriente','tarjeta','cheque')),
    CONSTRAINT fk_compra_usuario
        FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
        ON DELETE SET NULL,
    CONSTRAINT fk_compra_proveedor
        FOREIGN KEY (id_proveedor) REFERENCES Proveedor(id_proveedor)
        ON DELETE RESTRICT,
    INDEX idx_compra_fecha (fecha),
    INDEX idx_compra_proveedor (id_proveedor),
    INDEX idx_compra_estado (estado)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS PagoProveedor (
    id_pago_prov INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    monto DECIMAL(10,2) NOT NULL,
    metodo VARCHAR(50) NOT NULL,
    observacion TEXT,
    id_proveedor INT NOT NULL,
    id_usuario INT,
    CHECK (monto > 0),
    CONSTRAINT fk_pagoprov_proveedor FOREIGN KEY (id_proveedor) REFERENCES Proveedor(id_proveedor),
    CONSTRAINT fk_pagoprov_usuario FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS DetalleCompra (
    id_detalle_compra INT AUTO_INCREMENT PRIMARY KEY,
    id_compra INT NOT NULL,
    id_producto INT NULL,
    nombre_producto VARCHAR(120) NULL,
    codigo_barras VARCHAR(32) NULL,
    cantidad DECIMAL(10, 3) NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    precio_venta_historico DECIMAL(10,2) NULL,
    subtotal DECIMAL(10,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,
    CHECK (cantidad > 0),
    CHECK (precio_unitario > 0),
    CONSTRAINT fk_detalle_compra_compra
        FOREIGN KEY (id_compra) REFERENCES Compra(id_compra)
        ON DELETE CASCADE,
    CONSTRAINT fk_detalle_compra_producto
        FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_detalle_compra_compra (id_compra),
    INDEX idx_detalle_compra_producto (id_producto)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Proveedor_Producto (
    id_proveedor INT NOT NULL,
    id_producto INT NOT NULL,
    PRIMARY KEY (id_proveedor, id_producto),
    CONSTRAINT fk_pp_proveedor
        FOREIGN KEY (id_proveedor) REFERENCES Proveedor(id_proveedor) ON DELETE CASCADE,
    CONSTRAINT fk_pp_producto
        FOREIGN KEY (id_producto) REFERENCES Producto(id_producto) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================================================
-- 5) CAJA Y SESIONES (Definidas antes que Venta para FK)
-- =========================================================
CREATE TABLE IF NOT EXISTS caja_session (
    id_session INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario_apertura INT NOT NULL,
    fecha_apertura DATETIME DEFAULT CURRENT_TIMESTAMP,
    monto_apertura DECIMAL(10,2) NOT NULL,
    id_usuario_cierre INT NULL,
    fecha_cierre DATETIME NULL,
    efectivo_esperado DECIMAL(10,2) NULL,
    efectivo_contado DECIMAL(10,2) NULL,
    diferencia DECIMAL(10,2) NULL,
    observaciones_cierre TEXT NULL,
    estado ENUM('abierta', 'cerrada') DEFAULT 'abierta',
    FOREIGN KEY (id_usuario_apertura) REFERENCES Usuario(id_usuario),
    FOREIGN KEY (id_usuario_cierre) REFERENCES Usuario(id_usuario),
    INDEX idx_caja_estado (estado),
    INDEX idx_caja_fecha (fecha_apertura)
) ENGINE=InnoDB;

-- =========================================================
-- 6) Ventas
-- =========================================================
CREATE TABLE IF NOT EXISTS Venta (
    id_venta INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(10,2) DEFAULT 0.00,
    id_usuario INT,
    id_cliente INT NULL,
    estado VARCHAR(20) DEFAULT 'pendiente',
    tipo_pago VARCHAR(20) DEFAULT 'efectivo',
    id_session INT NULL, 
    CHECK (total >= 0),
    CHECK (estado IN ('completada','cancelada','pendiente')),
    CHECK (tipo_pago IN ('efectivo','tarjeta','cuenta_corriente','transferencia')),
    CONSTRAINT fk_venta_usuario
        FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
        ON DELETE SET NULL,
    CONSTRAINT fk_venta_cliente
        FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
        ON DELETE RESTRICT,
    CONSTRAINT fk_venta_session
        FOREIGN KEY (id_session) REFERENCES caja_session(id_session)
        ON DELETE SET NULL,
    INDEX idx_venta_fecha (fecha),
    INDEX idx_venta_cliente (id_cliente),
    INDEX idx_venta_usuario (id_usuario),
    INDEX idx_venta_estado (estado),
    INDEX idx_venta_session (id_session)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS DetalleVenta (
    id_detalle_venta INT AUTO_INCREMENT PRIMARY KEY,
    id_venta INT NOT NULL,
    id_producto INT NULL,
    nombre_producto VARCHAR(120) NULL,
    codigo_barras VARCHAR(32) NULL,
    cantidad DECIMAL(10, 3) NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,
    CHECK (cantidad > 0),
    CHECK (precio_unitario > 0),
    CONSTRAINT fk_detalle_venta_venta
        FOREIGN KEY (id_venta) REFERENCES Venta(id_venta)
        ON DELETE CASCADE,
    CONSTRAINT fk_detalle_venta_producto
        FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_detalle_venta_venta (id_venta),
    INDEX idx_detalle_venta_producto (id_producto)
) ENGINE=InnoDB;

-- =========================================================
-- 7) CAJA MOVIMIENTOS, NOTAS DE CRÉDITO Y AUDITORÍA
-- =========================================================
CREATE TABLE IF NOT EXISTS caja_movimiento (
    id_movimiento INT AUTO_INCREMENT PRIMARY KEY,
    id_session INT NOT NULL,
    tipo ENUM('ingreso', 'egreso') NOT NULL,
    monto DECIMAL(10,2) NOT NULL CHECK (monto > 0),
    medio ENUM('efectivo', 'tarjeta', 'transferencia', 'cuenta_corriente') NOT NULL,
    motivo ENUM(
        'apertura_caja',
        'venta_efectivo',
        'venta_tarjeta',
        'venta_transferencia',
        'venta_cuenta_corriente',
        'pago_cuenta_corriente_efectivo',
        'pago_cuenta_corriente_transferencia',
        'pago_cuenta_corriente_tarjeta',
        'cobro_cuenta_corriente',
        'pago_proveedor',
        'gasto_vario',
        'retiro_caja',
        'devolucion_efectivo',
        'ajuste_positivo',
        'ajuste_negativo',
        'otro'
    ) NOT NULL,
    id_usuario INT NOT NULL,
    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_venta INT NULL,
    id_cliente INT NULL,
    id_compra INT NULL,
    descripcion TEXT NULL,
    FOREIGN KEY (id_session) REFERENCES caja_session(id_session),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario),
    FOREIGN KEY (id_venta) REFERENCES Venta(id_venta) ON DELETE SET NULL,
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente),
    FOREIGN KEY (id_compra) REFERENCES Compra(id_compra),
    INDEX idx_mov_session (id_session),
    INDEX idx_mov_tipo (tipo)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS nota_credito (
    id_nota_credito INT AUTO_INCREMENT PRIMARY KEY,
    id_venta INT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    tipo_devolucion ENUM('reembolso_efectivo', 'credito_a_favor') NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_usuario INT NOT NULL,
    motivo TEXT,
    FOREIGN KEY (id_venta) REFERENCES Venta(id_venta),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS AuditoriaInventario (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    id_producto INT NOT NULL,
    cantidad_anterior DECIMAL(10, 3) NOT NULL,
    cantidad_nueva DECIMAL(10, 3) NOT NULL,
    tipo_movimiento VARCHAR(50) NOT NULL,
    id_referencia INT,
    id_usuario INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observaciones TEXT,
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS AuditoriaAcciones (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    accion VARCHAR(100) NOT NULL,
    tabla_afectada VARCHAR(50),
    id_registro INT,
    datos_anteriores JSON,
    datos_nuevos JSON,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE SET NULL
) ENGINE=InnoDB;

-- =========================================================
-- 8) Triggers
-- =========================================================
DELIMITER $$

DROP TRIGGER IF EXISTS trg_detalle_venta_ai_total $$
CREATE TRIGGER trg_detalle_venta_ai_total
AFTER INSERT ON DetalleVenta
FOR EACH ROW
BEGIN
    UPDATE Venta
    SET total = (SELECT COALESCE(SUM(subtotal),0) FROM DetalleVenta WHERE id_venta = NEW.id_venta)
    WHERE id_venta = NEW.id_venta;
END $$

DROP TRIGGER IF EXISTS trg_detalle_compra_ai_total $$
CREATE TRIGGER trg_detalle_compra_ai_total
AFTER INSERT ON DetalleCompra
FOR EACH ROW
BEGIN
    UPDATE Compra
    SET total = (SELECT COALESCE(SUM(subtotal),0) FROM DetalleCompra WHERE id_compra = NEW.id_compra)
    WHERE id_compra = NEW.id_compra;
END $$

DROP TRIGGER IF EXISTS trg_auditoria_venta_inventario $$
CREATE TRIGGER trg_auditoria_venta_inventario
AFTER INSERT ON DetalleVenta
FOR EACH ROW
BEGIN
    DECLARE v_cant_anterior DECIMAL(10, 3) DEFAULT 0.000;
    IF NEW.id_producto IS NOT NULL THEN
        SELECT cantidad INTO v_cant_anterior FROM Inventario WHERE id_producto = NEW.id_producto;
        INSERT INTO AuditoriaInventario (id_producto, cantidad_anterior, cantidad_nueva, tipo_movimiento, id_referencia)
        VALUES (NEW.id_producto, v_cant_anterior, GREATEST(v_cant_anterior - NEW.cantidad, 0), 'venta', NEW.id_venta);
    END IF;
END $$

DROP TRIGGER IF EXISTS trg_venta_au_cuentacorriente $$
CREATE TRIGGER trg_venta_au_cuentacorriente
AFTER UPDATE ON Venta
FOR EACH ROW
BEGIN
    IF NEW.id_cliente IS NOT NULL THEN
        IF NEW.tipo_pago = 'cuenta_corriente' AND OLD.tipo_pago <> 'cuenta_corriente' THEN
            UPDATE CuentaCorriente SET saldo = saldo - NEW.total WHERE id_cliente = NEW.id_cliente;
        ELSEIF NEW.tipo_pago = 'cuenta_corriente' AND NEW.total <> OLD.total THEN
            UPDATE CuentaCorriente SET saldo = saldo - (NEW.total - OLD.total) WHERE id_cliente = NEW.id_cliente;
        END IF;
    END IF;
END $$

DELIMITER ;

-- =========================================================
-- 9) Vistas
-- =========================================================
CREATE OR REPLACE VIEW vista_stock_bajo AS
SELECT p.id_producto, p.nombre, p.precio, p.es_pesable, c.nombre AS categoria, 
       i.cantidad, i.stock_minimo, (i.stock_minimo - i.cantidad) AS unidades_faltantes
FROM Producto p
JOIN Inventario i ON p.id_producto = i.id_producto
LEFT JOIN Categoria c ON p.id_categoria = c.id_categoria
WHERE i.cantidad <= i.stock_minimo AND p.activo = 1
ORDER BY i.cantidad ASC;

CREATE OR REPLACE VIEW vista_ventas_diarias AS
SELECT DATE(v.fecha) AS fecha, COUNT(v.id_venta) AS total_ventas, SUM(v.total) AS monto_total
FROM Venta v WHERE v.estado = 'completada' GROUP BY DATE(v.fecha) ORDER BY fecha DESC;

CREATE OR REPLACE VIEW vista_clientes_deuda AS
SELECT c.id_cliente, c.nombre, c.dni, c.telefono, c.email, cc.saldo, cc.limite_credito
FROM Cliente c
JOIN CuentaCorriente cc ON c.id_cliente = cc.id_cliente
WHERE cc.saldo < 0 AND c.activo = 1
ORDER BY cc.saldo ASC;