-- =========================================================
-- Supermercado Don Atilio - Esquema completo
-- Compatible MySQL 8.x / MariaDB 10.4+
-- =========================================================

-- 0) Base de datos
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
  contraseña VARCHAR(255) NOT NULL,        -- espacio para bcrypt/argon2
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
  direccion VARCHAR(200),
  telefono VARCHAR(20),
  email VARCHAR(255) UNIQUE,
  activo BOOLEAN DEFAULT TRUE,
  fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CHECK (email IS NULL OR email LIKE '%@%.%'),
  INDEX idx_cliente_nombre (nombre),
  INDEX idx_cliente_email (email),
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
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_categoria_nombre (nombre),
  INDEX idx_categoria_activa (activa)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Producto (
  id_producto INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  descripcion TEXT,
  precio DECIMAL(10,2) NOT NULL,
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
  cantidad INT NOT NULL DEFAULT 0,
  stock_minimo INT NOT NULL DEFAULT 5,
  stock_maximo INT DEFAULT 100,
  id_producto INT NOT NULL UNIQUE,
  ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CHECK (cantidad >= 0),
  CHECK (stock_minimo >= 0),
  CHECK (stock_maximo > stock_minimo),
  CONSTRAINT fk_inventario_producto
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
    ON DELETE CASCADE,               -- si se borra producto, cae inventario
  INDEX idx_inventario_cantidad (cantidad),
  INDEX idx_inventario_alerta (cantidad, stock_minimo)
) ENGINE=InnoDB;

-- =========================================================
-- 4) Proveedores / Compras
-- =========================================================
CREATE TABLE IF NOT EXISTS Proveedor (
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

CREATE TABLE IF NOT EXISTS Compra (
  id_compra INT AUTO_INCREMENT PRIMARY KEY,
  fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
  total DECIMAL(10,2) DEFAULT 0.00,
  id_usuario INT,
  id_proveedor INT NOT NULL,
  estado VARCHAR(20) DEFAULT 'pendiente',
  numero_factura VARCHAR(50),
  CHECK (total >= 0),
  CHECK (estado IN ('pendiente','recibida','cancelada')),
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

CREATE TABLE IF NOT EXISTS DetalleCompra (
  id_detalle_compra INT AUTO_INCREMENT PRIMARY KEY,
  id_compra INT NOT NULL,
  id_producto INT NULL,                          -- NULL permitido para poder borrar productos
  nombre_producto VARCHAR(120) NULL,             -- snapshot
  codigo_barras   VARCHAR(32)  NULL,             -- snapshot
  cantidad INT NOT NULL,
  precio_unitario DECIMAL(10,2) NOT NULL,
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

-- =========================================================
-- 5) Ventas
-- =========================================================
CREATE TABLE IF NOT EXISTS Venta (
  id_venta INT AUTO_INCREMENT PRIMARY KEY,
  fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
  total DECIMAL(10,2) DEFAULT 0.00,
  id_usuario INT,
  id_cliente INT NULL,                            -- NULL = consumidor final
  estado VARCHAR(20) DEFAULT 'completada',
  tipo_pago VARCHAR(20) DEFAULT 'efectivo',
  CHECK (total >= 0),
  CHECK (estado IN ('completada','cancelada','pendiente')),
  CHECK (tipo_pago IN ('efectivo','tarjeta','cuenta_corriente','transferencia')),
  CONSTRAINT fk_venta_usuario
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
    ON DELETE SET NULL,
  CONSTRAINT fk_venta_cliente
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
    ON DELETE RESTRICT,
  INDEX idx_venta_fecha (fecha),
  INDEX idx_venta_cliente (id_cliente),
  INDEX idx_venta_usuario (id_usuario),
  INDEX idx_venta_estado (estado)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS DetalleVenta (
  id_detalle_venta INT AUTO_INCREMENT PRIMARY KEY,
  id_venta INT NOT NULL,
  id_producto INT NULL,                           -- NULL permitido (SET NULL)
  nombre_producto VARCHAR(120) NULL,              -- snapshot
  codigo_barras   VARCHAR(32)  NULL,              -- snapshot
  cantidad INT NOT NULL,
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
-- 6) Auditoría de Inventario
-- =========================================================
CREATE TABLE IF NOT EXISTS AuditoriaInventario (
  id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
  id_producto INT NOT NULL,
  cantidad_anterior INT NOT NULL,
  cantidad_nueva INT NOT NULL,
  tipo_movimiento VARCHAR(50) NOT NULL,   -- 'venta','compra','ajuste','devolución'
  id_referencia INT,
  id_usuario INT,
  fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  observaciones TEXT,
  CONSTRAINT fk_auditoria_producto
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
    ON DELETE CASCADE,
  CONSTRAINT fk_auditoria_usuario
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
    ON DELETE SET NULL,
  INDEX idx_auditoria_producto (id_producto),
  INDEX idx_auditoria_fecha (fecha),
  INDEX idx_auditoria_tipo (tipo_movimiento)
) ENGINE=InnoDB;

-- =========================================================
-- 7) Triggers (totales / auditoría / cuenta corriente)
-- =========================================================
DELIMITER $$

CREATE TRIGGER IF NOT EXISTS trg_detalle_venta_ai_total
AFTER INSERT ON DetalleVenta
FOR EACH ROW
BEGIN
  UPDATE Venta
  SET total = (
    SELECT COALESCE(SUM(subtotal),0)
    FROM DetalleVenta
    WHERE id_venta = NEW.id_venta
  )
  WHERE id_venta = NEW.id_venta;
END$$

CREATE TRIGGER IF NOT EXISTS trg_detalle_compra_ai_total
AFTER INSERT ON DetalleCompra
FOR EACH ROW
BEGIN
  UPDATE Compra
  SET total = (
    SELECT COALESCE(SUM(subtotal),0)
    FROM DetalleCompra
    WHERE id_compra = NEW.id_compra
  )
  WHERE id_compra = NEW.id_compra;
END$$

-- Auditoría de inventario en ventas (descuento)
CREATE TRIGGER IF NOT EXISTS trg_auditoria_venta_inventario
AFTER INSERT ON DetalleVenta
FOR EACH ROW
BEGIN
  DECLARE v_cant_anterior INT DEFAULT 0;
  SELECT cantidad INTO v_cant_anterior FROM Inventario WHERE id_producto = NEW.id_producto;
  INSERT INTO AuditoriaInventario
    (id_producto, cantidad_anterior, cantidad_nueva, tipo_movimiento, id_referencia, id_usuario)
  VALUES
    (NEW.id_producto, v_cant_anterior, GREATEST(v_cant_anterior - NEW.cantidad, 0), 'venta', NEW.id_venta, NULL);
END$$

-- Ajuste automático de cuenta corriente cuando cambia el total de una venta CC
CREATE TRIGGER IF NOT EXISTS trg_venta_au_cuentacorriente
AFTER UPDATE ON Venta
FOR EACH ROW
BEGIN
  IF NEW.tipo_pago = 'cuenta_corriente' AND NEW.id_cliente IS NOT NULL THEN
    IF NEW.total <> OLD.total THEN
      UPDATE CuentaCorriente
      SET saldo = saldo - (NEW.total - OLD.total)
      WHERE id_cliente = NEW.id_cliente;
    END IF;
  END IF;
END$$

DELIMITER ;

-- =========================================================
-- 8) Datos iniciales (roles, categorías)
-- =========================================================
INSERT IGNORE INTO Rol (id_rol, nombre, descripcion) VALUES
  (1, 'admin', 'Administrador del sistema con todos los permisos'),
  (2, 'vendedor', 'Usuario que puede realizar ventas'),
  (3, 'supervisor', 'Usuario que puede gestionar inventario y ver reportes');

INSERT IGNORE INTO Categoria (id_categoria, nombre, descripcion) VALUES
  (1, 'Bebidas', 'Bebidas alcohólicas y no alcohólicas'),
  (2, 'Almacén', 'Productos de almacén y despensa'),
  (3, 'Lácteos', 'Productos lácteos y derivados'),
  (4, 'Carnes', 'Carnes y embutidos'),
  (5, 'Limpieza', 'Productos de limpieza e higiene'),
  (6, 'Panadería', 'Productos de panadería y pastelería');

-- (Nota) No insertamos Cliente id=0: ventas sin cliente usan id_cliente = NULL.

-- =========================================================
-- 9) Vistas útiles
-- =========================================================
CREATE OR REPLACE VIEW vista_stock_bajo AS
SELECT
  p.id_producto,
  p.nombre,
  p.precio,
  c.nombre AS categoria,
  i.cantidad,
  i.stock_minimo,
  (i.stock_minimo - i.cantidad) AS unidades_faltantes
FROM Producto p
JOIN Inventario i ON p.id_producto = i.id_producto
LEFT JOIN Categoria c ON p.id_categoria = c.id_categoria
WHERE i.cantidad <= i.stock_minimo
ORDER BY i.cantidad ASC;

CREATE OR REPLACE VIEW vista_ventas_diarias AS
SELECT
  DATE(v.fecha) AS fecha,
  COUNT(v.id_venta) AS total_ventas,
  SUM(v.total) AS monto_total
FROM Venta v
WHERE v.estado = 'completada'
GROUP BY DATE(v.fecha)
ORDER BY fecha DESC;

CREATE OR REPLACE VIEW vista_productos_mas_vendidos AS
SELECT
  p.id_producto,
  p.nombre,
  p.precio,
  c.nombre AS categoria,
  SUM(dv.cantidad) AS total_vendido,
  SUM(dv.subtotal) AS ingresos_generados
FROM Producto p
JOIN DetalleVenta dv ON p.id_producto = dv.id_producto
JOIN Venta v ON dv.id_venta = v.id_venta
LEFT JOIN Categoria c ON p.id_categoria = c.id_categoria
WHERE v.estado = 'completada'
GROUP BY p.id_producto
ORDER BY total_vendido DESC;

CREATE OR REPLACE VIEW vista_clientes_deuda AS
SELECT
  c.id_cliente,
  c.nombre,
  c.telefono,
  c.email,
  cc.saldo,
  cc.limite_credito,
  (cc.limite_credito + cc.saldo) AS credito_disponible
FROM Cliente c
JOIN CuentaCorriente cc ON c.id_cliente = cc.id_cliente
WHERE cc.saldo < 0
ORDER BY cc.saldo ASC;

-- =========================================================
-- 10) Índices compuestos adicionales
-- =========================================================
CREATE INDEX IF NOT EXISTS idx_venta_fecha_cliente ON Venta(fecha, id_cliente);
CREATE INDEX IF NOT EXISTS idx_producto_categoria_activo ON Producto(id_categoria, activo);
CREATE INDEX IF NOT EXISTS idx_auditoria_producto_fecha ON AuditoriaInventario(id_producto, fecha);
