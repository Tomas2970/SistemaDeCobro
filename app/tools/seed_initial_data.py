from __future__ import annotations
import sys
import bcrypt
import mysql.connector 
from typing import Optional
from datetime import datetime, timedelta

try:
    from app.database.DB import conectar
except Exception as e:
    print("ERROR: no se pudo importar app.database.DB.conectar:", e, file=sys.stderr)
    sys.exit(1)

# ==========================================
# FUNCIONES AUXILIARES DE BÚSQUEDA
# ==========================================
def get_rol_id(cur, nombre: str) -> Optional[int]:
    cur.execute("SELECT id_rol FROM Rol WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    return int(row[0]) if row else None

def get_categoria_id(cur, nombre: str) -> Optional[int]:
    cur.execute("SELECT id_categoria FROM Categoria WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    return int(row[0]) if row else None

def get_producto_info(cur, nombre: str) -> Optional[tuple[int, float, str]]:
    cur.execute("SELECT id_producto, precio, nombre FROM Producto WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    return (int(row[0]), float(row[1]), str(row[2])) if row else (None, None, None)

def get_cliente_id(cur, nombre: str) -> Optional[int]:
    cur.execute("SELECT id_cliente FROM Cliente WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    return int(row[0]) if row else None

def get_user_id(cur, nombre: str) -> Optional[int]:
    cur.execute("SELECT id_usuario FROM Usuario WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    return int(row[0]) if row else None

def get_proveedor_id(cur, nombre: str) -> Optional[int]:
    cur.execute("SELECT id_proveedor FROM Proveedor WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    return int(row[0]) if row else None

# ==========================================
# ROLES
# ==========================================
def ensure_roles(cur) -> None:
    print("Asegurando roles...")
    cur.execute("""
        INSERT IGNORE INTO Rol (id_rol, nombre, descripcion) VALUES
        (1, 'admin', 'Administrador del sistema con todos los permisos'),
        (2, 'vendedor', 'Usuario que puede realizar ventas'),
        (3, 'supervisor', 'Usuario que puede gestionar inventario y ver reportes')
    """)

# ==========================================
# USUARIOS
# ==========================================
def user_exists(cur, nombre: str) -> bool:
    cur.execute("SELECT 1 FROM Usuario WHERE nombre=%s", (nombre,))
    return cur.fetchone() is not None

def ensure_user(cur, nombre: str, password: str, rol_nombre: str) -> None:
    rid = get_rol_id(cur, rol_nombre)
    if not rid:
        raise RuntimeError(f"Rol '{rol_nombre}' no existe.")
    if user_exists(cur, nombre):
        print(f"   - Usuario '{nombre}' ya existe. Omitiendo.")
        return
    print(f"   + Creando usuario '{nombre}'...")
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    cur.execute(
        "INSERT INTO Usuario (nombre, contraseña, id_rol, activo) VALUES (%s, %s, %s, TRUE)",
        (nombre, hashed, rid),
    )

# ==========================================
# CATEGORÍAS
# ==========================================
def ensure_categorias(cur) -> None:
    print("Asegurando categorías iniciales...")
    cur.execute("""
        INSERT IGNORE INTO Categoria (id_categoria, nombre, descripcion, activa, margen_ganancia) VALUES
        (1, 'Bebidas', 'Bebidas alcohólicas y no alcohólicas', TRUE, 30.00),
        (2, 'Almacén', 'Productos de almacén y despensa', TRUE, 30.00),
        (3, 'Lácteos', 'Productos lácteos y derivados', TRUE, 25.00),
        (4, 'Carnes', 'Carnes y embutidos', TRUE, 35.00),
        (5, 'Limpieza', 'Productos de limpieza e higiene', TRUE, 30.00),
        (6, 'Panadería', 'Productos de panadería y pastelería', TRUE, 40.00),
        (7, 'Congelados', 'Productos congelados y listos para cocinar', TRUE, 30.00),
        (8, 'Golosinas', 'Golosinas, snacks y alfajores', TRUE, 40.00),
        (99, 'General', 'Productos sin categoría específica', TRUE, 30.00)
    """)

# ==========================================
# PROVEEDORES
# ==========================================
def ensure_proveedor(cur, nombre: str, empresa: str = "", telefono: str = "", email: str = "") -> None:
    try:
        cur.execute(
            "INSERT IGNORE INTO Proveedor (nombre, empresa, telefono, email, activo) VALUES (%s, %s, %s, %s, TRUE)",
            (nombre.strip(), empresa.strip() or None, telefono.strip() or None, email.strip() or None)
        )
        if cur.rowcount > 0: print(f"   + Proveedor '{nombre}' creado")
    except mysql.connector.Error as e:
        print(f"   ! Error al crear proveedor '{nombre}': {e}")

# ==========================================
# CLIENTES
# ==========================================
def ensure_cliente(cur, nombre: str, dni: str = "", limite: float = 50000.00) -> None:
    try:
        cur.execute("SELECT id_cliente FROM Cliente WHERE nombre=%s", (nombre,))
        if cur.fetchone():
            print(f"   - Cliente '{nombre}' ya existe. Omitiendo.")
            return
        cur.execute(
            "INSERT INTO Cliente (nombre, dni, activo) VALUES (%s, %s, TRUE)",
            (nombre, dni or None)
        )
        id_cliente = cur.lastrowid
        cur.execute(
            "INSERT INTO CuentaCorriente (id_cliente, saldo, limite_credito) VALUES (%s, 0.00, %s)",
            (id_cliente, limite)
        )
        print(f"   + Cliente '{nombre}' creado")
    except mysql.connector.Error as e:
        print(f"   ! Error al crear cliente '{nombre}': {e}")

def set_cliente_deuda(cur, nombre_cliente: str, monto_deuda: float) -> None:
    try:
        id_cliente = get_cliente_id(cur, nombre_cliente)
        if not id_cliente: return
        cur.execute("UPDATE CuentaCorriente SET saldo = %s WHERE id_cliente = %s", (monto_deuda, id_cliente))
        if cur.rowcount > 0: print(f"   + Deuda de ${monto_deuda} asignada a '{nombre_cliente}'.")
    except mysql.connector.Error as e:
        print(f"   ! Error deuda: {e}")

# ==========================================
# PRODUCTOS
# ==========================================
def ensure_producto(cur, nombre: str, precio: float, categoria: str, stock_inicial: float, stock_min: int, es_pesable: bool, codigo: str = "") -> None:
    try:
        cur.execute("SELECT 1 FROM Producto WHERE nombre=%s", (nombre,))
        if cur.fetchone():
            print(f"   - Producto '{nombre}' ya existe. Omitiendo.")
            return

        id_cat = get_categoria_id(cur, categoria) or get_categoria_id(cur, "General")
        
        cur.execute(
            "INSERT INTO Producto (nombre, precio, id_categoria, es_pesable, codigo_barras, activo) VALUES (%s, %s, %s, %s, %s, TRUE)",
            (nombre, precio, id_cat, es_pesable, codigo or None)
        )
        id_prod = cur.lastrowid
        cur.execute(
            "INSERT INTO Inventario (id_producto, cantidad, stock_minimo) VALUES (%s, %s, %s)",
            (id_prod, stock_inicial, stock_min)
        )
        print(f"   + Producto '{nombre}' creado")
    except mysql.connector.Error as e:
        print(f"   ! Error producto '{nombre}': {e}")

# ==========================================
# HISTORIAL DE VENTAS
# ==========================================
def ensure_venta_historica(cur, cliente_nombre: str, vendedor_nombre: str, productos_nombres: list[tuple[str, float]], metodo_pago: str, dias_atras: int) -> None:
    id_cliente = get_cliente_id(cur, cliente_nombre)
    id_usuario = get_user_id(cur, vendedor_nombre)
    
    if not id_cliente or not id_usuario:
        print(f"  ! Skip Venta: Cliente/Usuario no encontrado ({cliente_nombre}/{vendedor_nombre})")
        return

    total_venta = 0.0
    detalles = []

    for prod_nom, cant in productos_nombres:
        info = get_producto_info(cur, prod_nom)
        if not info[0]:
             print(f"  ! Skip prod {prod_nom}")
             continue
        id_prod, precio, nombre = info
        total_venta += (precio * cant)
        detalles.append((id_prod, cant, precio, nombre))
    
    if not detalles: return

    fecha = datetime.now() - timedelta(days=dias_atras)
    
    # Insertar Venta
    cur.execute(
        "INSERT INTO Venta (id_cliente, id_usuario, tipo_pago, fecha, estado, total) VALUES (%s, %s, %s, %s, 'completada', %s)",
        (id_cliente, id_usuario, metodo_pago, fecha, total_venta)
    )
    id_venta = cur.lastrowid

    # Insertar Detalles
    for d in detalles:
        cur.execute(
            "INSERT INTO DetalleVenta (id_venta, id_producto, nombre_producto, cantidad, precio_unitario) VALUES (%s, %s, %s, %s, %s)",
            (id_venta, d[0], d[3], d[1], d[2])
        )
        # Stock
        cur.execute("UPDATE Inventario SET cantidad = cantidad - %s WHERE id_producto = %s", (d[1], d[0]))

    print(f"   + Venta Histórica ID {id_venta} creada.")

# ==========================================
# HISTORIAL DE COMPRAS
# ==========================================
def ensure_compra_historica(cur, proveedor_nombre: str, usuario_nombre: str, productos_comprados: list[tuple[str, float, float]], dias_atras: int) -> None:
    id_prov = get_proveedor_id(cur, proveedor_nombre)
    id_usu = get_user_id(cur, usuario_nombre)
    
    if not id_prov or not id_usu: return

    detalles = []
    for prod_nom, cant, costo in productos_comprados:
        info = get_producto_info(cur, prod_nom)
        if info[0]:
            detalles.append((info[0], info[2], cant, costo))

    if not detalles: return
    
    fecha = datetime.now() - timedelta(days=dias_atras)
    cur.execute(
        "INSERT INTO Compra (id_usuario, id_proveedor, fecha, estado) VALUES (%s, %s, %s, 'recibida')",
        (id_usu, id_prov, fecha)
    )
    id_compra = cur.lastrowid

    for d in detalles:
        cur.execute(
            "INSERT INTO DetalleCompra (id_compra, id_producto, nombre_producto, cantidad, precio_unitario) VALUES (%s, %s, %s, %s, %s)",
            (id_compra, d[0], d[1], d[2], d[3])
        )
        # Stock
        cur.execute("UPDATE Inventario SET cantidad = cantidad + %s WHERE id_producto = %s", (d[2], d[0]))
    
    print(f"   + Compra Histórica ID {id_compra} creada.")

# ==========================================
# MAIN
# ==========================================
def main() -> None:
    conn = None
    try:
        conn = conectar()
        # ¡IMPORTANTE! buffered=True evita el error "Unread result found"
        cur = conn.cursor(buffered=True)
        
        print("=== CARGA DE DATOS (Con Cursor Bufferizado) ===")
        
        ensure_roles(cur)
        ensure_user(cur, "admin", "admin123", "admin")
        ensure_user(cur, "tomas", "tomas123", "vendedor")
        ensure_user(cur, "supervisor", "super123", "supervisor")
        
        ensure_categorias(cur)
        
        ensure_proveedor(cur, "Coca-Cola FEMSA")
        ensure_proveedor(cur, "Arcor")
        ensure_proveedor(cur, "La Serenísima")
        
        ensure_cliente(cur, "Juan Perez", "30123456", 75000.00)
        ensure_cliente(cur, "Maria Gonzalez", "28999111", 100000.00)
        
        ensure_producto(cur, "Coca-Cola 1.5L", 1200.00, "Bebidas", 50, 10, False, "7790123456789")
        ensure_producto(cur, "Leche Entera 1L", 800.00, "Lácteos", 30, 5, False, "7790987654321")
        ensure_producto(cur, "Pan Suelto (Kg)", 1500.00, "Panadería", 10.000, 2, True)
        ensure_producto(cur, "Alfajor Jorgito", 500.00, "Golosinas", 100, 20, False, "7793333444466")

        ensure_venta_historica(cur, "Juan Perez", "tomas", [("Coca-Cola 1.5L", 2), ("Alfajor Jorgito", 3)], "efectivo", 5)
        
        ensure_compra_historica(cur, "Coca-Cola FEMSA", "admin", [("Coca-Cola 1.5L", 50, 700.00)], 10)

        conn.commit()
        print("\n✅ CARGA COMPLETADA EXITOSAMENTE (Commit realizado).")

    except Exception as e:
        if conn: conn.rollback()
        print(f"\n❌ ERROR CRÍTICO: {e}")
        sys.exit(1)
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    main()