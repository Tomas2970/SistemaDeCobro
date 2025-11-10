# app/database/DB.py
from __future__ import annotations

import os
import logging # ¡CAMBIO! Mantenemos el import
from typing import Any, Optional

import bcrypt
import mysql.connector
from mysql.connector.connection import MySQLConnection
from dotenv import load_dotenv

# (Configuración y Conexión sin cambios)
# ...
# ------------------------------------------------------
# Configuración y logger
# ------------------------------------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "supermercado_don_atilio")

# --- ¡CAMBIO! ---
# logging.basicConfig(...) # Se elimina esta línea
logger = logging.getLogger(__name__) # Obtenemos el logger configurado en main.py
# --- FIN CAMBIO ---


# ------------------------------------------------------
# Conexión
# ------------------------------------------------------
def conectar() -> MySQLConnection:
    # --- ¡CAMBIO! Añadimos charset y collation ---
    # Esto asegura que la conexión respete el 'utf8mb4_unicode_ci' 
    # de tu base de datos, lo cual maneja acentos y mayúsculas.
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False,
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci"
    )
    # --- FIN CAMBIO ---

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
def insertar_cliente(nombre: str, dni: str = "", direccion: str = "", telefono: str = "", email: str = "", limite_credito: float = 50000.00) -> Optional[int]:
    if not nombre.strip():
        raise ValueError("El nombre del cliente es obligatorio.")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
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
        
        nuevo_id_cliente = cur.lastrowid
        
        try:
            limite_valido = float(limite_credito)
            if limite_valido < 0:
                limite_valido = 50000.00
        except (ValueError, TypeError):
            limite_valido = 50000.00
            
        cur.execute(
            "INSERT IGNORE INTO CuentaCorriente (id_cliente, saldo, limite_credito) VALUES (%s, 0.00, %s)",
            (nuevo_id_cliente, limite_valido)
        )
        
        conn.commit()
        return nuevo_id_cliente
        
    except mysql.connector.IntegrityError as e:
        logger.warning(f"insertar_cliente (IntegrityError): {e}")
        if conn: conn.rollback()
        return None
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

def actualizar_cliente_completo(id_cliente: int, nombre: str, dni: str, direccion: str, telefono: str, email: str, limite_credito: float) -> bool:
    if not nombre.strip():
        raise ValueError("El nombre del cliente es obligatorio.")
    
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        
        conn.start_transaction()
        
        cur.execute(
            """
            UPDATE Cliente 
            SET nombre=%s, dni=%s, direccion=%s, telefono=%s, email=%s
            WHERE id_cliente=%s
            """,
            (
                nombre.strip(),
                dni.strip() or None,
                direccion.strip() or None,
                telefono.strip() or None,
                email.strip() or None,
                id_cliente
            )
        )
        
        cur.execute(
            """
            UPDATE CuentaCorriente
            SET limite_credito=%s
            WHERE id_cliente=%s
            """,
            (float(limite_credito), id_cliente)
        )
        
        conn.commit()
        return True
        
    except mysql.connector.IntegrityError as e:
        logger.warning(f"actualizar_cliente_completo (IntegrityError): {e}")
        if conn: conn.rollback()
        return False
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"actualizar_cliente_completo: {e}")
        return False
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

def obtener_clientes_con_saldos(incluir_inactivos: bool = False) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        sql = """
            SELECT 
                c.id_cliente, c.nombre, c.dni, c.direccion, c.telefono, c.email, c.activo,
                cc.saldo, 
                cc.limite_credito
            FROM Cliente c
            LEFT JOIN CuentaCorriente cc ON c.id_cliente = cc.id_cliente
        """
        if not incluir_inactivos:
            sql += " WHERE c.activo=1"
        sql += " ORDER BY c.nombre"
        cur.execute(sql)
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_clientes_con_saldos: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def obtener_cliente_completo(id_cliente: int) -> Optional[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT 
                c.id_cliente, c.nombre, c.dni, c.direccion, c.telefono, c.email,
                cc.limite_credito
            FROM Cliente c
            LEFT JOIN CuentaCorriente cc ON c.id_cliente = cc.id_cliente
            WHERE c.id_cliente = %s
            """,
            (id_cliente,)
        )
        return cur.fetchone()
    except Exception as e:
        logger.error(f"obtener_cliente_completo: {e}")
        return None
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
        
        # --- ¡CAMBIO! Usamos LOWER() en ambos lados ---
        # La 'collation' de la conexión ya maneja acentos.
        like = f"%{patron}%"
        cur.execute(
            "SELECT id_cliente, nombre, dni, direccion, telefono, email FROM Cliente WHERE LOWER(nombre) LIKE LOWER(%s) AND activo=1 ORDER BY nombre",
            (like,),
        )
        # --- FIN CAMBIO ---
        
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
def insertar_producto(nombre: str, precio: float, id_categoria: Optional[int], es_pesable: bool = False) -> Optional[int]:
    if not nombre.strip():
        raise ValueError("El nombre del producto es obligatorio.")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Producto (nombre, precio, id_categoria, es_pesable) VALUES (%s, %s, %s, %s)",
            (nombre.strip(), float(precio), id_categoria, bool(es_pesable)),
        )
        pid = cur.lastrowid
        cur.execute("INSERT INTO Inventario (id_producto, cantidad, stock_minimo) VALUES (%s, %s, %s)", (pid, 0.000, 5))
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
    nombre: str, precio: float, id_categoria: Optional[int], stock_inicial: float, stock_minimo: int, es_pesable: bool = False
) -> Optional[int]:
    pid = insertar_producto(nombre, precio, id_categoria, es_pesable)
    if not pid:
        return None
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("UPDATE Inventario SET stock_minimo=%s WHERE id_producto=%s", (int(stock_minimo), pid))
        if stock_inicial:
            cur.execute("UPDATE Inventario SET cantidad=cantidad+%s WHERE id_producto=%s", (float(stock_inicial), pid))
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


def _select_producto_campos() -> str:
    return """
        SELECT
            p.id_producto, p.nombre, p.precio, p.es_pesable, 
            p.codigo_barras, p.id_categoria,
            c.nombre AS nombre_categoria,
            COALESCE(i.cantidad, 0.000) AS stock,
            COALESCE(i.stock_minimo, 0) AS stock_minimo
    """

def _select_producto_joins() -> str:
    return """
        FROM Producto p
        LEFT JOIN Categoria c ON p.id_categoria = c.id_categoria
        LEFT JOIN Inventario i ON p.id_producto = i.id_producto
    """

def buscar_producto_por_nombre(patron: str) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        base_sql = _select_producto_campos() + _select_producto_joins() + " WHERE p.activo = 1"
        
        if not patron:
            cur.execute(base_sql + " ORDER BY p.id_producto")
            return list(cur.fetchall() or [])
            
        # --- ¡CAMBIO! Usamos LOWER() en ambos lados ---
        like = f"%{patron}%"
        cur.execute(base_sql + " AND LOWER(p.nombre) LIKE LOWER(%s) ORDER BY p.nombre", (like,))
        # --- FIN CAMBIO ---
        
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
        sql = _select_producto_campos() + _select_producto_joins() + " WHERE p.activo = 1 AND p.codigo_barras = %s"
        cur.execute(sql, (codigo,))
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

def buscar_producto_por_id(id_producto: int) -> Optional[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        sql = _select_producto_campos() + _select_producto_joins() + " WHERE p.activo = 1 AND p.id_producto = %s"
        cur.execute(sql, (id_producto,))
        return cur.fetchone()
    except Exception as e:
        logger.error(f"buscar_producto_por_id: {e}")
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


def obtener_stock_por_producto(id_producto: int) -> float:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT cantidad FROM Inventario WHERE id_producto = %s", (id_producto,))
        row = cur.fetchone()
        return float(row[0]) if row and row[0] is not None else 0.0
    except Exception as e:
        logger.error(f"obtener_stock_por_producto: {e}")
        return 0.0
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


def actualizar_inventario_absoluto(id_producto: int, cantidad_abs: float, stock_minimo: Optional[int] = None) -> bool:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM Inventario WHERE id_producto=%s", (id_producto,))
        if not cur.fetchone():
            cur.execute("INSERT INTO Inventario (id_producto, cantidad, stock_minimo) VALUES (%s,%s,%s)",
                        (id_producto, 0.000, int(stock_minimo) if stock_minimo is not None else 5))
        if stock_minimo is not None:
            cur.execute(
                "UPDATE Inventario SET cantidad=%s, stock_minimo=%s WHERE id_producto=%s",
                (float(cantidad_abs), int(stock_minimo), id_producto),
            )
        else:
            cur.execute("UPDATE Inventario SET cantidad=%s WHERE id_producto=%s", (float(cantidad_abs), id_producto))
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
    es_pesable: Optional[bool] = None 
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
    if es_pesable is not None:
        campos.append("es_pesable=%s"); params.append(bool(es_pesable))

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


def actualizar_stock(id_producto: int, delta: float, *_compat) -> bool:
    if not isinstance(delta, (int, float)):
        raise ValueError("delta debe ser int o float")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM Inventario WHERE id_producto=%s", (id_producto,))
        if not cur.fetchone():
            cur.execute("INSERT INTO Inventario (id_producto, cantidad, stock_minimo) VALUES (%s,%s,%s)", (id_producto, 0.000, 5))
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
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT *, (stock_minimo - cantidad) AS unidades_faltantes FROM vista_stock_bajo ORDER BY unidades_faltantes DESC")
        rows = cur.fetchall()
        return list(rows or [])
    except mysql.connector.Error as e:
        if e.errno == 1146:
            logger.warning("La vista 'vista_stock_bajo' no existe. Ejecutando consulta de fallback.")
            cur.execute(
                """
                SELECT
                  p.id_producto, p.nombre, p.precio, p.es_pesable,
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
        else:
            logger.error(f"obtener_stock_bajo (vista): {e}")
            return []
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
    # ¡Esta función está OBSOLETA! Se reemplaza por 'registrar_venta_completa'
    logger.warning("Llamada a función obsoleta: insertar_venta")
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


def insertar_detalle_venta(id_venta: int, id_producto: int, cantidad: float, precio_unitario: float) -> bool:
    # ¡Esta función está OBSOLETA! Se reemplaza por 'registrar_venta_completa'
    logger.warning("Llamada a función obsoleta: insertar_detalle_venta")
    if cantidad <= 0 or precio_unitario <= 0:
        raise ValueError("Cantidad y precio_unitario deben ser > 0")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        # --- ¡CORRECCIÓN! Agregamos FOR UPDATE para bloquear ---
        cur.execute("SELECT cantidad FROM Inventario WHERE id_producto=%s FOR UPDATE", (id_producto,))
        inv = cur.fetchone()
        stock_actual = float(inv["cantidad"]) if inv else 0.0
        
        if stock_actual < cantidad:
            conn.rollback() # Liberar bloqueo
            raise ValueError(f"Stock insuficiente (disp: {stock_actual:.3f}, req: {cantidad:.3f})")
        
        cur.execute("SELECT nombre, codigo_barras FROM Producto WHERE id_producto=%s", (id_producto,))
        prod = cur.fetchone()
        if not prod:
            raise ValueError(f"Producto {id_producto} inexistente")
        cur.execute(
            """
            INSERT INTO DetalleVenta (id_venta, id_producto, nombre_producto, codigo_barras, cantidad, precio_unitario)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (id_venta, id_producto, prod["nombre"], prod["codigo_barras"], cantidad, precio_unitario),
        )
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

def insertar_detalle_venta_libre(id_venta: int, nombre_producto: str, cantidad: float, precio_unitario: float) -> bool:
    # ¡Esta función está OBSOLETA! Se reemplaza por 'registrar_venta_completa'
    logger.warning("Llamada a función obsoleta: insertar_detalle_venta_libre")
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
    # ¡Esta función está OBSOLETA! Se reemplaza por 'registrar_venta_completa'
    logger.warning("Llamada a función obsoleta: actualizar_pago_y_estado_venta")
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

# --- ¡NUEVA FUNCIÓN ATÓMICA! ---
def registrar_venta_completa(id_usuario: int, id_cliente: int | None, items: list, tipo_pago: str) -> int | None:
    """
    Registra una venta completa (Maestro, Detalles, Stock, C/C) en una sola transacción.
    Si algo falla, revierte todo.
    """
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        # 1. Iniciar transacción
        conn.start_transaction()
        
        # 2. Insertar la venta (con total 0 temporal) y obtener el ID
        cur.execute(
            "INSERT INTO Venta (id_usuario, id_cliente, estado, tipo_pago, total) VALUES (%s, %s, 'completada', %s, 0)", 
            (id_usuario, id_cliente, tipo_pago)
        )
        id_venta = cur.lastrowid
        
        if not id_venta:
            raise RuntimeError("No se pudo crear el registro de Venta.")
            
        total_real = 0.0
        
        # 3. Recorrer items, validar stock e insertar detalles
        for (id_producto, nombre, cant, precio, _) in items:
            
            # Si el item no tiene ID (venta libre), solo lo insertamos
            if id_producto is None:
                cur.execute(
                    """
                    INSERT INTO DetalleVenta (id_venta, id_producto, nombre_producto, codigo_barras, cantidad, precio_unitario)
                    VALUES (%s, NULL, %s, NULL, %s, %s)
                    """,
                    (id_venta, nombre, cant, precio),
                )
            else:
                # --- ¡CORRECCIÓN DE CONCURRENCIA! ---
                # 1. Bloquear la fila de inventario
                cur.execute("SELECT cantidad FROM Inventario WHERE id_producto=%s FOR UPDATE", (id_producto,))
                # --- FIN CORRECCIÓN ---
                
                inv = cur.fetchone()
                stock_actual = float(inv["cantidad"]) if inv else 0.0
                
                if stock_actual < cant:
                    # (El rollback automático liberará el bloqueo)
                    raise ValueError(f"Stock insuficiente para '{nombre}' (disp: {stock_actual:.3f}, req: {cant:.3f})")
                
                # 2. Insertar detalle
                cur.execute(
                    """
                    INSERT INTO DetalleVenta (id_venta, id_producto, nombre_producto, cantidad, precio_unitario)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (id_venta, id_producto, nombre, cant, precio),
                )
                
                # 3. Descontar stock (la fila ya está bloqueada)
                cur.execute("UPDATE Inventario SET cantidad = cantidad - %s WHERE id_producto=%s", (cant, id_producto))
            
            total_real += (cant * precio)

        # 4. Actualizar el total real en la Venta
        cur.execute("UPDATE Venta SET total = %s WHERE id_venta = %s", (total_real, id_venta))
        
        # 5. Si es Cuenta Corriente, actualizar el saldo
        if tipo_pago == "cuenta_corriente" and id_cliente is not None:
            # --- ¡CORRECCIÓN DE CONCURRENCIA! ---
            cur.execute("SELECT saldo, limite_credito FROM CuentaCorriente WHERE id_cliente = %s FOR UPDATE", (id_cliente,))
            # --- FIN CORRECCIÓN ---
            
            cuenta = cur.fetchone()
            
            if not cuenta:
                raise RuntimeError(f"El cliente {id_cliente} no tiene cuenta corriente.")
            
            saldo_proyectado = float(cuenta['saldo']) - total_real
            
            if saldo_proyectado < -float(cuenta['limite_credito']):
                raise ValueError(f"Límite de crédito excedido. (Disponible: {float(cuenta['limite_credito']) + float(cuenta['saldo']):.2f})")
            
            cur.execute("UPDATE CuentaCorriente SET saldo = %s WHERE id_cliente = %s", (saldo_proyectado, id_cliente))

        # 6. Si todo salió bien, confirmar (esto libera todos los bloqueos 'FOR UPDATE')
        conn.commit()
        return id_venta
        
    except Exception as e:
        if conn:
            try: conn.rollback() # Liberar bloqueos en caso de error
            except Exception: pass
        logger.error(f"Error en registrar_venta_completa (TRANSACCIÓN REVERTIDA): {e}")
        raise # Re-lanzamos el error para que el adapter lo capture
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass
# --- FIN NUEVA FUNCIÓN ---


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
            SELECT 
                u.nombre AS vendedor,
                COUNT(v.id_venta) AS total_ventas,
                SUM(v.total) AS monto_total
            FROM Venta v
            JOIN Usuario u ON u.id_usuario = v.id_usuario
            WHERE v.fecha BETWEEN %s AND %s AND v.estado = 'completada'
        """
        params: list[Any] = [f"{desde} 00:00:00", f"{hasta} 23:59:59"]
        
        if id_vendedor:
            sql += " AND v.id_usuario = %s"
            params.append(id_vendedor)
            
        sql += " GROUP BY u.id_usuario, u.nombre ORDER BY monto_total DESC"
        
        cur.execute(sql, tuple(params))
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"reporte_ventas_por_vendedor (agrupado): {e}")
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

def insertar_proveedor(nombre: str, empresa: str = "", telefono: str = "", email: str = "") -> Optional[int]:
    if not nombre.strip():
        raise ValueError("El nombre del proveedor es obligatorio.")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Proveedor (nombre, empresa, telefono, email, activo) VALUES (%s, %s, %s, %s, TRUE)",
            (
                nombre.strip(), 
                empresa.strip() or None,
                telefono.strip() or None, 
                email.strip() or None
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

def actualizar_proveedor(id_proveedor: int, nombre: str, empresa: str, telefono: str, email: str) -> bool:
    if not nombre.strip():
        raise ValueError("El nombre del proveedor es obligatorio.")
    
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE Proveedor
            SET nombre=%s, empresa=%s, telefono=%s, email=%s
            WHERE id_proveedor=%s
            """,
            (
                nombre.strip(),
                empresa.strip() or None,
                telefono.strip() or None,
                email.strip() or None,
                id_proveedor
            )
        )
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"actualizar_proveedor: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def obtener_proveedor_completo(id_proveedor: int) -> Optional[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id_proveedor, nombre, empresa, telefono, email FROM Proveedor WHERE id_proveedor = %s",
            (id_proveedor,)
        )
        return cur.fetchone()
    except Exception as e:
        logger.error(f"obtener_proveedor_completo: {e}")
        return None
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def eliminar_proveedor_logico(id_proveedor: int) -> bool:
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

def obtener_productos_por_proveedor(id_proveedor: int) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        sql = (
            _select_producto_campos() + 
            _select_producto_joins() +
            " JOIN Proveedor_Producto pp ON p.id_producto = pp.id_producto "
            " WHERE pp.id_proveedor = %s AND p.activo = 1 ORDER BY p.nombre"
        )
        
        cur.execute(sql, (id_proveedor,))
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_productos_por_proveedor: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def obtener_productos_sin_asignar(id_proveedor: int) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        sql = (
            _select_producto_campos() +
            _select_producto_joins() +
            " WHERE p.activo = 1 AND p.id_producto NOT IN ( "
            "   SELECT id_producto FROM Proveedor_Producto WHERE id_proveedor = %s "
            " ) ORDER BY p.nombre"
        )
        
        cur.execute(sql, (id_proveedor,))
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_productos_sin_asignar: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def asignar_producto_a_proveedor(id_proveedor: int, id_producto: int) -> bool:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            "INSERT IGNORE INTO Proveedor_Producto (id_proveedor, id_producto) VALUES (%s, %s)",
            (id_proveedor, id_producto)
        )
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"asignar_producto_a_proveedor: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception: pass

def quitar_producto_a_proveedor(id_proveedor: int, id_producto: int) -> bool:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM Proveedor_Producto WHERE id_proveedor = %s AND id_producto = %s",
            (id_proveedor, id_producto)
        )
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"quitar_producto_a_proveedor: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception: pass


# ======================================================
# COMPRAS (Ingreso de mercadería)
# ======================================================
def insertar_compra(id_usuario: int, id_proveedor: int) -> Optional[int]:
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

def insertar_detalle_compra(id_compra: int, id_producto: int, cantidad: float, precio_costo: float) -> bool:
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
        
        # --- ¡CORRECCIÓN! Suma de stock en compra (float) ---
        cur.execute("UPDATE Inventario SET cantidad = cantidad + %s WHERE id_producto=%s", (float(cantidad), id_producto))
        
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
            if id_cliente == 0: 
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
        return None 
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
    # ======================================================
# AUDITORÍA DE ACCIONES (agregar al final de DB.py)
# ======================================================
def registrar_auditoria(
    id_usuario: Optional[int],
    accion: str,
    tabla_afectada: Optional[str] = None,
    id_registro: Optional[int] = None,
    datos_anteriores: Optional[dict] = None,
    datos_nuevos: Optional[dict] = None
) -> bool:
    """
    Registra una acción en la tabla AuditoriaAcciones
    
    Args:
        id_usuario: ID del usuario que realizó la acción
        accion: Descripción de la acción (ej: 'CREAR_PRODUCTO')
        tabla_afectada: Tabla afectada (ej: 'Producto')
        id_registro: ID del registro afectado
        datos_anteriores: Dict con datos antes del cambio
        datos_nuevos: Dict con datos después del cambio
    
    Returns:
        True si se registró correctamente, False si falló
    """
    import json
    
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        
        # Convertir dicts a JSON
        datos_ant_json = json.dumps(datos_anteriores, ensure_ascii=False) if datos_anteriores else None
        datos_new_json = json.dumps(datos_nuevos, ensure_ascii=False) if datos_nuevos else None
        
        cur.execute(
            """
            INSERT INTO AuditoriaAcciones 
            (id_usuario, accion, tabla_afectada, id_registro, datos_anteriores, datos_nuevos)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (id_usuario, accion, tabla_afectada, id_registro, datos_ant_json, datos_new_json)
        )
        
        conn.commit()
        return True
        
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"registrar_auditoria: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass