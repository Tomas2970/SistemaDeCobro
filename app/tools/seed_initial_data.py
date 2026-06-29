from __future__ import annotations
import sys
import os
import bcrypt
import mysql.connector 
from typing import Optional

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


# ==========================================
# CONFIGURACIÓN DE CONEXIÓN
# ==========================================
def conectar():
    """Conexión directa sin depender de app.database.DB"""
    from dotenv import load_dotenv
    
    # Cargar .env desde el directorio actual (donde está el .exe)
    load_dotenv()
    
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3307"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "supermercado_don_atilio")
    
    print(f"📡 Conectando a MySQL...")
    print(f"   Host: {DB_HOST}")
    print(f"   Puerto: {DB_PORT}")
    print(f"   Base de datos: {DB_NAME}")
    
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False,
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci"
    )
    
    print("✓ Conexión establecida\n")
    return conn

# ==========================================
# VERIFICACIÓN DE ESTRUCTURA
# ==========================================
def verificar_tablas(cur) -> bool:
    """Verifica que las tablas necesarias existan"""
    print("🔍 Verificando estructura de base de datos...")
    
    tablas_requeridas = ['Rol', 'Usuario', 'Categoria', 'Producto', 'Cliente']
    
    for tabla in tablas_requeridas:
        cur.execute(f"SHOW TABLES LIKE '{tabla}'")
        if not cur.fetchone():
            print(f"   ❌ Tabla '{tabla}' NO EXISTE")
            print("\n🚨 ERROR CRÍTICO:")
            print("   La estructura de la base de datos no está creada.")
            print("\n📋 SOLUCIÓN:")
            print("   1. Ejecuta 'Reparar MySQL' desde el menú Inicio")
            print("   2. O ejecuta manualmente:")
            print("      mysql\\bin\\mysql.exe -u root --port=3307 < schema.sql")
            return False
        print(f"   ✓ {tabla}")
    
    print("   ✅ Todas las tablas necesarias existen\n")
    return True

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================
def get_rol_id(cur, nombre: str) -> Optional[int]:
    cur.execute("SELECT id_rol FROM Rol WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    return int(row[0]) if row else None

def user_exists(cur, nombre: str) -> bool:
    cur.execute("SELECT 1 FROM Usuario WHERE nombre=%s", (nombre,))
    return cur.fetchone() is not None

def categoria_exists(cur, nombre: str) -> bool:
    cur.execute("SELECT 1 FROM Categoria WHERE nombre=%s", (nombre,))
    return cur.fetchone() is not None

# ==========================================
# 1. ROLES (Estructural)
# ==========================================
def ensure_roles(cur) -> None:
    print("📋 Asegurando roles...")
    cur.execute("""
        INSERT IGNORE INTO Rol (id_rol, nombre, descripcion) VALUES
        (1, 'admin', 'Administrador del sistema con todos los permisos'),
        (2, 'vendedor', 'Usuario que puede realizar ventas'),
        (3, 'supervisor', 'Usuario que puede gestionar inventario y ver reportes')
    """)
    print("   ✓ Roles: admin, vendedor, supervisor")

# ==========================================
# 2. USUARIO ADMIN (Acceso inicial)
# ==========================================
def ensure_admin_user(cur) -> None:
    print("\n👤 Verificando usuario administrador...")
    nombre = "admin"
    password = "admin123" 
    
    if user_exists(cur, nombre):
        print(f"   ℹ Usuario '{nombre}' ya existe (actualizando contraseña por seguridad)")
        # Actualizar contraseña por si fue modificada
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
        rid = get_rol_id(cur, "admin")
        cur.execute(
            "UPDATE Usuario SET contraseña=%s, id_rol=%s, activo=TRUE WHERE nombre=%s",
            (hashed, rid, nombre)
        )
        print(f"   ✓ Usuario actualizado: {nombre} / {password}")
        return

    rid = get_rol_id(cur, "admin")
    if not rid:
        print("   ✗ Error: No se encontró el rol 'admin'")
        return

    print(f"   + Creando usuario inicial '{nombre}'...")
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    
    cur.execute(
        "INSERT INTO Usuario (nombre, contraseña, id_rol, activo) VALUES (%s, %s, %s, TRUE)",
        (nombre, hashed, rid),
    )
    print(f"   ✓ Usuario creado: {nombre} / {password}")

# ==========================================
# 3. CATEGORÍAS (Configuración Base)
# ==========================================
def ensure_categorias(cur) -> None:
    print("\n🏷️ Cargando categorías iniciales...")
    
    categorias = [
        (1, 'Bebidas', 30.00),
        (2, 'Almacén', 30.00),
        (3, 'Lácteos', 25.00),
        (4, 'Carnes', 35.00),
        (5, 'Limpieza', 30.00),
        (6, 'Panadería', 40.00),
        (7, 'Congelados', 30.00),
        (8, 'Golosinas', 40.00),
        (9, 'Verdulería', 35.00),
        (99, 'General', 30.00)
    ]

    categorias_insertadas = 0
    for cat_id, nombre, margen in categorias:
        if not categoria_exists(cur, nombre):
            cur.execute(
                """
                INSERT INTO Categoria 
                (nombre, margen_ganancia, activa) 
                VALUES (%s, %s, 1)
                """,
                (nombre, margen)
            )
            print(f"   ✓ {nombre} (margen: {margen}%)")
            categorias_insertadas += 1
        else:
            print(f"   ℹ {nombre} ya existe")
    
    if categorias_insertadas > 0:
        print(f"\n   📦 {categorias_insertadas} categorías nuevas insertadas")
    else:
        print(f"\n   ℹ Todas las categorías ya estaban cargadas")

# ==========================================
# MAIN
# ==========================================
def main() -> None:
    conn = None
    try:
        print("\n" + "="*60)
        print("  CARGA DE DATOS INICIALES - Sistema Don Atilio")
        print("="*60 + "\n")
        
        # Conectar
        conn = conectar()
        cur = conn.cursor(buffered=True)
        
        # 🔥 VERIFICAR QUE EXISTAN LAS TABLAS
        if not verificar_tablas(cur):
            sys.exit(1)
        
        # 1. Roles
        ensure_roles(cur)
        
        # 2. Usuario Admin (para poder entrar)
        ensure_admin_user(cur)
        
        # 3. Categorías (para agilizar carga de productos)
        ensure_categorias(cur)

        # Commit
        conn.commit()
        
        print("\n" + "="*60)
        print("  ✅ CARGA COMPLETADA EXITOSAMENTE")
        print("="*60)
        print("\n📌 Datos cargados:")
        print("   • Roles: admin, vendedor, supervisor")
        print("   • Usuario: admin / admin123")
        print("   • Categorías: 10 categorías predefinidas")
        print("\n💡 El sistema está listo para usarse")
        print("\n🔐 Credenciales de acceso:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")

    except mysql.connector.Error as e:
        if conn: conn.rollback()
        print(f"\n❌ ERROR DE BASE DE DATOS: {e}")
        print(f"\n🔍 Verifica que:")
        print("   1. MySQL esté corriendo (servicio MySQL_DonAtilio)")
        print("   2. El puerto 3307 esté disponible")
        print("   3. La base de datos 'supermercado_don_atilio' exista")
        print("\n💡 Para verificar:")
        print("   sc query MySQL_DonAtilio")
        print("   mysql\\bin\\mysql.exe -u root --port=3307 -e \"SHOW DATABASES;\"")
        sys.exit(1)
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        if conn: 
            conn.close()
            print("\n🔌 Conexión cerrada")

if __name__ == "__main__":
    main()