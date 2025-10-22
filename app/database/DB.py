import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, date

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# =====================================
# Conexión a la base de datos
# =====================================
def conectar():
    """Establece conexión con la base de datos usando variables de entorno"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3307)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "supermercado_don_atilio")
        )
        return connection
    except mysql.connector.Error as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        raise

# =====================================
# Funciones para CLIENTE
# =====================================
def insertar_cliente(nombre, direccion="", telefono="", email=""):
    """Inserta un nuevo cliente en la base de datos"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Validar que el nombre no esté vacío
        if not nombre.strip():
            raise ValueError("El nombre del cliente no puede estar vacío")
        
        sql = "INSERT INTO Cliente (nombre, direccion, telefono, email) VALUES (%s, %s, %s, %s)"
        valores = (nombre.strip(), direccion.strip(), telefono.strip(), email.strip())
        cursor.execute(sql, valores)
        conn.commit()
        
        logger.info(f"Cliente '{nombre}' insertado correctamente con ID: {cursor.lastrowid}")
        return cursor.lastrowid
        
    except mysql.connector.IntegrityError as e:
        logger.error(f"Error de integridad al insertar cliente: {e}")
        return None
    except mysql.connector.Error as e:
        logger.error(f"Error de base de datos al insertar cliente: {e}")
        return None
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_clientes():
    """Obtiene todos los clientes"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Cliente ORDER BY nombre")
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener clientes: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def buscar_cliente_por_email(email):
    """Busca un cliente por su email"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Cliente WHERE email = %s", (email,))
        resultado = cursor.fetchone()
        return resultado
    except mysql.connector.Error as e:
        logger.error(f"Error al buscar cliente por email: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# =====================================
# Funciones para PRODUCTO
# =====================================
def insertar_producto(nombre, precio, id_categoria):
    """Inserta un nuevo producto"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Validaciones
        if not nombre.strip():
            raise ValueError("El nombre del producto no puede estar vacío")
        if precio <= 0:
            raise ValueError("El precio debe ser mayor a 0")
        
        sql = "INSERT INTO Producto (nombre, precio, id_categoria) VALUES (%s, %s, %s)"
        valores = (nombre.strip(), precio, id_categoria)
        cursor.execute(sql, valores)
        conn.commit()
        
        logger.info(f"Producto '{nombre}' insertado correctamente con ID: {cursor.lastrowid}")
        return cursor.lastrowid
        
    except mysql.connector.Error as e:
        logger.error(f"Error al insertar producto: {e}")
        return None
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_productos():
    """Obtiene todos los productos"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, c.nombre as nombre_categoria 
            FROM Producto p
            LEFT JOIN Categoria c ON p.id_categoria = c.id_categoria
            ORDER BY p.nombre
        """)
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener productos: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# =====================================
# Funciones para INVENTARIO
# =====================================
def actualizar_stock(id_producto, cantidad):
    """Actualiza el stock de un producto con validación"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Verificar stock actual
        cursor.execute("SELECT cantidad FROM Inventario WHERE id_producto = %s", (id_producto,))
        resultado = cursor.fetchone()
        
        if not resultado:
            raise ValueError(f"No existe inventario para el producto con ID {id_producto}")
        
        stock_actual = resultado[0]
        nuevo_stock = stock_actual + cantidad
        
        # Validar que el stock no quede negativo
        if nuevo_stock < 0:
            raise ValueError(f"Stock insuficiente. Stock actual: {stock_actual}, intentando restar: {abs(cantidad)}")
        
        sql = "UPDATE Inventario SET cantidad = %s WHERE id_producto = %s"
        cursor.execute(sql, (nuevo_stock, id_producto))
        conn.commit()
        
        logger.info(f"Stock actualizado para producto ID {id_producto}: {stock_actual} -> {nuevo_stock}")
        return True
        
    except mysql.connector.Error as e:
        logger.error(f"Error al actualizar stock: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_inventario():
    """Obtiene el inventario completo con alertas de stock bajo"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                p.id_producto,
                p.nombre, 
                i.cantidad, 
                i.stock_minimo,
                CASE 
                    WHEN i.cantidad <= i.stock_minimo THEN 'ALERTA'
                    WHEN i.cantidad <= i.stock_minimo * 1.5 THEN 'ADVERTENCIA'
                    ELSE 'OK'
                END as estado_stock
            FROM Inventario i
            JOIN Producto p ON i.id_producto = p.id_producto
            ORDER BY i.cantidad ASC
        """)
        inventario = cursor.fetchall()
        return inventario
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener inventario: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# =====================================
# Funciones para VENTAS (con transacciones)
# =====================================
def insertar_venta(id_usuario, id_cliente=0):
    """Inserta nueva venta; id_cliente opcional (0/None -> NULL)."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        id_cliente_db = None if (id_cliente in (0, None)) else id_cliente
        sql = "INSERT INTO Venta (id_usuario, id_cliente) VALUES (%s, %s)"
        cursor.execute(sql, (id_usuario, id_cliente_db))
        conn.commit()
        id_venta = cursor.lastrowid
        
        cliente_info = "SIN cliente (NULL)" if (id_cliente in (0, None)) else f"Cliente ID {id_cliente}"
        logger.info(f"Venta registrada con ID: {id_venta} - {cliente_info}")
        return id_venta
        
    except mysql.connector.Error as e:
        logger.error(f"Error al insertar venta: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def insertar_detalle_venta(id_venta, id_producto, cantidad, precio_unitario):
    """Inserta un detalle de venta y actualiza el stock"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Validaciones
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        if precio_unitario <= 0:
            raise ValueError("El precio unitario debe ser mayor a 0")
        
        # Verificar stock disponible ANTES de insertar
        cursor.execute("SELECT cantidad FROM Inventario WHERE id_producto = %s", (id_producto,))
        resultado = cursor.fetchone()
        
        if not resultado:
            raise ValueError(f"No existe inventario para el producto con ID {id_producto}")
        
        stock_actual = resultado[0]
        if stock_actual < cantidad:
            raise ValueError(f"Stock insuficiente. Disponible: {stock_actual}, solicitado: {cantidad}")
        
        # Insertar detalle de venta
        sql = "INSERT INTO DetalleVenta (id_venta, id_producto, cantidad, precio_unitario) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (id_venta, id_producto, cantidad, precio_unitario))
        
        # Reducir stock
        sql_stock = "UPDATE Inventario SET cantidad = cantidad - %s WHERE id_producto = %s"
        cursor.execute(sql_stock, (cantidad, id_producto))
        
        conn.commit()
        logger.info(f"Detalle venta insertado: Producto ID {id_producto}, Cantidad: {cantidad}")
        return True
        
    except mysql.connector.Error as e:
        logger.error(f"Error al insertar detalle de venta: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# =====================================
# Funciones para USUARIOS (con seguridad)
# =====================================
def insertar_usuario(nombre, contraseña, id_rol):
    """Inserta un nuevo usuario con contraseña hasheada"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Validaciones
        if not nombre.strip():
            raise ValueError("El nombre de usuario no puede estar vacío")
        if len(contraseña) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        
        # Hashear contraseña
        password_hash = bcrypt.hashpw(contraseña.encode('utf-8'), bcrypt.gensalt())
        
        sql = "INSERT INTO Usuario (nombre, contraseña, id_rol) VALUES (%s, %s, %s)"
        cursor.execute(sql, (nombre.strip(), password_hash.decode('utf-8'), id_rol))
        conn.commit()
        
        logger.info(f"Usuario '{nombre}' insertado correctamente con ID: {cursor.lastrowid}")
        return cursor.lastrowid
        
    except mysql.connector.IntegrityError as e:
        logger.error(f"Error de integridad al insertar usuario: {e}")
        return None
    except mysql.connector.Error as e:
        logger.error(f"Error de base de datos al insertar usuario: {e}")
        return None
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def verificar_contraseña(nombre_usuario, contraseña):
    """Verifica las credenciales de un usuario"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Usuario WHERE nombre = %s", (nombre_usuario,))
        usuario = cursor.fetchone()
        
        if not usuario:
            logger.warning(f"Intento de login fallido: usuario '{nombre_usuario}' no encontrado")
            return None
        
        # Verificar contraseña
        if bcrypt.checkpw(contraseña.encode('utf-8'), usuario['contraseña'].encode('utf-8')):
            logger.info(f"Login exitoso para usuario '{nombre_usuario}'")
            return usuario
        else:
            logger.warning(f"Intento de login fallido: contraseña incorrecta para '{nombre_usuario}'")
            return None
            
    except mysql.connector.Error as e:
        logger.error(f"Error al verificar contraseña: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_usuarios():
    """Obtiene todos los usuarios (sin mostrar contraseñas)"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, r.nombre as rol
            FROM Usuario u
            JOIN Rol r ON u.id_rol = r.id_rol
            ORDER BY u.nombre
        """)
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener usuarios: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def eliminar_usuario(id_usuario):
    """Elimina un usuario (considera usar soft delete en producción)"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Verificar que el usuario existe
        cursor.execute("SELECT nombre FROM Usuario WHERE id_usuario = %s", (id_usuario,))
        usuario = cursor.fetchone()
        
        if not usuario:
            raise ValueError(f"No existe usuario con ID {id_usuario}")
        
        sql = "DELETE FROM Usuario WHERE id_usuario = %s"
        cursor.execute(sql, (id_usuario,))
        conn.commit()
        
        logger.info(f"Usuario '{usuario[0]}' (ID: {id_usuario}) eliminado correctamente")
        return True
        
    except mysql.connector.Error as e:
        logger.error(f"Error al eliminar usuario: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def modificar_usuario(id_usuario, nombre=None, contraseña=None, id_rol=None):
    """Modifica los datos de un usuario"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        updates = []
        valores = []
        
        if nombre is not None and nombre.strip():
            updates.append("nombre = %s")
            valores.append(nombre.strip())
        
        if contraseña is not None:
            if len(contraseña) < 6:
                raise ValueError("La contraseña debe tener al menos 6 caracteres")
            password_hash = bcrypt.hashpw(contraseña.encode('utf-8'), bcrypt.gensalt())
            updates.append("contraseña = %s")
            valores.append(password_hash.decode('utf-8'))
        
        if id_rol is not None:
            updates.append("id_rol = %s")
            valores.append(id_rol)
        
        if not updates:
            raise ValueError("No se especificaron campos para actualizar")
        
        sql = f"UPDATE Usuario SET {', '.join(updates)} WHERE id_usuario = %s"
        valores.append(id_usuario)
        cursor.execute(sql, valores)
        conn.commit()
        
        logger.info(f"Usuario ID {id_usuario} modificado correctamente")
        return True
        
    except mysql.connector.Error as e:
        logger.error(f"Error al modificar usuario: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# =====================================
# Funciones para VISTAS
# =====================================
def obtener_stock_bajo():
    """Obtiene productos con stock bajo o crítico usando la vista"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vista_stock_bajo")
        resultados = cursor.fetchall()
        logger.info(f"Se encontraron {len(resultados)} productos con stock bajo")
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener stock bajo: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_ventas_diarias(fecha_inicio=None, fecha_fin=None):
    """Obtiene resumen de ventas por día usando la vista"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        
        if fecha_inicio and fecha_fin:
            sql = """
                SELECT * FROM vista_ventas_diarias 
                WHERE fecha BETWEEN %s AND %s
                ORDER BY fecha DESC
            """
            cursor.execute(sql, (fecha_inicio, fecha_fin))
        else:
            cursor.execute("SELECT * FROM vista_ventas_diarias LIMIT 30")
        
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener ventas diarias: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_productos_mas_vendidos(limite=10):
    """Obtiene los productos más vendidos usando la vista"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        sql = f"SELECT * FROM vista_productos_mas_vendidos LIMIT {limite}"
        cursor.execute(sql)
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener productos más vendidos: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_clientes_con_deuda():
    """Obtiene clientes con deuda usando la vista"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vista_clientes_deuda")
        resultados = cursor.fetchall()
        logger.info(f"Se encontraron {len(resultados)} clientes con deuda")
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener clientes con deuda: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# =====================================
# Funciones para PROCEDIMIENTOS ALMACENADOS
# =====================================
def crear_producto_completo(nombre, precio, id_categoria, stock_inicial, stock_minimo):
    """Crea un producto con su inventario usando procedimiento almacenado"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Validaciones
        if not nombre.strip():
            raise ValueError("El nombre del producto no puede estar vacío")
        if precio <= 0:
            raise ValueError("El precio debe ser mayor a 0")
        if stock_inicial < 0:
            raise ValueError("El stock inicial no puede ser negativo")
        
        # Llamar al procedimiento almacenado
        cursor.callproc('crear_producto_con_inventario', 
                       [nombre.strip(), precio, id_categoria, stock_inicial, stock_minimo])
        
        # Obtener el resultado
        for result in cursor.stored_results():
            producto_id = result.fetchone()[0]
        
        conn.commit()
        logger.info(f"Producto '{nombre}' creado con inventario. ID: {producto_id}")
        return producto_id
        
    except mysql.connector.Error as e:
        logger.error(f"Error al crear producto completo: {e}")
        if 'conn' in locals():
            conn.rollback()
        return None
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def procesar_venta_completa(id_usuario, id_cliente, tipo_pago):
    """Procesa una venta completa usando procedimiento almacenado"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Validar tipo de pago
        tipos_validos = ['efectivo', 'tarjeta', 'cuenta_corriente', 'transferencia']
        if tipo_pago not in tipos_validos:
            raise ValueError(f"Tipo de pago inválido. Debe ser: {', '.join(tipos_validos)}")
        
        # Llamar al procedimiento almacenado
        cursor.callproc('procesar_venta', [id_usuario, id_cliente, tipo_pago])
        
        # Obtener el ID de la venta creada
        for result in cursor.stored_results():
            venta_id = result.fetchone()[0]
        
        conn.commit()
        logger.info(f"Venta procesada correctamente. ID: {venta_id}")
        return venta_id
        
    except mysql.connector.Error as e:
        logger.error(f"Error al procesar venta: {e}")
        if 'conn' in locals():
            conn.rollback()
        return None
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def registrar_pago_cuenta(id_cuenta, monto, metodo, id_usuario, referencia=""):
    """Registra un pago y actualiza cuenta corriente usando procedimiento almacenado"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Validaciones
        if monto <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        
        metodos_validos = ['efectivo', 'tarjeta_debito', 'tarjeta_credito', 'transferencia', 'cheque']
        if metodo not in metodos_validos:
            raise ValueError(f"Método inválido. Debe ser: {', '.join(metodos_validos)}")
        
        # Llamar al procedimiento almacenado
        cursor.callproc('registrar_pago_cuenta', 
                       [id_cuenta, monto, metodo, id_usuario, referencia])
        
        conn.commit()
        logger.info(f"Pago de ${monto} registrado en cuenta {id_cuenta}")
        return True
        
    except mysql.connector.Error as e:
        logger.error(f"Error al registrar pago: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# =====================================
# Funciones ADICIONALES ÚTILES
# =====================================
def buscar_producto_por_nombre(nombre):
    """Busca productos por nombre (búsqueda parcial)"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT p.*, c.nombre as categoria, i.cantidad as stock
            FROM Producto p
            LEFT JOIN Categoria c ON p.id_categoria = c.id_categoria
            LEFT JOIN Inventario i ON p.id_producto = i.id_producto
            WHERE p.nombre LIKE %s AND p.activo = TRUE
            ORDER BY p.nombre
        """
        cursor.execute(sql, (f"%{nombre}%",))
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al buscar producto: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def buscar_producto_por_codigo_barras(codigo_barras):
    """Busca un producto por su código de barras (para lector de código de barras)"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        
        # Validar que el código no esté vacío
        if not codigo_barras or not codigo_barras.strip():
            raise ValueError("El código de barras no puede estar vacío")
        
        sql = """
            SELECT 
                p.*,
                c.nombre as categoria,
                i.cantidad as stock,
                i.stock_minimo
            FROM Producto p
            LEFT JOIN Categoria c ON p.id_categoria = c.id_categoria
            LEFT JOIN Inventario i ON p.id_producto = i.id_producto
            WHERE p.codigo_barras = %s AND p.activo = TRUE
        """
        cursor.execute(sql, (codigo_barras.strip(),))
        resultado = cursor.fetchone()
        
        if resultado:
            logger.info(f"Producto encontrado por código de barras: {resultado['nombre']}")
        else:
            logger.warning(f"No se encontró producto con código de barras: {codigo_barras}")
        
        return resultado
        
    except mysql.connector.Error as e:
        logger.error(f"Error al buscar por código de barras: {e}")
        return None
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_productos_por_categoria(id_categoria):
    """Obtiene todos los productos de una categoría"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT p.*, i.cantidad as stock, i.stock_minimo
            FROM Producto p
            LEFT JOIN Inventario i ON p.id_producto = i.id_producto
            WHERE p.id_categoria = %s AND p.activo = TRUE
            ORDER BY p.nombre
        """
        cursor.execute(sql, (id_categoria,))
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener productos por categoría: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_categorias():
    """Obtiene todas las categorías activas"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Categoria WHERE activa = TRUE ORDER BY nombre")
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener categorías: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_ventas_cliente(id_cliente):
    """Obtiene todas las ventas de un cliente"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT v.*, u.nombre as vendedor
            FROM Venta v
            LEFT JOIN Usuario u ON v.id_usuario = u.id_usuario
            WHERE v.id_cliente = %s
            ORDER BY v.fecha DESC
        """
        cursor.execute(sql, (id_cliente,))
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener ventas del cliente: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_detalle_venta(id_venta):
    """Obtiene el detalle completo de una venta"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT dv.*, p.nombre as producto
            FROM DetalleVenta dv
            JOIN Producto p ON dv.id_producto = p.id_producto
            WHERE dv.id_venta = %s
        """
        cursor.execute(sql, (id_venta,))
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener detalle de venta: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_auditoria_producto(id_producto, limite=50):
    """Obtiene el historial de auditoría de un producto"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT a.*, u.nombre as usuario
            FROM AuditoriaInventario a
            LEFT JOIN Usuario u ON a.id_usuario = u.id_usuario
            WHERE a.id_producto = %s
            ORDER BY a.fecha DESC
            LIMIT %s
        """
        cursor.execute(sql, (id_producto, limite))
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener auditoría: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_cuenta_corriente_cliente(id_cliente):
    """Obtiene la información de cuenta corriente de un cliente"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT cc.*, c.nombre as cliente
            FROM CuentaCorriente cc
            JOIN Cliente c ON cc.id_cliente = c.id_cliente
            WHERE cc.id_cliente = %s
        """
        cursor.execute(sql, (id_cliente,))
        resultado = cursor.fetchone()
        return resultado
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener cuenta corriente: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_pagos_cliente(id_cliente):
    """Obtiene todos los pagos realizados por un cliente"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT p.*, u.nombre as registrado_por
            FROM Pago p
            JOIN CuentaCorriente cc ON p.id_cuenta = cc.id_cuenta
            LEFT JOIN Usuario u ON p.id_usuario = u.id_usuario
            WHERE cc.id_cliente = %s
            ORDER BY p.fecha DESC
        """
        cursor.execute(sql, (id_cliente,))
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener pagos: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_proveedores():
    """Obtiene todos los proveedores activos"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Proveedor WHERE activo = TRUE ORDER BY nombre")
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener proveedores: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_roles():
    """Obtiene todos los roles disponibles"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Rol ORDER BY nombre")
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener roles: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# =====================================
# Funciones de ESTADÍSTICAS
# =====================================
def obtener_estadisticas_generales():
    """Obtiene estadísticas generales del sistema"""
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        
        estadisticas = {}
        
        # Total de productos
        cursor.execute("SELECT COUNT(*) as total FROM Producto WHERE activo = TRUE")
        estadisticas['total_productos'] = cursor.fetchone()['total']
        
        # Total de clientes
        cursor.execute("SELECT COUNT(*) as total FROM Cliente WHERE activo = TRUE")
        estadisticas['total_clientes'] = cursor.fetchone()['total']
        
        # Total de ventas del mes
        cursor.execute("""
            SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as monto
            FROM Venta 
            WHERE MONTH(fecha) = MONTH(CURRENT_DATE())
            AND YEAR(fecha) = YEAR(CURRENT_DATE())
            AND estado = 'completada'
        """)
        ventas_mes = cursor.fetchone()
        estadisticas['ventas_mes'] = ventas_mes['total']
        estadisticas['monto_ventas_mes'] = ventas_mes['monto']
        
        # Productos con stock bajo
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM Inventario i
            WHERE i.cantidad <= i.stock_minimo
        """)
        estadisticas['productos_stock_bajo'] = cursor.fetchone()['total']
        
        return estadisticas
        
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        return {}
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# =====================================
# Funciones de INFORMES ADICIONALES
# =====================================
def obtener_ventas_por_vendedor(fecha_inicio=None, fecha_fin=None):
    """Obtiene un informe de ventas agrupadas por vendedor
    
    Args:
        fecha_inicio: Fecha de inicio del periodo (opcional)
        fecha_fin: Fecha de fin del periodo (opcional)
    
    Returns:
        Lista de diccionarios con información de ventas por vendedor
    """
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        
        sql = """
            SELECT 
                u.id_usuario,
                u.nombre as vendedor,
                r.nombre as rol,
                COUNT(v.id_venta) as total_ventas,
                COALESCE(SUM(v.total), 0) as monto_total,
                COALESCE(AVG(v.total), 0) as promedio_venta,
                MIN(v.fecha) as primera_venta,
                MAX(v.fecha) as ultima_venta
            FROM Usuario u
            LEFT JOIN Rol r ON u.id_rol = r.id_rol
            LEFT JOIN Venta v ON u.id_usuario = v.id_usuario AND v.estado = 'completada'
        """
        
        parametros = []
        
        # Agregar filtro de fechas si se proporcionan
        if fecha_inicio and fecha_fin:
            sql += " WHERE v.fecha BETWEEN %s AND %s"
            parametros.extend([fecha_inicio, fecha_fin])
        elif fecha_inicio:
            sql += " WHERE v.fecha >= %s"
            parametros.append(fecha_inicio)
        elif fecha_fin:
            sql += " WHERE v.fecha <= %s"
            parametros.append(fecha_fin)
        
        sql += """
            GROUP BY u.id_usuario, u.nombre, r.nombre
            ORDER BY monto_total DESC
        """
        
        cursor.execute(sql, parametros)
        resultados = cursor.fetchall()
        
        logger.info(f"Informe de ventas por vendedor generado: {len(resultados)} vendedores")
        return resultados
        
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener ventas por vendedor: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_cierre_caja(fecha=None, id_usuario=None):
    """Genera un informe de cierre de caja
    
    Args:
        fecha: Fecha del cierre (por defecto: hoy)
        id_usuario: ID del usuario/vendedor (opcional, para cierre individual)
    
    Returns:
        Diccionario con información del cierre de caja
    """
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        
        # Si no se proporciona fecha, usar hoy
        if not fecha:
            from datetime import date
            fecha = date.today()
        
        cierre = {}
        
        # Query base
        sql_base = """
            FROM Venta v
            WHERE DATE(v.fecha) = %s
            AND v.estado = 'completada'
        """
        parametros = [fecha]
        
        # Agregar filtro de usuario si se proporciona
        if id_usuario:
            sql_base += " AND v.id_usuario = %s"
            parametros.append(id_usuario)
        
        # 1. Total general
        sql = f"SELECT COUNT(*) as total_ventas, COALESCE(SUM(v.total), 0) as monto_total {sql_base}"
        cursor.execute(sql, parametros)
        resultado = cursor.fetchone()
        cierre['total_ventas'] = resultado['total_ventas']
        cierre['monto_total'] = resultado['monto_total']
        
        # 2. Ventas por tipo de pago
        sql = f"""
            SELECT 
                v.tipo_pago,
                COUNT(*) as cantidad,
                COALESCE(SUM(v.total), 0) as monto
            {sql_base}
            GROUP BY v.tipo_pago
        """
        cursor.execute(sql, parametros)
        cierre['por_tipo_pago'] = cursor.fetchall()
        
        # 3. Detalle por vendedor (solo si no se filtró por usuario)
        if not id_usuario:
            sql = f"""
                SELECT 
                    u.nombre as vendedor,
                    COUNT(*) as total_ventas,
                    COALESCE(SUM(v.total), 0) as monto_total
                {sql_base}
                LEFT JOIN Usuario u ON v.id_usuario = u.id_usuario
                GROUP BY u.id_usuario, u.nombre
                ORDER BY monto_total DESC
            """
            cursor.execute(sql, parametros)
            cierre['por_vendedor'] = cursor.fetchall()
        else:
            # Si se filtró por usuario, obtener nombre
            cursor.execute("SELECT nombre FROM Usuario WHERE id_usuario = %s", (id_usuario,))
            usuario = cursor.fetchone()
            cierre['vendedor'] = usuario['nombre'] if usuario else 'Desconocido'
        
        # 4. Productos más vendidos del día
        sql = f"""
            SELECT 
                p.nombre as producto,
                SUM(dv.cantidad) as cantidad_vendida,
                COALESCE(SUM(dv.subtotal), 0) as total_vendido
            FROM DetalleVenta dv
            JOIN Producto p ON dv.id_producto = p.id_producto
            JOIN Venta v ON dv.id_venta = v.id_venta
            WHERE DATE(v.fecha) = %s
            AND v.estado = 'completada'
        """
        params_productos = [fecha]
        
        if id_usuario:
            sql += " AND v.id_usuario = %s"
            params_productos.append(id_usuario)
        
        sql += """
            GROUP BY p.id_producto, p.nombre
            ORDER BY cantidad_vendida DESC
            LIMIT 10
        """
        cursor.execute(sql, params_productos)
        cierre['top_productos'] = cursor.fetchall()
        
        # 5. Información adicional
        cierre['fecha'] = fecha
        cierre['fecha_generacion'] = datetime.now()
        
        logger.info(f"Cierre de caja generado para fecha: {fecha}")
        return cierre
        
    except mysql.connector.Error as e:
        logger.error(f"Error al generar cierre de caja: {e}")
        return {}
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obtener_ventas_por_periodo(fecha_inicio, fecha_fin, agrupar_por='dia'):
    """Obtiene ventas agrupadas por periodo
    
    Args:
        fecha_inicio: Fecha de inicio
        fecha_fin: Fecha de fin
        agrupar_por: 'dia', 'semana', 'mes' (por defecto: 'dia')
    
    Returns:
        Lista de ventas agrupadas por el periodo especificado
    """
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        
        # Determinar el formato de agrupación
        if agrupar_por == 'semana':
            fecha_format = "DATE_FORMAT(v.fecha, '%Y-%u')"
            fecha_label = "semana"
        elif agrupar_por == 'mes':
            fecha_format = "DATE_FORMAT(v.fecha, '%Y-%m')"
            fecha_label = "mes"
        else:  # dia
            fecha_format = "DATE(v.fecha)"
            fecha_label = "fecha"
        
        sql = f"""
            SELECT 
                {fecha_format} as {fecha_label},
                COUNT(*) as total_ventas,
                COALESCE(SUM(v.total), 0) as monto_total,
                COALESCE(AVG(v.total), 0) as promedio_venta
            FROM Venta v
            WHERE v.fecha BETWEEN %s AND %s
            AND v.estado = 'completada'
            GROUP BY {fecha_format}
            ORDER BY {fecha_format}
        """
        
        cursor.execute(sql, (fecha_inicio, fecha_fin))
        resultados = cursor.fetchall()
        
        return resultados
        
    except mysql.connector.Error as e:
        logger.error(f"Error al obtener ventas por periodo: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def obtener_vendedores():
    """
    Retorna lista de vendedores [{id_usuario, nombre}] para filtros en reportes.
    """
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id_usuario, nombre FROM Usuario ORDER BY nombre ASC")
        rows = cur.fetchall() or []
        return [{"id_usuario": r["id_usuario"], "nombre": r["nombre"]} for r in rows]
    except mysql.connector.Error as e:
        logger.error(f"Error en obtener_vendedores: {e}")
        return []
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass

def reporte_ventas_por_vendedor(desde: str, hasta: str, id_vendedor: int | None = None):
    """
    Filas separadas por fecha y vendedor:
    [{"Fecha": "YYYY-MM-DD", "Vendedor": "Nombre", "Cant. Ventas": int, "Monto Total": float}, ...]
    """
    where = []
    params = []
    if desde:
        where.append("DATE(v.fecha) >= %s"); params.append(desde)
    if hasta:
        where.append("DATE(v.fecha) <= %s"); params.append(hasta)
    if id_vendedor is not None:
        where.append("v.id_usuario = %s"); params.append(int(id_vendedor))
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT
            DATE(v.fecha) AS Fecha,
            COALESCE(u.nombre, 'Desconocido') AS Vendedor,
            COUNT(v.id_venta) AS `Cant. Ventas`,
            COALESCE(SUM(v.total), 0) AS `Monto Total`
        FROM Venta AS v
        LEFT JOIN Usuario AS u ON u.id_usuario = v.id_usuario
        {where_sql}
        GROUP BY DATE(v.fecha), u.nombre
        ORDER BY DATE(v.fecha) ASC, u.nombre ASC
    """
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall() or []
        out = []
        for r in rows:
            out.append({
                "Fecha": r.get("Fecha") or r.get("fecha"),
                "Vendedor": r.get("Vendedor") or r.get("vendedor"),
                "Cant. Ventas": r.get("Cant. Ventas") or r.get("Cant_Ventas") or r.get("cant_ventas") or 0,
                "Monto Total": r.get("Monto Total") or r.get("Monto_Total") or r.get("monto_total") or 0.0,
            })
        return out
    except mysql.connector.Error as e:
        logger.error(f"Error en reporte_ventas_por_vendedor: {e}")
        return []
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass
