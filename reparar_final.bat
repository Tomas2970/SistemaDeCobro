import mysql.connector
import os
from dotenv import load_dotenv

# Configuración forzada para tu sistema Don Atilio
DB_HOST = "localhost"
DB_PORT = 3307  # <--- IMPORTANTE: Tu sistema usa este puerto
DB_USER = "root"
DB_PASSWORD = "" # Asumimos vacío por defecto en tu setup portable
DB_NAME = "supermercado_don_atilio"

def reparar():
    print(f"🔌 Conectando a {DB_HOST}:{DB_PORT}...")
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, 
            port=DB_PORT, 
            user=DB_USER, 
            password=DB_PASSWORD, 
            database=DB_NAME
        )
        cursor = conn.cursor()
        print("✅ Conexión exitosa.")
        
        # 1. Reparar Categoria
        try:
            cursor.execute("SELECT es_pesable_default FROM Categoria LIMIT 1")
            print("   -> Tabla Categoria OK.")
        except mysql.connector.Error as err:
            if err.errno == 1054:
                print("   ⚠️ Agregando columna 'es_pesable_default'...")
                cursor.execute("ALTER TABLE Categoria ADD COLUMN es_pesable_default BOOLEAN DEFAULT FALSE")
                print("   ✅ Listo.")

        # 2. Reparar Proveedor
        try:
            cursor.execute("SELECT saldo FROM Proveedor LIMIT 1")
            print("   -> Tabla Proveedor OK.")
        except mysql.connector.Error as err:
            if err.errno == 1054:
                print("   ⚠️ Agregando columna 'saldo'...")
                cursor.execute("ALTER TABLE Proveedor ADD COLUMN saldo DECIMAL(10,2) DEFAULT 0.00")
                print("   ✅ Listo.")

        conn.commit()
        conn.close()
        print("\n✨ BASE DE DATOS REPARADA EXITOSAMENTE ✨")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Asegúrate de que el programa Don Atilio esté CERRADO pero el servicio MySQL corriendo.")
        # Nota: A veces es más fácil correr esto con el programa abierto para asegurar que MySQL está activo.

if __name__ == "__main__":
    reparar()