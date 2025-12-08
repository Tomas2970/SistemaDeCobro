import mysql.connector
import os
from dotenv import load_dotenv

# Cargar variables de entorno (asumiendo que tienes el .env en la misma carpeta o raíz)
load_dotenv()

# Configuración (intentamos leer del .env, si no usa defaults)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "supermercado_don_atilio")

def reparar():
    print(f"🔌 Conectando a {DB_HOST}:{DB_PORT} usuario={DB_USER}...")
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, 
            port=DB_PORT, 
            user=DB_USER, 
            password=DB_PASSWORD, 
            database=DB_NAME
        )
        cursor = conn.cursor()
        print("✅ Conexión exitosa. Verificando estructura...")
        
        # ---------------------------------------------------------
        # 1. Reparar Tabla Categoria (Falta es_pesable_default)
        # ---------------------------------------------------------
        try:
            print("🔍 Verificando tabla 'Categoria'...")
            cursor.execute("SELECT es_pesable_default FROM Categoria LIMIT 1")
            print("   -> La columna 'es_pesable_default' YA existe.")
        except mysql.connector.Error as err:
            if err.errno == 1054: # Error 1054: Unknown column
                print("   ⚠️ Columna faltante. Agregando 'es_pesable_default'...")
                cursor.execute("ALTER TABLE Categoria ADD COLUMN es_pesable_default BOOLEAN DEFAULT FALSE")
                print("   ✅ ¡Columna agregada con éxito!")
            else:
                print(f"   ❌ Error inesperado verificando Categoria: {err}")

        # ---------------------------------------------------------
        # 2. Reparar Tabla Proveedor (Falta saldo) - Por si acaso
        # ---------------------------------------------------------
        try:
            print("🔍 Verificando tabla 'Proveedor'...")
            cursor.execute("SELECT saldo FROM Proveedor LIMIT 1")
            print("   -> La columna 'saldo' YA existe.")
        except mysql.connector.Error as err:
            if err.errno == 1054:
                print("   ⚠️ Columna faltante. Agregando 'saldo'...")
                cursor.execute("ALTER TABLE Proveedor ADD COLUMN saldo DECIMAL(10,2) DEFAULT 0.00")
                print("   ✅ ¡Columna agregada con éxito!")
            else:
                print(f"   ❌ Error inesperado verificando Proveedor: {err}")

        conn.commit()
        conn.close()
        print("\n✨ REPARACIÓN COMPLETADA ✨")
        print("Ahora puedes abrir el sistema y crear categorías normalmente.")
        
    except mysql.connector.Error as err:
        if err.errno == 1049:
            print(f"\n❌ La base de datos '{DB_NAME}' no existe.")
            print("   Debes ejecutar primero el script de instalación inicial o setup_mysql.bat")
        else:
            print(f"\n❌ Error de conexión: {err}")
            print("   Verifica que XAMPP/MySQL esté corriendo y las credenciales en .env sean correctas.")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")

if __name__ == "__main__":
    reparar()