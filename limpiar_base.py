import sys; sys.stdout.reconfigure(encoding='utf-8')
import mysql.connector
import os
from dotenv import load_dotenv

# Cargar configuración actual (como hace tu app)
load_dotenv()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3307"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "supermercado_don_atilio")

print(f"⚠️ ATENCIÓN: Estás por BORRAR TODA LA BASE DE DATOS '{DB_NAME}'")
confirmacion = input("Escribí 'BORRAR' en mayúsculas para confirmar: ")

if confirmacion == "BORRAR":
    try:
        # Nos conectamos SIN especificar la base (para poder borrarla)
        conn = mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD
        )
        cur = conn.cursor()
        
        # Borramos y volvemos a crearla vacía
        cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        cur.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        print("✅ Base de datos limpiada con éxito. Está 100% vacía.")
        
        cur.close()
        conn.close()
        
        print("\n🚀 Reconstruyendo la estructura de las tablas...")
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # 1. Ejecutar schema.sql base
        print("\n📜 Ejecutando schema.sql base...")
        import subprocess
        mysql_exe = os.path.join("mysql", "bin", "mysql.exe")
        if not os.path.exists(mysql_exe):
            mysql_exe = "mysql" # Fallback si está en PATH
            
        cmd = f'"{mysql_exe}" -h {DB_HOST} -P {DB_PORT} -u {DB_USER} '
        if DB_PASSWORD:
            cmd += f'-p"{DB_PASSWORD}" '
        cmd += f'{DB_NAME} < app\\database\\schema.sql'
        
        resultado = os.system(cmd)
        if resultado != 0:
            print("⚠️ Hubo un problema al ejecutar schema.sql, revisá que mysql.exe funcione.")

        # 2. Ejecutar auto_migrate (parches posteriores)
        print("🔧 Aplicando auto_migraciones...")
        from app.database import auto_migrate
        auto_migrate.ejecutar_migraciones()
        
        # 3. Insertar roles, categorías iniciales y usuario admin123
        print("\n🔐 Generando usuario admin y datos base...")
        from app.tools import seed_initial_data
        seed_initial_data.main()
        
        # Borrar también el archivo de progreso del generador por las dudas
        if os.path.exists("demo_progress.json"):
            os.remove("demo_progress.json")
            
        print("\n🎉 ¡Limpieza y reconstrucción completadas!")
        print("Ya podés ingresar al sistema con:")
        print("Usuario: admin")
        print("Contraseña: admin123")
        
    except Exception as e:
        print(f"❌ Error al intentar limpiar la base: {e}")
else:
    print("Operación cancelada. No se tocó nada.")
