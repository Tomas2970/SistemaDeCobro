"""
demo_generator.py
==================
Genera ~6 meses de historial REALISTA para el sistema de supermercado,
usando EXCLUSIVAMENTE las funciones reales de backend_adapter.py.
No se hace ningún INSERT/UPDATE manual ni se saltea ninguna validación.

USO:
    python demo_generator.py               # corre 180 días
    python demo_generator.py --dias 7      # prueba corta
    python demo_generator.py --dias 7 --boost 8  # prueba corta con más eventos raros
    python demo_generator.py --self-test   # valida el mecanismo de fecha
    python demo_generator.py --reset       # borra el checkpoint y arranca de cero

IMPORTANTE antes de correr:
    1) Apuntá a una base de datos de DESARROLLO, nunca a producción.
    2) La base debe estar inicializada (schema.sql + auto_migrate.py).
       El script llama a auto_migrate explícitamente al arrancar.
    3) Si ya existe un usuario admin en la base (id_rol=1), el script
       lo detecta automáticamente. Si no existe ninguno, hay que crearlo
       a mano primero (seed_initial_data.py o --seed-data).
"""

import os
import sys
import json
import random
import logging
import argparse
import unicodedata
from datetime import datetime, timedelta
from unittest.mock import patch
from decimal import Decimal

from freezegun import freeze_time

from app.database import DB
from app.database.backend_adapter import BackendAdapter

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("demo_generator.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("DemoGenerator")

# ============================================================
# MOCK DE TIEMPO A NIVEL SQL (SET TIMESTAMP)
# ============================================================
original_conectar = DB.conectar
current_simulated_epoch: int | None = None


def mock_conectar(*args, **kwargs):
    """Intercepta el pool para inyectar SET TIMESTAMP en cada conexión nueva.
    Como pool_reset_session=True, las variables de sesión se limpian solas
    al devolver la conexión al pool, así que hay que re-inyectar siempre."""
    conn = original_conectar(*args, **kwargs)
    if conn is not None and current_simulated_epoch is not None:
        try:
            cur = conn.cursor()
            cur.execute(f"SET TIMESTAMP = {current_simulated_epoch}")
            cur.close()
        except Exception as e:
            logger.error(f"No se pudo inyectar SET TIMESTAMP: {e}")
    return conn


def set_epoch(fecha_dt: datetime) -> None:
    global current_simulated_epoch
    current_simulated_epoch = int(fecha_dt.timestamp())


def avanzar_tiempo(frozen_datetime, nueva_fecha: datetime) -> None:
    """Mueve el reloj de Python (freezegun) Y el epoch de MySQL juntos.
    Si se hace por separado, datetime.now() y NOW() en la BD quedan
    desincronizados."""
    frozen_datetime.move_to(nueva_fecha)
    set_epoch(nueva_fecha)


# ============================================================
# HELPERS
# ============================================================
def _normalizar(texto: str) -> str:
    """Minúsculas sin acentos, para comparar nombres sin importar tildes."""
    texto = (texto or "").lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def _generar_cuit(tipo: str, identificador: str) -> str:
    """CUIT con dígito verificador real (algoritmo AFIP), 11 dígitos sin guiones."""
    identificador = str(identificador).zfill(8)
    base = f"{tipo}{identificador}"
    pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    suma = sum(int(d) * p for d, p in zip(base, pesos))
    resto = suma % 11
    digito = 11 - resto
    if digito == 11:
        digito = 0
    elif digito == 10:
        digito = 9
    return f"{base}{digito}"


def _f(v) -> float:
    """Convierte Decimal o cualquier tipo numérico a float.
    La BD devuelve columnas DECIMAL como decimal.Decimal; Python no puede
    multiplicar float * Decimal sin conversión explícita."""
    if isinstance(v, Decimal):
        return float(v)
    return float(v) if v is not None else 0.0


# ============================================================
# CONFIGURACIÓN
# ============================================================
PROGRESS_FILE = "demo_progress.json"

CONFIG = {
    "saltar_domingos": True,
    "capital_inicial": 150000.0,        # fondo inicial del día 1 en tesorería
    "monto_inicial_caja": 10000.0,      # fondo de cambio de apertura de cada caja
    "stock_inicial_min": 80,
    "stock_inicial_max": 150,
    "prob_cliente_nuevo_por_dia": 0.06,
    "prob_anulacion_venta": 0.02,
    "porc_ventas_a_cuenta_corriente": 0.12,
    "prob_pago_cc_por_dia": 0.25,
    "prob_pago_proveedor_por_dia": 0.20,
    "prob_compra_rutina": 0.15,
    # porcentaje del efectivo recaudado del cajero que se transfiere a tesorería
    # al cierre de turno (el resto queda como fondo de cambio para el día siguiente)
    "porc_transferencia_tesoreria": 0.85,
}

# tipo_pago para ventas (sin "cuenta_corriente", que se decide aparte)
TIPOS_PAGO_VENTA = [("efectivo", 0.85), ("tarjeta", 0.15)]

ROLES = {"admin": 1, "vendedor": 2, "supervisor": 3}

USUARIOS_A_CREAR = [
    # vendedores (cajeros)
    ("lucia",     "lucia10",     ROLES["vendedor"]),
    ("martin",    "martin10",    ROLES["vendedor"]),
    ("sofia",     "sofia10",     ROLES["vendedor"]),
    ("carlos",    "carlos10",    ROLES["vendedor"]),
    # supervisora — siempre última, se usa como supervisor_id
    ("valentina", "valentina10", ROLES["supervisor"]),
]

# Palabras clave para mapear a categorías YA EXISTENTES en la base.
# Nunca se crean categorías nuevas.
CATEGORIA_KEYWORDS = {
    "Bebidas":    ["bebida", "gaseosa", "jugo", "agua", "refresco"],
    "Golosinas":  ["golosina", "dulce", "snack", "caramelo", "kiosco"],
    "Lacteos":    ["lacteo", "fresco", "leche"],
    "Almacen":    ["almacen", "comestible", "abarrote", "general"],
    "Limpieza":   ["limpieza", "higiene"],
}

# Proveedores con día de reparto fijo (weekday: Lunes=0..Sábado=5)
# CUIT: 11 dígitos sin guiones (calculado). Tel: 10 dígitos sin guiones.
PROVEEDORES_RAW = [
    {"nombre": "Danone Lácteos",            "empresa": "Danone Argentina S.A.",         "dni_base": "20458712", "dni_vendedor": "24876531", "tel": "1145237891", "email": "pedidos@danonelacteos.com.ar",       "direccion": "Av. Rivadavia 4521, CABA",              "cat_grupo": "Lacteos",   "dia_reparto": 0},
    {"nombre": "Coca Cola Arg",             "empresa": "Embotelladora del Litoral S.A.","dni_base": "33125478", "dni_vendedor": "27456123", "tel": "3414553210", "email": "ventas@embotelladoralitoral.com.ar", "direccion": "Bv. Oroño 2245, Rosario",               "cat_grupo": "Bebidas",   "dia_reparto": 1},
    {"nombre": "Distribuidora Almacén Sur", "empresa": "Almacén Sur Distrib. S.R.L.",   "dni_base": "30774521", "dni_vendedor": "25998743", "tel": "3514891122", "email": "contacto@almacensur.com.ar",        "direccion": "Av. Colón 1873, Córdoba",               "cat_grupo": "Almacen",   "dia_reparto": 2},
    {"nombre": "Arcor",                     "empresa": "Arcor S.A.I.C.",                "dni_base": "30556234", "dni_vendedor": "29112456", "tel": "2614206677", "email": "comercial@arcorsaic.com.ar",        "direccion": "Calle San Martín 980, Mendoza",          "cat_grupo": "Golosinas", "dia_reparto": 3},
    {"nombre": "Distribuidora Limpieza Sur","empresa": "Limpieza Sur S.A.",             "dni_base": "27893461", "dni_vendedor": "26678234", "tel": "2234519034", "email": "info@limpiezasur.com.ar",           "direccion": "Av. Luro 3312, Mar del Plata",           "cat_grupo": "Limpieza",  "dia_reparto": 4},
]

PROVEEDORES = []
for _p in PROVEEDORES_RAW:
    _p = dict(_p)
    _p["cuit"] = _generar_cuit("30", _p["dni_base"])
    PROVEEDORES.append(_p)

# (nombre, costo, margen_%, cat_grupo, prov_idx, es_pesable, stock_min)
CATALOGO = [
    # Bebidas (Coca Cola Arg)
    ("Coca Cola 2.25L",         1500, 30, "Bebidas",   1, False, 15),
    ("Coca Cola 1.5L",          1100, 30, "Bebidas",   1, False, 15),
    ("Sprite 2.25L",            1400, 30, "Bebidas",   1, False, 12),
    ("Fanta 2.25L",             1400, 30, "Bebidas",   1, False, 12),
    ("Agua Mineral 1.5L",        600, 35, "Bebidas",   1, False, 20),
    ("Agua Saborizada 1.5L",     750, 32, "Bebidas",   1, False, 15),
    ("Jugo Cepita 1L",           900, 30, "Bebidas",   1, False, 12),
    ("Gatorade 500ml",          1100, 35, "Bebidas",   1, False, 10),
    ("Powerade 500ml",          1050, 35, "Bebidas",   1, False, 10),
    ("Soda Siphon 1L",           700, 28, "Bebidas",   1, False, 10),
    # Golosinas (Arcor)
    ("Alfajor Jorgito",          280, 45, "Golosinas", 3, False, 20),
    ("Alfajor Guaymallén",       260, 45, "Golosinas", 3, False, 20),
    ("Turrón Arcor",             200, 50, "Golosinas", 3, False, 15),
    ("Caramelos Media Hora",     150, 55, "Golosinas", 3, False, 15),
    ("Chocolate Águila",         900, 40, "Golosinas", 3, False, 12),
    ("Chocolate Bon o Bon",      850, 40, "Golosinas", 3, False, 12),
    ("Mantecol",                1200, 38, "Golosinas", 3, False,  8),
    ("Bizcochos Don Satur",      700, 35, "Golosinas", 3, False, 10),
    ("Obleas Tita",              250, 48, "Golosinas", 3, False, 15),
    ("Chicles Beldent",          300, 50, "Golosinas", 3, False, 15),
    # Lácteos (Danone)
    ("Yogur Danone Frutilla",    800, 35, "Lacteos",   0, False, 12),
    ("Yogur Danone Vainilla",    800, 35, "Lacteos",   0, False, 12),
    ("Yogur Bebible Serenito",   700, 35, "Lacteos",   0, False, 12),
    ("Queso Cremoso x Kg",      4000, 25, "Lacteos",   0,  True,  5),
    ("Queso Rallado x Kg",      5200, 25, "Lacteos",   0,  True,  5),
    ("Manteca La Serenísima",   1300, 30, "Lacteos",   0, False, 10),
    ("Crema de Leche",          1100, 28, "Lacteos",   0, False,  8),
    ("Leche Entera 1L",          900, 22, "Lacteos",   0, False, 20),
    ("Leche Descremada 1L",      950, 22, "Lacteos",   0, False, 15),
    ("Dulce de Leche Ser.",     1600, 30, "Lacteos",   0, False, 10),
    # Almacén (Distribuidora Almacén Sur)
    ("Arroz Gallo Oro 1Kg",     1300, 28, "Almacen",   2, False, 15),
    ("Fideos Matarazzo 500g",    900, 30, "Almacen",   2, False, 18),
    ("Aceite Natura 900ml",     2200, 25, "Almacen",   2, False, 12),
    ("Puré de Tomate Arcor",     700, 32, "Almacen",   2, False, 15),
    ("Yerba Playadito 1Kg",     3500, 28, "Almacen",   2, False, 15),
    ("Azúcar Ledesma 1Kg",      1100, 25, "Almacen",   2, False, 18),
    ("Harina Pureza 1Kg",        950, 25, "Almacen",   2, False, 18),
    ("Sal Fina Celusal 500g",    500, 35, "Almacen",   2, False, 15),
    ("Café La Virginia 250g",   3200, 30, "Almacen",   2, False,  8),
    ("Polenta Pampa 500g",       800, 28, "Almacen",   2, False, 10),
    # Limpieza (Distribuidora Limpieza Sur)
    ("Detergente Magistral 750ml",1200,32, "Limpieza", 4, False, 12),
    ("Lavandina Ayudín 1L",      700, 30, "Limpieza",  4, False, 15),
    ("Jabón Polvo Skip 800g",   2400, 28, "Limpieza",  4, False, 10),
    ("Suavizante Vivere 900ml", 1800, 28, "Limpieza",  4, False, 10),
    ("Papel Higiénico x4",      1900, 30, "Limpieza",  4, False, 12),
    ("Esponja Scotch Brite",     400, 50, "Limpieza",  4, False, 15),
    ("Trapo de Piso",            600, 45, "Limpieza",  4, False, 10),
    ("Limpiador Cif 500ml",     1300, 30, "Limpieza",  4, False, 12),
    ("Desodorante Glade",       1500, 35, "Limpieza",  4, False, 10),
    ("Bolsas de Residuos x10",   900, 38, "Limpieza",  4, False, 15),
]

def _tipo_cuit(nombre: str) -> str:
    return "27" if nombre.split()[0].lower().endswith("a") else "20"

CLIENTES_POOL_RAW = [
    {"nombre": "Juan Manuel Pérez",         "dni": "28456123", "tel": "1155234471", "direccion": "Av. Cabildo 2140, CABA"},
    {"nombre": "María Belén Gómez",         "dni": "30112456", "tel": "1155448821", "direccion": "Calle Mitre 845, San Isidro"},
    {"nombre": "Carlos Alberto Fernández",  "dni": "25887112", "tel": "3514772390", "direccion": "Bv. San Juan 612, Córdoba"},
    {"nombre": "Lucía Romina Sosa",         "dni": "33221456", "tel": "1155671290", "direccion": "Av. Maipú 3310, Vicente López"},
    {"nombre": "Diego Martín Rodríguez",    "dni": "27654321", "tel": "3414987765", "direccion": "Calle Urquiza 1455, Rosario"},
    {"nombre": "Florencia Noemí Acosta",    "dni": "31998877", "tel": "1156123398", "direccion": "Av. Belgrano 980, CABA"},
    {"nombre": "Pablo Ezequiel Medina",     "dni": "29887766", "tel": "2614335512", "direccion": "Calle Las Heras 220, Mendoza"},
    {"nombre": "Gisela Andrea Torres",      "dni": "32445566", "tel": "1154782261", "direccion": "Av. Pueyrredón 1120, CABA"},
    {"nombre": "Sebastián Nicolás Ríos",    "dni": "26334455", "tel": "2234897741", "direccion": "Calle Rivadavia 540, Mar del Plata"},
    {"nombre": "Romina Vanesa Díaz",        "dni": "34112233", "tel": "1153908854", "direccion": "Av. Triunvirato 2980, CABA"},
    {"nombre": "Matías Ezequiel López",     "dni": "28223344", "tel": "1156210033", "direccion": "Calle Moreno 765, Quilmes"},
    {"nombre": "Antonella Soledad Vega",    "dni": "35001122", "tel": "3514627789", "direccion": "Av. Vélez Sarsfield 890, Córdoba"},
    {"nombre": "Federico Andrés Castro",    "dni": "27889900", "tel": "1157342210", "direccion": "Calle Sarmiento 1340, Avellaneda"},
    {"nombre": "Yamila Esther Molina",      "dni": "33667788", "tel": "3414559981", "direccion": "Bv. Avellaneda 770, Rosario"},
    {"nombre": "Nicolás Ariel Herrera",     "dni": "29556677", "tel": "1152984471", "direccion": "Av. Directorio 1890, CABA"},
]

CLIENTES_POOL = []
for _c in CLIENTES_POOL_RAW:
    _c = dict(_c)
    _c["cuit"] = _generar_cuit(_tipo_cuit(_c["nombre"]), _c["dni"])
    _c["email"] = f"cliente.{_c['dni']}@demo-clientes.com.ar"
    CLIENTES_POOL.append(_c)


# ============================================================
# CLASE PRINCIPAL
# ============================================================
class DemoGenerator:
    def __init__(self, dias: int):
        self.adapter = BackendAdapter()
        self.dias_simular = dias
        self.fecha_fin = datetime.now()
        self.fecha_inicio = self.fecha_fin - timedelta(days=self.dias_simular)
        self.estado = self._cargar_estado()
        # productos_info: persiste costo e id_proveedor (obtener_productos() no los devuelve)
        self.productos_info: dict = self.estado.get("setup", {}).get("productos", {})

    # ----------------------------------------------------------
    # CHECKPOINT
    # ----------------------------------------------------------
    def _cargar_estado(self) -> dict:
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "setup" not in data:
                    raise ValueError("Checkpoint inválido")
                return data
            except Exception as e:
                logger.warning(f"Checkpoint no usable, arrancando de cero: {e}")
        return {
            "admin_id": None,
            "setup": {
                "completado": False,
                "usuarios": {},               # nombre -> id_usuario
                "categorias": {},             # grupo_logico -> id_categoria
                "proveedores": {},            # nombre -> id_proveedor
                "productos": {},              # str(id_producto) -> info dict
                "compras_iniciales": [],      # nombres de proveedor ya abastecidos
                "capital_inicial": False,
            },
            "dias_completados": [],
            "dia_actual": None,
            "estado_dia_actual": {},
            "clientes_creados": {},           # nombre -> id_cliente
        }

    def _guardar_estado(self) -> None:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.estado, f, indent=2, ensure_ascii=False)

    # ----------------------------------------------------------
    # SELF TEST
    # ----------------------------------------------------------
    def self_test(self) -> None:
        logger.info("=== SELF-TEST: validando inyección de fecha simulada ===")
        admin_id = self._obtener_admin_id()
        if admin_id is None:
            logger.error("Self-test abortado: no hay usuario admin.")
            return
        fecha_prueba = datetime.now() - timedelta(days=10)
        with patch("app.database.DB.conectar", mock_conectar):
            with freeze_time(fecha_prueba) as frozen:
                avanzar_tiempo(frozen, fecha_prueba)
                logger.info(f"Fecha simulada objetivo : {fecha_prueba}")
                logger.info(f"datetime.now() bajo freeze: {datetime.now()}")
                try:
                    tesoreria = self.adapter.obtener_o_crear_tesoreria_hoy(admin_id)
                    logger.info(f"Tesorería devuelta: {tesoreria}")
                    logger.info(
                        "Revisá que el campo de fecha de ese registro coincida con "
                        "la fecha simulada de arriba. Si es así, SET TIMESTAMP + "
                        "freezegun están funcionando correctamente."
                    )
                except Exception as e:
                    logger.error(f"Self-test falló: {e}")
        logger.info("=== FIN SELF-TEST ===")

    # ----------------------------------------------------------
    # ADMIN
    # ----------------------------------------------------------
    def _obtener_admin_id(self) -> int | None:
        if self.estado.get("admin_id"):
            return self.estado["admin_id"]
        try:
            usuarios = self.adapter.obtener_usuarios_con_rol()
        except Exception as e:
            logger.error(f"No se pudo listar usuarios: {e}")
            return None
        admin = next((u for u in usuarios if u.get("id_rol") == ROLES["admin"]), None)
        if not admin:
            logger.error(
                "No hay ningún usuario con id_rol=1 (admin) en la base. "
                "Corré primero seed_initial_data.py (o --seed-data en app.main) "
                "para crear el usuario admin inicial."
            )
            return None
        self.estado["admin_id"] = admin["id_usuario"]
        self._guardar_estado()
        return admin["id_usuario"]

    # ----------------------------------------------------------
    # FLUJO PRINCIPAL
    # ----------------------------------------------------------
    def simular(self) -> None:
        # Asegurar que auto_migrate corrió (el script no pasa por app.main)
        try:
            from app.database.auto_migrate import ejecutar_migraciones
            ejecutar_migraciones()
            logger.info("auto_migrate: chequeo de integridad completado.")
        except Exception as e:
            logger.warning(f"auto_migrate no pudo correr: {e}. Continuando de todas formas.")

        admin_id = self._obtener_admin_id()
        if admin_id is None:
            sys.exit(1)

        with patch("app.database.DB.conectar", mock_conectar):

            # FASE 1: SETUP INICIAL
            if not self.estado["setup"]["completado"]:
                logger.info(">>> SETUP INICIAL en fecha de hace 180 días...")
                with freeze_time(self.fecha_inicio) as frozen:
                    avanzar_tiempo(frozen, self.fecha_inicio)
                    self._ejecutar_setup_inicial(admin_id)
                self.estado["setup"]["completado"] = True
                self._guardar_estado()
            else:
                logger.info(">>> Setup inicial ya hecho, se omite.")

            # FASE 2: BUCLE DIARIO
            logger.info(">>> BUCLE DIARIO histórico...")
            for d in range(self.dias_simular + 1):
                fecha_sim = self.fecha_inicio + timedelta(days=d)
                str_fecha = fecha_sim.strftime("%Y-%m-%d")

                if str_fecha in self.estado["dias_completados"]:
                    continue

                if CONFIG["saltar_domingos"] and fecha_sim.weekday() == 6:
                    logger.info(f"--- {str_fecha} Domingo, local cerrado. ---")
                    self.estado["dias_completados"].append(str_fecha)
                    self._guardar_estado()
                    continue

                with freeze_time(fecha_sim) as frozen:
                    self._simular_dia(frozen, fecha_sim, str_fecha, admin_id)

                self.estado["dias_completados"].append(str_fecha)
                self.estado["dia_actual"] = None
                self.estado["estado_dia_actual"] = {}
                self._guardar_estado()

        logger.info(">>> SIMULACIÓN FINALIZADA CON ÉXITO <<<")

    # ----------------------------------------------------------
    # SETUP INICIAL
    # ----------------------------------------------------------
    def _mapear_categorias(self, setup: dict) -> None:
        """Mapea grupos lógicos a categorías YA EXISTENTES por palabra clave.
        NUNCA crea categorías nuevas."""
        try:
            cats_db = self.adapter.obtener_categorias()
        except Exception as e:
            logger.error(f"No se pudieron obtener categorías: {e}")
            return
        if not cats_db:
            logger.error("No hay categorías en la base. Corré seed_initial_data.py primero.")
            return
        for grupo, keywords in CATEGORIA_KEYWORDS.items():
            if grupo in setup["categorias"]:
                continue
            match = next(
                (c for c in cats_db if any(kw in _normalizar(c["nombre"]) for kw in keywords)),
                None,
            )
            if match:
                setup["categorias"][grupo] = match["id_categoria"]
                self._guardar_estado()
                logger.info(f"Grupo '{grupo}' -> '{match['nombre']}' (id {match['id_categoria']})")
            else:
                logger.warning(
                    f"No se encontró categoría para el grupo '{grupo}' "
                    f"(keywords: {keywords}). Productos de ese grupo serán omitidos. "
                    f"Categorías disponibles: {[c['nombre'] for c in cats_db]}"
                )

    def _ejecutar_setup_inicial(self, admin_id: int) -> None:
        setup = self.estado["setup"]

        # 1) Categorías (mapeo a las existentes)
        self._mapear_categorias(setup)

        # 2) Usuarios adicionales (cajeros + supervisor demo)
        try:
            usuarios_db = self.adapter.obtener_usuarios_con_rol()
        except Exception:
            usuarios_db = []
        nombres_existentes = {u["nombre"].lower() for u in usuarios_db}

        for nombre, password, id_rol in USUARIOS_A_CREAR:
            if nombre in setup["usuarios"]:
                continue
            if nombre.lower() in nombres_existentes:
                u = next(u for u in usuarios_db if u["nombre"].lower() == nombre.lower())
                setup["usuarios"][nombre] = u["id_usuario"]
                self._guardar_estado()
                continue
            try:
                new_id = self.adapter.crear_usuario(nombre, password, id_rol=id_rol, id_usuario_admin=admin_id)
                if new_id is None:
                    logger.error(f"crear_usuario devolvió None para '{nombre}' — usuario NO creado en BD")
                    continue
                setup["usuarios"][nombre] = new_id
                self._guardar_estado()
                logger.info(f"Usuario: {nombre} (rol {id_rol}) -> id {new_id}")
            except Exception as e:
                logger.error(f"Error creando usuario {nombre}: {e}")

        # 3) Proveedores
        try:
            provs_db = self.adapter.obtener_proveedores()
        except Exception:
            provs_db = []
        nombres_prov = {p["nombre"].lower() for p in provs_db}

        for p in PROVEEDORES:
            if p["nombre"] in setup["proveedores"]:
                continue
            if p["nombre"].lower() in nombres_prov:
                pr = next(pr for pr in provs_db if pr["nombre"].lower() == p["nombre"].lower())
                setup["proveedores"][p["nombre"]] = pr["id_proveedor"]
                self._guardar_estado()
                continue
            try:
                new_id = self.adapter.crear_proveedor(
                    p["nombre"], p["empresa"], p["cuit"], p["dni_vendedor"],
                    p["tel"], p["email"], p["direccion"], id_usuario_admin=admin_id,
                )
                setup["proveedores"][p["nombre"]] = new_id
                self._guardar_estado()
                logger.info(f"Proveedor: {p['nombre']} -> id {new_id}")
            except Exception as e:
                logger.error(f"Error creando proveedor {p['nombre']}: {e}")

        # 4) Productos
        try:
            prods_db = self.adapter.obtener_productos()
        except Exception:
            prods_db = []
        nombres_prod = {p["nombre"].lower(): p for p in prods_db}

        for nombre, costo, margen, cat_grupo, prov_idx, pesable, stock_min in CATALOGO:
            ya_en_checkpoint = any(i["nombre"] == nombre for i in setup["productos"].values())
            if ya_en_checkpoint:
                continue

            id_categoria = setup["categorias"].get(cat_grupo)
            id_proveedor = setup["proveedores"].get(PROVEEDORES[prov_idx]["nombre"])
            if not id_categoria or not id_proveedor:
                logger.warning(f"Omitiendo {nombre}: falta categoría '{cat_grupo}' o proveedor idx {prov_idx}")
                continue

            precio_venta = round(costo * (1 + margen / 100), 2)

            if nombre.lower() in nombres_prod:
                existente = nombres_prod[nombre.lower()]
                id_producto = existente["id_producto"]
                codigo_barras = existente.get("codigo_barras")
            else:
                codigo_barras = f"77{random.randint(10**8, 10**9 - 1)}"
                try:
                    id_producto = self.adapter.crear_producto_completo(
                        nombre=nombre, categoria_id=id_categoria,
                        codigo_barras=codigo_barras, precio=precio_venta,
                        stock_inicial=0, stock_minimo=stock_min,
                        es_pesable=pesable, id_usuario=admin_id,
                    )
                except Exception as e:
                    logger.error(f"Error creando producto {nombre}: {e}")
                    continue

            if id_producto:
                # Siempre intentar asignar proveedor (cubre el caso de reintento)
                try:
                    self.adapter.asignar_producto_a_proveedor(id_proveedor, id_producto)
                except Exception as e:
                    logger.error(f"Error asignando proveedor a {nombre}: {e}")

                setup["productos"][str(id_producto)] = {
                    "nombre": nombre, "costo": costo, "precio_venta": precio_venta,
                    "id_categoria": id_categoria, "id_proveedor": id_proveedor,
                    "es_pesable": pesable, "codigo_barras": codigo_barras,
                }
                self._guardar_estado()
                logger.info(f"Producto: {nombre} -> id {id_producto}")

        self.productos_info = setup["productos"]

        # 5) Compras iniciales (única forma de generar stock real)
        for prov in PROVEEDORES:
            if prov["nombre"] in setup["compras_iniciales"]:
                continue
            id_proveedor = setup["proveedores"].get(prov["nombre"])
            if not id_proveedor:
                continue
            items = [
                {"id": int(pid), "cant": random.randint(CONFIG["stock_inicial_min"], CONFIG["stock_inicial_max"]),
                 "costo": info["costo"], "precio_venta": info["precio_venta"]}
                for pid, info in self.productos_info.items()
                if info["id_proveedor"] == id_proveedor
            ]
            if not items:
                continue
            try:
                resultado = self.adapter.registrar_compra_mixta(
                    admin_id, id_proveedor, items,
                    medio_real="efectivo", monto_efectivo=0.0,
                )
                setup["compras_iniciales"].append(prov["nombre"])
                self._guardar_estado()
                logger.info(f"Compra inicial: {prov['nombre']} ({len(items)} productos) -> {resultado.get('id_compra')}")
            except Exception as e:
                logger.error(f"Error compra inicial {prov['nombre']}: {e}")

        # 6) Capital inicial en tesorería
        if not setup["capital_inicial"]:
            try:
                self.adapter.obtener_o_crear_tesoreria_hoy(admin_id)
                self.adapter.registrar_ingreso_capital(
                    CONFIG["capital_inicial"], "Capital inicial - puesta en marcha demo", admin_id
                )
                setup["capital_inicial"] = True
                self._guardar_estado()
                logger.info(f"Capital inicial: ${CONFIG['capital_inicial']}")
            except Exception as e:
                logger.error(f"Error ingresando capital inicial: {e}")

        logger.info("Setup inicial completo.")

    # ----------------------------------------------------------
    # SIMULACIÓN DE UN DÍA
    # ----------------------------------------------------------
    def _simular_dia(self, frozen, fecha_sim: datetime, str_fecha: str, admin_id: int) -> None:
        logger.info(f"--- {str_fecha} ({fecha_sim.strftime('%A')}) ---")

        # Inicializar estado del día (checkpoint granular)
        if self.estado["dia_actual"] != str_fecha:
            self.estado["dia_actual"] = str_fecha
            # Filtrar None: si crear_usuario falló, el ID puede ser None
            todos_ids = [v for v in self.estado["setup"]["usuarios"].values() if v is not None]
            # El supervisor es siempre el último en USUARIOS_A_CREAR
            supervisor_id = todos_ids[-1] if len(todos_ids) > 1 else admin_id
            vendedores_ids = todos_ids[:-1] if len(todos_ids) > 1 else todos_ids
            # Rotación de cajeros: distintos vendedores trabajan distintos días
            if len(vendedores_ids) >= 2:
                dias_hechos = len(self.estado.get("dias_completados", []))
                idx1 = dias_hechos % len(vendedores_ids)
                idx2 = (dias_hechos + 1) % len(vendedores_ids)
                cajeros_ids = [vendedores_ids[idx1], vendedores_ids[idx2]]
            else:
                cajeros_ids = vendedores_ids
            weekday = fecha_sim.weekday()
            if weekday in (4, 5):  # Viernes/Sábado
                ventas_meta = random.randint(35, 55)
                cajeros_hoy = cajeros_ids if random.random() < 0.7 else cajeros_ids[:1]
            else:
                ventas_meta = random.randint(15, 30)
                cajeros_hoy = cajeros_ids[:1] if random.random() < 0.8 else cajeros_ids
            if not cajeros_hoy:
                cajeros_hoy = cajeros_ids[:1] if cajeros_ids else [admin_id]

            self.estado["estado_dia_actual"] = {
                "cajeros_hoy": cajeros_hoy,
                "supervisor_id": supervisor_id,
                "sesiones": {},          # str(id_usuario) -> id_session
                "cierres_hechos": [],
                "ventas_realizadas": 0,
                "ventas_meta": ventas_meta,
                "compras_hechas": [],
                "pago_cc_hecho": False,
                "pago_proveedor_hecho": False,
                "cliente_nuevo_hecho": False,
                "transferencia_tesoreria_hecha": False,
            }
            self._guardar_estado()

        estado_hoy = self.estado["estado_dia_actual"]

        # 1) Apertura de caja(s)
        hora_ap = fecha_sim.replace(hour=8, minute=random.randint(0, 30), second=0)
        for cajero_id in estado_hoy["cajeros_hoy"]:
            if str(cajero_id) in estado_hoy["sesiones"]:
                continue
            avanzar_tiempo(frozen, hora_ap)
            try:
                self.adapter.obtener_o_crear_tesoreria_hoy(admin_id)
                self.adapter.abrir_caja_session(cajero_id, CONFIG["monto_inicial_caja"], "turno")
                session = self.adapter.obtener_session_abierta(cajero_id)
                if session:
                    estado_hoy["sesiones"][str(cajero_id)] = session["id_session"]
                    self._guardar_estado()
                    logger.info(f"Caja abierta usuario {cajero_id} -> sesión {session['id_session']}")
            except Exception as e:
                logger.error(f"Error abriendo caja usuario {cajero_id}: {e}")
            hora_ap += timedelta(minutes=random.randint(5, 20))

        if not estado_hoy["sesiones"]:
            logger.error("No se pudo abrir ninguna caja. Se omite el día.")
            return

        # 2) Cliente nuevo (crecimiento orgánico)
        if not estado_hoy["cliente_nuevo_hecho"] and random.random() < CONFIG["prob_cliente_nuevo_por_dia"]:
            self._dar_alta_cliente_nuevo(fecha_sim, frozen, estado_hoy["supervisor_id"])
            estado_hoy["cliente_nuevo_hecho"] = True
            self._guardar_estado()

        # 3) Compras (días de reparto + reposición de emergencia)
        self._procesar_compras(fecha_sim, frozen, admin_id, estado_hoy)

        # 4) Ventas
        self._procesar_ventas(fecha_sim, frozen, estado_hoy)

        # 5) Pagos
        self._procesar_pagos(fecha_sim, frozen, estado_hoy)

        # 6) Cierre de caja(s) y transferencia a tesorería
        hora_cierre = fecha_sim.replace(hour=20, minute=random.randint(30, 59), second=0)
        for cajero_id_str, id_session in estado_hoy["sesiones"].items():
            if id_session in estado_hoy["cierres_hechos"]:
                continue
            avanzar_tiempo(frozen, hora_cierre)
            # Transferir excedente a tesorería antes de cerrar
            if not estado_hoy["transferencia_tesoreria_hecha"]:
                self._transferir_a_tesoreria(frozen, fecha_sim, hora_cierre, id_session, int(cajero_id_str), admin_id, estado_hoy)
            self._cerrar_caja(id_session, int(cajero_id_str))
            estado_hoy["cierres_hechos"].append(id_session)
            self._guardar_estado()
            hora_cierre += timedelta(minutes=random.randint(2, 10))

    # ----------------------------------------------------------
    def _transferir_a_tesoreria(self, frozen, fecha_sim, hora_base, id_session_cajero, cajero_id, admin_id, estado_hoy) -> None:
        """Transfiere el excedente de la caja del cajero a la tesorería.
        Esto es lo que le da fondos reales a la tesorería para pagar proveedores."""
        try:
            resumen = self.adapter.obtener_resumen_cierre(id_session_cajero)
            saldo_cajero = _f(resumen.get("efectivo_esperado", 0))
            excedente = max(0.0, round(saldo_cajero - CONFIG["monto_inicial_caja"], 2))
            if excedente <= 0:
                return
            monto_a_transferir = round(excedente * CONFIG["porc_transferencia_tesoreria"], 2)
            if monto_a_transferir <= 0:
                return

            tesoreria = self.adapter.obtener_o_crear_tesoreria_hoy(admin_id)
            id_session_tesoreria = tesoreria["id_session"]
            supervisor_id = estado_hoy["supervisor_id"]

            avanzar_tiempo(frozen, hora_base + timedelta(minutes=random.randint(1, 10)))
            self.adapter.transferir_entre_cajas(
                id_session_cajero, id_session_tesoreria, monto_a_transferir,
                admin_id, "Cierre de turno", "Recaudación del día",
                "Transferencia automática fin de turno demo",
                id_autorizador=supervisor_id,
            )
            estado_hoy["transferencia_tesoreria_hecha"] = True
            self._guardar_estado()
            logger.info(f"Transferencia a tesorería: ${monto_a_transferir:.2f}")
        except Exception as e:
            logger.error(f"Error transfiriendo a tesorería: {e}")

    def _cerrar_caja(self, id_session: int, id_usuario_cierre: int) -> None:
        try:
            resumen = self.adapter.obtener_resumen_cierre(id_session)
            esperado = _f(resumen.get("efectivo_esperado", CONFIG["monto_inicial_caja"]))
        except Exception as e:
            logger.error(f"Error obteniendo resumen cierre sesión {id_session}: {e}")
            esperado = CONFIG["monto_inicial_caja"]

        # 95% cuadran perfecto; 5% tienen diferencia pequeña (más realista)
        contado = round(esperado + random.uniform(-300, 300), 2) if random.random() < 0.05 else esperado
        diferencia = round(contado - esperado, 2)

        try:
            self.adapter.cerrar_caja_session(
                id_session, id_usuario_cierre, esperado, contado, diferencia,
                "Cierre demo - generado automáticamente",
            )
            logger.info(f"Caja cerrada (sesión {id_session}). Esperado: ${esperado:.2f} | Diferencia: ${diferencia:.2f}")
        except Exception as e:
            logger.error(f"Error cerrando caja {id_session}: {e}")

    # ----------------------------------------------------------
    def _dar_alta_cliente_nuevo(self, fecha_sim, frozen, supervisor_id) -> None:
        ya_creados = set(self.estado["clientes_creados"].keys())
        disponibles = [c for c in CLIENTES_POOL if c["nombre"] not in ya_creados]
        if not disponibles:
            return
        cliente = random.choice(disponibles)
        avanzar_tiempo(frozen, fecha_sim.replace(hour=random.randint(9, 19), minute=random.randint(0, 59)))
        try:
            id_cliente = self.adapter.crear_cliente(
                cliente["nombre"], cliente["dni"], cliente["cuit"],
                cliente["direccion"], cliente["tel"], cliente["email"],
                limite_credito=30000.00, id_usuario_admin=supervisor_id,
            )
            if id_cliente:
                self.adapter.crear_cuenta_corriente_si_no_existe(id_cliente)
                self.estado["clientes_creados"][cliente["nombre"]] = id_cliente
                self._guardar_estado()
                logger.info(f"Cliente nuevo: {cliente['nombre']} -> id {id_cliente}")
        except Exception as e:
            logger.error(f"Error creando cliente {cliente['nombre']}: {e}")

    # ----------------------------------------------------------
    def _procesar_compras(self, fecha_sim, frozen, admin_id, estado_hoy) -> None:
        weekday = fecha_sim.weekday()
        try:
            prods_db = self.adapter.obtener_productos()
        except Exception as e:
            logger.error(f"Error obteniendo productos para compras: {e}")
            return
        stock_por_id = {p["id_producto"]: _f(p.get("stock", 0)) for p in prods_db}

        for prov in PROVEEDORES:
            id_proveedor = self.estado["setup"]["proveedores"].get(prov["nombre"])
            if not id_proveedor or prov["nombre"] in estado_hoy["compras_hechas"]:
                continue

            es_dia_reparto = (weekday == prov["dia_reparto"])
            productos_del_prov = [
                (int(pid), info) for pid, info in self.productos_info.items()
                if info["id_proveedor"] == id_proveedor
            ]

            items = []
            for id_prod, info in productos_del_prov:
                prod_db = next((p for p in prods_db if p["id_producto"] == id_prod), None)
                stock_min = _f(prod_db.get("stock_minimo", 10)) if prod_db else 10.0
                stock_actual = stock_por_id.get(id_prod, 0.0)
                necesita = stock_actual <= stock_min * 1.5
                rutina = es_dia_reparto and random.random() < CONFIG["prob_compra_rutina"]
                if necesita or rutina:
                    cant = random.randint(30, 70) if necesita else random.randint(15, 35)
                    items.append({"id": id_prod, "cant": cant, "costo": info["costo"], "precio_venta": info["precio_venta"]})

            if not items:
                continue

            avanzar_tiempo(frozen, fecha_sim.replace(hour=random.randint(9, 13), minute=random.randint(0, 59)))
            try:
                res = self.adapter.registrar_compra_mixta(
                    admin_id, id_proveedor, items,
                    medio_real="cuenta_corriente", monto_efectivo=0.0,
                )
                estado_hoy["compras_hechas"].append(prov["nombre"])
                self._guardar_estado()
                logger.info(f"Compra {prov['nombre']}: {len(items)} productos -> compra #{res.get('id_compra')}")
            except Exception as e:
                logger.error(f"Error compra {prov['nombre']}: {e}")

    # ----------------------------------------------------------
    def _procesar_ventas(self, fecha_sim, frozen, estado_hoy) -> None:
        sesiones = list(estado_hoy["sesiones"].items())
        if not sesiones:
            return
        hora = fecha_sim.replace(hour=9, minute=0, second=0)
        clientes_disp = list(self.estado["clientes_creados"].items())

        while estado_hoy["ventas_realizadas"] < estado_hoy["ventas_meta"]:
            hora += timedelta(minutes=random.randint(8, 35))
            if hora.hour >= 20:
                break
            avanzar_tiempo(frozen, hora)

            try:
                prods_db = self.adapter.obtener_productos()
            except Exception as e:
                logger.error(f"Error obteniendo productos para ventas: {e}")
                break

            con_stock = [p for p in prods_db if _f(p.get("stock", 0)) > 1]
            if not con_stock:
                logger.warning("Sin stock. Fin de jornada.")
                break

            cajero_str, id_session = random.choice(sesiones)
            cajero_id = int(cajero_str)

            seleccion = random.sample(con_stock, min(random.randint(1, 4), len(con_stock)))
            items_tupla = []
            for prod in seleccion:
                cant = round(random.uniform(0.3, 2.0), 3) if prod["es_pesable"] else float(random.randint(1, min(3, int(_f(prod["stock"])))))
                if cant <= 0:
                    continue
                items_tupla.append((
                    prod["id_producto"], prod["nombre"], cant,
                    _f(prod["precio"]), prod.get("codigo_barras") or "",
                ))

            if not items_tupla:
                continue

            # Calcular total para verificar crédito
            total_venta = sum(cant * precio for _, _, cant, precio, _ in items_tupla)
            
            # Tipo de pago: CC solo si hay clientes disponibles y con margen de crédito
            tipo_pago = _elegir_tipo_pago()
            id_cliente = None
            if clientes_disp and random.random() < CONFIG["porc_ventas_a_cuenta_corriente"]:
                nombre_c, idx_c = random.choice(clientes_disp)
                # Validar margen de crédito antes de intentar la venta
                try:
                    cuenta = self.adapter.obtener_cuenta_por_cliente(idx_c)
                    if cuenta:
                        saldo_actual = float(cuenta["saldo"])
                        limite = float(cuenta["limite_credito"])
                        if saldo_actual - total_venta >= -limite:
                            tipo_pago = "cuenta_corriente"
                            id_cliente = idx_c
                except Exception:
                    pass

            try:
                id_venta = self.adapter.registrar_venta_completa(
                    id_usuario=cajero_id, id_cliente=id_cliente,
                    items=items_tupla, tipo_pago=tipo_pago, id_session=id_session,
                )
                estado_hoy["ventas_realizadas"] += 1
                self._guardar_estado()

                # Evento raro: anulación (solo supervisor puede)
                if id_venta and random.random() < CONFIG["prob_anulacion_venta"]:
                    hora += timedelta(minutes=random.randint(2, 15))
                    avanzar_tiempo(frozen, hora)
                    try:
                        self.adapter.anular_venta(
                            id_venta, estado_hoy["supervisor_id"],
                            motivo="Anulación demo - cliente cambió de opinión",
                        )
                        logger.info(f"Venta {id_venta} anulada (evento raro).")
                    except Exception as e:
                        logger.error(f"Error anulando venta {id_venta}: {e}")

            except Exception as e:
                logger.error(f"Error venta: {e}")
                estado_hoy["ventas_realizadas"] += 1  # evita loop infinito
                self._guardar_estado()

    # ----------------------------------------------------------
    def _procesar_pagos(self, fecha_sim, frozen, estado_hoy) -> None:
        supervisor_id = estado_hoy["supervisor_id"]

        # Cobro de cuenta corriente de cliente
        if not estado_hoy["pago_cc_hecho"] and random.random() < CONFIG["prob_pago_cc_por_dia"]:
            try:
                clientes_con_saldo = self.adapter.obtener_clientes_con_saldos()
                con_deuda = [c for c in clientes_con_saldo if _f(c.get("saldo", 0)) > 0]
                if con_deuda:
                    cliente = random.choice(con_deuda)
                    saldo = _f(cliente["saldo"])
                    if random.random() < 0.30:
                        monto = saldo
                    else:
                        monto = round(saldo * random.uniform(0.4, 0.9), 2)
                    avanzar_tiempo(frozen, fecha_sim.replace(hour=random.randint(10, 18), minute=random.randint(0, 59)))
                    try:
                        cuenta = self.adapter.obtener_cuenta_por_cliente(cliente["id_cliente"])
                        if cuenta:
                            self.adapter.registrar_pago_cuenta_corriente(
                                cuenta["id_cuenta"], monto, "efectivo", supervisor_id
                            )
                            logger.info(f"CC cobrada: {cliente['nombre']} ${monto:.2f}")
                    except Exception as e:
                        logger.error(f"Error cobrando CC {cliente.get('nombre')}: {e}")
            except Exception as e:
                logger.error(f"Error procesando pagos CC: {e}")
            estado_hoy["pago_cc_hecho"] = True
            self._guardar_estado()

        # Pago a proveedor
        if not estado_hoy["pago_proveedor_hecho"] and random.random() < CONFIG["prob_pago_proveedor_por_dia"]:
            try:
                provs_db = self.adapter.obtener_proveedores()
                con_deuda = [p for p in provs_db if _f(p.get("saldo", 0)) > 0]
                if con_deuda:
                    prov = random.choice(con_deuda)
                    saldo = _f(prov["saldo"])
                    if random.random() < 0.30:
                        monto = saldo
                    else:
                        monto = round(saldo * random.uniform(0.4, 0.9), 2)
                    avanzar_tiempo(frozen, fecha_sim.replace(hour=random.randint(10, 18), minute=random.randint(0, 59)))
                    try:
                        self.adapter.registrar_pago_proveedor(
                            prov["id_proveedor"], monto, "efectivo", supervisor_id,
                            "Pago demo - generado automáticamente",
                        )
                        logger.info(f"Pago proveedor: {prov['nombre']} ${monto:.2f}")
                    except ValueError as ve:
                        logger.warning(f"Fondos insuficientes para pagar a {prov['nombre']}: {ve}")
                    except Exception as e:
                        logger.error(f"Error pagando proveedor {prov.get('nombre')}: {e}")
            except Exception as e:
                logger.error(f"Error procesando pagos proveedores: {e}")
            estado_hoy["pago_proveedor_hecho"] = True
            self._guardar_estado()


def _elegir_tipo_pago() -> str:
    r = random.random()
    acum = 0.0
    for tipo, prob in TIPOS_PAGO_VENTA:
        acum += prob
        if r <= acum:
            return tipo
    return TIPOS_PAGO_VENTA[0][0]


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Generador de base demo - Supermercado Don Atilio")
    parser.add_argument("--dias", type=int, default=180)
    parser.add_argument("--reset", action="store_true", help="Borra el checkpoint y arranca de cero.")
    parser.add_argument("--self-test", action="store_true", help="Solo valida el mecanismo de fecha simulada.")
    parser.add_argument(
        "--boost", type=float, default=1.0,
        help="Multiplica probabilidades de eventos raros. Solo para pruebas cortas (ej. --dias 7 --boost 8).",
    )
    args = parser.parse_args()

    if args.reset and os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        logger.info(f"Checkpoint {PROGRESS_FILE} eliminado.")

    if args.boost != 1.0:
        for k in ("prob_cliente_nuevo_por_dia", "porc_ventas_a_cuenta_corriente",
                  "prob_pago_cc_por_dia", "prob_pago_proveedor_por_dia", "prob_anulacion_venta"):
            CONFIG[k] = min(1.0, CONFIG[k] * args.boost)
        logger.warning(f"Modo boost x{args.boost} activado. Solo usar en pruebas cortas.")

    logger.info("=" * 50)
    logger.info("  GENERADOR DE BASE DEMO - DON ATILIO")
    logger.info(f"  Días a simular: {args.dias}")
    logger.info("=" * 50)

    demo = DemoGenerator(dias=args.dias)

    if args.self_test:
        demo.self_test()
        return

    demo.simular()


if __name__ == "__main__":
    main()
