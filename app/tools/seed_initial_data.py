# app/tools/seed_initial_data.py
from __future__ import annotations
import sys
import bcrypt
from typing import Optional
try:
    # Usa tu misma conexión del proyecto
    from app.database.DB import conectar
except Exception as e:
    print("ERROR: no se pudo importar app.database.DB.conectar:", e, file=sys.stderr)
    sys.exit(1)


def get_rol_id(cur, nombre: str) -> Optional[int]:
    cur.execute("SELECT id_rol FROM Rol WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    return int(row[0]) if row else None


def ensure_roles(cur) -> None:
    cur.execute("""
        INSERT IGNORE INTO Rol (id_rol, nombre, descripcion) VALUES
        (1, 'admin', 'Administrador del sistema con todos los permisos'),
        (2, 'vendedor', 'Usuario que puede realizar ventas'),
        (3, 'supervisor', 'Usuario que puede gestionar inventario y ver reportes')
    """)
    # Si no soporta INSERT IGNORE por id, intentá por nombre:
    cur.execute("""
        INSERT IGNORE INTO Rol (nombre, descripcion) VALUES
        ('admin','Administrador del sistema con todos los permisos'),
        ('vendedor','Usuario que puede realizar ventas'),
        ('supervisor','Usuario que puede gestionar inventario y ver reportes')
    """)


def user_exists(cur, nombre: str) -> bool:
    cur.execute("SELECT 1 FROM Usuario WHERE nombre=%s", (nombre,))
    return cur.fetchone() is not None


def ensure_user(cur, nombre: str, password: str, rol_nombre: str) -> None:
    rid = get_rol_id(cur, rol_nombre)
    if not rid:
        raise RuntimeError(f"Rol '{rol_nombre}' no existe.")
    if user_exists(cur, nombre):
        return
    # Hash bcrypt (cost 12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    cur.execute(
        "INSERT INTO Usuario (nombre, contraseña, id_rol, activo) VALUES (%s, %s, %s, TRUE)",
        (nombre, hashed, rid),
    )


def main() -> None:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        ensure_roles(cur)

        # Usuarios iniciales
        ensure_user(cur, "admin", "admin123", "admin")
        ensure_user(cur, "vendedor1", "vender123", "vendedor")
        ensure_user(cur, "supervisor", "super123", "supervisor")

        conn.commit()
        print("✅ Seed OK: roles y usuarios iniciales creados (o ya existentes).")
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        print("❌ Error en seed:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
