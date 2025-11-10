# app/tools/seed_initial_data.py
from __future__ import annotations
import sys
import bcrypt
import mysql.connector 
from typing import Optional

try:
    from app.database.DB import conectar
except Exception as e:
    print("ERROR: no se pudo importar app.database.DB.conectar:", e, file=sys.stderr)
    print("Asegúrate de ejecutar esto como un módulo desde la raíz: python -m app.tools.seed_initial_data", file=sys.stderr)
    sys.exit(1)

# ==========================================
# ROLES
# ==========================================
def get_rol_id(cur, nombre: str) -> Optional[int]:
    cur.execute("SELECT id_rol FROM Rol WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    return int(row[0]) if row else None

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
        print(f"  - Usuario '{nombre}' ya existe. Omitiendo.")
        return
        
    print(f"  + Creando usuario '{nombre}'...")
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    cur.execute(
        "INSERT INTO Usuario (nombre, contraseña, id_rol, activo) VALUES (%s, %s, %s, TRUE)",
        (nombre, hashed, rid),
    )

# ==========================================
# CATEGORÍAS
# ==========================================
def get_categoria_id(cur, nombre: str) -> Optional[int]:
    cur.execute("SELECT id_categoria FROM Categoria WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    return int(row[0]) if row else None

def ensure_categorias(cur) -> None:
    print("Asegurando categorías iniciales...")
    cur.execute("""
        INSERT IGNORE INTO Categoria (id_categoria, nombre, descripcion) VALUES
        (1, 'Bebidas', 'Bebidas alcohólicas y no alcohólicas'),
        (2, 'Almacén', 'Productos de almacén y despensa'),
        (3, 'Lácteos', 'Productos lácteos y derivados'),
        (4, 'Carnes', 'Carnes y embutidos'),
        (5, 'Limpieza', 'Productos de limpieza e higiene'),
        (6, 'Panadería', 'Productos de panadería y pastelería'),
        (99, 'General', 'Productos sin categoría específica')
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
            print(f"  + Proveedor '{nombre}' creado")
    except mysql.connector.Error as e:
        print(f"  ! Error al crear proveedor '{nombre}': {e}")

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
        print(f"  + Cliente '{nombre}' creado")
    except mysql.connector.Error as e:
        if e.errno == 1062:
            print(f"  - Cliente '{nombre}' ya existe. Omitiendo.")
        else:
            print(f"  ! Error al crear cliente '{nombre}': {e}")

# ==========================================
# PRODUCTOS
# ==========================================
def ensure_producto(cur, nombre: str, precio: float, categoria: str, stock_inicial: float, stock_min: int, es_pesable: bool, codigo: str = "") -> None:
    id_cat = get_categoria_id(cur, categoria)
    if not id_cat:
        print(f"  ! ADVERTENCIA: Categoría '{categoria}' no encontrada. Usando 'General'.")
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
        print(f"  + Producto '{nombre}' creado")
    except mysql.connector.Error as e:
        if e.errno == 1062:
            print(f"  - Producto '{nombre}' ya existe. Omitiendo.")
        else:
            print(f"  ! Error al crear producto '{nombre}': {e}")

# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================
def main() -> None:
    conn = cur = None
    errores = 0
    
    try:
        conn = conectar()
        cur = conn.cursor()
        
        print("=" * 60)
        print("  CARGA DE DATOS INICIALES - Don Atilio")
        print("=" * 60)
        print()

        print("PASO 1/6: Asegurando Roles...")
        try:
            ensure_roles(cur)
            print("✓ Roles OK")
        except Exception as e:
            print(f"✗ Error en roles: {e}")
            errores += 1

        print("\nPASO 2/6: Asegurando Usuarios...")
        try:
            ensure_user(cur, "admin", "admin123", "admin")
            ensure_user(cur, "tomas", "tomas123", "vendedor")
            ensure_user(cur, "supervisor", "super123", "supervisor")
            print("✓ Usuarios OK")
        except Exception as e:
            print(f"✗ Error en usuarios: {e}")
            errores += 1

        print("\nPASO 3/6: Asegurando Categorías...")
        try:
            ensure_categorias(cur)
            print("✓ Categorías OK")
        except Exception as e:
            print(f"✗ Error en categorías: {e}")
            errores += 1
        
        print("\nPASO 4/6: Asegurando Proveedores...")
        try:
            ensure_proveedor(cur, "Proveedor General", "S/D", "S/D", "general@proveedor.com")
            ensure_proveedor(cur, "Coca-Cola FEMSA", "Coca-Cola", "0800-123-4567", "pedidos@coca.com")
            ensure_proveedor(cur, "Panadería El Sol", "El Sol SRL", "456-7890", "pan@elsol.com")
            print("✓ Proveedores OK")
        except Exception as e:
            print(f"✗ Error en proveedores: {e}")
            errores += 1
        
        print("\nPASO 5/6: Asegurando Clientes...")
        try:
            ensure_cliente(cur, "Consumidor Final", "00000000", 0.00)
            ensure_cliente(cur, "Juan Perez", "30123456", 75000.00)
            print("✓ Clientes OK")
        except Exception as e:
            print(f"✗ Error en clientes: {e}")
            errores += 1
        
        print("\nPASO 6/6: Asegurando Productos...")
        try:
            ensure_producto(cur, "Coca-Cola 1.5L", 1200.00, "Bebidas", 50, 10, False, "7790123456789")
            ensure_producto(cur, "Leche Entera 1L", 800.00, "Lácteos", 30, 5, False, "7790987654321")
            ensure_producto(cur, "Pan Suelto (Kg)", 1500.00, "Panadería", 10.000, 2, True)
            ensure_producto(cur, "Milanesa de Pollo (Kg)", 4500.00, "Carnes", 5.500, 1, True)
            ensure_producto(cur, "Lavandina 1L", 650.00, "Limpieza", 40, 10, False, "7791111222233")
            print("✓ Productos OK")
        except Exception as e:
            print(f"✗ Error en productos: {e}")
            errores += 1
        
        if errores == 0:
            conn.commit()
            print("\n" + "=" * 60)
            print("  ✅ TODOS LOS DATOS INICIALES FUERON CARGADOS")
            print("=" * 60)
        else:
            conn.rollback()
            print("\n" + "=" * 60)
            print(f"  ⚠️  COMPLETADO CON {errores} ERRORES")
            print("=" * 60)
            print("  Los datos se revirtieron. Revisa los errores arriba.")
        
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