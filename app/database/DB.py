# app/database/DB.py
from __future__ import annotations

import os
import logging
from typing import Any, Optional

import bcrypt
import mysql.connector
from mysql.connector.connection import MySQLConnection
from dotenv import load_dotenv

# ------------------------------------------------------
# Configuración y logger
# ------------------------------------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "supermercado_don_atilio")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ------------------------------------------------------
# Conexión
# ------------------------------------------------------
def conectar() -> MySQLConnection:
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False,
    )


# ======================================================
# AUTENTICACIÓN
# ======================================================
def verificar_contraseña(usuario: str, contraseña: str) -> Optional[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id_usuario, nombre, contraseña, id_rol, activo FROM Usuario WHERE nombre=%s",
            (usuario,),
        )
        row = cur.fetchone()
        if not row or not row["activo"]:
            return None
        hashed = row["contraseña"].encode("utf-8")
        if bcrypt.checkpw(contraseña.encode("utf-8"), hashed):
            return {"id_usuario": row["id_usuario"], "nombre": row["nombre"], "id_rol": row["id_rol"]}
        return None
    except Exception as e:
        logger.error(f"verificar_contraseña: {e}")
        return None
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


# ======================================================
# CLIENTES
# ======================================================
def insertar_cliente(nombre: str, direccion: str = "", telefono: str = "", email: str = "") -> Optional[int]:
    if not nombre.strip():
        raise ValueError("El nombre del cliente es obligatorio.")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Cliente (nombre, direccion, telefono, email) VALUES (%s,%s,%s,%s)",
            (nombre.strip(), direccion.strip(), telefono.strip(), email.strip() or None),
        )
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"insertar_cliente: {e}")
        return None
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def obtener_clientes() -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id_cliente, nombre, direccion, telefono, email, activo FROM Cliente ORDER BY nombre")
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_clientes: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def buscar_cliente_por_nombre(patron: str) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        like = f"%{patron}%"
        cur.execute(
            "SELECT id_cliente, nombre, direccion, telefono, email FROM Cliente WHERE nombre LIKE %s ORDER BY nombre",
            (like,),
        )
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"buscar_cliente_por_nombre: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


# ======================================================
# CATEGORÍAS
# ======================================================
def obtener_categorias() -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id_categoria, nombre FROM Categoria WHERE activa=1 ORDER BY nombre")
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_categorias: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


# ======================================================
# PRODUCTOS / INVENTARIO (con stock mínimo)
# ======================================================
def insertar_producto(nombre: str, precio: float, id_categoria: Optional[int]) -> Optional[int]:
    """Crea producto + Inventario(0, stock_minimo=5)."""
    if not nombre.strip():
        raise ValueError("El nombre del producto es obligatorio.")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Producto (nombre, precio, id_categoria) VALUES (%s,%s,%s)",
            (nombre.strip(), float(precio), id_categoria),
        )
        pid = cur.lastrowid
        cur.execute("INSERT INTO Inventario (id_producto, cantidad, stock_minimo) VALUES (%s,%s,%s)", (pid, 0, 5))
        conn.commit()
        return pid
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"insertar_producto: {e}")
        return None
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def crear_producto_completo(
    nombre: str, precio: float, id_categoria: Optional[int], stock_inicial: int, stock_minimo: int
) -> Optional[int]:
    """Alta + inventario inicial + stock_minimo."""
    pid = insertar_producto(nombre, precio, id_categoria)
    if not pid:
        return None
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        # set stock_minimo si difiere del default
        cur.execute("UPDATE Inventario SET stock_minimo=%s WHERE id_producto=%s", (int(stock_minimo), pid))
        if stock_inicial:
            cur.execute("UPDATE Inventario SET cantidad=cantidad+%s WHERE id_producto=%s", (int(stock_inicial), pid))
        conn.commit()
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.warning(f"crear_producto_completo.set_min_stock: {e}")
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass
    return pid


def _select_producto_join() -> str:
    return """
        SELECT
            p.id_producto, p.nombre, p.precio, p.codigo_barras, p.id_categoria,
            c.nombre AS nombre_categoria,
            COALESCE(i.cantidad, 0) AS stock,
            COALESCE(i.stock_minimo, 0) AS stock_minimo
        FROM Producto p
        LEFT JOIN Categoria c ON p.id_categoria = c.id_categoria
        LEFT JOIN Inventario i ON p.id_producto = i.id_producto
    """


def buscar_producto_por_nombre(patron: str) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        if not patron:
            cur.execute(_select_producto_join() + " ORDER BY p.id_producto")
            return list(cur.fetchall() or [])
        like = f"%{patron}%"
        cur.execute(_select_producto_join() + " WHERE p.nombre LIKE %s ORDER BY p.nombre", (like,))
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"buscar_producto_por_nombre: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def buscar_producto_por_codigo_barras(codigo: str) -> Optional[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute(_select_producto_join() + " WHERE p.codigo_barras = %s", (codigo,))
        return cur.fetchone()
    except Exception as e:
        logger.error(f"buscar_producto_por_codigo_barras: {e}")
        return None
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def obtener_productos() -> list[dict]:
    return buscar_producto_por_nombre("")


def obtener_inventario() -> list[dict]:
    return buscar_producto_por_nombre("")


def obtener_stock_por_producto(id_producto: int) -> int:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT cantidad FROM Inventario WHERE id_producto = %s", (id_producto,))
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as e:
        logger.error(f"obtener_stock_por_producto: {e}")
        return 0
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def obtener_stock_minimo(id_producto: int) -> int:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT stock_minimo FROM Inventario WHERE id_producto = %s", (id_producto,))
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as e:
        logger.error(f"obtener_stock_minimo: {e}")
        return 0
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def actualizar_stock_minimo(id_producto: int, stock_minimo: int) -> bool:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("UPDATE Inventario SET stock_minimo=%s WHERE id_producto=%s", (int(stock_minimo), id_producto))
        conn.commit()
        return True
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"actualizar_stock_minimo: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def actualizar_inventario_absoluto(id_producto: int, cantidad_abs: int, stock_minimo: Optional[int] = None) -> bool:
    """Setea cantidad absoluta y, opcionalmente, stock_minimo en una sola transacción."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM Inventario WHERE id_producto=%s", (id_producto,))
        if not cur.fetchone():
            cur.execute("INSERT INTO Inventario (id_producto, cantidad, stock_minimo) VALUES (%s,%s,%s)",
                        (id_producto, 0, int(stock_minimo) if stock_minimo is not None else 5))
        if stock_minimo is not None:
            cur.execute(
                "UPDATE Inventario SET cantidad=%s, stock_minimo=%s WHERE id_producto=%s",
                (int(cantidad_abs), int(stock_minimo), id_producto),
            )
        else:
            cur.execute("UPDATE Inventario SET cantidad=%s WHERE id_producto=%s", (int(cantidad_abs), id_producto))
        conn.commit()
        return True
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"actualizar_inventario_absoluto: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def actualizar_producto(
    id_producto: int,
    nombre: Optional[str] = None,
    precio: Optional[float] = None,
    id_categoria: Optional[int] = None,
    codigo_barras: Optional[str] = None,
) -> bool:
    campos: list[str] = []
    params: list[Any] = []

    if nombre is not None:
        campos.append("nombre=%s"); params.append(nombre.strip())
    if precio is not None:
        campos.append("precio=%s"); params.append(float(precio))
    if id_categoria is not None:
        campos.append("id_categoria=%s"); params.append(id_categoria)
    if codigo_barras is not None:
        campos.append("codigo_barras=%s"); params.append(codigo_barras or None)

    if not campos:
        return True

    sql = f"UPDATE Producto SET {', '.join(campos)} WHERE id_producto=%s"
    params.append(id_producto)

    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(sql, tuple(params))
        conn.commit()
        return True
    except mysql.connector.IntegrityError as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.warning(f"actualizar_producto: integridad {e}")
        return False
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"actualizar_producto: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def actualizar_stock(id_producto: int, delta: int, *_compat) -> bool:
    if not isinstance(delta, int):
        raise ValueError("delta debe ser int")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM Inventario WHERE id_producto=%s", (id_producto,))
        if not cur.fetchone():
            cur.execute("INSERT INTO Inventario (id_producto, cantidad, stock_minimo) VALUES (%s,%s,%s)", (id_producto, 0, 5))
        cur.execute("UPDATE Inventario SET cantidad = GREATEST(cantidad + %s, 0) WHERE id_producto=%s", (delta, id_producto))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"actualizar_stock: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def eliminar_producto(id_producto: int) -> bool:
    """
    Baja dura. Requiere:
      - DetalleVenta.id_producto  ON DELETE SET NULL
      - DetalleCompra.id_producto ON DELETE SET NULL
    Inventario cae por ON DELETE CASCADE.
    """
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("DELETE FROM Producto WHERE id_producto=%s", (id_producto,))
        ok = cur.rowcount > 0
        conn.commit()
        return ok
    except mysql.connector.IntegrityError as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"eliminar_producto (FK RESTRICT): {e}")
        return False
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"eliminar_producto: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def obtener_stock_bajo() -> list[dict]:
    """
    Productos con cantidad <= stock_minimo.
    Usa vista 'vista_stock_bajo' si existe; de lo contrario, hace la consulta equivalente.
    """
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        # intentar vista
        try:
            cur.execute("SELECT * FROM vista_stock_bajo ORDER BY cantidad ASC")
            rows = cur.fetchall()
            if rows is not None:
                return list(rows)
        except Exception:
            pass
        # fallback
        cur.execute(
            """
            SELECT
              p.id_producto, p.nombre, p.precio,
              c.nombre AS categoria,
              i.cantidad, i.stock_minimo, (i.stock_minimo - i.cantidad) AS unidades_faltantes
            FROM Producto p
            JOIN Inventario i ON p.id_producto = i.id_producto
            LEFT JOIN Categoria c ON p.id_categoria = c.id_categoria
            WHERE i.cantidad <= i.stock_minimo
            ORDER BY i.cantidad ASC
            """
        )
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_stock_bajo: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


# ======================================================
# VENTAS (con snapshot en detalle)
# ======================================================
def insertar_venta(id_usuario: int, id_cliente: Optional[int]) -> Optional[int]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("INSERT INTO Venta (id_usuario, id_cliente) VALUES (%s,%s)", (id_usuario, id_cliente))
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"insertar_venta: {e}")
        return None
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def insertar_detalle_venta(id_venta: int, id_producto: int, cantidad: int, precio_unitario: float) -> bool:
    if cantidad <= 0 or precio_unitario <= 0:
        raise ValueError("Cantidad y precio_unitario deben ser > 0")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        # stock
        cur.execute("SELECT cantidad FROM Inventario WHERE id_producto=%s", (id_producto,))
        inv = cur.fetchone()
        if not inv or int(inv["cantidad"]) < cantidad:
            raise ValueError(f"Stock insuficiente (disp: {inv['cantidad'] if inv else 0}, req: {cantidad})")
        # snapshot
        cur.execute("SELECT nombre, codigo_barras FROM Producto WHERE id_producto=%s", (id_producto,))
        prod = cur.fetchone()
        if not prod:
            raise ValueError(f"Producto {id_producto} inexistente")
        # insertar
        cur.execute(
            """
            INSERT INTO DetalleVenta (id_venta, id_producto, nombre_producto, codigo_barras, cantidad, precio_unitario)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (id_venta, id_producto, prod["nombre"], prod["codigo_barras"], cantidad, precio_unitario),
        )
        # descuenta
        cur.execute("UPDATE Inventario SET cantidad = cantidad - %s WHERE id_producto=%s", (cantidad, id_producto))
        conn.commit()
        return True
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"insertar_detalle_venta: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


# ======================================================
# REPORTES
# ======================================================
def obtener_vendedores() -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT u.id_usuario, u.nombre
            FROM Usuario u
            JOIN Rol r ON r.id_rol = u.id_rol
            WHERE u.activo = 1 AND r.nombre IN ('vendedor','admin','supervisor')
            ORDER BY u.nombre
            """
        )
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_vendedores: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def reporte_ventas_por_vendedor(desde: str, hasta: str, id_vendedor: Optional[int] = None) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        sql = """
            SELECT v.id_venta, v.fecha, u.id_usuario AS id_vendedor, u.nombre AS vendedor, v.total
            FROM Venta v
            LEFT JOIN Usuario u ON u.id_usuario = v.id_usuario
            WHERE v.fecha BETWEEN %s AND %s
        """
        params: list[Any] = [f"{desde} 00:00:00", f"{hasta} 23:59:59"]
        if id_vendedor:
            sql += " AND v.id_usuario = %s"; params.append(id_vendedor)
        sql += " ORDER BY v.fecha DESC, v.id_venta DESC"
        cur.execute(sql, tuple(params))
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"reporte_ventas_por_vendedor: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def obtener_ventas_diarias(desde: Optional[str] = None, hasta: Optional[str] = None) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        base = """
            SELECT DATE(v.fecha) AS fecha, COUNT(v.id_venta) AS total_ventas, SUM(v.total) AS monto_total
            FROM Venta v
        """
        where = []
        params: list[Any] = []
        if desde:
            where.append("DATE(v.fecha) >= %s"); params.append(desde)
        if hasta:
            where.append("DATE(v.fecha) <= %s"); params.append(hasta)
        if where:
            base += " WHERE " + " AND ".join(where)
        base += " GROUP BY DATE(v.fecha) ORDER BY fecha DESC"
        cur.execute(base, tuple(params))
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_ventas_diarias: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass
