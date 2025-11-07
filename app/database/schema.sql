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
  dni VARCHAR(15) NULL UNIQUE,
  direccion VARCHAR(200),
  telefono VARCHAR(20),
  email VARCHAR(255) UNIQUE,
  activo BOOLEAN DEFAULT TRUE,
  fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CHECK (email IS NULL OR email LIKE '%@%.%'),
  INDEX idx_cliente_nombre (nombre),
  INDEX idx_cliente_dni (dni),
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
-- 4) Proveedores / Compras / Mapeo
-- =========================================================
CREATE TABLE IF NOT EXISTS Proveedor (
  id_proveedor INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  empresa VARCHAR(200),
  telefono VARCHAR(20),
  email VARCHAR(255) UNIQUE,
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
  id_producto INT NULL,
  nombre_producto VARCHAR(120) NULL,
  codigo_barras   VARCHAR(32)  NULL,
  cantidad DECIMAL(10, 3) NOT NULL, 
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

CREATE TABLE IF NOT EXISTS Proveedor_Producto (
    id_proveedor INT NOT NULL,
    id_producto INT NOT NULL,

    PRIMARY KEY (id_proveedor, id_producto),
    
    CONSTRAINT fk_pp_proveedor
        FOREIGN KEY (id_proveedor) 
        REFERENCES Proveedor(id_proveedor)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_pp_producto
        FOREIGN KEY (id_producto) 
        REFERENCES Producto(id_producto)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================================================
-- 5) Ventas
-- =========================================================
CREATE TABLE IF NOT EXISTS Venta (
  id_venta INT AUTO_INCREMENT PRIMARY KEY,
  fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
  total DECIMAL(10,2) DEFAULT 0.00,
  id_usuario INT,
  id_cliente INT NULL,
  estado VARCHAR(20) DEFAULT 'pendiente', 
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
  id_producto INT NULL, 
  nombre_producto VARCHAR(120) NULL,
  codigo_barras   VARCHAR(32)  NULL,
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
-- 6) Auditoría
-- =========================================================
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
  CONSTRAINT fk_auditoria_inv_producto
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
    ON DELETE CASCADE,
  CONSTRAINT fk_auditoria_inv_usuario
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
    ON DELETE SET NULL,
  INDEX idx_auditoria_inv_producto (id_producto),
  INDEX idx_auditoria_inv_fecha (fecha),
  INDEX idx_auditoria_inv_tipo (tipo_movimiento)
) ENGINE=InnoDB;

-- --- ¡NUEVA TABLA DE AUDITORÍA DE ACCIONES! ---
CREATE TABLE IF NOT EXISTS AuditoriaAcciones (
  id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario INT,
  accion VARCHAR(100) NOT NULL,
  tabla_afectada VARCHAR(50),
  id_registro INT,
  datos_anteriores JSON,
  datos_nuevos JSON,
  fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT fk_auditoria_acc_usuario
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
    ON DELETE SET NULL,
    
  INDEX idx_auditoria_acc_fecha (fecha),
  INDEX idx_auditoria_acc_usuario (id_usuario),
  INDEX idx_auditoria_acc_accion (accion)
) ENGINE=InnoDB;
-- --- FIN NUEVA TABLA ---

-- =========================================================
-- 7) Triggers
-- =========================================================
DELIMITER $$

DROP TRIGGER IF EXISTS trg_detalle_venta_ai_total $$
CREATE TRIGGER trg_detalle_venta_ai_total
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
END $$

DROP TRIGGER IF EXISTS trg_detalle_compra_ai_total $$
CREATE TRIGGER trg_detalle_compra_ai_total
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
END $$

DROP TRIGGER IF EXISTS trg_auditoria_venta_inventario $$
CREATE TRIGGER trg_auditoria_venta_inventario
AFTER INSERT ON DetalleVenta
FOR EACH ROW
BEGIN
  DECLARE v_cant_anterior DECIMAL(10, 3) DEFAULT 0.000; 
  IF NEW.id_producto IS NOT NULL THEN
    SELECT cantidad INTO v_cant_anterior
    FROM Inventario WHERE id_producto = NEW.id_producto;
    INSERT INTO AuditoriaInventario
      (id_producto, cantidad_anterior, cantidad_nueva, tipo_movimiento, id_referencia, id_usuario)
    VALUES
      (NEW.id_producto, v_cant_anterior, GREATEST(v_cant_anterior - NEW.cantidad, 0), 'venta', NEW.id_venta, NULL);
  END IF;
END $$

DROP TRIGGER IF EXISTS trg_venta_au_cuentacorriente $$
CREATE TRIGGER trg_venta_au_cuentacorriente
AFTER UPDATE ON Venta
FOR EACH ROW
BEGIN
  IF NEW.id_cliente IS NOT NULL THEN
    IF NEW.tipo_pago = 'cuenta_corriente' AND OLD.tipo_pago <> 'cuenta_corriente' THEN
      UPDATE CuentaCorriente
      SET saldo = saldo - NEW.total 
      WHERE id_cliente = NEW.id_cliente;
    ELSIF NEW.tipo_pago = 'cuenta_corriente' AND NEW.total <> OLD.total THEN
      UPDATE CuentaCorriente
      SET saldo = saldo - (NEW.total - OLD.total) 
      WHERE id_cliente = NEW.id_cliente;
    ELSIF OLD.tipo_pago = 'cuenta_corriente' AND NEW.tipo_pago <> 'cuenta_corriente' THEN
      UPDATE CuentaCorriente
      SET saldo = saldo + OLD.total 
      WHERE id_cliente = NEW.id_cliente;
    END IF;
  END IF;
END $$

DELIMITER ;

-- =========================================================
-- 8) Datos iniciales (roles, categorías)
-- =========================================================
-- (Se movieron a 'app/tools/seed_initial_data.py')

-- =========================================================
-- 9) Vistas útiles
-- =========================================================
CREATE OR REPLACE VIEW vista_stock_bajo AS
SELECT
  p.id_producto,
  p.nombre,
  p.precio,
  p.es_pesable,
  c.nombre AS categoria,
  i.cantidad,
  i.stock_minimo,
  (i.stock_minimo - i.cantidad) AS unidades_faltantes
FROM Producto p
JOIN Inventario i ON p.id_producto = i.id_producto
LEFT JOIN Categoria c ON p.id_categoria = c.id_categoria
WHERE i.cantidad <= i.stock_minimo AND p.activo = 1
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
WHERE v.estado = 'completada' AND p.activo = 1
GROUP BY p.id_producto
ORDER BY total_vendido DESC;

CREATE OR REPLACE VIEW vista_clientes_deuda AS
SELECT
  c.id_cliente,
  c.nombre,
  c.dni,
  c.telefono,
  c.email,
  cc.saldo,
  cc.limite_credito,
  (cc.limite_credito + cc.saldo) AS credito_disponible
FROM Cliente c
JOIN CuentaCorriente cc ON c.id_cliente = cc.id_cliente
WHERE cc.saldo < 0 AND c.activo = 1
ORDER BY cc.saldo ASC;

-- =========================================================
-- 10) Índices compuestos adicionales
-- =========================================================
DELIMITER $$

DROP PROCEDURE IF EXISTS ensure_index $$
CREATE PROCEDURE ensure_index(
  IN p_table VARCHAR(64),
  IN p_index VARCHAR(64),
  IN p_cols  VARCHAR(255)
)
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name   = p_table
      AND index_name   = p_index
  ) THEN
    SET @sql = CONCAT('CREATE INDEX ', p_index, ' ON ', p_table, ' (', p_cols, ')');
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END $$
DELIMITER ;

CALL ensure_index('Venta',               'idx_venta_fecha_cliente',       'fecha, id_cliente');
CALL ensure_index('Producto',            'idx_producto_categoria_activo', 'id_categoria, activo');
CALL ensure_index('AuditoriaInventario', 'idx_auditoria_producto_fecha',  'id_producto, fecha');

DROP PROCEDURE IF EXISTS ensure_index;