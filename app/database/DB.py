
from __future__ import annotations 

import os
import logging 
from typing import Any, Optional
import json
from datetime import date, datetime

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
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci"
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
def insertar_cliente(nombre: str, dni: str = "", cuit: str = "", direccion: str = "", telefono: str = "", email: str = "", limite_credito: float = 50000.00) -> Optional[int]:
    if not nombre.strip(): raise ValueError("El nombre es obligatorio.")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        # Asumiendo que la columna CUIT fue añadida a la tabla Cliente
        cur.execute(
            "INSERT INTO Cliente (nombre, dni, cuit, direccion, telefono, email) VALUES (%s,%s,%s,%s,%s,%s)",
            (nombre.strip(), dni.strip() or None, cuit.strip() or None, direccion.strip() or None, telefono.strip() or None, email.strip() or None),
        )
        cid = cur.lastrowid
        cur.execute("INSERT IGNORE INTO CuentaCorriente (id_cliente, saldo, limite_credito) VALUES (%s, 0.00, %s)", (cid, float(limite_credito)))
        conn.commit()
        return cid
    except mysql.connector.IntegrityError as e:
        if conn: conn.rollback()
        if getattr(e, "errno", None) == 1062:
            msg = str(e).lower()
            if "dni" in msg: raise ValueError("DNI_DUPLICADO") from e
            if "email" in msg: raise ValueError("EMAIL_DUPLICADO") from e
        return None
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"insertar_cliente: {e}")
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()

def actualizar_cliente_completo(id_cliente: int, nombre: str, dni: str, cuit: str, direccion: str, telefono: str, email: str, limite_credito: float) -> bool:
    if not nombre.strip(): raise ValueError("Nombre obligatorio.")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        conn.start_transaction()
        # Asumiendo que la columna CUIT fue añadida a la tabla Cliente
        cur.execute(
            "UPDATE Cliente SET nombre=%s, dni=%s, cuit=%s, direccion=%s, telefono=%s, email=%s WHERE id_cliente=%s",
            (nombre.strip(), dni.strip() or None, cuit.strip() or None, direccion.strip() or None, telefono.strip() or None, email.strip() or None, id_cliente)
        )
        cur.execute("UPDATE CuentaCorriente SET limite_credito=%s WHERE id_cliente=%s", (float(limite_credito), id_cliente))
        conn.commit()
        return True
    except mysql.connector.IntegrityError as e:
        if conn: conn.rollback()
        if getattr(e, "errno", None) == 1062:
            msg = str(e).lower()
            if "dni" in msg: raise ValueError("DNI_DUPLICADO") from e
            if "email" in msg: raise ValueError("EMAIL_DUPLICADO") from e
        return False
    except Exception:
        if conn: conn.rollback()
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()

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

def obtener_cliente_completo(id_cliente: int) -> Optional[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        # Asumiendo que la columna CUIT fue añadida a la tabla Cliente
        cur.execute(
            """SELECT c.id_cliente, c.nombre, c.dni, c.cuit, c.direccion, c.telefono, c.email, cc.limite_credito
               FROM Cliente c LEFT JOIN CuentaCorriente cc ON c.id_cliente = cc.id_cliente WHERE c.id_cliente = %s""", (id_cliente,)
        )
        return cur.fetchone()
    except Exception: return None
    finally:
        if cur: cur.close()
        if conn: conn.close()

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
        
        # --- CAMBIO: Usamos LOWER() en ambos lados ---
        like = f"%{patron}%"
        cur.execute(
            "SELECT id_cliente, nombre, dni, direccion, telefono, email FROM Cliente WHERE LOWER(nombre) LIKE LOWER(%s) AND activo=1 ORDER BY nombre",
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

def activar_cliente_logico(id_cliente: int) -> bool:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("UPDATE Cliente SET activo=TRUE WHERE id_cliente=%s", (id_cliente,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"activar_cliente_logico: {e}")
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
# En app/database/DB.py

def obtener_categorias() -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        # AGREGAMOS 'es_pesable_default'
        cur.execute("SELECT id_categoria, nombre, margen_ganancia, es_pesable_default FROM Categoria WHERE activa=1 ORDER BY nombre")
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_categorias: {e}")
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception: pass

def crear_categoria(nombre: str, margen: float, es_pesable: bool = False) -> bool:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Categoria (nombre, margen_ganancia, es_pesable_default, activa) VALUES (%s, %s, %s, 1)",
            (nombre, float(margen), bool(es_pesable))
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"crear_categoria: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception: pass

def actualizar_categoria(id_categoria: int, nombre: str, margen: float, es_pesable: bool) -> bool:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            "UPDATE Categoria SET nombre=%s, margen_ganancia=%s, es_pesable_default=%s WHERE id_categoria=%s",
            (nombre, float(margen), bool(es_pesable), id_categoria)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"actualizar_categoria: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception: pass

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
            
        # --- CAMBIO: Usamos LOWER() en ambos lados ---
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
# VENTA COMPLETA (NUEVA IMPLEMENTACIÓN ATÓMICA)
# ======================================================
def registrar_venta_completa(
    id_usuario: int,
    id_cliente: int | None,
    items: list[tuple[int | None, str, float, float, str]],
    tipo_pago: str
) -> int | None:
    """
    Registra una venta completa de forma atómica.
    
    Args:
        id_usuario: ID del usuario/vendedor
        id_cliente: ID del cliente (None para consumidor final)
        items: Lista de tuplas (id_producto, nombre, cantidad, precio_unitario, codigo_barras)
        tipo_pago: 'efectivo', 'tarjeta', 'cuenta_corriente', 'transferencia'
    
    Returns:
        ID de la venta creada o None si falla
    """
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        # Iniciar transacción explícita
        conn.start_transaction()
        
        # 1. Crear venta maestra
        cur.execute(
            """
            INSERT INTO Venta (id_usuario, id_cliente, estado, tipo_pago)
            VALUES (%s, %s, 'completada', %s)
            """,
            (id_usuario, id_cliente, tipo_pago)
        )
        id_venta = cur.lastrowid
        
        total_venta = 0.0
        
        # 2. Procesar cada ítem
        for id_producto, nombre, cantidad, precio_unitario, codigo_barras in items:
            
            # Validaciones
            if cantidad <= 0:
                raise ValueError(f"Cantidad inválida para {nombre}: {cantidad}")
            if precio_unitario <= 0:
                raise ValueError(f"Precio inválido para {nombre}: {precio_unitario}")
            
            # Si es producto catalogado, validar stock
            if id_producto is not None:
                # BLOQUEAR fila de inventario para evitar race conditions
                cur.execute(
                    "SELECT cantidad FROM Inventario WHERE id_producto = %s FOR UPDATE",
                    (id_producto,)
                )
                inv_row = cur.fetchone()
                
                if not inv_row:
                    raise ValueError(f"Producto {nombre} sin registro de inventario")
                
                stock_actual = float(inv_row['cantidad'])
                
                if stock_actual < cantidad:
                    raise ValueError(
                        f"Stock insuficiente para {nombre}\n"
                        f"Disponible: {stock_actual:.3f}\n"
                        f"Requerido: {cantidad:.3f}"
                    )
                
                # Obtener datos del producto para snapshot
                cur.execute(
                    "SELECT nombre, codigo_barras FROM Producto WHERE id_producto = %s",
                    (id_producto,)
                )
                prod_row = cur.fetchone()
                
                if not prod_row:
                    raise ValueError(f"Producto con ID {id_producto} no encontrado")
                
                nombre_snapshot = prod_row['nombre']
                codigo_snapshot = prod_row['codigo_barras']
                
            else:
                # Producto libre (sin ID)
                nombre_snapshot = nombre
                codigo_snapshot = codigo_barras or None
            
            # 3. Insertar detalle de venta
            cur.execute(
                """
                INSERT INTO DetalleVenta 
                (id_venta, id_producto, nombre_producto, codigo_barras, cantidad, precio_unitario)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (id_venta, id_producto, nombre_snapshot, codigo_snapshot, cantidad, precio_unitario)
            )
            
            # 4. Descontar stock (solo si es producto catalogado)
            if id_producto is not None:
                cur.execute(
                    """
                    UPDATE Inventario 
                    SET cantidad = GREATEST(cantidad - %s, 0)
                    WHERE id_producto = %s
                    """,
                    (cantidad, id_producto)
                )
                
                if cur.rowcount == 0:
                    raise ValueError(f"No se pudo actualizar inventario de {nombre}")
            
            # Acumular total
            total_venta += cantidad * precio_unitario
        
        # 5. Actualizar total de venta
        cur.execute(
            "UPDATE Venta SET total = %s WHERE id_venta = %s",
            (total_venta, id_venta)
        )
        
        # 6. Si es cuenta corriente, actualizar saldo
        if tipo_pago == 'cuenta_corriente' and id_cliente:
            cur.execute(
                "UPDATE CuentaCorriente SET saldo = saldo - %s WHERE id_cliente = %s",
                (total_venta, id_cliente)
            )
            
            if cur.rowcount == 0:
                raise ValueError(f"Cliente {id_cliente} no tiene cuenta corriente")
        
        # 7. Registrar movimiento de caja (si hay sesión abierta)
        if tipo_pago == 'efectivo':
            cur.execute(
                "SELECT id_session FROM caja_session WHERE estado = 'abierta' LIMIT 1"
            )
            session_row = cur.fetchone()
            
            if session_row:
                id_session = session_row['id_session']
                cur.execute(
                    """
                    INSERT INTO caja_movimiento 
                    (id_session, tipo, monto, medio, motivo, id_usuario, id_venta, descripcion)
                    VALUES (%s, 'ingreso', %s, 'efectivo', 'venta_efectivo', %s, %s, %s)
                    """,
                    (
                        id_session,
                        total_venta,
                        id_usuario,
                        id_venta,
                        f"Venta #{id_venta} - Efectivo"
                    )
                )
        
        # 8. Commit transacción
        conn.commit()
        
        logger.info(f"✅ Venta #{id_venta} registrada: ${total_venta:.2f} ({tipo_pago})")
        return id_venta
        
    except ValueError as ve:
        # Errores de validación (stock, etc.)
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.warning(f"Validación fallida en venta: {ve}")
        raise  # Re-lanzar para que la UI lo capture
        
    except Exception as e:
        # Errores inesperados
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.error(f"registrar_venta_completa: {e}")
        raise RuntimeError(f"Error al registrar venta: {e}") from e
        
    finally:
        try:
            if cur:
                cur.close()
            if conn:
                conn.close()
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
# En app/database/DB.py

def registrar_pago_proveedor(id_proveedor: int, monto: float, medio_pago: str, id_usuario: int, observacion: str = "") -> bool:
        """
        Registra un pago a proveedor.
        1. Guarda el registro en la tabla PagoProveedor (con observación).
        2. Actualiza el saldo del proveedor.
        3. Si es efectivo, VALIDA SALDO y descuenta de la caja.
        """
        conn = cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            conn.start_transaction()

            id_session = None
            saldo_caja_actual = 0.0
            
            # 1. VALIDAR CAJA SI ES EFECTIVO
            if medio_pago == 'efectivo':
                cur.execute("SELECT id_session, monto_apertura FROM caja_session WHERE estado = 'abierta' LIMIT 1")
                session_row = cur.fetchone()
                if not session_row:
                    raise ValueError("⚠️ No puedes pagar en EFECTIVO con la caja cerrada.")
                
                id_session = session_row['id_session']
                monto_apertura = float(session_row['monto_apertura'])
                
                # 🔥 CALCULAR SALDO ACTUAL DE EFECTIVO EN CAJA
                # Solo contamos movimientos QUE NO SEAN la apertura
                cur.execute("""
                    SELECT 
                        motivo,
                        tipo,
                        medio,
                        SUM(monto) as total
                    FROM caja_movimiento
                    WHERE id_session = %s
                    GROUP BY motivo, tipo, medio
                """, (id_session,))
                
                movimientos = cur.fetchall()
                
                ingresos = 0.0
                egresos = 0.0
                
                for mov in movimientos:
                    motivo = mov['motivo']
                    tipo = mov['tipo']
                    medio_mov = mov['medio']
                    monto_mov = float(mov['total'])
                    
                    # 🔥 IGNORAR COMPLETAMENTE EL MOVIMIENTO DE APERTURA
                    if motivo == 'apertura_caja':
                        continue
                    
                    # Solo contar efectivo
                    if medio_mov != 'efectivo':
                        continue
                    
                    if tipo == 'ingreso':
                        ingresos += monto_mov
                    elif tipo == 'egreso':
                        egresos += monto_mov
                
                # 🔥 FÓRMULA CORRECTA: Apertura + Ingresos reales - Egresos reales
                saldo_caja_actual = monto_apertura + ingresos - egresos
                
                logger.info(f"💰 Validando pago efectivo: Apertura=${monto_apertura:.2f} + Ingresos=${ingresos:.2f} - Egresos=${egresos:.2f} = Disponible=${saldo_caja_actual:.2f}")
                
                # 🔥 VALIDAR SALDO SUFICIENTE
                if saldo_caja_actual < monto:
                    raise ValueError(
                        f"❌ SALDO INSUFICIENTE EN CAJA\n\n"
                        f"Disponible: ${saldo_caja_actual:,.2f}\n"
                        f"Intentas pagar: ${monto:,.2f}\n"
                        f"Faltante: ${(monto - saldo_caja_actual):,.2f}\n\n"
                        f"💡 Opciones:\n"
                        f"• Paga con Transferencia o Cheque\n"
                        f"• Realiza pagos parciales"
                    )

            # 2. Guardar el Registro del Pago (Historial)
            cur.execute(
                """
                INSERT INTO PagoProveedor (monto, metodo, observacion, id_proveedor, id_usuario)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (monto, medio_pago, observacion, id_proveedor, id_usuario)
            )

            # 3. Actualizar Saldo Proveedor (SUMAMOS para achicar la deuda negativa)
            cur.execute(
                "UPDATE Proveedor SET saldo = saldo + %s WHERE id_proveedor = %s",
                (monto, id_proveedor)
            )

            # 4. Registrar Movimiento en Caja (Solo si es efectivo)
            if medio_pago == 'efectivo' and id_session:
                cur.execute(
                    """
                    INSERT INTO caja_movimiento (id_session, tipo, monto, medio, motivo, id_usuario, descripcion)
                    VALUES (%s, 'egreso', %s, 'efectivo', 'pago_proveedor', %s, %s)
                    """,
                    (id_session, monto, id_usuario, f"Pago a Prov. #{id_proveedor} - {observacion}")
                )

            conn.commit()
            logger.info(f"✅ Pago a proveedor #{id_proveedor} registrado: ${monto:.2f}")
            return True

        except ValueError as ve:
            if conn:
                try: conn.rollback()
                except: pass
            logger.warning(f"Validación fallida en pago proveedor: {ve}")
            raise
            
        except Exception as e:
            if conn:
                try: conn.rollback()
                except: pass
            logger.error(f"registrar_pago_proveedor: {e}")
            raise
        finally:
            try:
                if cur: cur.close()
                if conn: conn.close()
            except: pass
    

def obtener_proveedores(incluir_inactivos: bool = False) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        # 🔥 CAMBIO: Incluir dni, cuit, y direccion (se asume que los nombres son 'dni' y 'cuit' en la DB)
        sql = "SELECT id_proveedor, nombre, empresa, telefono, email, dni, cuit, direccion, saldo, activo FROM Proveedor"
        
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

def insertar_proveedor(nombre: str, empresa: str, cuit_empresa: str, dni_vendedor: str, telefono: str = "", email: str = "", direccion: str = "") -> Optional[int]:
    if not nombre.strip(): raise ValueError("Nombre proveedor obligatorio.")
    if not empresa.strip(): raise ValueError("Nombre empresa obligatorio.")
    if not dni_vendedor.strip(): raise ValueError("DNI del vendedor obligatorio.")
    if not cuit_empresa.strip(): raise ValueError("CUIT de la empresa obligatorio.")

    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        
        # Insertamos todos los campos nuevos y viejos
        cur.execute(
            "INSERT INTO Proveedor (nombre, empresa, cuit, dni, telefono, email, direccion, activo) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)",
            (nombre.strip(), empresa.strip(), cuit_empresa.strip(), dni_vendedor.strip(), telefono.strip() or None, email.strip() or None, direccion.strip() or None)
        )
        conn.commit()
        return cur.lastrowid
    except mysql.connector.IntegrityError as e:
        if conn: conn.rollback()
        if getattr(e, "errno", None) == 1062:
            msg = str(e).lower()
            if "dni" in msg: raise ValueError("DNI_PROVEEDOR_DUPLICADO") from e
            if "email" in msg: raise ValueError("EMAIL_DUPLICADO") from e
        return None
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"insertar_proveedor: {e}")
        raise e
    finally:
        if cur: cur.close()
        if conn: conn.close()

def actualizar_proveedor(id_proveedor: int, nombre: str, empresa: str, cuit_empresa: str, dni_vendedor: str, telefono: str, email: str, direccion: str) -> bool:
    if not nombre.strip() or not empresa.strip() or not dni_vendedor.strip() or not cuit_empresa.strip():
        raise ValueError("Campos obligatorios vacíos.")
    
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        
        # Actualizamos todos los campos
        cur.execute(
            """UPDATE Proveedor SET nombre=%s, empresa=%s, cuit=%s, dni=%s, telefono=%s, email=%s, direccion=%s WHERE id_proveedor=%s""",
            (nombre.strip(), empresa.strip(), cuit_empresa.strip(), dni_vendedor.strip(), telefono.strip() or None, email.strip() or None, direccion.strip() or None, id_proveedor)
        )
        conn.commit()
        return cur.rowcount > 0
    except mysql.connector.IntegrityError as e:
        if conn: conn.rollback()
        if getattr(e, "errno", None) == 1062:
            msg = str(e).lower()
            if "dni" in msg: raise ValueError("DNI_PROVEEDOR_DUPLICADO")
            if "email" in msg: raise ValueError("EMAIL_DUPLICADO")
        return False
    except Exception:
        if conn: conn.rollback()
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()

def obtener_proveedores(incluir_inactivos: bool = False) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        # Traemos DNI, CUIT, y Dirección
        sql = "SELECT id_proveedor, nombre, empresa, cuit, dni, telefono, email, direccion, saldo, activo FROM Proveedor"
        if not incluir_inactivos: sql += " WHERE activo=1"
        sql += " ORDER BY nombre"
        cur.execute(sql)
        return list(cur.fetchall() or [])
    except Exception as e: 
        logger.error(f"obtener_proveedores: Fallo al traer datos. Error: {e}") 
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()

def obtener_proveedor_completo(id_proveedor: int) -> Optional[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        # Traemos TODOS los campos para la edición
        cur.execute("SELECT * FROM Proveedor WHERE id_proveedor = %s", (id_proveedor,))
        return cur.fetchone()
    except Exception: return None
    finally:
        if cur: cur.close()
        if conn: conn.close()

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
def activar_proveedor_logico(id_proveedor: int) -> bool:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("UPDATE Proveedor SET activo=TRUE WHERE id_proveedor=%s", (id_proveedor,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"activar_proveedor_logico: {e}")
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


def insertar_compra(id_usuario: int, id_proveedor: int, items: list[dict], medio_pago: str = 'efectivo') -> int | None:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        conn.start_transaction()

        if medio_pago == 'efectivo':
            cur.execute("SELECT id_session FROM caja_session WHERE estado = 'abierta' LIMIT 1")
            session_row = cur.fetchone()
            if not session_row: raise ValueError("Caja cerrada.")
            id_session = session_row['id_session']

        cur.execute("INSERT INTO Compra (id_usuario, id_proveedor, estado, medio_pago) VALUES (%s, %s, 'recibida', %s)", (id_usuario, id_proveedor, medio_pago))
        id_compra = cur.lastrowid
        total_compra = 0.0

        for item in items:
            id_prod = item['id']
            cantidad = float(item['cant'])
            costo = float(item['costo'])
            # 🔥 NUEVO: Precio venta nuevo
            precio_venta = float(item.get('precio_venta', 0.0))

            cur.execute("SELECT nombre, codigo_barras FROM Producto WHERE id_producto=%s", (id_prod,))
            prod = cur.fetchone()
            
            # Insertar detalle con el precio de venta historico (Requiere ALTER TABLE DetalleCompra)
            cur.execute(
                """INSERT INTO DetalleCompra (id_compra, id_producto, nombre_producto, codigo_barras, cantidad, precio_unitario, precio_venta_historico)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (id_compra, id_prod, prod['nombre'], prod['codigo_barras'], cantidad, costo, precio_venta)
            )
            cur.execute("UPDATE Inventario SET cantidad = cantidad + %s WHERE id_producto=%s", (cantidad, id_prod))
            total_compra += cantidad * costo

        cur.execute("UPDATE Compra SET total = %s WHERE id_compra = %s", (total_compra, id_compra))

        if medio_pago == 'efectivo' and id_session:
            cur.execute("INSERT INTO caja_movimiento (id_session, tipo, monto, medio, motivo, id_usuario, id_compra, descripcion) VALUES (%s, 'egreso', %s, 'efectivo', 'pago_proveedor', %s, %s, %s)", (id_session, total_compra, id_usuario, id_compra, f"Compra #{id_compra}"))
        elif medio_pago == 'cuenta_corriente':
            cur.execute("UPDATE Proveedor SET saldo = saldo - %s WHERE id_proveedor = %s", (total_compra, id_proveedor))

        conn.commit()
        return id_compra
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"insertar_compra: {e}")
        raise
    finally:
        if cur: cur.close()
        if conn: conn.close()
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
# HISTORIAL DE MOVIMIENTOS DE CAJA (MEJORADO CON CIERRES)
# ======================================================

def obtener_historial_movimientos_caja(
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    tipo: str | None = None,
    motivo: str | None = None,
    id_usuario: int | None = None
) -> list[dict]:
    """
    Obtiene el historial UNIFICADO: Movimientos normales + Cierres de Caja.
    """
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        # 1. QUERY DE MOVIMIENTOS NORMALES
        # --------------------------------
        sql_movs = """
            SELECT 
                cm.id_movimiento,
                cm.fecha_hora,
                cm.tipo,
                cm.monto,
                cm.medio,
                cm.motivo,
                cm.descripcion,
                u.nombre AS usuario_nombre,
                'movimiento' as origen_dato
            FROM caja_movimiento cm
            LEFT JOIN Usuario u ON cm.id_usuario = u.id_usuario
            WHERE 1=1
        """
        params_movs = []
        
        if fecha_desde:
            sql_movs += " AND DATE(cm.fecha_hora) >= %s"
            params_movs.append(fecha_desde)
        if fecha_hasta:
            sql_movs += " AND DATE(cm.fecha_hora) <= %s"
            params_movs.append(fecha_hasta)
        if tipo and tipo != 'cierre': # 'cierre' es un tipo especial visual
            sql_movs += " AND cm.tipo = %s"
            params_movs.append(tipo)
        if motivo and motivo not in ('cierre_caja', 'apertura_cierre'):
            sql_movs += " AND cm.motivo = %s"
            params_movs.append(motivo)
        if id_usuario:
            sql_movs += " AND cm.id_usuario = %s"
            params_movs.append(id_usuario)

        # 2. QUERY DE CIERRES DE CAJA (Simulados como movimientos)
        # --------------------------------------------------------
        sql_cierres = """
            SELECT
                cs.id_session + 9000000 as id_movimiento, -- ID ficticio alto para no chocar
                cs.fecha_cierre as fecha_hora,
                'cierre' as tipo,
                cs.efectivo_contado as monto,
                'efectivo' as medio,
                'cierre_caja' as motivo,
                CONCAT('Cierre de Caja. Esperado: $', FORMAT(cs.efectivo_esperado, 2), '. Diferencia: $', FORMAT(cs.diferencia, 2)) as descripcion,
                u.nombre as usuario_nombre,
                'cierre' as origen_dato
            FROM caja_session cs
            LEFT JOIN Usuario u ON cs.id_usuario_cierre = u.id_usuario
            WHERE cs.fecha_cierre IS NOT NULL
        """
        params_cierres = []
        
        if fecha_desde:
            sql_cierres += " AND DATE(cs.fecha_cierre) >= %s"
            params_cierres.append(fecha_desde)
        if fecha_hasta:
            sql_cierres += " AND DATE(cs.fecha_cierre) <= %s"
            params_cierres.append(fecha_hasta)
        if id_usuario:
            sql_cierres += " AND cs.id_usuario_cierre = %s"
            params_cierres.append(id_usuario)

        # 3. UNIR Y ORDENAR
        # -----------------
        # Si el usuario filtra por "ingreso" estricto, no mostramos cierres.
        # Si filtra por "egreso" estricto, no mostramos cierres.
        # Si filtra por "cierre", solo mostramos cierres.
        
        sql_final = ""
        params_final = []

        incluir_movs = True
        incluir_cierres = True

        if tipo == 'cierre': 
            incluir_movs = False
        if tipo in ('ingreso', 'egreso'): 
            incluir_cierres = False
        
        # Filtro especial de motivos agrupados
        if motivo == 'cierre_caja': 
            incluir_movs = False
            incluir_cierres = True
        
        if motivo == 'apertura_caja': # Si solo quiere aperturas, no traemos cierres
            incluir_cierres = False

        if incluir_movs and incluir_cierres:
            sql_final = f"({sql_movs}) UNION ALL ({sql_cierres}) ORDER BY fecha_hora DESC"
            params_final = params_movs + params_cierres
        elif incluir_movs:
            sql_final = f"{sql_movs} ORDER BY fecha_hora DESC"
            params_final = params_movs
        elif incluir_cierres:
            sql_final = f"{sql_cierres} ORDER BY fecha_hora DESC"
            params_final = params_cierres
        else:
            return [] # Nada que mostrar

        cur.execute(sql_final, tuple(params_final))
        return list(cur.fetchall() or [])
        
    except Exception as e:
        logger.error(f"obtener_historial_movimientos_caja: {e}")
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()

# ======================================================
# HISTORIAL DE COMPRAS (CORREGIDO PARA FILTROS)
# ======================================================
# En app/database/DB.py

def obtener_compras_maestro(
    fecha_desde: Optional[str], 
    fecha_hasta: Optional[str], 
    id_proveedor: Optional[int]
) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        # Definimos los WHERE para las subconsultas
        where_compra = ["1=1"]
        where_pago = ["1=1"]
        
        if id_proveedor is not None:
             where_compra.append(f"c.id_proveedor = {id_proveedor}")
             where_pago.append(f"pp.id_proveedor = {id_proveedor}")

        if fecha_desde:
             where_compra.append(f"DATE(c.fecha) >= '{fecha_desde}'")
             where_pago.append(f"DATE(pp.fecha) >= '{fecha_desde}'")
             
        if fecha_hasta:
             where_compra.append(f"DATE(c.fecha) <= '{fecha_hasta}'")
             where_pago.append(f"DATE(pp.fecha) <= '{fecha_hasta}'")


        # REHACEMOS LA QUERY: Más clara y eficiente con WHERE inyectado
        sql = f"""
            SELECT 
                c.id_compra, c.fecha, c.total, c.estado, c.medio_pago,
                p.nombre AS proveedor, u.nombre AS usuario, 'COMPRA' as tipo_registro
            FROM Compra c
            JOIN Proveedor p ON c.id_proveedor = p.id_proveedor
            LEFT JOIN Usuario u ON c.id_usuario = u.id_usuario
            WHERE {' AND '.join(where_compra)}

            UNION ALL

            SELECT 
                pp.id_pago_prov, pp.fecha, pp.monto, 'PAGO DEUDA', pp.metodo,
                p.nombre, u.nombre, 'PAGO'
            FROM PagoProveedor pp
            JOIN Proveedor p ON pp.id_proveedor = p.id_proveedor
            LEFT JOIN Usuario u ON pp.id_usuario = u.id_usuario
            WHERE {' AND '.join(where_pago)}
            
            ORDER BY fecha DESC
        """
        
        # Como inyectamos los parámetros directamente en el string SQL, no necesitamos pasar una tupla vacía
        cur.execute(sql)
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
        # 🔥 Ahora traemos precio_venta_historico
        cur.execute(
            """SELECT id_producto, nombre_producto, codigo_barras, cantidad, precio_unitario, precio_venta_historico, subtotal
               FROM DetalleCompra WHERE id_compra = %s ORDER BY id_detalle_compra ASC""", (id_compra,)
        )
        return list(cur.fetchall() or [])
    except Exception: return []
    finally:
        if cur: cur.close()
        if conn: conn.close()

# ... (dentro de app/database/DB.py)

# ======================================================
# HISTORIAL DE PAGOS (NUEVO)
# ======================================================
def obtener_pagos_maestro(
    fecha_desde: Optional[str], 
    fecha_hasta: Optional[str], 
    id_cliente: Optional[int], 
    id_usuario: Optional[int]
) -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        sql = """
            SELECT
                p.id_pago, p.fecha, p.monto, p.metodo,
                c.nombre AS cliente_nombre,
                u.nombre AS usuario_nombre
            FROM Pago p
            JOIN CuentaCorriente cc ON p.id_cuenta = cc.id_cuenta
            JOIN Cliente c ON cc.id_cliente = c.id_cliente
            LEFT JOIN Usuario u ON p.id_usuario = u.id_usuario
        """
        where_clauses = []
        params = []
        
        # Filtro de Fechas
        if fecha_desde:
            where_clauses.append("DATE(p.fecha) >= %s")
            params.append(fecha_desde)
        if fecha_hasta:
            where_clauses.append("DATE(p.fecha) <= %s")
            params.append(fecha_hasta)

        # Filtro de Cliente
        if id_cliente is not None and id_cliente != 0:
            where_clauses.append("c.id_cliente = %s")
            params.append(id_cliente)
            
        # Filtro de Usuario (quien registró el pago)
        if id_usuario is not None:
            where_clauses.append("p.id_usuario = %s")
            params.append(id_usuario)

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
            
        sql += " ORDER BY p.fecha DESC"
        
        cur.execute(sql, tuple(params))
        return list(cur.fetchall() or [])
    except Exception as e:
        logger.error(f"obtener_pagos_maestro: {e}")
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

# app/database/DB.py (Fragmento con la corrección de Caja)

# ... (Líneas anteriores)

def registrar_pago_cuenta_corriente(id_cuenta: int, monto: float, metodo: str, id_usuario: int) -> bool:
    if monto <= 0:
        raise ValueError("El monto del pago debe ser positivo.")
    
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        conn.start_transaction()

        # 🔥 CORRECCIÓN: Validar caja si es efectivo y obtener id_session
        id_session = None
        if metodo == 'efectivo':
            # Verificamos la caja abierta del usuario
            cur.execute(
                "SELECT id_session FROM caja_session WHERE estado = 'abierta' AND id_usuario_apertura = %s LIMIT 1",
                (id_usuario,)
            )
            session_row = cur.fetchone()
            
            if not session_row:
                raise ValueError("CAJA_CERRADA") 
            id_session = session_row['id_session']
        # -------------------------------------------------------------
        
        # 1. Obtener ID del cliente para referencia
        cur.execute("SELECT id_cliente FROM CuentaCorriente WHERE id_cuenta = %s", (id_cuenta,))
        cuenta_row = cur.fetchone()
        if not cuenta_row:
            raise ValueError("Cuenta corriente no encontrada")
        id_cliente = cuenta_row['id_cliente']
        
        # 2. Registrar pago
        cur.execute(
            "INSERT INTO Pago (id_cuenta, monto, metodo, id_usuario) VALUES (%s, %s, %s, %s)",
            (id_cuenta, monto, metodo, id_usuario)
        )
        
        # 3. Actualizar saldo (sumar porque es ingreso)
        cur.execute(
            "UPDATE CuentaCorriente SET saldo = saldo + %s WHERE id_cuenta = %s",
            (monto, id_cuenta)
        )
        
        # 4. SI ES EFECTIVO, REGISTRAR EN CAJA
        if metodo == 'efectivo' and id_session:
            cur.execute(
                """
                INSERT INTO caja_movimiento 
                (id_session, tipo, monto, medio, motivo, id_usuario, id_cliente, descripcion)
                VALUES (%s, 'ingreso', %s, 'efectivo', 'pago_cuenta_corriente_efectivo', %s, %s, %s)
                """,
                (
                    id_session,
                    monto,
                    id_usuario,
                    id_cliente,
                    f"Pago Cta.Cte. Cliente #{id_cliente} - ${monto:.2f}"
                )
            )
        
        conn.commit()
        logger.info(f"✅ Pago registrado: ${monto:.2f} ({metodo}) para cuenta #{id_cuenta}")
        return True
        
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"registrar_pago_cuenta_corriente: {e}")
        # 🔥 Aseguramos que el error de caja cerrada se propague
        if str(e) == "CAJA_CERRADA":
            raise ValueError("CAJA_CERRADA") from e
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
        cur.execute("SELECT u.id_usuario, u.nombre, u.id_rol, u.activo, r.nombre AS rol_nombre FROM Usuario u LEFT JOIN Rol r ON u.id_rol = r.id_rol ORDER BY u.nombre")
        return list(cur.fetchall() or [])
    except Exception: return []
    finally: 
        if cur: cur.close() 
        if conn: conn.close()

def obtener_roles() -> list[dict]:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id_rol, nombre FROM Rol ORDER BY nombre")
        return list(cur.fetchall() or [])
    except Exception: return []
    finally: 
        if cur: cur.close() 
        if conn: conn.close()

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

def activar_usuario(id_usuario: int) -> bool:
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("UPDATE Usuario SET activo=TRUE WHERE id_usuario=%s", (id_usuario,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"activar_usuario: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass


def actualizar_nombre_usuario(id_usuario: int, nuevo_nombre: str) -> bool:
    if not nuevo_nombre.strip():
        raise ValueError("El nombre no puede estar vacío.")
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("UPDATE Usuario SET nombre=%s WHERE id_usuario=%s", (nuevo_nombre.strip(), id_usuario))
        conn.commit()
        return cur.rowcount > 0
    except mysql.connector.IntegrityError as e:
        if conn: conn.rollback()
        # 🔥 PROPAGAR error de nombre duplicado para que la UI lo maneje de forma clara
        if getattr(e, "errno", None) == 1062:
            raise ValueError("NOMBRE_DUPLICADO") from e
        logger.warning(f"actualizar_nombre_usuario (IntegrityError): {e}")
        return False
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        logger.error(f"actualizar_nombre_usuario: {e}")
        return False
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass
            
# ======================================================
# AUDITORÍA DE ACCIONES (CORREGIDO)
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
    Registra una acción en la tabla AuditoriaAcciones.
    Incluye corrección para serializar Decimal y Fechas.
    """
    
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        
        # --- CORRECCIÓN: Encoder personalizado para JSON ---
        def default_serializer(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()  # Convierte fechas a texto ISO
            if hasattr(obj, '__str__'): 
                return str(obj)         # Convierte Decimales a string
            return str(obj)             # Fallback genérico

        # Usar 'default=default_serializer' para evitar el error de Decimal
        datos_ant_json = json.dumps(datos_anteriores, ensure_ascii=False, default=default_serializer) if datos_anteriores else None
        datos_new_json = json.dumps(datos_nuevos, ensure_ascii=False, default=default_serializer) if datos_nuevos else None
        
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


# ======================================================
# CAJA INDIVIDUAL POR USUARIO (MODIFICADO)
# ======================================================

def obtener_session_abierta(id_usuario: int) -> dict | None:
    """
    Retorna la caja abierta DEL USUARIO ESPECÍFICO.
    Sistema de caja individual: cada usuario tiene su propia caja.
    """
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        # Buscar SOLO la caja del usuario especificado
        cur.execute(
            "SELECT * FROM caja_session WHERE id_usuario_apertura = %s AND estado = 'abierta' LIMIT 1",
            (id_usuario,)
        )
        
        return cur.fetchone()
    except Exception as e:
        logger.error(f"obtener_session_abierta: {e}")
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()

def abrir_caja_session(id_usuario: int, monto_inicial: float) -> bool:
    """
    Abre una nueva sesión de caja PARA EL USUARIO ESPECÍFICO.
    Valida que el usuario NO tenga ya una caja abierta.
    """
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        
        # Validar que el usuario NO tenga ya una caja abierta
        cur.execute(
            "SELECT id_session FROM caja_session WHERE id_usuario_apertura=%s AND estado='abierta'",
            (id_usuario,)
        )
        if cur.fetchone():
            raise ValueError(f"El usuario ya tiene una caja abierta.")

        # 1. Crear Sesión
        cur.execute(
            "INSERT INTO caja_session (id_usuario_apertura, monto_apertura, estado) VALUES (%s, %s, 'abierta')",
            (id_usuario, monto_inicial)
        )
        id_session = cur.lastrowid
        
        # 2. Registrar movimiento de apertura
        cur.execute(
            """
            INSERT INTO caja_movimiento (id_session, tipo, monto, medio, motivo, id_usuario, descripcion)
            VALUES (%s, 'ingreso', %s, 'efectivo', 'apertura_caja', %s, 'Saldo Inicial de Apertura')
            """,
            (id_session, monto_inicial, id_usuario)
        )
        
        conn.commit()
        logger.info(f"✅ Caja abierta por usuario {id_usuario} con ${monto_inicial}")
        return True
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"abrir_caja_session: {e}")
        raise  # Re-lanzar para que la UI muestre el mensaje
    finally:
        if cur: cur.close()
        if conn: conn.close()

def registrar_movimiento_manual(id_session: int, tipo: str, monto: float, motivo: str, descripcion: str, id_usuario: int) -> bool:
    """Para movimientos manuales (Retiros, Gastos, Ajustes)."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO caja_movimiento (id_session, tipo, monto, medio, motivo, id_usuario, descripcion)
            VALUES (%s, %s, %s, 'efectivo', %s, %s, %s)
            """,
            (id_session, tipo, monto, motivo, id_usuario, descripcion)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"registrar_movimiento_manual: {e}")
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()

def obtener_resumen_cierre(id_session: int) -> dict:
    """Calcula todos los totales para el arqueo."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        # Datos de la sesión
        cur.execute("SELECT * FROM caja_session WHERE id_session = %s", (id_session,))
        session = cur.fetchone()
        if not session: return {}
        
        monto_inicial = float(session['monto_apertura'])
        
        # Calcular totales por motivo
        cur.execute("""
            SELECT motivo, tipo, SUM(monto) as total 
            FROM caja_movimiento 
            WHERE id_session = %s 
            GROUP BY motivo, tipo
        """, (id_session,))
        rows = cur.fetchall()
        
        resumen = {
            'monto_inicial': monto_inicial,
            'ventas_efectivo': 0.0,
            'cobros_ctacte': 0.0,
            'otros_ingresos': 0.0,
            'pagos_proveedores': 0.0,
            'retiros': 0.0,
            'gastos_varios': 0.0,
            'otros_egresos': 0.0
        }
        
        total_ingresos = 0.0
        total_egresos = 0.0
        
        for r in rows:
            motivo = r['motivo']
            monto = float(r['total'])
            tipo = r['tipo']
            
            if motivo == 'apertura_caja': continue
            
            if tipo == 'ingreso':
                total_ingresos += monto
                if motivo == 'venta_efectivo': resumen['ventas_efectivo'] += monto
                elif motivo == 'pago_cuenta_corriente_efectivo': resumen['cobros_ctacte'] += monto
                else: resumen['otros_ingresos'] += monto
            else:
                total_egresos += monto
                if motivo == 'pago_proveedor': resumen['pagos_proveedores'] += monto
                elif motivo == 'retiro_caja': resumen['retiros'] += monto
                elif motivo == 'gasto_vario': resumen['gastos_varios'] += monto
                else: resumen['otros_egresos'] += monto
                
        efectivo_esperado = monto_inicial + total_ingresos - total_egresos
        
        resumen['total_ingresos'] = total_ingresos
        resumen['total_egresos'] = total_egresos
        resumen['efectivo_esperado'] = efectivo_esperado
        resumen['fecha_apertura'] = session['fecha_apertura']
        resumen['usuario_apertura'] = session['id_usuario_apertura']
        
        return resumen
        
    except Exception as e:
        logger.error(f"obtener_resumen_cierre: {e}")
        return {}
    finally:
        if cur: cur.close()
        if conn: conn.close()

def cerrar_caja_session(id_session: int, id_usuario_cierre: int, efectivo_esperado: float, efectivo_contado: float, diferencia: float, obs: str) -> bool:
    """Cierra la sesión de caja."""
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE caja_session 
            SET fecha_cierre = NOW(), 
                id_usuario_cierre = %s,
                estado = 'cerrada',
                efectivo_esperado = %s,
                efectivo_contado = %s,
                diferencia = %s,
                observaciones_cierre = %s
            WHERE id_session = %s
            """,
            (id_usuario_cierre, efectivo_esperado, efectivo_contado, diferencia, obs, id_session)
        )
        
        # Auditoría
        cur.execute(
            "INSERT INTO AuditoriaAcciones (id_usuario, accion, tabla_afectada, id_registro, datos_nuevos) VALUES (%s, 'CIERRE_CAJA', 'caja_session', %s, %s)",
            (id_usuario_cierre, id_session, json.dumps({'diferencia': diferencia, 'contado': efectivo_contado}))
        )
        
        conn.commit()
        logger.info(f"✅ Caja #{id_session} cerrada por usuario {id_usuario_cierre}")
        return True
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"cerrar_caja_session: {e}")
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()
# ======================================================
# REPORTE RESUMEN DIARIO (PARA TICKET)
# ======================================================
def obtener_resumen_diario(fecha: str | None = None) -> dict:
    """
    Obtiene resumen de ventas del día por:
    - Categorías (con cantidad y monto)
    - Métodos de pago
    - Ventas por Vendedor (NUEVO)
    
    Args:
        fecha: Fecha en formato 'YYYY-MM-DD'. Si es None, usa hoy.
    """
    conn = cur = None
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        
        # Si no especifican fecha, usar hoy
        if not fecha:
            fecha = date.today().strftime("%Y-%m-%d")
        
        fecha_desde = f"{fecha} 00:00:00"
        fecha_hasta = f"{fecha} 23:59:59"
        
        # 1. RESUMEN GENERAL
        cur.execute("""
            SELECT 
                COUNT(*) as total_ventas,
                SUM(total) as monto_total
            FROM Venta
            WHERE fecha BETWEEN %s AND %s AND estado = 'completada'
        """, (fecha_desde, fecha_hasta))
        general = cur.fetchone()
        
        # 2. VENTAS POR CATEGORÍA
        cur.execute("""
            SELECT 
                COALESCE(c.nombre, 'Sin Categoría') as nombre_categoria,
                COUNT(DISTINCT v.id_venta) as cantidad_ventas,
                SUM(dv.subtotal) as monto_total
            FROM Venta v
            JOIN DetalleVenta dv ON v.id_venta = dv.id_venta
            LEFT JOIN Producto p ON dv.id_producto = p.id_producto
            LEFT JOIN Categoria c ON p.id_categoria = c.id_categoria
            WHERE v.fecha BETWEEN %s AND %s AND v.estado = 'completada'
            GROUP BY c.id_categoria, c.nombre
            ORDER BY monto_total DESC
        """, (fecha_desde, fecha_hasta))
        categorias = list(cur.fetchall() or [])
        
        # 3. VENTAS POR VENDEDOR (¡NUEVO!)
        cur.execute("""
            SELECT 
                u.nombre as vendedor,
                COUNT(v.id_venta) as cantidad_ventas,
                SUM(v.total) as monto_total
            FROM Venta v
            LEFT JOIN Usuario u ON v.id_usuario = u.id_usuario
            WHERE v.fecha BETWEEN %s AND %s AND v.estado = 'completada'
            GROUP BY u.id_usuario, u.nombre
            ORDER BY monto_total DESC
        """, (fecha_desde, fecha_hasta))
        ventas_por_vendedor = list(cur.fetchall() or [])
        
        # 4. MÉTODOS DE PAGO
        cur.execute("""
            SELECT 
                tipo_pago,
                SUM(total) as monto
            FROM Venta
            WHERE fecha BETWEEN %s AND %s AND estado = 'completada'
            GROUP BY tipo_pago
        """, (fecha_desde, fecha_hasta))
        metodos = {row['tipo_pago']: float(row['monto']) for row in cur.fetchall()}
        
        # 5. MOVIMIENTOS DE CAJA DEL DÍA
        cur.execute("""
            SELECT 
                SUM(CASE WHEN motivo = 'pago_cuenta_corriente_efectivo' THEN monto ELSE 0 END) as cobros_cc,
                SUM(CASE WHEN tipo = 'egreso' THEN monto ELSE 0 END) as egresos
            FROM caja_movimiento cm
            WHERE DATE(cm.fecha_hora) = %s
        """, (fecha,))
        caja = cur.fetchone() or {'cobros_cc': 0, 'egresos': 0}
        
        efectivo_ventas = metodos.get('efectivo', 0.0)
        efectivo_final = efectivo_ventas + float(caja['cobros_cc'] or 0) - float(caja['egresos'] or 0)
        
        return {
            'fecha': fecha,
            'total_ventas': int(general['total_ventas'] or 0),
            'monto_total': float(general['monto_total'] or 0),
            'categorias': categorias,
            'ventas_por_vendedor': ventas_por_vendedor, # <--- Agregamos esto al resultado
            'metodos_pago': metodos,
            'movimientos_caja': {
                'cobros_cc': float(caja['cobros_cc'] or 0),
                'egresos': float(caja['egresos'] or 0),
                'efectivo_final': efectivo_final
            }
        }
        
    except Exception as e:
        logger.error(f"obtener_resumen_diario: {e}")
        return {}
    finally:
        if cur: cur.close()
        if conn: conn.close()