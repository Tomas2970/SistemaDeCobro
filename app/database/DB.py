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
DB_PORT = int(os.getenv("DB_PORT", "3307"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tomas")
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
def insertar_cliente(nombre: str, dni: str = "", direccion: str = "", telefono: str = "", email: str = "") -> Optional[int]:
    if not nombre.strip():
        raise ValueError("El nombre del cliente es obligatorio.")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        # Convierte strings vacíos "" a None (NULL) para la BD (Arregla chk_1)
        cur.execute(
            "INSERT INTO Cliente (nombre, dni, direccion, telefono, email) VALUES (%s,%s,%s,%s,%s)",
            (
                nombre.strip(), 
                dni.strip() or None,
                direccion.strip() or None, 
                telefono.strip() or None, 
                email.strip() or None
            ),
        )
        conn.commit()
        return cur.lastrowid
    except mysql.connector.IntegrityError as e:
        logger.warning(f"insertar_cliente (IntegrityError): {e}")
        if conn: conn.rollback()
        return None # Devuelve None si el DNI o email ya existe
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


def obtener_clientes(incluir_inactivos: bool = False) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        sql = "SELECT id_cliente, nombre, dni, direccion, telefono, email, activo FROM Cliente"
        if not incluir_inactivos:
            sql += " WHERE activo=1"
        sql += " ORDER BY nombre"
        cur.execute(sql)
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
            "SELECT id_cliente, nombre, dni, direccion, telefono, email FROM Cliente WHERE nombre LIKE %s AND activo=1 ORDER BY nombre",
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

def buscar_cliente_por_dni(dni: str) -> Optional[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id_cliente, nombre, dni, direccion, telefono, email FROM Cliente WHERE dni = %s AND activo=1",
            (dni,),
        )
        return cur.fetchone()
    except Exception as e:
        logger.error(f"buscar_cliente_por_dni: {e}")
        return None
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def eliminar_cliente_logico(id_cliente: int) -> bool:
    """Desactiva un cliente (baja lógica)."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("UPDATE Cliente SET activo=FALSE WHERE id_cliente=%s", (id_cliente,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"eliminar_cliente_logico: {e}")
        return False
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
# PRODUCTOS / INVENTARIO
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
    # --- FILTRA POR p.activo = 1 ---
    return """
        SELECT
            p.id_producto, p.nombre, p.precio, p.codigo_barras, p.id_categoria,
            c.nombre AS nombre_categoria,
            COALESCE(i.cantidad, 0) AS stock,
            COALESCE(i.stock_minimo, 0) AS stock_minimo
        FROM Producto p
        LEFT JOIN Categoria c ON p.id_categoria = c.id_categoria
        LEFT JOIN Inventario i ON p.id_producto = i.id_producto
        WHERE p.activo = 1
    """


def buscar_producto_por_nombre(patron: str) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        base_sql = _select_producto_join()
        if not patron:
            cur.execute(base_sql + " ORDER BY p.id_producto")
            return list(cur.fetchall() or [])
        like = f"%{patron}%"
        cur.execute(base_sql + " AND p.nombre LIKE %s ORDER BY p.nombre", (like,))
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
        cur.execute(_select_producto_join() + " AND p.codigo_barras = %s", (codigo,))
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
    """Baja lógica: setea activo=FALSE en Producto."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("UPDATE Producto SET activo=FALSE WHERE id_producto=%s", (id_producto,))
        ok = cur.rowcount > 0
        conn.commit()
        return ok
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"eliminar_producto (lógico): {e}")
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
            WHERE i.cantidad <= i.stock_minimo AND p.activo = 1
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
        cur.execute(
            "INSERT INTO Venta (id_usuario, id_cliente, estado, tipo_pago) VALUES (%s,%s, 'pendiente', 'efectivo')", 
            (id_usuario, id_cliente)
        )
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

def insertar_detalle_venta_libre(id_venta: int, nombre_producto: str, cantidad: int, precio_unitario: float) -> bool:
    """Inserta un item manual (sin ID) en DetalleVenta. NO toca stock."""
    if cantidad <= 0 or precio_unitario <= 0:
        raise ValueError("Cantidad y precio_unitario deben ser > 0")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO DetalleVenta (id_venta, id_producto, nombre_producto, codigo_barras, cantidad, precio_unitario)
            VALUES (%s, NULL, %s, NULL, %s, %s)
            """,
            (id_venta, nombre_producto, cantidad, precio_unitario),
        )
        conn.commit()
        return True
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"insertar_detalle_venta_libre: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def actualizar_pago_y_estado_venta(id_venta: int, tipo_pago: str, estado: str = "completada") -> bool:
    """
    Actualiza el tipo de pago y el estado de una venta.
    ¡Esto dispara el trigger 'trg_venta_au_cuentacorriente' si el tipo_pago es 'cuenta_corriente'!
    """
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            "UPDATE Venta SET tipo_pago = %s, estado = %s WHERE id_venta = %s",
            (tipo_pago, estado, id_venta)
        )
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"actualizar_pago_y_estado_venta: {e}")
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
            WHERE v.fecha BETWEEN %s AND %s AND v.estado = 'completada'
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
        where = ["v.estado = 'completada'"]
        params: list[Any] = []
        if desde:
            where.append("DATE(v.fecha) >= %s"); params.append(desde)
        if hasta:
            where.append("DATE(v.fecha) <= %s"); params.append(hasta)
        
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

# ======================================================
# PROVEEDORES
# ======================================================
def obtener_proveedores(incluir_inactivos: bool = False) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        sql = "SELECT id_proveedor, nombre, empresa, telefono, email, activo FROM Proveedor"
        if not incluir_inactivos:
            sql += " WHERE activo=1"
        sql += " ORDER BY nombre"
        cur.execute(sql)
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_proveedores: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def insertar_proveedor(nombre: str, empresa: str = "", telefono: str = "", email: str = "", contacto: str = "") -> Optional[int]:
    """Crea un nuevo proveedor y devuelve su ID."""
    if not nombre.strip():
        raise ValueError("El nombre del proveedor es obligatorio.")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Proveedor (nombre, empresa, telefono, email, contacto, activo) VALUES (%s, %s, %s, %s, %s, TRUE)",
            (
                nombre.strip(), 
                empresa.strip() or None,
                telefono.strip() or None, 
                email.strip() or None, 
                contacto.strip() or None
            ),
        )
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"insertar_proveedor: {e}")
        return None
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def eliminar_proveedor_logico(id_proveedor: int) -> bool:
    """Desactiva un proveedor (baja lógica)."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("UPDATE Proveedor SET activo=FALSE WHERE id_proveedor=%s", (id_proveedor,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"eliminar_proveedor_logico: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

# ======================================================
# COMPRAS (Ingreso de mercadería)
# ======================================================
def insertar_compra(id_usuario: int, id_proveedor: int) -> Optional[int]:
    """Crea el registro maestro 'Compra' y devuelve el ID."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Compra (id_usuario, id_proveedor, estado) VALUES (%s, %s, 'recibida')",
            (id_usuario, id_proveedor)
        )
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"insertar_compra: {e}")
        return None
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def insertar_detalle_compra(id_compra: int, id_producto: int, cantidad: int, precio_costo: float) -> bool:
    """Inserta un item en DetalleCompra Y SUMA EL STOCK en Inventario."""
    if cantidad <= 0 or precio_costo < 0:
        raise ValueError("Cantidad debe ser > 0 y precio_costo >= 0")
    
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("SELECT nombre, codigo_barras FROM Producto WHERE id_producto=%s", (id_producto,))
        prod = cur.fetchone()
        if not prod:
            raise ValueError(f"Producto {id_producto} inexistente")

        cur.execute(
            """
            INSERT INTO DetalleCompra (id_compra, id_producto, nombre_producto, codigo_barras, cantidad, precio_unitario)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (id_compra, id_producto, prod["nombre"], prod["codigo_barras"], cantidad, precio_costo),
        )
        
        cur.execute("UPDATE Inventario SET cantidad = cantidad + %s WHERE id_producto=%s", (cantidad, id_producto))
        
        conn.commit()
        return True
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"insertar_detalle_compra: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


# ======================================================
# HISTORIAL DE VENTAS
# ======================================================
def obtener_ventas_maestro(
    fecha_desde: Optional[str], 
    fecha_hasta: Optional[str], 
    id_cliente: Optional[int], 
    id_vendedor: Optional[int]
) -> list[dict]:
    """
    Busca ventas (maestro) con filtros dinámicos.
    id_cliente = 0 busca Consumidor Final (NULL).
    """
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        sql = """
            SELECT
                v.id_venta, v.fecha, v.total, v.estado, v.tipo_pago,
                u.nombre AS vendedor,
                c.nombre AS cliente
            FROM Venta v
            LEFT JOIN Usuario u ON v.id_usuario = u.id_usuario
            LEFT JOIN Cliente c ON v.id_cliente = c.id_cliente
        """
        
        where_clauses = []
        params = []
        
        if fecha_desde:
            where_clauses.append("DATE(v.fecha) >= %s")
            params.append(fecha_desde)
        if fecha_hasta:
            where_clauses.append("DATE(v.fecha) <= %s")
            params.append(fecha_hasta)
        if id_vendedor is not None:
            where_clauses.append("v.id_usuario = %s")
            params.append(id_vendedor)
        
        if id_cliente is not None:
            if id_cliente == 0: # Caso especial para Consumidor Final
                where_clauses.append("v.id_cliente IS NULL")
            else:
                where_clauses.append("v.id_cliente = %s")
                params.append(id_cliente)
                
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
            
        sql += " ORDER BY v.fecha DESC, v.id_venta DESC"
        
        cur.execute(sql, tuple(params))
        return list(cur.fetchall() or [])
        
    except Exception as e:
        logger.error(f"obtener_ventas_maestro: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def obtener_venta_detalle(id_venta: int) -> list[dict]:
    """Obtiene los productos (detalle) de una venta específica."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT
                dv.id_producto,
                dv.nombre_producto,
                dv.codigo_barras,
                dv.cantidad,
                dv.precio_unitario,
                dv.subtotal
            FROM DetalleVenta dv
            WHERE dv.id_venta = %s
            ORDER BY dv.id_detalle_venta ASC
            """,
            (id_venta,)
        )
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_venta_detalle: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

# ======================================================
# HISTORIAL DE COMPRAS
# ======================================================
def obtener_compras_maestro(
    fecha_desde: Optional[str], 
    fecha_hasta: Optional[str], 
    id_proveedor: Optional[int]
) -> list[dict]:
    """Busca compras (maestro) con filtros dinámicos."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        sql = """
            SELECT
                c.id_compra, c.fecha, c.total, c.estado,
                p.nombre AS proveedor,
                u.nombre AS usuario
            FROM Compra c
            LEFT JOIN Proveedor p ON c.id_proveedor = p.id_proveedor
            LEFT JOIN Usuario u ON c.id_usuario = u.id_usuario
        """
        
        where_clauses = []
        params = []
        
        if fecha_desde:
            where_clauses.append("DATE(c.fecha) >= %s")
            params.append(fecha_desde)
        if fecha_hasta:
            where_clauses.append("DATE(c.fecha) <= %s")
            params.append(fecha_hasta)
        if id_proveedor is not None:
            where_clauses.append("c.id_proveedor = %s")
            params.append(id_proveedor)
                
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
            
        sql += " ORDER BY c.fecha DESC, c.id_compra DESC"
        
        cur.execute(sql, tuple(params))
        return list(cur.fetchall() or [])
        
    except Exception as e:
        logger.error(f"obtener_compras_maestro: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def obtener_compra_detalle(id_compra: int) -> list[dict]:
    """Obtiene los productos (detalle) de una compra específica."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT
                dc.id_producto,
                dc.nombre_producto,
                dc.codigo_barras,
                dc.cantidad,
                dc.precio_unitario,
                dc.subtotal
            FROM DetalleCompra dc
            WHERE dc.id_compra = %s
            ORDER BY dc.id_detalle_compra ASC
            """,
            (id_compra,)
        )
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_compra_detalle: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

# ======================================================
# CUENTA CORRIENTE
# ======================================================
def obtener_clientes_con_deuda() -> list[dict]:
    """Obtiene clientes y su saldo de la vista vista_clientes_deuda."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM vista_clientes_deuda ORDER BY saldo ASC")
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_clientes_con_deuda: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def crear_cuenta_corriente_si_no_existe(id_cliente: int) -> bool:
    """Crea una CC para un cliente si no la tiene. Usa INSERT IGNORE."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            "INSERT IGNORE INTO CuentaCorriente (id_cliente, limite_credito) VALUES (%s, 50000.00)",
            (id_cliente,)
        )
        conn.commit()
        return True
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"crear_cuenta_corriente_si_no_existe: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def obtener_cuenta_por_cliente(id_cliente: int) -> Optional[dict]:
    """Obtiene los datos de la CC de un cliente."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM CuentaCorriente WHERE id_cliente = %s", (id_cliente,))
        return cur.fetchone()
    except Exception as e:
        logger.error(f"obtener_cuenta_por_cliente: {e}")
        return None
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def registrar_pago_cuenta_corriente(id_cuenta: int, monto: float, metodo: str, id_usuario: int) -> bool:
    """Registra un pago y actualiza el saldo en una transacción."""
    if monto <= 0:
        raise ValueError("El monto del pago debe ser positivo.")
    
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO Pago (id_cuenta, monto, metodo, id_usuario) VALUES (%s, %s, %s, %s)",
            (id_cuenta, monto, metodo, id_usuario)
        )
        
        cur.execute(
            "UPDATE CuentaCorriente SET saldo = saldo + %s WHERE id_cuenta = %s",
            (monto, id_cuenta)
        )
        
        conn.commit()
        return True
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"registrar_pago_cuenta_corriente: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

# ======================================================
# GESTIÓN DE USUARIOS
# ======================================================
def _hash_password(password: str) -> str:
    """Genera un hash bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

def obtener_usuarios_con_rol() -> list[dict]:
    """Obtiene todos los usuarios (incluyendo inactivos) con el nombre de su rol."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT 
                u.id_usuario, u.nombre, u.id_rol, u.activo,
                r.nombre AS rol_nombre
            FROM Usuario u
            LEFT JOIN Rol r ON u.id_rol = r.id_rol
            ORDER BY u.nombre
        """)
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_usuarios_con_rol: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def obtener_roles() -> list[dict]:
    """Obtiene la lista de todos los roles (ID y Nombre)."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id_rol, nombre FROM Rol ORDER BY nombre")
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_roles: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def crear_usuario(nombre: str, password_plana: str, id_rol: int) -> Optional[int]:
    """Crea un nuevo usuario con contraseña hasheada."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        
        hashed_pass = _hash_password(password_plana)
        
        cur.execute(
            "INSERT INTO Usuario (nombre, contraseña, id_rol, activo) VALUES (%s, %s, %s, TRUE)",
            (nombre.strip(), hashed_pass, id_rol)
        )
        conn.commit()
        return cur.lastrowid
    except mysql.connector.IntegrityError as e:
        logger.warning(f"crear_usuario (IntegrityError): {e}")
        if conn: conn.rollback()
        return None # Nombre de usuario ya existe
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"crear_usuario: {e}")
        return None
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def actualizar_rol_usuario(id_usuario: int, id_rol_nuevo: int) -> bool:
    """Actualiza el rol de un usuario existente."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("UPDATE Usuario SET id_rol=%s WHERE id_usuario=%s", (id_rol_nuevo, id_usuario))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"actualizar_rol_usuario: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def resetear_password_usuario(id_usuario: int, password_plana_nueva: str) -> bool:
    """Actualiza la contraseña de un usuario."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        
        hashed_pass = _hash_password(password_plana_nueva)
        
        cur.execute("UPDATE Usuario SET contraseña=%s WHERE id_usuario=%s", (hashed_pass, id_usuario))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"resetear_password_usuario: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def desactivar_usuario(id_usuario: int) -> bool:
    """Desactiva un usuario (baja lógica)."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("UPDATE Usuario SET activo=FALSE WHERE id_usuario=%s", (id_usuario,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"desactivar_usuario: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass
