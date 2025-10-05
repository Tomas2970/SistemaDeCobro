import mysql.connector

# =====================================
# Conexión a la base de datos
# =====================================
def conectar():
    return mysql.connector.connect(
        host="localhost",
        port=3307,
        user="root",
        password="tomas",
        database="supermercado_don_atilio"
    )

# =====================================
# Funciones para CLIENTE
# =====================================
def insertar_cliente(nombre, direccion, telefono, email):
    conn = conectar()
    cursor = conn.cursor()
    sql = "INSERT INTO Cliente (nombre, direccion, telefono, email) VALUES (%s, %s, %s, %s)"
    valores = (nombre, direccion, telefono, email)
    cursor.execute(sql, valores)
    conn.commit()
    cursor.close()
    conn.close()
    print("Cliente insertado correctamente.")

def obtener_clientes():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Cliente")
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados

# =====================================
# Funciones para PRODUCTO
# =====================================
def insertar_producto(nombre, precio, id_categoria):
    conn = conectar()
    cursor = conn.cursor()
    sql = "INSERT INTO Producto (nombre, precio, id_categoria) VALUES (%s, %s, %s)"
    valores = (nombre, precio, id_categoria)
    cursor.execute(sql, valores)
    conn.commit()
    cursor.close()
    conn.close()
    print("Producto insertado correctamente.")

def obtener_productos():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Producto")
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados

# =====================================
# Funciones para INVENTARIO
# =====================================
def actualizar_stock(id_producto, cantidad):
    conn = conectar()
    cursor = conn.cursor()
    sql = "UPDATE Inventario SET cantidad = cantidad + %s WHERE id_producto = %s"
    cursor.execute(sql, (cantidad, id_producto))
    conn.commit()
    cursor.close()
    conn.close()

def obtener_inventario():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.nombre, i.cantidad, i.stock_minimo
        FROM Inventario i
        JOIN Producto p ON i.id_producto = p.id_producto
    """)
    inventario = cursor.fetchall()
    cursor.close()
    conn.close()
    return inventario

# =====================================
# Funciones para VENTAS
# =====================================
def insertar_venta(id_usuario, id_cliente):
    conn = conectar()
    cursor = conn.cursor()
    sql = "INSERT INTO Venta (id_usuario, id_cliente) VALUES (%s, %s)"
    cursor.execute(sql, (id_usuario, id_cliente))
    conn.commit()
    id_venta = cursor.lastrowid
    cursor.close()
    conn.close()
    return id_venta

def insertar_detalle_venta(id_venta, id_producto, cantidad, precio_unitario):
    conn = conectar()
    cursor = conn.cursor()
    sql = "INSERT INTO DetalleVenta (id_venta, id_producto, cantidad, precio_unitario) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (id_venta, id_producto, cantidad, precio_unitario))
    conn.commit()
    cursor.close()
    conn.close()
    # Reducir stock
    actualizar_stock(id_producto, -cantidad)

# =====================================
# Funciones para USUARIOS
# =====================================
def insertar_usuario(nombre, contraseña, id_rol):
    conn = conectar()
    cursor = conn.cursor()
    sql = "INSERT INTO Usuario (nombre, contraseña, id_rol) VALUES (%s, %s, %s)"
    cursor.execute(sql, (nombre, contraseña, id_rol))
    conn.commit()
    cursor.close()
    conn.close()
    print("Usuario insertado correctamente.")

def obtener_usuarios():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Usuario")
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados

def eliminar_usuario(id_usuario):
    conn = conectar()
    cursor = conn.cursor()
    sql = "DELETE FROM Usuario WHERE id_usuario = %s"
    cursor.execute(sql, (id_usuario,))
    conn.commit()
    cursor.close()
    conn.close()
    print("Usuario eliminado correctamente.")

def modificar_usuario(id_usuario, nombre=None, contraseña=None, id_rol=None):
    conn = conectar()
    cursor = conn.cursor()
    updates = []
    valores = []
    if nombre is not None:
        updates.append("nombre = %s")
        valores.append(nombre)
    if contraseña is not None:
        updates.append("contraseña = %s")
        valores.append(contraseña)
    if id_rol is not None:
        updates.append("id_rol = %s")
        valores.append(id_rol)
    if updates:
        sql = f"UPDATE Usuario SET {', '.join(updates)} WHERE id_usuario = %s"
        valores.append(id_usuario)
        cursor.execute(sql, valores)
        conn.commit()
    cursor.close()
    conn.close()
    print("Usuario modificado correctamente.")
