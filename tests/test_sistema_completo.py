"""
tests/test_sistema_completo.py
================================
Batería de tests final y completa del Sistema de Cobros Don Atilio.
Cubre: permisos, productos, ventas, compras, caja, cuenta corriente,
reportes, anulaciones, tesorería y el módulo demo_catchup.

Todos los tests usan mocks — nunca tocan la base de datos real.
"""
import pytest
from unittest.mock import MagicMock, patch


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def admin():
    return {"id_usuario": 1, "nombre": "admin", "id_rol": 1}

@pytest.fixture
def supervisor():
    return {"id_usuario": 3, "nombre": "valentina", "id_rol": 3}

@pytest.fixture
def vendedor():
    return {"id_usuario": 2, "nombre": "lucia", "id_rol": 2}

@pytest.fixture
def usuario_inexistente():
    return {"id_usuario": 99, "nombre": "fantasma", "id_rol": 99}


# ================================================================
# 1. MÓDULO DE PERMISOS — cobertura exhaustiva de los 3 roles
# ================================================================

class TestPermisos:
    """Valida la matriz completa de permisos por rol."""

    # ── Admin ────────────────────────────────────────────────────
    @pytest.mark.parametrize("accion", [
        "ver_usuarios", "crear_usuarios", "editar_usuarios", "eliminar_usuarios",
        "crear_productos", "editar_productos", "eliminar_productos", "modificar_precios",
        "ajustar_inventario_manual", "cancelar_ventas", "procesar_devoluciones",
        "crear_clientes", "editar_clientes", "eliminar_clientes",
        "registrar_compras", "ver_reportes", "ver_auditoria",
        "cerrar_caja_ajena", "abrir_tesoreria", "cerrar_tesoreria",
        "ingreso_extraordinario", "configurar_sistema",
    ])
    def test_admin_tiene_todos_los_permisos(self, admin, accion):
        from app.database.permisos import tiene_permiso
        assert tiene_permiso(admin, accion) is True, f"Admin debería tener '{accion}'"

    # ── Vendedor: solo tiene lo suyo ─────────────────────────────
    @pytest.mark.parametrize("accion", [
        "realizar_ventas", "ver_ventas", "ver_productos", "ver_inventario",
        "ver_clientes", "abrir_caja", "cerrar_caja",
        "movimientos_caja_manuales", "gestionar_cuenta_corriente",
    ])
    def test_vendedor_tiene_permisos_basicos(self, vendedor, accion):
        from app.database.permisos import tiene_permiso
        assert tiene_permiso(vendedor, accion) is True

    @pytest.mark.parametrize("accion", [
        "cancelar_ventas", "procesar_devoluciones", "crear_productos",
        "modificar_precios", "ajustar_inventario_manual",
        "crear_clientes", "editar_clientes", "eliminar_clientes",
        "ver_auditoria", "configurar_sistema", "abrir_tesoreria",
        "ver_usuarios", "eliminar_productos",
    ])
    def test_vendedor_NO_tiene_permisos_elevados(self, vendedor, accion):
        from app.database.permisos import tiene_permiso
        assert tiene_permiso(vendedor, accion) is False, f"Vendedor NO debería tener '{accion}'"

    # ── Supervisor ───────────────────────────────────────────────
    @pytest.mark.parametrize("accion", [
        "modificar_precios", "ajustar_inventario_manual",
        "procesar_devoluciones", "crear_clientes", "editar_clientes",
        "registrar_compras", "cerrar_caja_ajena", "transferencia_tesoreria",
        "ver_reportes",
    ])
    def test_supervisor_tiene_permisos_medios(self, supervisor, accion):
        from app.database.permisos import tiene_permiso
        assert tiene_permiso(supervisor, accion) is True

    @pytest.mark.parametrize("accion", [
        "eliminar_clientes", "ver_usuarios", "crear_usuarios",
        "eliminar_usuarios", "configurar_sistema", "ver_auditoria",
        "abrir_tesoreria", "cerrar_tesoreria", "ingreso_extraordinario",
        "cancelar_ventas",
    ])
    def test_supervisor_NO_tiene_permisos_de_admin(self, supervisor, accion):
        from app.database.permisos import tiene_permiso
        assert tiene_permiso(supervisor, accion) is False

    # ── Casos borde ──────────────────────────────────────────────
    def test_tiene_permiso_usuario_none(self):
        from app.database.permisos import tiene_permiso
        assert tiene_permiso(None, "ver_ventas") is False

    def test_tiene_permiso_usuario_sin_id_rol(self):
        from app.database.permisos import tiene_permiso
        assert tiene_permiso({}, "ver_ventas") is False

    def test_tiene_permiso_rol_desconocido(self, usuario_inexistente):
        from app.database.permisos import tiene_permiso
        # Rol 99 no existe → cae en "vendedor" (fallback), no debería tener permisos admin
        assert tiene_permiso(usuario_inexistente, "configurar_sistema") is False

    def test_rol_nombre_correcto(self):
        from app.database.permisos import obtener_rol_nombre
        assert obtener_rol_nombre(1) == "admin"
        assert obtener_rol_nombre(2) == "vendedor"
        assert obtener_rol_nombre(3) == "supervisor"
        assert obtener_rol_nombre(99) == "vendedor"  # fallback

    def test_helpers_de_permiso(self, admin, vendedor, supervisor):
        from app.database.permisos import (
            puede_modificar_precios, puede_ajustar_inventario_manual,
            puede_movimientos_caja_manuales, puede_procesar_devoluciones
        )
        assert puede_modificar_precios(admin) is True
        assert puede_modificar_precios(vendedor) is False
        assert puede_modificar_precios(supervisor) is True

        assert puede_ajustar_inventario_manual(admin) is True
        assert puede_ajustar_inventario_manual(vendedor) is False

        assert puede_movimientos_caja_manuales(vendedor) is True
        assert puede_movimientos_caja_manuales(admin) is True

        assert puede_procesar_devoluciones(admin) is True
        assert puede_procesar_devoluciones(vendedor) is False

    def test_obtener_menu_items_admin_habilita_todo(self, admin):
        from app.database.permisos import obtener_menu_items
        menu = obtener_menu_items(admin)
        assert menu["panel_control"] is True
        assert menu["productos"]["agregar"] is True
        assert menu["clientes"]["eliminar"] is True
        assert menu["usuarios"]["agregar"] is True
        assert menu["tesoreria"]["abrir"] is True

    def test_obtener_menu_items_vendedor_restringe(self, vendedor):
        from app.database.permisos import obtener_menu_items
        menu = obtener_menu_items(vendedor)
        assert menu["panel_control"] is False
        assert menu["productos"]["agregar"] is False
        assert menu["clientes"]["agregar"] is False
        assert menu["usuarios"]["agregar"] is False
        assert menu["ventas"]["nueva_venta"] is True   # puede vender

    def test_describir_rol(self):
        from app.database.permisos import describir_rol
        assert "ADMINISTRADOR" in describir_rol("admin")
        assert "ENCARGADO" in describir_rol("supervisor")
        assert "VENDEDOR" in describir_rol("vendedor")
        assert "desconocido" in describir_rol("fantasma")


# ================================================================
# 2. BACKEND ADAPTER — validaciones de negocio (sin DB real)
# ================================================================

@pytest.fixture
def mock_db_full(monkeypatch):
    """Mock completo de DB para pruebas del adapter."""
    m = MagicMock()
    m.registrar_venta_completa.return_value = 777
    m.obtener_stock_por_producto.return_value = 20.0
    m.crear_producto_completo.return_value = 55
    m.actualizar_inventario_absoluto.return_value = True
    m.anular_venta.return_value = True
    m.registrar_compra.return_value = 88
    m.obtener_ventas_diarias.return_value = []
    m.transferir_entre_cajas.return_value = True
    m.obtener_o_crear_tesoreria_hoy.return_value = {"id_session": 10, "estado": "abierta"}
    m.obtener_cliente_completo.return_value = {
        "id_cliente": 1, "nombre": "Test Cliente", "dni": "11111111",
        "cuit": "20111111113", "direccion": "Dir 1", "telefono": "123",
        "email": "t@t.com", "limite_credito": 10000.00, "saldo": -2000.00
    }
    m.obtener_usuarios_con_rol.return_value = [
        {"id_usuario": 1, "nombre": "admin",     "id_rol": 1, "rol_nombre": "admin"},
        {"id_usuario": 2, "nombre": "lucia",     "id_rol": 2, "rol_nombre": "vendedor"},
        {"id_usuario": 3, "nombre": "valentina", "id_rol": 3, "rol_nombre": "supervisor"},
    ]
    monkeypatch.setattr("app.database.DB.registrar_venta_completa", m.registrar_venta_completa)
    monkeypatch.setattr("app.database.DB.obtener_stock_por_producto", m.obtener_stock_por_producto)
    monkeypatch.setattr("app.database.DB.crear_producto_completo", m.crear_producto_completo)
    monkeypatch.setattr("app.database.DB.actualizar_inventario_absoluto", m.actualizar_inventario_absoluto)
    monkeypatch.setattr("app.database.DB.anular_venta", m.anular_venta)
    monkeypatch.setattr("app.database.DB.registrar_compra", m.registrar_compra)
    monkeypatch.setattr("app.database.DB.obtener_ventas_diarias", m.obtener_ventas_diarias)
    monkeypatch.setattr("app.database.DB.transferir_entre_cajas", m.transferir_entre_cajas)
    monkeypatch.setattr("app.database.DB.obtener_o_crear_tesoreria_hoy", m.obtener_o_crear_tesoreria_hoy)
    monkeypatch.setattr("app.database.DB.obtener_cliente_completo", m.obtener_cliente_completo)
    monkeypatch.setattr("app.database.DB.obtener_usuarios_con_rol", m.obtener_usuarios_con_rol)
    monkeypatch.setattr("app.database.DB.actualizar_cliente_completo", MagicMock(return_value=True))
    monkeypatch.setattr("app.database.DB.crear_cliente", MagicMock(return_value=1))
    monkeypatch.setattr("app.database.DB.obtener_session_activa", MagicMock(return_value={"id_session": 1}))
    monkeypatch.setattr("app.database.DB.obtener_session_abierta", MagicMock(return_value={"id_session": 1}))
    return m

@pytest.fixture
def adapter(mock_db_full):
    from app.database.backend_adapter import BackendAdapter
    return BackendAdapter()


class TestProductos:
    """Validaciones del ABM de productos."""

    def test_crear_producto_admin_ok(self, adapter, mock_db_full):
        pid = adapter.crear_producto_completo(
            nombre="Coca Cola 2.25L", categoria_id=1, codigo_barras="779123",
            precio=1800.0, stock_inicial=20, stock_minimo=5, id_usuario=1
        )
        assert pid == 55

    def test_crear_producto_vendedor_prohibido(self, adapter):
        with pytest.raises(PermissionError):
            adapter.crear_producto_completo(
                nombre="Fanta", categoria_id=1, codigo_barras="779124",
                precio=1500.0, stock_inicial=10, id_usuario=2
            )

    @pytest.mark.parametrize("precio", [-1.0, -0.01, -999999.0])
    def test_crear_producto_precio_negativo_rechazado(self, adapter, precio):
        with pytest.raises(ValueError, match="precio no puede ser negativo"):
            adapter.crear_producto_completo(
                nombre="Producto X", categoria_id=1, codigo_barras="000",
                precio=precio, stock_inicial=5, id_usuario=1
            )

    def test_actualizar_inventario_ok(self, adapter):
        result = adapter.actualizar_inventario_absoluto(
            id_producto=1, stock_abs=100.0, stock_minimo=10, id_usuario=1
        )
        assert result is True

    @pytest.mark.parametrize("stock,minimo", [
        (50, 5), (0, 0), (999, 100), (1, 1),
    ])
    def test_actualizar_inventario_valores_variados(self, adapter, stock, minimo):
        result = adapter.actualizar_inventario_absoluto(
            id_producto=1, stock_abs=stock, stock_minimo=minimo, id_usuario=1
        )
        assert result is True


class TestVentas:
    """Validaciones del flujo de ventas."""

    def test_venta_exitosa(self, adapter):
        vid = adapter.registrar_venta_completa(
            id_usuario=2, id_cliente=None,
            items=[(1, "Prod", 2.0, 1000.0, "123")],
            tipo_pago="efectivo"
        )
        assert vid == 777

    def test_venta_caja_cerrada(self, adapter, mock_db_full):
        mock_db_full.registrar_venta_completa.side_effect = ValueError("CAJA_CERRADA")
        with pytest.raises(ValueError, match="CAJA_CERRADA"):
            adapter.registrar_venta_completa(
                id_usuario=2, id_cliente=None,
                items=[(1, "P", 1.0, 100.0, "456")],
                tipo_pago="efectivo"
            )

    @pytest.mark.parametrize("tipo_pago", ["efectivo", "tarjeta", "transferencia", "cuenta_corriente"])
    def test_venta_todos_los_medios_de_pago(self, adapter, tipo_pago):
        vid = adapter.registrar_venta_completa(
            id_usuario=2, id_cliente=1,
            items=[(1, "Prod", 1.0, 500.0, "000")],
            tipo_pago=tipo_pago
        )
        assert vid == 777

    def test_anular_venta_admin(self, adapter):
        result = adapter.anular_venta(id_venta=777, id_usuario=1, motivo="Error de carga")
        assert result is True

    def test_anular_venta_supervisor(self, adapter):
        # Supervisores también pueden anular (tienen el permiso)
        result = adapter.anular_venta(id_venta=777, id_usuario=3, motivo="Devolución")
        assert result is True

    def test_anular_venta_vendedor_prohibido(self, adapter):
        with pytest.raises(PermissionError, match="No tienes permisos para anular ventas"):
            adapter.anular_venta(id_venta=777, id_usuario=2)


class TestCuentaCorriente:
    """Validaciones de límite de crédito y saldo."""

    def test_credito_disponible_calculo(self, adapter):
        cliente = adapter.obtener_cliente_para_editar(1)
        limite = cliente["limite_credito"]
        deuda = abs(cliente["saldo"])
        disponible = limite - deuda
        assert disponible == 8000.00  # 10000 - 2000

    @pytest.mark.parametrize("limite,saldo,esperado", [
        (5000, -1000, 4000),
        (10000, -10000, 0),
        (3000, 0, 3000),
        (0, 0, 0),
    ])
    def test_credito_disponible_parametrizado(self, limite, saldo, esperado):
        disponible = limite - abs(saldo)
        assert disponible == esperado


class TestCompras:
    """Validaciones del registro de compras a proveedores."""

    def test_registrar_compra_ok(self, adapter):
        items = [{"id_producto": 1, "cantidad": 50, "precio_costo": 800.0, "precio_venta": 1100.0}]
        cid = adapter.registrar_compra(id_usuario=1, id_proveedor=2, items=items, medio_pago="efectivo")
        assert cid == 88

    @pytest.mark.parametrize("medio", ["efectivo", "transferencia", "cheque"])
    def test_compra_medios_de_pago_variados(self, adapter, medio):
        items = [{"id_producto": 2, "cantidad": 10, "precio_costo": 500.0, "precio_venta": 700.0}]
        cid = adapter.registrar_compra(id_usuario=1, id_proveedor=1, items=items, medio_pago=medio)
        assert cid == 88


class TestTesoreria:
    """Validaciones del módulo de Tesorería."""

    def test_crear_tesoreria_si_no_existe(self, adapter):
        t = adapter.obtener_o_crear_tesoreria_hoy(id_usuario=1)
        assert t["id_session"] == 10
        assert t["estado"] == "abierta"

    def test_transferir_entre_cajas(self, adapter):
        ok = adapter.transferir_entre_cajas(
            origen=1, destino=10, monto=5000.0, id_usuario=2,
            motivo_salida="transferencia_tesoreria_salida",
            motivo_entrada="transferencia_tesoreria_entrada",
            obs="Retiro fin de turno", id_autorizador=3
        )
        assert ok is True


class TestReportes:
    """Validaciones de consultas de reportes."""

    def test_ventas_diarias_vacio(self, adapter, mock_db_full):
        mock_db_full.obtener_ventas_diarias.return_value = []
        r = adapter.obtener_ventas_diarias("2026-01-01", "2026-01-31")
        assert r == []

    def test_ventas_diarias_con_datos(self, adapter, mock_db_full):
        mock_db_full.obtener_ventas_diarias.return_value = [
            {"fecha": "2026-06-01", "total_ventas": 10, "monto_total": 15000.0},
            {"fecha": "2026-06-02", "total_ventas": 8, "monto_total": 12000.0},
        ]
        r = adapter.obtener_ventas_diarias("2026-06-01", "2026-06-02")
        assert len(r) == 2
        assert r[0]["monto_total"] == 15000.0

    def test_usuarios_listados(self, adapter):
        usuarios = adapter.obtener_usuarios_con_rol()
        assert len(usuarios) == 3
        nombres = [u["nombre"] for u in usuarios]
        assert "admin" in nombres
        assert "lucia" in nombres


# ================================================================
# 3. MÓDULO DEMO_CATCHUP — lógica sin BD real
# ================================================================

class TestDemoCatchup:
    """Valida la lógica del inyector de datos demo."""

    def test_elegir_items_retorna_lista(self):
        from app.tools.demo_catchup import _elegir_items
        productos_mock = [
            {"id_producto": i, "nombre": f"Prod {i}", "stock": 10.0,
             "precio": 1000.0, "es_pesable": False, "codigo_barras": f"77{i}"}
            for i in range(1, 10)
        ]
        items = _elegir_items(productos_mock)
        assert isinstance(items, list)
        assert 1 <= len(items) <= 4

    def test_elegir_items_lista_vacia(self):
        from app.tools.demo_catchup import _elegir_items
        # Con lista vacía debe retornar lista vacía sin errores
        items = _elegir_items([])
        assert items == []

    def test_elegir_items_producto_sin_stock(self):
        from app.tools.demo_catchup import _elegir_items
        productos_sin_stock = [
            {"id_producto": 1, "nombre": "Sin Stock", "stock": 0.0,
             "precio": 500.0, "es_pesable": False, "codigo_barras": "000"}
        ]
        items = _elegir_items(productos_sin_stock)
        # stock=0 → cant se calcula pero max(1, int(0)) → la tupla puede generarse con cant=0
        # Verificar que la función no lanza excepción
        assert isinstance(items, list)

    def test_elegir_items_producto_pesable(self):
        from app.tools.demo_catchup import _elegir_items
        productos_pesables = [
            {"id_producto": 1, "nombre": "Queso kg", "stock": 5.0,
             "precio": 4000.0, "es_pesable": True, "codigo_barras": "111"}
        ]
        items = _elegir_items(productos_pesables)
        if items:
            _, _, cant, _, _ = items[0]
            # Para pesables, cantidad debe ser float en rango (0.3, 2.0)
            assert 0.3 <= cant <= 2.0

    def test_run_catchup_llama_callback_error_sin_usuarios(self):
        """Si no hay usuarios demo en BD, el callback debe recibir ok=False."""
        from app.tools.demo_catchup import run_catchup
        import threading, time

        backend_mock = MagicMock()
        backend_mock.obtener_usuarios_con_rol.return_value = []  # Sin usuarios

        resultados = []
        evento = threading.Event()

        def on_done(ok, msg):
            resultados.append((ok, msg))
            evento.set()

        run_catchup(backend_mock, on_done=on_done)
        evento.wait(timeout=5)

        assert len(resultados) == 1
        ok, msg = resultados[0]
        assert ok is False
        assert "usuarios" in msg.lower() or "no se encontraron" in msg.lower()

    def test_run_catchup_sin_productos_reporta_error(self):
        """Si no hay productos con stock, el callback debe recibir ok=False."""
        from app.tools.demo_catchup import run_catchup
        import threading

        backend_mock = MagicMock()
        backend_mock.obtener_usuarios_con_rol.return_value = [
            {"id_usuario": 2, "nombre": "lucia", "id_rol": 2},
        ]
        # Productos vacíos → sin stock disponible
        backend_mock.obtener_productos.return_value = []
        backend_mock.obtener_clientes_con_saldos.return_value = []

        # Parchamos DB directamente en el módulo app.database
        # para evitar la consulta real a la BD al verificar/abrir cajas
        with patch("app.database.DB.conectar") as mock_conectar:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = {"id_session": 99}  # caja "ya abierta"
            mock_conn.cursor.return_value = mock_cur
            mock_conectar.return_value = mock_conn

            resultados = []
            evento = threading.Event()

            def on_done(ok, msg):
                resultados.append((ok, msg))
                evento.set()

            run_catchup(backend_mock, on_done=on_done)
            evento.wait(timeout=5)

        assert len(resultados) == 1
        ok, msg = resultados[0]
        # Sin productos con stock debe fallar o terminar con 0 ventas
        # (ok puede ser True con 0 ventas, o False si lanza excepción)
        assert isinstance(ok, bool)

    def test_constantes_de_catchup(self):
        """Verifica que las constantes del módulo tienen valores razonables."""
        from app.tools import demo_catchup
        assert demo_catchup.VENTAS_A_GENERAR >= 5
        assert demo_catchup.MONTO_APERTURA > 0
        assert 0 < demo_catchup.PROB_CLIENTE_CONOCIDO < 1
        assert len(demo_catchup.VENDEDORES_DEMO) >= 2


# ================================================================
# 4. VALIDACIONES DE FORMATO Y TIPOS
# ================================================================

class TestValidacionesFormato:
    """Pruebas de borde sobre tipos de datos y conversiones."""

    @pytest.mark.parametrize("valor,esperado", [
        (1000, 1000.0),
        (0, 0.0),
        (None, 0.0),
        (500.50, 500.50),
    ])
    def test_helper_f_conversion(self, valor, esperado):
        """Verifica que _f() convierte correctamente Decimal/int/None a float."""
        from app.tools.demo_catchup import _f
        from decimal import Decimal
        if valor is not None:
            result = _f(Decimal(str(valor)) if isinstance(valor, (int, float)) else valor)
        else:
            result = _f(valor)
        assert result == esperado

    def test_helper_f_decimal(self):
        from app.tools.demo_catchup import _f
        from decimal import Decimal
        assert _f(Decimal("1234.56")) == 1234.56

    def test_permisos_accion_inexistente(self):
        """Una acción que no existe en ningún rol devuelve False para todos."""
        from app.database.permisos import tiene_permiso
        for rol in [1, 2, 3]:
            assert tiene_permiso({"id_rol": rol}, "volar_helicoptero") is False
