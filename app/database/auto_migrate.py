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

def _ejecutar_paso(cursor, descripcion, sql, params=None):
    """Ejecuta un paso de migración de forma aislada. Si falla, loguea y continúa."""
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return True
    except Exception as e:
        err_code = getattr(e, 'errno', 0)
        # Ignorar errores de "ya existe" (1060=col duplicada, 1061=key duplicada, 1050=tabla existente)
        if err_code in (1060, 1061, 1050):
            return True
        # Error 1932 = tabla corrupted en engine: intentar DROP y reintentar CREATE
        if err_code == 1932 and 'CREATE TABLE' in sql.upper():
            try:
                # Extraer nombre de tabla del SQL
                import re as _re
                match = _re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)', sql, _re.IGNORECASE)
                if match:
                    tabla = match.group(1)
                    logger.warning(f"Tabla {tabla} corrupta en engine. Intentando DROP + CREATE...")
                    try:
                        cursor.execute(f"DROP TABLE IF EXISTS {tabla}")
                    except: pass
                    cursor.execute(sql)
                    return True
            except Exception as e2:
                logger.warning(f"Migración '{descripcion}' (reintento): {e2}")
                return False
        logger.warning(f"Migración '{descripcion}': {e}")
        return False

def ejecutar_migraciones():
    """
    Verifica y aplica cambios estructurales faltantes en la base de datos.
    Se ejecuta al inicio del programa. Cada paso es independiente.
    """
    conn = get_connection()
    if not conn:
        logger.warning("No se pudo conectar a la BD para auto-migración. Saltando...")
        return

    cursor = conn.cursor()
    try:
        logger.info("Iniciando chequeo de integridad de base de datos...")

        # ============================================================
        # PASO 0: CREAR TABLAS FALTANTES (ANTES de cualquier ALTER)
        # ============================================================
        
        # 0a. caja_session (necesaria para FK de Venta y caja_movimiento)
        cursor.execute("SHOW TABLES LIKE 'caja_session'")
        if not cursor.fetchone():
            logger.info("🔧 Creando tabla caja_session...")
            _ejecutar_paso(cursor, "crear caja_session", """
                CREATE TABLE IF NOT EXISTS caja_session (
                    id_session INT AUTO_INCREMENT PRIMARY KEY,
                    id_usuario_apertura INT NOT NULL,
                    fecha_apertura DATETIME DEFAULT CURRENT_TIMESTAMP,
                    monto_apertura DECIMAL(10,2) NOT NULL,
                    id_usuario_cierre INT NULL,
                    fecha_cierre DATETIME NULL,
                    efectivo_esperado DECIMAL(10,2) NULL,
                    efectivo_contado DECIMAL(10,2) NULL,
                    diferencia DECIMAL(10,2) NULL,
                    observaciones_cierre TEXT NULL,
                    estado ENUM('abierta', 'cerrada') DEFAULT 'abierta',
                    tipo_caja ENUM('turno', 'administrativa') DEFAULT 'turno',
                    FOREIGN KEY (id_usuario_apertura) REFERENCES Usuario(id_usuario),
                    FOREIGN KEY (id_usuario_cierre) REFERENCES Usuario(id_usuario),
                    INDEX idx_caja_estado (estado),
                    INDEX idx_caja_fecha (fecha_apertura)
                ) ENGINE=InnoDB
            """)

        # 0b. caja_movimiento
        cursor.execute("SHOW TABLES LIKE 'caja_movimiento'")
        if not cursor.fetchone():
            logger.info("🔧 Creando tabla caja_movimiento...")
            _ejecutar_paso(cursor, "crear caja_movimiento", """
                CREATE TABLE IF NOT EXISTS caja_movimiento (
                    id_movimiento INT AUTO_INCREMENT PRIMARY KEY,
                    id_session INT NOT NULL,
                    tipo ENUM('ingreso', 'egreso') NOT NULL,
                    monto DECIMAL(10,2) NOT NULL CHECK (monto > 0),
                    medio ENUM('efectivo', 'tarjeta', 'transferencia', 'cuenta_corriente') NOT NULL,
                    motivo ENUM(
                        'apertura_caja', 'venta_efectivo', 'venta_tarjeta',
                        'venta_transferencia', 'venta_cuenta_corriente',
                        'pago_cuenta_corriente_efectivo', 'pago_cuenta_corriente_transferencia',
                        'pago_cuenta_corriente_tarjeta', 'cobro_cuenta_corriente',
                        'pago_proveedor', 'gasto_vario', 'retiro_caja',
                        'devolucion_efectivo', 'ajuste_positivo', 'ajuste_negativo',
                        'transferencia_tesoreria_salida', 'transferencia_tesoreria_entrada',
                        'ingreso_extraordinario', 'otro'
                    ) NOT NULL,
                    id_usuario INT NOT NULL,
                    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                    id_venta INT NULL,
                    id_cliente INT NULL,
                    id_compra INT NULL,
                    descripcion TEXT NULL,
                    FOREIGN KEY (id_session) REFERENCES caja_session(id_session),
                    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario),
                    FOREIGN KEY (id_venta) REFERENCES Venta(id_venta) ON DELETE SET NULL,
                    INDEX idx_mov_session (id_session),
                    INDEX idx_mov_tipo (tipo)
                ) ENGINE=InnoDB
            """)

        # 0c. PagoProveedor
        cursor.execute("SHOW TABLES LIKE 'PagoProveedor'")
        if not cursor.fetchone():
            logger.info("🔧 Creando tabla PagoProveedor...")
            _ejecutar_paso(cursor, "crear PagoProveedor", """
                CREATE TABLE IF NOT EXISTS PagoProveedor (
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
                ) ENGINE=InnoDB
            """)

        # 0d. nota_credito
        cursor.execute("SHOW TABLES LIKE 'nota_credito'")
        if not cursor.fetchone():
            logger.info("🔧 Creando tabla nota_credito...")
            _ejecutar_paso(cursor, "crear nota_credito", """
                CREATE TABLE IF NOT EXISTS nota_credito (
                    id_nota_credito INT AUTO_INCREMENT PRIMARY KEY,
                    id_venta INT NOT NULL,
                    monto DECIMAL(10,2) NOT NULL,
                    tipo_devolucion ENUM('reembolso_efectivo', 'credito_a_favor') NOT NULL,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    id_usuario INT NOT NULL,
                    motivo TEXT,
                    FOREIGN KEY (id_venta) REFERENCES Venta(id_venta),
                    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
                ) ENGINE=InnoDB
            """)

        # 0e. AuditoriaAcciones
        cursor.execute("SHOW TABLES LIKE 'AuditoriaAcciones'")
        if not cursor.fetchone():
            logger.info("🔧 Creando tabla AuditoriaAcciones...")
            _ejecutar_paso(cursor, "crear AuditoriaAcciones", """
                CREATE TABLE IF NOT EXISTS AuditoriaAcciones (
                    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
                    id_usuario INT,
                    accion VARCHAR(100) NOT NULL,
                    tabla_afectada VARCHAR(50),
                    id_registro INT,
                    datos_anteriores JSON,
                    datos_nuevos JSON,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE SET NULL
                ) ENGINE=InnoDB
            """)

        # 0f. AuditoriaInventario
        cursor.execute("SHOW TABLES LIKE 'AuditoriaInventario'")
        if not cursor.fetchone():
            logger.info("🔧 Creando tabla AuditoriaInventario...")
            _ejecutar_paso(cursor, "crear AuditoriaInventario", """
                CREATE TABLE IF NOT EXISTS AuditoriaInventario (
                    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
                    id_producto INT NOT NULL,
                    cantidad_anterior DECIMAL(10, 3) NOT NULL,
                    cantidad_nueva DECIMAL(10, 3) NOT NULL,
                    tipo_movimiento VARCHAR(50) NOT NULL,
                    id_referencia INT,
                    id_usuario INT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observaciones TEXT,
                    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto) ON DELETE CASCADE,
                    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE SET NULL
                ) ENGINE=InnoDB
            """)

        conn.commit()

        # ============================================================
        # PASO 1-8: MIGRACIONES INCREMENTALES (cada una independiente)
        # ============================================================

        # 1. CATEGORIA
        cursor.execute("DESCRIBE Categoria")
        cols_cat = [row[0] for row in cursor.fetchall()]
        if "margen_ganancia" not in cols_cat:
            _ejecutar_paso(cursor, "cat.margen_ganancia", "ALTER TABLE Categoria ADD COLUMN margen_ganancia DECIMAL(5,2) DEFAULT 30.00")
        if "es_pesable_default" not in cols_cat:
            _ejecutar_paso(cursor, "cat.es_pesable_default", "ALTER TABLE Categoria ADD COLUMN es_pesable_default BOOLEAN DEFAULT FALSE")

        # 2. CLIENTE
        cursor.execute("DESCRIBE Cliente")
        cols_cliente = [row[0] for row in cursor.fetchall()]
        if "dni" not in cols_cliente:
            _ejecutar_paso(cursor, "cli.dni", "ALTER TABLE Cliente ADD COLUMN dni VARCHAR(8) NULL UNIQUE")
        if "cuit" not in cols_cliente:
            _ejecutar_paso(cursor, "cli.cuit", "ALTER TABLE Cliente ADD COLUMN cuit VARCHAR(11) NULL UNIQUE")
        if "direccion" not in cols_cliente:
            _ejecutar_paso(cursor, "cli.direccion", "ALTER TABLE Cliente ADD COLUMN direccion VARCHAR(200) NULL")

        # 3. PROVEEDOR
        cursor.execute("DESCRIBE Proveedor")
        cols_prov = [row[0] for row in cursor.fetchall()]
        if "dni" not in cols_prov:
            _ejecutar_paso(cursor, "prov.dni", "ALTER TABLE Proveedor ADD COLUMN dni VARCHAR(8) NULL UNIQUE")
        if "cuit" not in cols_prov:
            _ejecutar_paso(cursor, "prov.cuit", "ALTER TABLE Proveedor ADD COLUMN cuit VARCHAR(11) NOT NULL DEFAULT ''")
        if "direccion" not in cols_prov:
            _ejecutar_paso(cursor, "prov.direccion", "ALTER TABLE Proveedor ADD COLUMN direccion VARCHAR(200) NULL")
        if "saldo" not in cols_prov:
            _ejecutar_paso(cursor, "prov.saldo", "ALTER TABLE Proveedor ADD COLUMN saldo DECIMAL(10,2) DEFAULT 0.00")

        # 4. COMPRA Y DETALLECOMPRA
        cursor.execute("DESCRIBE Compra")
        cols_compra = [row[0] for row in cursor.fetchall()]
        if "medio_pago" not in cols_compra:
            _ejecutar_paso(cursor, "compra.medio_pago", "ALTER TABLE Compra ADD COLUMN medio_pago VARCHAR(50) DEFAULT 'efectivo'")
        if "id_session" not in cols_compra:
            _ejecutar_paso(cursor, "compra.id_session", "ALTER TABLE Compra ADD COLUMN id_session INT NULL")

        cursor.execute("DESCRIBE DetalleCompra")
        cols_dc = [row[0] for row in cursor.fetchall()]
        if "precio_venta_historico" not in cols_dc:
            _ejecutar_paso(cursor, "dc.precio_venta_historico", "ALTER TABLE DetalleCompra ADD COLUMN precio_venta_historico DECIMAL(10,2) NULL AFTER precio_unitario")

        # 5. VENTA (id_session)
        cursor.execute("DESCRIBE Venta")
        cols_venta = [row[0] for row in cursor.fetchall()]
        if "id_session" not in cols_venta:
            logger.info("🔧 Migrando: Agregando id_session a Venta")
            _ejecutar_paso(cursor, "venta.id_session", "ALTER TABLE Venta ADD COLUMN id_session INT NULL")
            _ejecutar_paso(cursor, "venta.fk_session", "ALTER TABLE Venta ADD CONSTRAINT fk_venta_session FOREIGN KEY (id_session) REFERENCES caja_session(id_session) ON DELETE SET NULL")

        # 6. CAJA_MOVIMIENTO (id_session si ya existía sin esa columna)
        try:
            cursor.execute("DESCRIBE caja_movimiento")
            cols_mov = [row[0] for row in cursor.fetchall()]
            if "id_session" not in cols_mov:
                logger.info("🔧 Migrando: Agregando id_session a caja_movimiento")
                _ejecutar_paso(cursor, "mov.id_session", "ALTER TABLE caja_movimiento ADD COLUMN id_session INT NOT NULL AFTER id_movimiento")
        except Exception:
            pass  # Tabla recién creada, ya tiene id_session

        # 7. TESORERIA (tipo_caja y nuevos motivos)
        try:
            cursor.execute("DESCRIBE caja_session")
            cols_session = [row[0] for row in cursor.fetchall()]
            if "tipo_caja" not in cols_session:
                logger.info("🔧 Migrando: Agregando tipo_caja a caja_session")
                _ejecutar_paso(cursor, "session.tipo_caja", "ALTER TABLE caja_session ADD COLUMN tipo_caja ENUM('turno', 'administrativa') DEFAULT 'turno'")
                _ejecutar_paso(cursor, "session.tipo_caja_update", "UPDATE caja_session SET tipo_caja = 'turno'")
                
            # Para modificar ENUM de forma segura en MySQL
            logger.info("🔧 Migrando: Ampliando motivos de caja_movimiento para Tesorería")
            _ejecutar_paso(cursor, "mov.motivo_enum", """
                ALTER TABLE caja_movimiento MODIFY COLUMN motivo ENUM(
                    'apertura_caja', 'venta_efectivo', 'venta_tarjeta',
                    'venta_transferencia', 'venta_cuenta_corriente',
                    'pago_cuenta_corriente_efectivo', 'pago_cuenta_corriente_transferencia',
                    'pago_cuenta_corriente_tarjeta', 'cobro_cuenta_corriente',
                    'pago_proveedor', 'gasto_vario', 'retiro_caja',
                    'devolucion_efectivo', 'ajuste_positivo', 'ajuste_negativo',
                    'transferencia_tesoreria_salida', 'transferencia_tesoreria_entrada',
                    'ingreso_extraordinario', 'ingreso_capital', 'otro'
                ) NOT NULL
            """)
        except Exception as e:
            logger.error(f"Error en migración de Tesorería: {e}")

        # 8. SEMILLA DE CATEGORÍAS
        cursor.execute("SELECT COUNT(*) FROM Categoria")
        if cursor.fetchone()[0] == 0:
            logger.info("🔧 Migrando: Sembrando categorías iniciales")
            _ejecutar_paso(cursor, "seed categorias", """
            INSERT INTO Categoria (nombre, margen_ganancia, es_pesable_default, activa) VALUES 
            ('Almacén', 30.0, 0, 1),
            ('Bebidas', 30.0, 0, 1),
            ('Fiambrería', 40.0, 1, 1),
            ('Limpieza', 25.0, 0, 1),
            ('Verdulería', 35.0, 1, 1),
            ('Carnicería', 35.0, 1, 1),
            ('Kiosco', 40.0, 0, 1)
            """)

        # 9. ÍNDICES DE RENDIMIENTO PARA HISTORIALES (NUEVO)
        logger.info("🔧 Migrando: Creando índices de rendimiento si no existen")
        _ejecutar_paso(cursor, "crear idx_mov_fecha_hora", "CREATE INDEX idx_mov_fecha_hora ON caja_movimiento (fecha_hora)")
        _ejecutar_paso(cursor, "crear idx_pagoprov_fecha", "CREATE INDEX idx_pagoprov_fecha ON PagoProveedor (fecha)")
        _ejecutar_paso(cursor, "crear idx_session_fecha_cierre", "CREATE INDEX idx_session_fecha_cierre ON caja_session (fecha_cierre)")
        _ejecutar_paso(cursor, "crear idx_auditoria_fecha", "CREATE INDEX idx_auditoria_fecha ON AuditoriaAcciones (fecha)")

        # 10. USUARIO (codigo_barras)
        cursor.execute("DESCRIBE Usuario")
        cols_usuario = [row[0] for row in cursor.fetchall()]
        if "codigo_barras" not in cols_usuario:
            logger.info("🔧 Migrando: Agregando codigo_barras a Usuario")
            _ejecutar_paso(cursor, "usuario.codigo_barras", "ALTER TABLE Usuario ADD COLUMN codigo_barras VARCHAR(100) UNIQUE NULL")

        conn.commit()
        logger.info("✅ Auto-migración completada exitosamente.")

    except Exception as e:
        logger.error(f"Error crítico durante auto-migración: {e}")
        try: conn.rollback()
        except: pass
    finally:
        if conn: conn.close()