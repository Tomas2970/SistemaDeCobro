import mysql.connector
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3307"))
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
        # 1. TABLA CATEGORIA
        # ----------------------------------------------------
        cursor.execute("DESCRIBE Categoria")
        cols_cat = [row[0] for row in cursor.fetchall()]
        if "margen_ganancia" not in cols_cat:
            cursor.execute("ALTER TABLE Categoria ADD COLUMN margen_ganancia DECIMAL(5,2) DEFAULT 30.00")
        if "es_pesable_default" not in cols_cat:
            cursor.execute("ALTER TABLE Categoria ADD COLUMN es_pesable_default BOOLEAN DEFAULT FALSE")

        # ----------------------------------------------------
        # 2. TABLA CLIENTE
        # ----------------------------------------------------
        cursor.execute("DESCRIBE Cliente")
        cols_cliente = [row[0] for row in cursor.fetchall()]
        if "dni" not in cols_cliente:
            cursor.execute("ALTER TABLE Cliente ADD COLUMN dni VARCHAR(8) NULL UNIQUE")
        if "cuit" not in cols_cliente:
            cursor.execute("ALTER TABLE Cliente ADD COLUMN cuit VARCHAR(11) NULL UNIQUE")
        if "direccion" not in cols_cliente:
            cursor.execute("ALTER TABLE Cliente ADD COLUMN direccion VARCHAR(200) NULL")

        # ----------------------------------------------------
        # 3. TABLA PROVEEDOR
        # ----------------------------------------------------
        cursor.execute("DESCRIBE Proveedor")
        cols_prov = [row[0] for row in cursor.fetchall()]
        if "dni" not in cols_prov:
            cursor.execute("ALTER TABLE Proveedor ADD COLUMN dni VARCHAR(8) NULL UNIQUE")
        if "cuit" not in cols_prov:
            cursor.execute("ALTER TABLE Proveedor ADD COLUMN cuit VARCHAR(11) NOT NULL DEFAULT ''")
        if "direccion" not in cols_prov:
            cursor.execute("ALTER TABLE Proveedor ADD COLUMN direccion VARCHAR(200) NULL")
        if "saldo" not in cols_prov:
            cursor.execute("ALTER TABLE Proveedor ADD COLUMN saldo DECIMAL(10,2) DEFAULT 0.00")

        # ----------------------------------------------------
        # 4. TABLA COMPRA Y DETALLE_COMPRA
        # ----------------------------------------------------
        cursor.execute("DESCRIBE Compra")
        cols_compra = [row[0] for row in cursor.fetchall()]
        if "medio_pago" not in cols_compra:
            cursor.execute("ALTER TABLE Compra ADD COLUMN medio_pago VARCHAR(50) DEFAULT 'efectivo'")
        if "id_session" not in cols_compra:
            cursor.execute("ALTER TABLE Compra ADD COLUMN id_session INT NULL")

        cursor.execute("DESCRIBE DetalleCompra")
        cols_detalle_compra = [row[0] for row in cursor.fetchall()]
        if "precio_venta_historico" not in cols_detalle_compra:
            cursor.execute("ALTER TABLE DetalleCompra ADD COLUMN precio_venta_historico DECIMAL(10,2) NULL AFTER precio_unitario")

        # ----------------------------------------------------
        # 5. 🔥 TABLA VENTA (id_session) - ARREGLA EL ERROR DE VENTAS
        # ----------------------------------------------------
        cursor.execute("DESCRIBE Venta")
        cols_venta = [row[0] for row in cursor.fetchall()]
        if "id_session" not in cols_venta:
            logger.info("🔧 Migrando: Agregando id_session a Venta")
            cursor.execute("ALTER TABLE Venta ADD COLUMN id_session INT NULL")
            try:
                cursor.execute("ALTER TABLE Venta ADD CONSTRAINT fk_venta_session FOREIGN KEY (id_session) REFERENCES caja_session(id_session) ON DELETE SET NULL")
            except: pass

        # ----------------------------------------------------
        # 6. 🔥 TABLA CAJA_MOVIMIENTO (id_session) - ARREGLA EL SALDO $0
        # ----------------------------------------------------
        cursor.execute("DESCRIBE caja_movimiento")
        cols_mov = [row[0] for row in cursor.fetchall()]
        if "id_session" not in cols_mov:
            logger.info("🔧 Migrando: Agregando id_session a caja_movimiento")
            cursor.execute("ALTER TABLE caja_movimiento ADD COLUMN id_session INT NOT NULL AFTER id_movimiento")

        # ----------------------------------------------------
        # 7. TABLA PAGO_PROVEEDOR (Crear si no existe)
        # ----------------------------------------------------
        cursor.execute("SHOW TABLES LIKE 'PagoProveedor'")
        if not cursor.fetchone():
            logger.info("🔧 Migrando: Creando tabla PagoProveedor")
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
        # 8. SEMILLA DE CATEGORÍAS (Si está vacía)
        # ----------------------------------------------------
        cursor.execute("SELECT COUNT(*) FROM Categoria")
        if cursor.fetchone()[0] == 0:
            logger.info("🔧 Migrando: Sembrando categorías iniciales")
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
        conn.rollback()
    finally:
        if conn: conn.close()