import mysql.connector
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3307")) # Asumimos puerto 3307 del instalador
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "supermercado_don_atilio")

def get_connection():
    try:
        return mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
        )
    except Exception as e:
        logger.error(f"Error conectando para migración: {e}")
        return None

def ejecutar_migraciones():
    """
    Verifica y aplica cambios estructurales faltantes en la base de datos.
    Se ejecuta al inicio del programa.
    """
    conn = get_connection()
    if not conn:
        logger.warning("No se pudo conectar a la BD para auto-migración. Saltando...")
        return

    cursor = conn.cursor()
    try:
        logger.info("Iniciando chequeo de integridad de base de datos...")

        # ----------------------------------------------------
        # 1. TABLA CATEGORIA (margen_ganancia, es_pesable_default)
        # ----------------------------------------------------
        cursor.execute("DESCRIBE Categoria")
        cols_cat = [row[0] for row in cursor.fetchall()]
        
        if "margen_ganancia" not in cols_cat:
            logger.info("Migrando: Agregando margen_ganancia a Categoria")
            cursor.execute("ALTER TABLE Categoria ADD COLUMN margen_ganancia DECIMAL(5,2) DEFAULT 30.00")
            
        if "es_pesable_default" not in cols_cat:
            logger.info("Migrando: Agregando es_pesable_default a Categoria")
            cursor.execute("ALTER TABLE Categoria ADD COLUMN es_pesable_default BOOLEAN DEFAULT FALSE")

        # ----------------------------------------------------
        # 2. TABLA PROVEEDOR (saldo)
        # ----------------------------------------------------
        cursor.execute("DESCRIBE Proveedor")
        cols_prov = [row[0] for row in cursor.fetchall()]
        
        if "saldo" not in cols_prov:
            logger.info("Migrando: Agregando saldo a Proveedor")
            cursor.execute("ALTER TABLE Proveedor ADD COLUMN saldo DECIMAL(10,2) DEFAULT 0.00")

        # ----------------------------------------------------
        # 3. TABLA COMPRA (medio_pago)
        # ----------------------------------------------------
        cursor.execute("DESCRIBE Compra")
        cols_compra = [row[0] for row in cursor.fetchall()]
        
        if "medio_pago" not in cols_compra:
            logger.info("Migrando: Agregando medio_pago a Compra")
            cursor.execute("ALTER TABLE Compra ADD COLUMN medio_pago VARCHAR(50) DEFAULT 'efectivo'")
            cursor.execute("UPDATE Compra SET medio_pago = 'efectivo' WHERE medio_pago IS NULL")

        # ----------------------------------------------------
        # 4. TABLA PAGO_PROVEEDOR (Crear si no existe)
        # ----------------------------------------------------
        cursor.execute("SHOW TABLES LIKE 'PagoProveedor'")
        if not cursor.fetchone():
            logger.info("Migrando: Creando tabla PagoProveedor")
            sql = """
            CREATE TABLE PagoProveedor (
              id_pago_prov INT AUTO_INCREMENT PRIMARY KEY,
              fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
              monto DECIMAL(10,2) NOT NULL,
              metodo VARCHAR(50) NOT NULL,
              observacion TEXT,
              id_proveedor INT NOT NULL,
              id_usuario INT,
              CHECK (monto > 0),
              CONSTRAINT fk_pagoprov_proveedor FOREIGN KEY (id_proveedor) REFERENCES Proveedor(id_proveedor),
              CONSTRAINT fk_pagoprov_usuario FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
            ) ENGINE=InnoDB;
            """
            cursor.execute(sql)

        # ----------------------------------------------------
        # 5. SEMILLA DE CATEGORÍAS (Si está vacía)
        # ----------------------------------------------------
        cursor.execute("SELECT COUNT(*) FROM Categoria")
        if cursor.fetchone()[0] == 0:
            logger.info("Migrando: Sembrando categorías iniciales")
            sql_seed = """
            INSERT INTO Categoria (nombre, margen_ganancia, es_pesable_default, activa) VALUES 
            ('Almacén', 30.0, 0, 1),
            ('Bebidas', 30.0, 0, 1),
            ('Fiambrería', 40.0, 1, 1),
            ('Limpieza', 25.0, 0, 1),
            ('Verdulería', 35.0, 1, 1),
            ('Carnicería', 35.0, 1, 1),
            ('Kiosco', 40.0, 0, 1);
            """
            cursor.execute(sql_seed)

        conn.commit()
        logger.info("✅ Auto-migración completada exitosamente.")

    except Exception as e:
        logger.error(f"Error crítico durante auto-migración: {e}")
    finally:
        if conn: conn.close()