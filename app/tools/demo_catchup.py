"""
demo_catchup.py
===============
Inyector de datos demo para el día actual.
Se invoca desde la pantalla de Login con Ctrl+Shift+D.

No usa freezegun ni SET TIMESTAMP: todo se registra con la fecha/hora
real del sistema para que quede en "hoy" sin trucos de reloj.

Flujo:
  1. Leer productos y clientes existentes en la BD.
  2. Verificar si los vendedores demo ya tienen una caja abierta HOY.
     Si no, abrirla. Si ya existe, usarla tal cual.
  3. Registrar ~15 ventas aleatorias variadas entre los cajeros disponibles.
  4. Llamar al callback on_done(ok, mensaje) cuando termina.
"""

import logging
import random
import threading
from decimal import Decimal

logger = logging.getLogger(__name__)

# ── Nombres de usuarios demo (deben existir en la BD) ─────────────────────────
VENDEDORES_DEMO = ["lucia", "martin", "sofia", "carlos"]

# ── Monto de apertura de caja si hay que crearla ──────────────────────────────
MONTO_APERTURA = 15_000.0

# ── Cantidad de ventas a generar ──────────────────────────────────────────────
VENTAS_A_GENERAR = 15

# ── Probabilidad de asignar cliente conocido (vs. consumidor final) ───────────
PROB_CLIENTE_CONOCIDO = 0.30


def _f(v) -> float:
    """Convierte Decimal a float (la BD devuelve DECIMAL como Decimal)."""
    if isinstance(v, Decimal):
        return float(v)
    return float(v) if v is not None else 0.0


def _elegir_items(productos_con_stock: list) -> list:
    """Selecciona entre 1 y 4 productos aleatorios y devuelve la tupla que
    espera registrar_venta_completa."""
    seleccion = random.sample(
        productos_con_stock,
        min(random.randint(1, 4), len(productos_con_stock)),
    )
    items = []
    for p in seleccion:
        stock = _f(p.get("stock", 0))
        if stock <= 0:
            continue
        es_pesable = bool(p.get("es_pesable", False))
        if es_pesable:
            cant = round(random.uniform(0.3, 2.0), 3)
        else:
            cant = float(random.randint(1, max(1, min(3, int(stock)))))
        items.append((
            p["id_producto"],
            p["nombre"],
            cant,
            _f(p.get("precio", 0)),
            p.get("codigo_barras") or "",
        ))
    return items


def _obtener_o_abrir_caja(adapter, usuario: dict) -> int | None:
    """Devuelve el id_session de la caja abierta del usuario.
    Si no tiene caja abierta, la abre ahora con MONTO_APERTURA.
    Si algo falla, devuelve None."""
    uid = usuario["id_usuario"]
    try:
        from app.database import DB
        conn = DB.conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id_session FROM caja_session "
            "WHERE estado='abierta' AND tipo_caja='turno' AND id_usuario_apertura = %s",
            (uid,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            id_session = int(row["id_session"])
            logger.info(f"[Catchup] Caja ya abierta para {usuario['nombre']}: id_session={id_session}")
            return id_session
    except Exception as e:
        logger.warning(f"[Catchup] No se pudo verificar caja existente: {e}")

    # No hay caja → abrir una nueva
    try:
        adapter.abrir_caja_session(uid, MONTO_APERTURA, "turno")
        # Recuperar la que acabamos de crear
        from app.database import DB
        conn = DB.conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id_session FROM caja_session "
            "WHERE estado='abierta' AND tipo_caja='turno' AND id_usuario_apertura = %s "
            "ORDER BY fecha_apertura DESC LIMIT 1",
            (uid,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            id_session = int(row["id_session"])
            logger.info(f"[Catchup] Caja abierta para {usuario['nombre']}: id_session={id_session}")
            return id_session
    except Exception as e:
        logger.error(f"[Catchup] Error abriendo caja para {usuario['nombre']}: {e}")
    return None



def run_catchup(backend, on_done=None):
    """
    Punto de entrada principal. Debe llamarse en un hilo separado para no
    congelar la UI.

    Args:
        backend: instancia de BackendAdapter (o DB directamente si la app lo usa así).
        on_done: callable(ok: bool, mensaje: str) — se llama al finalizar.
                 Se invoca desde el hilo worker, no desde el hilo principal.
                 La UI debe usar win.after() si quiere actualizarse.
    """
    def _worker():
        try:
            _ejecutar(backend)
            if on_done:
                on_done(True, "¡Entorno demo listo! Hay actividad cargada para hoy.")
        except Exception as e:
            logger.error(f"[Catchup] Error inesperado: {e}", exc_info=True)
            if on_done:
                on_done(False, f"Error al preparar el entorno: {e}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def _ejecutar(backend):
    """Lógica principal sincrónica."""
    logger.info("[Catchup] === INICIO CATCHUP DEMO ===")

    # ── 1. Obtener usuarios demo ──────────────────────────────────────────────
    try:
        todos_usuarios = backend.obtener_usuarios_con_rol()
    except Exception as e:
        raise RuntimeError(f"No se pudo obtener la lista de usuarios: {e}")

    vendedores_hoy = [
        u for u in todos_usuarios
        if u.get("nombre", "").lower() in VENDEDORES_DEMO
    ]
    if not vendedores_hoy:
        raise RuntimeError(
            "No se encontraron los usuarios demo (lucia, martin, sofia, carlos). "
            "¿El dump está cargado?"
        )

    # Elegir 2 cajeros al azar para el turno de hoy
    cajeros = random.sample(vendedores_hoy, min(2, len(vendedores_hoy)))
    logger.info(f"[Catchup] Cajeros del día: {[c['nombre'] for c in cajeros]}")

    # ── 2. Abrir/recuperar cajas ──────────────────────────────────────────────
    sesiones_hoy: list[tuple[int, int]] = []   # (id_usuario, id_session)
    for cajero in cajeros:
        id_session = _obtener_o_abrir_caja(backend, cajero)
        if id_session:
            sesiones_hoy.append((cajero["id_usuario"], id_session))

    if not sesiones_hoy:
        raise RuntimeError("No se pudo abrir ninguna caja de turno.")

    # ── 3. Obtener productos con stock ───────────────────────────────────────
    try:
        productos = backend.obtener_productos()
    except Exception as e:
        raise RuntimeError(f"No se pudo obtener el catálogo de productos: {e}")

    con_stock = [p for p in productos if _f(p.get("stock", 0)) > 1]
    if not con_stock:
        raise RuntimeError("No hay productos con stock disponible para generar ventas.")
    logger.info(f"[Catchup] Productos con stock: {len(con_stock)}")

    # ── 4. Obtener clientes ───────────────────────────────────────────────────
    clientes = []
    try:
        clientes = backend.obtener_clientes_con_saldos() or []
    except Exception as e:
        logger.warning(f"[Catchup] No se pudo obtener clientes: {e}")

    # ── 5. Registrar ventas ───────────────────────────────────────────────────
    ventas_ok = 0
    tipos_pago = ["efectivo", "efectivo", "efectivo", "tarjeta"]   # 75% efectivo

    for i in range(VENTAS_A_GENERAR):
        cajero_id, id_session = random.choice(sesiones_hoy)
        items = _elegir_items(con_stock)
        if not items:
            continue

        # Decidir cliente
        id_cliente = None
        tipo_pago = random.choice(tipos_pago)
        if clientes and random.random() < PROB_CLIENTE_CONOCIDO:
            c = random.choice(clientes)
            id_cliente = c["id_cliente"]
            # Si el cliente tiene cuenta corriente con margen, usarla a veces
            if random.random() < 0.40:
                try:
                    cuenta = backend.obtener_cuenta_por_cliente(id_cliente)
                    if cuenta:
                        total = sum(cant * precio for _, _, cant, precio, _ in items)
                        saldo = float(cuenta["saldo"])
                        limite = float(cuenta["limite_credito"])
                        if saldo - total >= -limite:
                            tipo_pago = "cuenta_corriente"
                except Exception:
                    pass

        try:
            id_venta = backend.registrar_venta_completa(
                id_usuario=cajero_id,
                id_cliente=id_cliente,
                items=items,
                tipo_pago=tipo_pago,
                id_session=id_session,
            )
            ventas_ok += 1
            logger.info(f"[Catchup] Venta #{i+1}: id={id_venta}, pago={tipo_pago}, items={len(items)}")

            # Actualizar stock para no vender lo que ya no hay
            con_stock = [p for p in backend.obtener_productos() if _f(p.get("stock", 0)) > 1]
            if not con_stock:
                logger.warning("[Catchup] Sin stock disponible, terminando antes.")
                break

        except Exception as e:
            logger.warning(f"[Catchup] Venta {i+1} falló (se omite): {e}")

    logger.info(f"[Catchup] === FIN CATCHUP: {ventas_ok}/{VENTAS_A_GENERAR} ventas generadas ===")
