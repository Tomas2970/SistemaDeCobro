CREATE DATABASE supermercado_don_atilio;

USE supermercado_don_atilio;

-- TABLAS DE SEGURIDAD
CREATE TABLE Rol (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE Usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    contraseña VARCHAR(100) NOT NULL,
    id_rol INT NOT NULL,
    FOREIGN KEY (id_rol) REFERENCES Rol(id_rol)
) ENGINE=InnoDB;


-- TABLAS DE CLIENTES Y CUENTA CORRIENTE

CREATE TABLE Cliente (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    direccion VARCHAR(100),
    telefono VARCHAR(20),
    email VARCHAR(50)
) ENGINE=InnoDB;

CREATE TABLE CuentaCorriente (
    id_cuenta INT AUTO_INCREMENT PRIMARY KEY,
    saldo DECIMAL(10,2) DEFAULT 0,
    id_cliente INT UNIQUE,
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
) ENGINE=InnoDB;

CREATE TABLE Pago (
    id_pago INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    monto DECIMAL(10,2) NOT NULL,
    metodo VARCHAR(50),
    id_cuenta INT,
    FOREIGN KEY (id_cuenta) REFERENCES CuentaCorriente(id_cuenta)
) ENGINE=InnoDB;

-- TABLAS DE PRODUCTOS E INVENTARIO

CREATE TABLE Categoria (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    descripcion VARCHAR(100)
) ENGINE=InnoDB;

CREATE TABLE Producto (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    id_categoria INT,
    FOREIGN KEY (id_categoria) REFERENCES Categoria(id_categoria)
) ENGINE=InnoDB;

CREATE TABLE Inventario (
    id_inventario INT AUTO_INCREMENT PRIMARY KEY,
    cantidad INT NOT NULL DEFAULT 0,
    stock_minimo INT NOT NULL DEFAULT 0,
    id_producto INT UNIQUE,
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
) ENGINE=InnoDB;


-- TABLAS DE PROVEEDORES Y COMPRAS

CREATE TABLE Proveedor (
    id_proveedor INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    telefono VARCHAR(20)
) ENGINE=InnoDB;

CREATE TABLE Compra (
    id_compra INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE DEFAULT (CURRENT_DATE),
    id_usuario INT,
    id_proveedor INT,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario),
    FOREIGN KEY (id_proveedor) REFERENCES Proveedor(id_proveedor)
) ENGINE=InnoDB;

CREATE TABLE DetalleCompra (
    id_detalle_compra INT AUTO_INCREMENT PRIMARY KEY,
    id_compra INT,
    id_producto INT,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (id_compra) REFERENCES Compra(id_compra),
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
) ENGINE=InnoDB;

-- TABLAS DE VENTAS

CREATE TABLE Venta (
    id_venta INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_usuario INT,
    id_cliente INT,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario),
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
) ENGINE=InnoDB;

CREATE TABLE DetalleVenta (
    id_detalle_venta INT AUTO_INCREMENT PRIMARY KEY,
    id_venta INT,
    id_producto INT,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (id_venta) REFERENCES Venta(id_venta),
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
) ENGINE=InnoDB;
