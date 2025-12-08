import mysql.connector
import sys

# Configuración (Puerto 3307)
DB_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "",
    "database": "supermercado_don_atilio"
}

def reparar_v3():
    print("\n" + "="*60)
    print(" 🛠️  REPARACIÓN V3: TABLA COMPRA Y MEDIOS DE PAGO")
    print("="*60)

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ Conectado a la BD.")
        
        # 1. Revisar Tabla COMPRA
        print("\n[1/2] Verificando tabla 'Compra'...")
        cursor.execute("DESCRIBE Compra")
        cols = [row[0] for row in cursor.fetchall()]
        
        if "medio_pago" not in cols:
            print("   ⚠️ Falta columna 'medio_pago'. Agregando...")
            # Agregamos la columna
            cursor.execute("ALTER TABLE Compra ADD COLUMN medio_pago VARCHAR(50) DEFAULT 'efectivo'")
            print("   ✅ Columna agregada.")
        else:
            print("   ✔️ La columna 'medio_pago' ya existe.")

        # 2. Revisar si hay compras viejas con estado NULL o medio_pago NULL
        print("\n[2/2] Normalizando datos existentes...")
        cursor.execute("UPDATE Compra SET medio_pago = 'efectivo' WHERE medio_pago IS NULL")
        
        conn.commit()
        print("\n✨ REPARACIÓN COMPLETADA. Ahora puedes registrar compras. ✨")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        try: conn.close()
        except: pass

if __name__ == "__main__":
    reparar_v3()