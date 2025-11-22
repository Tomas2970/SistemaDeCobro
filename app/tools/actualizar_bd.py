import sys
import mysql.connector
from app.database.DB import conectar

def actualizar_estructura():
    print("Iniciando actualización de estructura de Base de Datos...")
    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()

        # 1. Agregar margen_ganancia a Categoria si no existe
        try:
            cur.execute("SELECT margen_ganancia FROM Categoria LIMIT 1")
            print("✓ Columna 'margen_ganancia' ya existe.")
            cur.fetchall() # Limpiar cursor
        except mysql.connector.Error as err:
            if err.errno == 1054: # Unknown column
                print(">>> Agregando columna 'margen_ganancia'...")
                cur.execute("ALTER TABLE Categoria ADD COLUMN margen_ganancia DECIMAL(5,2) DEFAULT 30.00")
            else:
                raise err

        # 2. Crear tablas de Caja si no existen
        print(">>> Verificando tablas de Caja...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS AperturaCierreCaja (
          id_caja INT AUTO_INCREMENT PRIMARY KEY,
          id_usuario INT NOT NULL,
          fecha_apertura DATETIME DEFAULT CURRENT_TIMESTAMP,
          fecha_cierre DATETIME NULL,
          monto_inicial DECIMAL(10,2) NOT NULL,
          monto_final_real DECIMAL(10,2) NULL,
          monto_sistema DECIMAL(10,2) NULL,
          diferencia DECIMAL(10,2) NULL,
          observaciones TEXT,
          estado VARCHAR(20) DEFAULT 'abierta',
          CONSTRAINT fk_caja_usuario FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario),
          INDEX idx_caja_estado (estado)
        ) ENGINE=InnoDB;
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS MovimientoCaja (
          id_movimiento INT AUTO_INCREMENT PRIMARY KEY,
          id_caja INT NOT NULL,
          tipo VARCHAR(20) NOT NULL,
          monto DECIMAL(10,2) NOT NULL,
          descripcion VARCHAR(200),
          fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT fk_mov_caja FOREIGN KEY (id_caja) REFERENCES AperturaCierreCaja(id_caja)
          ON DELETE CASCADE,
          INDEX idx_mov_caja (id_caja)
        ) ENGINE=InnoDB;
        """)

        # 3. Trigger para Caja
        print(">>> Actualizando Trigger de Caja...")
        cur.execute("DROP TRIGGER IF EXISTS trg_venta_a_caja")
        cur.execute("""
        CREATE TRIGGER trg_venta_a_caja
        AFTER UPDATE ON Venta
        FOR EACH ROW
        BEGIN
            DECLARE v_id_caja INT;
            IF NEW.estado = 'completada' AND NEW.tipo_pago = 'efectivo' AND OLD.estado <> 'completada' THEN
                SELECT id_caja INTO v_id_caja FROM AperturaCierreCaja 
                WHERE estado = 'abierta' ORDER BY id_caja DESC LIMIT 1;
                
                IF v_id_caja IS NOT NULL THEN
                    INSERT INTO MovimientoCaja (id_caja, tipo, monto, descripcion)
                    VALUES (v_id_caja, 'venta_efectivo', NEW.total, CONCAT('Venta #', NEW.id_venta));
                END IF;
            END IF;
        END
        """)

        conn.commit()
        print("\n✅ Estructura actualizada correctamente.")

    except Exception as e:
        print(f"\n❌ Error actualizando BD: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    actualizar_estructura()