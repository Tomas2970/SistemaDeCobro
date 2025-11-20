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
    print("Asegúrate de ejecutar esto como un módulo desde la raíz: python -m app.tools.seed_initial_data", file=sys.stderr)
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
    """Busca un producto por nombre y devuelve (id, precio, nombre)"""
    cur.execute("SELECT id_producto, precio, nombre FROM Producto WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    return (int(row[0]), float(row[1]), str(row[2])) if row else (None, None, None)

def get_cliente_id(cur, nombre: str) -> Optional[int]:
    """Busca un cliente por nombre y devuelve (id)"""
    cur.execute("SELECT id_cliente FROM Cliente WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    return int(row[0]) if row else None

def get_user_id(cur, nombre: str) -> Optional[int]:
    """Busca un usuario por nombre y devuelve (id)"""
    cur.execute("SELECT id_usuario FROM Usuario WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    return int(row[0]) if row else None

# --- ¡NUEVO! ---
def get_proveedor_id(cur, nombre: str) -> Optional[int]:
    """Busca un proveedor por nombre y devuelve (id)"""
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
    cur.execute("ALTER TABLE Rol AUTO_INCREMENT = 10;")

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
        INSERT IGNORE INTO Categoria (id_categoria, nombre, descripcion, activa) VALUES
        (1, 'Bebidas', 'Bebidas alcohólicas y no alcohólicas', TRUE),
        (2, 'Almacén', 'Productos de almacén y despensa', TRUE),
        (3, 'Lácteos', 'Productos lácteos y derivados', TRUE),
        (4, 'Carnes', 'Carnes y embutidos', TRUE),
        (5, 'Limpieza', 'Productos de limpieza e higiene', TRUE),
        (6, 'Panadería', 'Productos de panadería y pastelería', TRUE),
        (7, 'Congelados', 'Productos congelados y listos para cocinar', TRUE),
        (8, 'Golosinas', 'Golosinas, snacks y alfajores', TRUE),
        (99, 'General', 'Productos sin categoría específica', TRUE)
    """)
    cur.execute("ALTER TABLE Categoria AUTO_INCREMENT = 100;")

# ==========================================
# PROVEEDORES
# ==========================================
def ensure_proveedor(cur, nombre: str, empresa: str = "", telefono: str = "", email: str = "") -> None:
    try:
        cur.execute(
            """
            INSERT IGNORE INTO Proveedor (nombre, empresa, telefono, email, activo) 
            VALUES (%s, %s, %s, %s, TRUE)
            """,
            (
                nombre.strip(),
                empresa.strip() or None,
                telefono.strip() or None,
                email.strip() or None
            )
        )
        if cur.rowcount > 0:
            print(f"   + Proveedor '{nombre}' creado")
    except mysql.connector.Error as e:
        print(f"   ! Error al crear proveedor '{nombre}': {e}")

# ==========================================
# CLIENTES
# ==========================================
def ensure_cliente(cur, nombre: str, dni: str = "", limite: float = 50000.00) -> None:
    try:
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
        if e.errno == 1062: # Error de duplicado
            print(f"   - Cliente '{nombre}' ya existe. Omitiendo.")
        else:
            print(f"   ! Error al crear cliente '{nombre}': {e}")

def set_cliente_deuda(cur, nombre_cliente: str, monto_deuda: float) -> None:
    """Asigna un saldo deudor inicial a un cliente existente."""
    try:
        id_cliente = get_cliente_id(cur, nombre_cliente)
        if not id_cliente:
            print(f"  ! No se pudo setear deuda: Cliente '{nombre_cliente}' no existe.")
            return
        
        # El monto_deuda debe ser negativo para ser deuda
        cur.execute(
            "UPDATE CuentaCorriente SET saldo = %s WHERE id_cliente = %s",
            (monto_deuda, id_cliente)
        )
        if cur.rowcount > 0:
            print(f"   + Deuda de ${monto_deuda} asignada a '{nombre_cliente}'.")
    except mysql.connector.Error as e:
        print(f"   ! Error al asignar deuda a '{nombre_cliente}': {e}")


# ==========================================
# PRODUCTOS
# ==========================================
def ensure_producto(cur, nombre: str, precio: float, categoria: str, stock_inicial: float, stock_min: int, es_pesable: bool, codigo: str = "") -> None:
    id_cat = get_categoria_id(cur, categoria)
    if not id_cat:
        print(f"   ! ADVERTENCIA: Categoría '{categoria}' no encontrada. Usando 'General'.")
        id_cat = get_categoria_id(cur, "General")

    try:
        cur.execute(
            """
            INSERT INTO Producto (nombre, precio, id_categoria, es_pesable, codigo_barras, activo)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            """,
            (nombre, precio, id_cat, es_pesable, codigo or None)
        )
        id_prod = cur.lastrowid
        cur.execute(
            "INSERT INTO Inventario (id_producto, cantidad, stock_minimo) VALUES (%s, %s, %s)",
            (id_prod, stock_inicial, stock_min)
        )
        print(f"   + Producto '{nombre}' creado")
    except mysql.connector.Error as e:
        if e.errno == 1062: # Error de duplicado
            print(f"   - Producto '{nombre}' ya existe. Omitiendo.")
        else:
            print(f"   ! Error al crear producto '{nombre}': {e}")

# ==========================================
# HISTORIAL DE VENTAS
# ==========================================
def ensure_venta_historica(cur, cliente_nombre: str, vendedor_nombre: str, productos_nombres: list[tuple[str, float]], metodo_pago: str, dias_atras: int) -> None:
    
    id_cliente = get_cliente_id(cur, cliente_nombre)
    id_usuario = get_user_id(cur, vendedor_nombre)
    
    if not id_cliente or not id_usuario:
        print(f"  ! Error Venta: Cliente '{cliente_nombre}' o Vendedor '{vendedor_nombre}' no encontrado.")
        return

    total_venta = 0.0
    detalles_para_insertar = [] # (id_producto, cantidad, precio_unitario, nombre_producto)

    for prod_nombre_buscado, cantidad in productos_nombres:
        id_producto, precio_unitario, nombre_producto = get_producto_info(cur, prod_nombre_buscado)
        
        if not id_producto:
            print(f"  ! Error Venta: Producto '{prod_nombre_buscado}' no encontrado. Venta cancelada.")
            raise RuntimeError(f"Producto {prod_nombre_buscado} no encontrado para venta")
        
        subtotal = precio_unitario * cantidad
        total_venta += subtotal
        detalles_para_insertar.append((id_producto, cantidad, precio_unitario, nombre_producto))
    
    if not detalles_para_insertar:
        print("  ! Error Venta: No hay productos para vender.")
        return

    fecha_venta = datetime.now() - timedelta(days=dias_atras)

    try:
        cur.execute(
            """
            INSERT INTO Venta (id_cliente, id_usuario, tipo_pago, fecha, estado)
            VALUES (%s, %s, %s, %s, 'completada')
            """,
            (id_cliente, id_usuario, metodo_pago, fecha_venta)
        )
        id_venta = cur.lastrowid

        sql_detalles = []
        for id_prod, cant, precio, nombre_prod in detalles_para_insertar:
            sql_detalles.append((id_venta, id_prod, nombre_prod, cant, precio))
            
            cur.execute(
                "UPDATE Inventario SET cantidad = cantidad - %s WHERE id_producto = %s",
                (cant, id_prod)
            )

        cur.executemany(
            """
            INSERT INTO DetalleVenta (id_venta, id_producto, nombre_producto, cantidad, precio_unitario)
            VALUES (%s, %s, %s, %s, %s)
            """,
            sql_detalles
        )
        
        if metodo_pago == 'cuenta_corriente':
            cur.execute(
                "UPDATE CuentaCorriente SET saldo = saldo - %s WHERE id_cliente = %s",
                (total_venta, id_cliente)
            )
            print(f"   + Venta (ID: {id_venta}) de ${total_venta} agregada a la C/C de '{cliente_nombre}'.")
        else:
            print(f"   + Venta (ID: {id_venta}) en {metodo_pago} por ${total_venta} creada.")
    
    except mysql.connector.Error as e:
        print(f"  ! Error al crear venta histórica: {e}")
        raise

# ==========================================
# HISTORIAL DE COMPRAS (¡NUEVO!)
# ==========================================
def ensure_compra_historica(cur, proveedor_nombre: str, usuario_nombre: str, productos_comprados: list[tuple[str, float, float]], dias_atras: int) -> None:
    """
    Crea una compra histórica y SUMA al inventario.
    productos_comprados = [(nombre_producto, cantidad, precio_costo)]
    """
    
    id_proveedor = get_proveedor_id(cur, proveedor_nombre)
    id_usuario = get_user_id(cur, usuario_nombre)
    
    if not id_proveedor or not id_usuario:
        print(f"  ! Error Compra: Proveedor '{proveedor_nombre}' o Usuario '{usuario_nombre}' no encontrado.")
        return

    total_compra = 0.0
    detalles_para_insertar = [] # (id_producto, nombre_producto, cantidad, precio_costo)
    stock_para_actualizar = [] # (cantidad_a_sumar, id_producto)

    for prod_nombre_buscado, cantidad, precio_costo in productos_comprados:
        id_producto, _, nombre_producto = get_producto_info(cur, prod_nombre_buscado)
        
        if not id_producto:
            print(f"  ! Error Compra: Producto '{prod_nombre_buscado}' no encontrado. Compra cancelada.")
            raise RuntimeError(f"Producto {prod_nombre_buscado} no encontrado para compra")
        
        total_compra += (cantidad * precio_costo)
        detalles_para_insertar.append((id_producto, nombre_producto, cantidad, precio_costo))
        stock_para_actualizar.append((cantidad, id_producto))
    
    if not detalles_para_insertar:
        print("  ! Error Compra: No hay productos para comprar.")
        return

    fecha_compra = datetime.now() - timedelta(days=dias_atras)

    try:
        # 1. Insertar Compra (el 'total' se calcula por trigger)
        cur.execute(
            """
            INSERT INTO Compra (id_usuario, id_proveedor, fecha, estado)
            VALUES (%s, %s, %s, 'recibida')
            """,
            (id_usuario, id_proveedor, fecha_compra)
        )
        id_compra = cur.lastrowid

        # 2. Preparar detalles
        sql_detalles = [(id_compra, id_prod, nombre_prod, cant, precio_costo) for id_prod, nombre_prod, cant, precio_costo in detalles_para_insertar]
        
        # 3. Insertar Detalles
        cur.executemany(
            """
            INSERT INTO DetalleCompra (id_compra, id_producto, nombre_producto, cantidad, precio_unitario)
            VALUES (%s, %s, %s, %s, %s)
            """,
            sql_detalles
        )
        
        # 4. Actualizar Inventario (SUMAR stock)
        cur.executemany(
            "UPDATE Inventario SET cantidad = cantidad + %s WHERE id_producto = %s",
            stock_para_actualizar
        )
        
        print(f"   + Compra (ID: {id_compra}) a '{proveedor_nombre}' por ~${total_compra} (stock actualizado).")
    
    except mysql.connector.Error as e:
        print(f"  ! Error al crear compra histórica: {e}")
        raise


# ==========================================
# FUNCIÓN PRINCIPAL (¡ACTUALIZADA!)
# ==========================================
def main() -> None:
    conn = cur = None
    errores = 0
    
    try:
        conn = conectar()
        cur = conn.cursor()
        
        print("=" * 60)
        print("   CARGA DE DATOS INICIALES (VERSIÓN COMPLETA) - Don Atilio")
        print("=" * 60)
        print()

        print("PASO 1/8: Asegurando Roles...")
        try:
            ensure_roles(cur)
            print("✓ Roles OK")
        except Exception as e:
            print(f"✗ Error en roles: {e}")
            errores += 1

        print("\nPASO 2/8: Asegurando Usuarios...")
        try:
            ensure_user(cur, "admin", "admin123", "admin")
            ensure_user(cur, "tomas", "tomas123", "vendedor")
            ensure_user(cur, "supervisor", "super123", "supervisor")
            ensure_user(cur, "caja1", "caja123", "vendedor")
            print("✓ Usuarios OK")
        except Exception as e:
            print(f"✗ Error en usuarios: {e}")
            errores += 1

        print("\nPASO 3/8: Asegurando Categorías...")
        try:
            ensure_categorias(cur)
            print("✓ Categorías OK")
        except Exception as e:
            print(f"✗ Error en categorías: {e}")
            errores += 1
        
        print("\nPASO 4/8: Asegurando Proveedores...")
        try:
            ensure_proveedor(cur, "Proveedor General", "S/D", "S/D", "general@proveedor.com")
            ensure_proveedor(cur, "Coca-Cola FEMSA", "Coca-Cola", "0800-123-4567", "pedidos@coca.com")
            ensure_proveedor(cur, "Panadería El Sol", "El Sol SRL", "456-7890", "pan@elsol.com")
            ensure_proveedor(cur, "Arcor", "Arcor SA", "0810-555-2726", "golosinas@arcor.com")
            ensure_proveedor(cur, "Frigorífico Rioplatense", "Frigorífico Rioplatense", "11-4567-8901", "carnes@frigo.com")
            ensure_proveedor(cur, "Granja del Sol", "GDS SA", "0800-333-4000", "congelados@gds.com")
            ensure_proveedor(cur, "La Serenísima", "Mastellone Hnos.", "0800-888-5283", "lacteos@laserenisima.com")
            print("✓ Proveedores OK")
        except Exception as e:
            print(f"✗ Error en proveedores: {e}")
            errores += 1
        
        print("\nPASO 5/8: Asegurando Clientes (y deudas)...")
        try:
            ensure_cliente(cur, "Consumidor Final", "00000000", 0.00)
            ensure_cliente(cur, "Juan Perez", "30123456", 75000.00)
            ensure_cliente(cur, "Maria Gonzalez", "28999111", 100000.00)
            ensure_cliente(cur, "Kiosco 'ElPaso'", "30-12345678-9", 250000.00)
            
            set_cliente_deuda(cur, "Maria Gonzalez", -15750.50)
            
            print("✓ Clientes OK")
        except Exception as e:
            print(f"✗ Error en clientes: {e}")
            errores += 1
        
        print("\nPASO 6/8: Asegurando Productos...")
        try:
            # (El stock inicial es ANTES de las ventas/compras históricas)
            # Bebidas
            ensure_producto(cur, "Coca-Cola 1.5L", 1200.00, "Bebidas", 50, 10, False, "7790123456789")
            ensure_producto(cur, "Agua Villavicencio 2L", 700.00, "Bebidas", 40, 10, False, "7790987123456")
            # Lácteos
            ensure_producto(cur, "Leche Entera 1L", 800.00, "Lácteos", 30, 5, False, "7790987654321")
            ensure_producto(cur, "Queso Cremoso (Kg)", 7500.00, "Lácteos", 10.000, 2, True)
            ensure_producto(cur, "Yogur Frutilla 1L", 950.00, "Lácteos", 25, 5, False, "7790987654111")
            # Panadería
            ensure_producto(cur, "Pan Suelto (Kg)", 1500.00, "Panadería", 10.000, 2, True)
            ensure_producto(cur, "Facturas (Docena)", 3800.00, "Panadería", 5, 1, False)
            # Carnes
            ensure_producto(cur, "Milanesa de Pollo (Kg)", 4500.00, "Carnes", 5.500, 1, True)
            ensure_producto(cur, "Carne Picada (Kg)", 5500.00, "Carnes", 8.000, 1, True)
            ensure_producto(cur, "Asado (Kg)", 7800.00, "Carnes", 12.000, 2, True)
            # Limpieza
            ensure_producto(cur, "Lavandina 1L", 650.00, "Limpieza", 40, 10, False, "7791111222233")
            ensure_producto(cur, "Detergente 500ml", 850.00, "Limpieza", 30, 10, False, "7791111222244")
            # Almacén
            ensure_producto(cur, "Arroz Gallo Oro 1kg", 1300.00, "Almacén", 80, 20, False, "7792222333344")
            ensure_producto(cur, "Fideos Matarazzo 500g", 950.00, "Almacén", 100, 20, False, "7792222333355")
            ensure_producto(cur, "Aceite Girasol 1.5L", 1800.00, "Almacén", 50, 15, False, "7792222333366")
            # Golosinas
            ensure_producto(cur, "Papas Fritas Lays 150g", 1500.00, "Golosinas", 50, 10, False, "7793333444455")
            ensure_producto(cur, "Alfajor Jorgito", 500.00, "Golosinas", 100, 20, False, "7793333444466")
            # Congelados
            ensure_producto(cur, "Medallones de Merluza (Kg)", 3800.00, "Congelados", 15.000, 3, True)
            ensure_producto(cur, "Papas Fritas Congeladas (Kg)", 2500.00, "Congelados", 20.000, 5, True)
            
            print("✓ Productos OK")
        except Exception as e:
            print(f"✗ Error en productos: {e}")
            errores += 1
        
        print("\nPASO 7/8: Creando Ventas Históricas (DESCUENTA STOCK)...")
        try:
            ensure_venta_historica(cur, "Consumidor Final", "tomas", 
                                  [("Coca-Cola 1.5L", 2), ("Pan Suelto (Kg)", 0.5), ("Alfajor Jorgito", 3)], 
                                  "efectivo", dias_atras=5)
            
            ensure_venta_historica(cur, "Juan Perez", "caja1", 
                                  [("Milanesa de Pollo (Kg)", 1.2), ("Papas Fritas Congeladas (Kg)", 1), ("Leche Entera 1L", 6)], 
                                  "cuenta_corriente", dias_atras=3)
            
            ensure_venta_historica(cur, "Kiosco 'ElPaso'", "supervisor", 
                                  [("Coca-Cola 1.5L", 12), ("Alfajor Jorgito", 24), ("Papas Fritas Lays 150g", 10)], 
                                  "cuenta_corriente", dias_atras=2)
            
            ensure_venta_historica(cur, "Consumidor Final", "tomas", 
                                  [("Facturas (Docena)", 1)], 
                                  "efectivo", dias_atras=1)
            
            ensure_venta_historica(cur, "Maria Gonzalez", "caja1", 
                                  [("Arroz Gallo Oro 1kg", 5), ("Fideos Matarazzo 500g", 5), ("Aceite Girasol 1.5L", 2)], 
                                  "cuenta_corriente", dias_atras=1)

            print("✓ Ventas Históricas OK")
        except Exception as e:
            print(f"✗ Error en ventas históricas: {e}")
            errores += 1
        
        # --- ¡NUEVO PASO! ---
        print("\nPASO 8/8: Creando Compras Históricas (SUMA STOCK)...")
        try:
            # Compra de bebidas (Costos inventados)
            ensure_compra_historica(cur, "Coca-Cola FEMSA", "supervisor",
                                    [("Coca-Cola 1.5L", 50, 700.00), # (Producto, Cantidad, PrecioCosto)
                                     ("Agua Villavicencio 2L", 40, 400.00)],
                                    dias_atras=10)
            
            # Compra de carnes
            ensure_compra_historica(cur, "Frigorífico Rioplatense", "admin",
                                    [("Asado (Kg)", 20.0, 4500.00),
                                     ("Carne Picada (Kg)", 15.0, 3000.00)],
                                    dias_atras=8)
            
            # Compra de golosinas
            ensure_compra_historica(cur, "Arcor", "admin",
                                    [("Alfajor Jorgito", 100, 250.00),
                                     ("Papas Fritas Lays 150g", 50, 800.00)],
                                    dias_atras=7)

            print("✓ Compras Históricas OK")
        except Exception as e:
            print(f"✗ Error en compras históricas: {e}")
            errores += 1
        
        # --- FIN NUEVO PASO ---
        
        if errores == 0:
            conn.commit()
            print("\n" + "=" * 60)
            print("   ✅ TODOS LOS DATOS INICIALES FUERON CARGADOS")
            print("=" * 60)
        else:
            conn.rollback()
            print("\n" + "=" * 60)
            print(f"   ⚠️  COMPLETADO CON {errores} ERRORES")
            print("=" * 60)
            print("   Los datos se revirtieron. Revisa los errores arriba.")
            sys.exit(1)
            
    except Exception as e:
        if conn:
            try: 
                conn.rollback()
            except: 
                pass
        print("\n❌ Error crítico en seed:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except:
            pass

if __name__ == "__main__":
    main()