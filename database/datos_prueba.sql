USE supermercado_don_atilio;

-- Roles
INSERT INTO Rol (nombre) VALUES ('Administrador'), ('Empleado');

-- Usuarios
INSERT INTO Usuario (nombre, contraseña, id_rol)
VALUES ('admin', '1234', 1),
       ('empleado1', '1234', 2);

-- Clientes
INSERT INTO Cliente (nombre, direccion, telefono, email)
VALUES ('Juan Pérez', 'San Martín 123', '3425551111', 'juan@mail.com'),
       ('María López', 'Belgrano 456', '3425552222', 'maria@mail.com');

-- Cuentas corrientes
INSERT INTO CuentaCorriente (saldo, id_cliente)
VALUES (0, 1), (5000, 2);

-- Pagos
INSERT INTO Pago (monto, metodo, id_cuenta)
VALUES (2000, 'Efectivo', 2);

-- Categorías
INSERT INTO Categoria (nombre, descripcion)
VALUES ('Almacén', 'Productos de almacén'),
       ('Bebidas', 'Gaseosas, jugos y agua');

-- Productos
INSERT INTO Producto (nombre, precio, id_categoria)
VALUES ('Yerba Mate', 1800, 1),
       ('Coca Cola 2L', 1200, 2);

-- Inventario
INSERT INTO Inventario (cantidad, stock_minimo, id_producto)
VALUES (50, 10, 1),
       (20, 5, 2);

-- Proveedor
INSERT INTO Proveedor (nombre, telefono)
VALUES ('Distribuidora Norte', '3425558888');

-- Compra
INSERT INTO Compra (id_usuario, id_proveedor)
VALUES (1, 1);

INSERT INTO DetalleCompra (id_compra, id_producto, cantidad, precio_unitario)
VALUES (1, 1, 100, 1600);

-- Venta
INSERT INTO Venta (id_usuario, id_cliente)
VALUES (2, 1);

INSERT INTO DetalleVenta (id_venta, id_producto, cantidad, precio_unitario)
VALUES (1, 1, 2, 1800),
       (1, 2, 1, 1200);
