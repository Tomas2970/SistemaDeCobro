import mysql.connector

# Configuración de la conexión
def conectar():
    return mysql.connector.connect(
        host="localhost",
        port = 3307,
        user="root",
        password="tomas",
        database="supermercado_don_atilio"
    )


# Funciones para CLIENTE

def insertar_cliente(nombre, direccion, telefono, email):
    conexion = conectar()
    cursor = conexion.cursor()
    sql = "INSERT INTO Cliente (nombre, direccion, telefono, email) VALUES (%s, %s, %s, %s)"
    valores = (nombre, direccion, telefono, email)
    cursor.execute(sql, valores)
    conexion.commit()
    conexion.close()
    print("✅ Cliente insertado correctamente.")

def obtener_clientes():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Cliente")
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

# Funciones para PRODUCTO

def insertar_producto(nombre, precio, id_categoria):
    conexion = conectar()
    cursor = conexion.cursor()
    sql = "INSERT INTO Producto (nombre, precio, id_categoria) VALUES (%s, %s, %s)"
    valores = (nombre, precio, id_categoria)
    cursor.execute(sql, valores)
    conexion.commit()
    conexion.close()
    print("✅ Producto insertado correctamente.")

def obtener_productos():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Producto")
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


# PRUEBA RÁPIDA

if __name__ == "__main__":
    # Insertar un cliente de prueba
    insertar_cliente("Juan Pérez", "San Martín 123", "3412345678", "juan@mail.com")

    # Listar clientes
    clientes = obtener_clientes()
    for c in clientes:
        print(c)
