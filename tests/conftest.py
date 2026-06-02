# tests/conftest.py
import pytest
import sys
import os
from unittest.mock import MagicMock

# Añadir el directorio raíz al path de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_db(monkeypatch):
    """Fixture que simula y mockea el módulo DB.py por completo."""
    mock = MagicMock()
    
    # Simular base_db methods
    mock.conectar = MagicMock()
    mock.obtener_stock_por_producto.return_value = 10.0
    mock.obtener_stock_minimo.return_value = 5
    mock.insertar_cliente.return_value = 1
    mock.actualizar_cliente_completo.return_value = True
    
    # Simular roles
    mock.obtener_usuarios_con_rol.return_value = [
        {"id_usuario": 1, "nombre": "admin", "id_rol": 1, "rol_nombre": "admin"},
        {"id_usuario": 2, "nombre": "vendedor1", "id_rol": 2, "rol_nombre": "vendedor"},
        {"id_usuario": 3, "nombre": "supervisor1", "id_rol": 3, "rol_nombre": "supervisor"}
    ]
    
    # Simular datos de clientes
    mock.obtener_cliente_completo.return_value = {
        "id_cliente": 1,
        "nombre": "Juan Perez",
        "dni": "12345678",
        "cuit": "20123456789",
        "direccion": "Calle Falsa 123",
        "telefono": "1123456789",
        "email": "juan@perez.com",
        "limite_credito": 5000.00,
        "saldo": -1000.00  # Debe $1000
    }
    
    # Simular sesión de caja abierta
    mock.obtener_session_activa.return_value = {
        "id_session": 1,
        "id_usuario_apertura": 1,
        "estado": "abierta"
    }
    mock.obtener_session_abierta.return_value = {
        "id_session": 1,
        "id_usuario_apertura": 1,
        "estado": "abierta"
    }
    
    # Reemplazar el módulo real DB por nuestro mock en el namespace
    monkeypatch.setattr("app.database.DB.conectar", mock.conectar)
    monkeypatch.setattr("app.database.DB.obtener_stock_por_producto", mock.obtener_stock_por_producto)
    monkeypatch.setattr("app.database.DB.obtener_stock_minimo", mock.obtener_stock_minimo)
    monkeypatch.setattr("app.database.DB.insertar_cliente", mock.insertar_cliente)
    monkeypatch.setattr("app.database.DB.actualizar_cliente_completo", mock.actualizar_cliente_completo)
    monkeypatch.setattr("app.database.DB.obtener_usuarios_con_rol", mock.obtener_usuarios_con_rol)
    monkeypatch.setattr("app.database.DB.obtener_cliente_completo", mock.obtener_cliente_completo)
    monkeypatch.setattr("app.database.DB.obtener_session_activa", mock.obtener_session_activa)
    monkeypatch.setattr("app.database.DB.obtener_session_abierta", mock.obtener_session_abierta)
    monkeypatch.setattr("app.database.DB.registrar_venta_completa", mock.registrar_venta_completa)
    monkeypatch.setattr("app.database.DB.crear_producto_completo", mock.crear_producto_completo)
    monkeypatch.setattr("app.database.DB.actualizar_producto", mock.actualizar_producto)
    monkeypatch.setattr("app.database.DB.actualizar_inventario_absoluto", mock.actualizar_inventario_absoluto)
    monkeypatch.setattr("app.database.DB.insertar_compra", mock.insertar_compra)
    monkeypatch.setattr("app.database.DB.anular_venta", mock.anular_venta)
    monkeypatch.setattr("app.database.DB.reporte_ventas_por_vendedor", mock.reporte_ventas_por_vendedor)
    monkeypatch.setattr("app.database.DB.obtener_ventas_diarias", mock.obtener_ventas_diarias)
    
    return mock

@pytest.fixture
def adapter(mock_db):
    """Fixture que provee el BackendAdapter listo para pruebas."""
    from app.database.backend_adapter import BackendAdapter
    return BackendAdapter()
