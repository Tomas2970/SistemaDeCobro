# tests/test_sistema.py
import pytest
from unittest.mock import MagicMock

# ======================================================
# 1. PRUEBAS DE PRODUCTOS Y ABM
# ======================================================

def test_crear_producto_admin_exito(adapter, mock_db):
    """Verifica que un administrador puede crear un producto correctamente."""
    mock_db.crear_producto_completo.return_value = 42
    
    pid = adapter.crear_producto_completo(
        nombre="Coca Cola 1.5L",
        categoria_id=1,
        codigo_barras="7791234567890",
        precio=1200.00,
        stock_inicial=50,
        stock_minimo=10,
        id_usuario=1  # ID de Admin
    )
    
    assert pid == 42
    mock_db.crear_producto_completo.assert_called_once_with(
        "Coca Cola 1.5L", 1200.00, 1, 50, 10, False
    )

def test_crear_producto_vendedor_denegado(adapter, mock_db):
    """Verifica que un vendedor no tiene permisos para crear un producto."""
    with pytest.raises(PermissionError, match="Los vendedores no tienen permisos"):
        adapter.crear_producto_completo(
            nombre="Sprite 1.5L",
            categoria_id=1,
            codigo_barras="7791234567891",
            precio=1200.00,
            stock_inicial=10,
            id_usuario=2  # ID de Vendedor
        )

def test_crear_producto_precio_negativo_error(adapter, mock_db):
    """Verifica que no se permiten precios negativos al crear productos."""
    with pytest.raises(ValueError, match="precio no puede ser negativo"):
        adapter.crear_producto_completo(
            nombre="Fanta 1.5L",
            categoria_id=1,
            codigo_barras="7791234567892",
            precio=-50.00,
            stock_inicial=10,
            id_usuario=1
        )

def test_actualizar_inventario_absoluto_exito(adapter, mock_db):
    """Verifica que se puede ajustar el stock físico absoluto (Admin/Supervisor)."""
    mock_db.actualizar_inventario_absoluto.return_value = True
    
    exito = adapter.actualizar_inventario_absoluto(
        id_producto=1,
        stock_abs=15.5,
        stock_minimo=5,
        id_usuario=1
    )
    
    assert exito is True
    mock_db.actualizar_inventario_absoluto.assert_called_once_with(1, 15.5, 5)


# ======================================================
# 2. PRUEBAS DE COMPRAS
# ======================================================

def test_registrar_compra_exito(adapter, mock_db):
    """Verifica que se asienta una compra a proveedores incrementando stock."""
    mock_db.registrar_compra.return_value = 100
    
    items_compra = [
        {"id_producto": 1, "cantidad": 20, "precio_costo": 500.0, "precio_venta": 650.0}
    ]
    
    cid = adapter.registrar_compra(
        id_usuario=1,
        id_proveedor=2,
        items=items_compra,
        medio_pago="efectivo"
    )
    
    assert cid == 100
    mock_db.registrar_compra.assert_called_once_with(1, 2, items_compra, "efectivo")


# ======================================================
# 3. PRUEBAS DE VENTAS Y CAJA
# ======================================================

def test_registrar_venta_completa_exito(adapter, mock_db):
    """Verifica que una venta transaccional se asienta con stock y caja abierta."""
    mock_db.registrar_venta_completa.return_value = 500
    
    items_venta = [
        (1, "Coca Cola 1.5L", 2.0, 1200.0, "7791234567890")
    ]
    
    vid = adapter.registrar_venta_completa(
        id_usuario=1,
        id_cliente=1,
        items=items_venta,
        tipo_pago="efectivo"
    )
    
    assert vid == 500
    mock_db.registrar_venta_completa.assert_called_once_with(1, 1, items_venta, "efectivo", None)

def test_registrar_venta_caja_cerrada_error(adapter, mock_db):
    """Verifica que una venta falla si no hay sesión de caja abierta."""
    mock_db.registrar_venta_completa.side_effect = ValueError("CAJA_CERRADA")
    
    with pytest.raises(ValueError, match="CAJA_CERRADA"):
        adapter.registrar_venta_completa(
            id_usuario=2,
            id_cliente=None,
            items=[(1, "Prod", 1.0, 100.0, "123")],
            tipo_pago="efectivo"
        )


# ======================================================
# 4. PRUEBAS DE CUENTA CORRIENTE Y CRÉDITO
# ======================================================

def test_cuenta_corriente_limite_credito(adapter, mock_db):
    """Verifica el cálculo correcto de crédito disponible para un cliente."""
    cliente = adapter.obtener_cliente_para_editar(1)
    
    limite = cliente["limite_credito"]
    deuda = abs(cliente["saldo"])
    credito_disponible = limite - deuda
    
    assert credito_disponible == 4000.00  # $5000 limite - $1000 deuda


# ======================================================
# 5. PRUEBAS DE USUARIOS, ACCESOS Y PERMISOS
# ======================================================

def test_rol_permisos_vendedor_cancelar_denegado(adapter):
    """Verifica que el rol Vendedor no tiene permisos para cancelar/anular ventas."""
    from app.database.permisos import tiene_permiso
    
    usuario_vendedor = {"id_rol": 2}  # Vendedor
    assert tiene_permiso(usuario_vendedor, "cancelar_ventas") is False

def test_rol_permisos_admin_cancelar_autorizado(adapter):
    """Verifica que el rol Administrador sí tiene permisos para cancelar/anular ventas."""
    from app.database.permisos import tiene_permiso
    
    usuario_admin = {"id_rol": 1}  # Admin
    assert tiene_permiso(usuario_admin, "cancelar_ventas") is True


# ======================================================
# 6. PRUEBAS DE REPORTES
# ======================================================

def test_reporte_ventas_diarias(adapter, mock_db):
    """Verifica la carga del reporte de ventas diarias por rango."""
    mock_db.obtener_ventas_diarias.return_value = [
        {"fecha": "2026-05-30", "total_ventas": 5, "monto_total": 6000.0}
    ]
    
    reporte = adapter.obtener_ventas_diarias("2026-05-01", "2026-05-30")
    
    assert len(reporte) == 1
    assert reporte[0]["monto_total"] == 6000.0
    mock_db.obtener_ventas_diarias.assert_called_once_with("2026-05-01", "2026-05-30")


# ======================================================
# 7. PRUEBAS DEL NUEVO SISTEMA DE ANULACIÓN DE VENTAS
# ======================================================

def test_anular_venta_admin_exito(adapter, mock_db):
    """Verifica que un Administrador puede anular una venta de forma exitosa."""
    mock_db.anular_venta.return_value = True
    
    exito = adapter.anular_venta(id_venta=500, id_usuario=1) # 1 = Admin
    
    assert exito is True
    mock_db.anular_venta.assert_called_once_with(500, 1, None)

def test_anular_venta_vendedor_denegado(adapter, mock_db):
    """Verifica que un Vendedor no puede anular ventas (lanzando PermissionError)."""
    with pytest.raises(PermissionError, match="No tienes permisos para anular ventas"):
        adapter.anular_venta(id_venta=500, id_usuario=2) # 2 = Vendedor

# ======================================================
# 8. PRUEBAS DE TRANSFERENCIA A TESORERÍA (CONTROL DUAL)
# ======================================================

def test_transferir_tesoreria_exito(adapter, mock_db):
    """Verifica la transferencia exitosa a la tesorería."""
    mock_db.transferir_entre_cajas.return_value = True
    
    exito = adapter.transferir_entre_cajas(
        origen=10, 
        destino=20, 
        monto=5000.0, 
        id_usuario=2, 
        motivo_salida='transferencia_tesoreria_salida',
        motivo_entrada='transferencia_tesoreria_entrada',
        obs='Retiro a tesorería',
        id_autorizador=1
    )
    
    assert exito is True
    mock_db.transferir_entre_cajas.assert_called_once_with(
        10, 20, 5000.0, 2, 'transferencia_tesoreria_salida', 'transferencia_tesoreria_entrada', 'Retiro a tesorería', 1
    )

def test_creacion_automatica_tesoreria(adapter, mock_db):
    """Verifica la lógica de crear tesorería si no existe."""
    mock_db.obtener_o_crear_tesoreria_hoy.return_value = {'id_session': 25, 'estado': 'abierta'}
    
    tesoreria = adapter.obtener_o_crear_tesoreria_hoy(id_usuario=1)
    
    assert tesoreria['id_session'] == 25
    mock_db.obtener_o_crear_tesoreria_hoy.assert_called_once()

