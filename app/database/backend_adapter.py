# app/database/backend_adapter.py
from __future__ import annotations
from typing import Any, Optional
import logging
import json # ¡NUEVO!

try:
    from app.database import DB
except Exception as e:
    raise ImportError("No se pudo importar app.database.DB.") from e

# --- ¡CAMBIO! Corregir typo ---
# logger = logging.getLoggaer(__name__) # <-- Tenía 'getLoggaer'
logger = logging.getLogger(__name__)    # <-- Corregido a 'getLogger'
# --- FIN CAMBIO ---

class BackendAdapter:
    
    # --- ¡NUEVA FUNCIÓN HELPER DE AUDITORÍA! ---
    def _registrar_auditoria(
        self,
        id_usuario: int | None,
        accion: str,
        tabla_afectada: str | None = None,
        id_registro: int | None = None,
        datos_anteriores: dict | None = None,
        datos_nuevos: dict | None = None
    ) -> None:
        """Helper interno para registrar en la base de datos."""
        try:
            # Limpiar datos para que solo se guarden los cambios
            if datos_anteriores and datos_nuevos:
                # Mantenemos solo las claves que realmente cambiaron
                keys_nuevas = set(datos_nuevos.keys())
                keys_viejas = set(datos_anteriores.keys())
                keys_comunes = keys_nuevas.intersection(keys_viejas)
                
                cambios_viejos = {}
                cambios_nuevos = {}
                
                for k in keys_comunes:
                    if datos_anteriores[k] != datos_nuevos[k]:
                        cambios_viejos[k] = datos_anteriores[k]
                        cambios_nuevos[k] = datos_nuevos[k]
                
                # Si no hubo cambios, no registrar
                if not cambios_nuevos:
                    return
                
                datos_anteriores = cambios_viejos
                datos_nuevos = cambios_nuevos
                
            DB.registrar_auditoria(
                id_usuario=id_usuario,
                accion=accion,
                tabla_afectada=tabla_afectada,
                id_registro=id_registro,
                datos_anteriores=datos_anteriores,
                datos_nuevos=datos_nuevos
            )
        except Exception as e:
            logger.error(f"Fallo al preparar auditoría: {e}")
            
    # --- FIN NUEVA FUNCIÓN ---
    
    
    # ---------- Auth ----------
    def verificar_contraseña(self, usuario: str, contraseña: str) -> dict | None:
        return DB.verificar_contraseña(usuario, contraseña)

    # ---------- Clientes ----------
    def insertar_cliente(self, nombre: str, dni: str, direccion: str, telefono: str, email: str, limite_credito: float = 50000.00) -> int | None:
        try:
            limite_valido = float(limite_credito)
        except (ValueError, TypeError):
            limite_valido = 50000.00
        return DB.insertar_cliente(nombre, dni, direccion, telefono, email, limite_valido)

    def actualizar_cliente(self, id_cliente: int, nombre: str, dni: str, direccion: str, telefono: str, email: str, limite_credito: float) -> bool:
        try:
            limite_valido = float(limite_credito)
        except (ValueError, TypeError):
            limite_valido = 0.00 
        return DB.actualizar_cliente_completo(id_cliente, nombre, dni, direccion, telefono, email, limite_valido)

    def listar_clientes(self, incluir_inactivos: bool = False) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_clientes", None)
        return list(fn(incluir_inactivos) or []) if callable(fn) else []

    def listar_clientes_con_saldos(self, incluir_inactivos: bool = False) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_clientes_con_saldos", None)
        return list(fn(incluir_inactivos) or []) if callable(fn) else []

    def obtener_cliente_para_editar(self, id_cliente: int) -> dict | None:
        fn = getattr(DB, "obtener_cliente_completo", None)
        return fn(id_cliente) if callable(fn) else None

    def buscar_cliente_por_nombre(self, patron: str) -> list[dict[str, Any]]:
        fn = getattr(DB, "buscar_cliente_por_nombre", None)
        return list(fn(patron) or []) if callable(fn) else []

    def buscar_cliente_por_dni(self, dni: str) -> dict | None:
        fn = getattr(DB, "buscar_cliente_por_dni", None)
        return fn(dni) if callable(fn) else None

    def eliminar_cliente_logico(self, id_cliente: int) -> bool:
        fn = getattr(DB, "eliminar_cliente_logico", None)
        return bool(fn(id_cliente)) if callable(fn) else False

    # ---------- Ventas ----------
    def insertar_venta(self, id_usuario: int, id_cliente: int | None = None) -> int | None:
        return DB.insertar_venta(id_usuario, None if id_cliente in (None, 0) else id_cliente)
    def insertar_detalle_venta(self, id_venta: int, id_producto: int, cantidad: float, precio_unitario: float) -> bool:
        return DB.insertar_detalle_venta(id_venta, id_producto, cantidad, precio_unitario)
    def insertar_detalle_venta_libre(self, id_venta: int, nombre: str, cantidad: float, precio_unitario: float) -> bool:
        fn = getattr(DB, "insertar_detalle_venta_libre", None)
        return bool(fn(id_venta, nombre, cantidad, precio_unitario)) if callable(fn) else False
    def actualizar_pago_y_estado_venta(self, id_venta: int, tipo_pago: str) -> bool:
        fn = getattr(DB, "actualizar_pago_y_estado_venta", None)
        return bool(fn(id_venta, tipo_pago, "completada")) if callable(fn) else False
        
    def registrar_venta_completa(
        self, 
        id_usuario: int, 
        id_cliente: int | None, 
        items: list, 
        tipo_pago: str
    ) -> int | None:
        try:
            # La lógica de auditoría de Venta ya está en el Trigger de Inventario,
            # pero podríamos agregar una auditoría de 'ACCIÓN' aquí si quisiéramos.
            return DB.registrar_venta_completa(id_usuario, id_cliente, items, tipo_pago)
        except Exception as e:
            logger.error(f"Error en registrar_venta_completa: {e}")
            raise 
    
    # ---------- Productos / Categorías ----------
    def obtener_categorias(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_categorias", None)
        return list(fn() or []) if callable(fn) else []
    def obtener_productos_full(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "buscar_producto_por_nombre", None)
        return list(fn("") or []) if callable(fn) else []
    def buscar_producto_por_nombre(self, patron: str) -> list[dict[str, Any]]:
        return list(DB.buscar_producto_por_nombre(patron) or [])
    def buscar_producto_por_codigo_barras(self, codigo: str) -> dict | None:
        fn = getattr(DB, "buscar_producto_por_codigo_barras", None)
        return fn(codigo) if callable(fn) else None
    def buscar_producto_por_id(self, id_producto: int) -> dict | None:
        fn_db = getattr(DB, "buscar_producto_por_id", None)
        if callable(fn_db):
            return fn_db(id_producto)
        for p in self.obtener_productos_full():
            try:
                if int(p.get("id_producto", -1)) == int(id_producto):
                    return p
            except Exception:
                pass
        return None
        
    def crear_producto_completo(
        self,
        nombre: str,
        categoria_id: Optional[int],
        codigo_barras: Optional[str],
        precio: float,
        stock_inicial: int,
        stock_minimo: int = 10,
        es_pesable: bool = False,
        id_usuario: int | None = None # ¡NUEVO!
    ) -> int | None:
        
        pid = DB.crear_producto_completo(nombre, precio, categoria_id, stock_inicial, stock_minimo, es_pesable)
        
        # Auditoría de Creación
        if pid:
            self._registrar_auditoria(
                id_usuario=id_usuario,
                accion="CREAR_PRODUCTO",
                tabla_afectada="Producto",
                id_registro=pid,
                datos_nuevos={"nombre": nombre, "precio": precio, "stock": stock_inicial, "es_pesable": es_pesable}
            )
            # Asignar código de barras (esto también debería auditarse si quisiéramos)
            if codigo_barras:
                fn = getattr(DB, "actualizar_producto", None)
                if callable(fn):
                    try:
                        fn(id_producto=pid, codigo_barras=codigo_barras)
                    except Exception as e:
                        logger.error(f"Fallo al setear codigo_barras post-creación: {e}")
                        pass
        return pid

    def actualizar_producto(
        self,
        id_producto: int,
        nombre: Optional[str] = None,
        id_categoria: Optional[int] = None,
        precio: Optional[float] = None,
        codigo_barras: Optional[str] = None,
        es_pesable: Optional[bool] = None,
        id_usuario: int | None = None # ¡NUEVO!
    ) -> bool:
        
        # 1. Obtener datos anteriores PARA AUDITAR
        producto_anterior = self.buscar_producto_por_id(id_producto)
        
        fn = getattr(DB, "actualizar_producto", None)
        kwargs = {
            "nombre": nombre,
            "id_categoria": id_categoria,
            "precio": precio,
            "codigo_barras": codigo_barras,
            "es_pesable": es_pesable 
        }
        params = {k: v for k, v in kwargs.items() if v is not None or k in ('codigo_barras', 'es_pesable')}
        
        # 2. Actualizar
        resultado = bool(fn(id_producto=id_producto, **params)) if callable(fn) else False
        
        # 3. Registrar auditoría (como en tu .docx)
        if resultado:
            self._registrar_auditoria(
                id_usuario=id_usuario,
                accion="MODIFICAR_PRODUCTO",
                tabla_afectada="Producto",
                id_registro=id_producto,
                datos_anteriores=producto_anterior,
                datos_nuevos=kwargs # Pasamos los cambios solicitados
            )
        
        return resultado


    # ---------- Stock & mínimo ----------
    def obtener_stock(self, id_producto: int) -> float: 
        fn = getattr(DB, "obtener_stock_por_producto", None)
        return float(fn(id_producto)) if callable(fn) else 0.0
    def obtener_stock_minimo(self, id_producto: int) -> int:
        fn = getattr(DB, "obtener_stock_minimo", None)
        return int(fn(id_producto)) if callable(fn) else 0
        
    def actualizar_inventario_absoluto(self, id_producto: int, stock_abs: float, stock_minimo: Optional[int], id_usuario: int | None = None) -> bool:
        
        # 1. Obtener datos anteriores PARA AUDITAR
        stock_anterior = self.obtener_stock(id_producto)
        stock_min_anterior = self.obtener_stock_minimo(id_producto)
        
        fn = getattr(DB, "actualizar_inventario_absoluto", None)
        
        # 2. Actualizar
        resultado = bool(fn(id_producto, float(stock_abs), int(stock_minimo) if stock_minimo is not None else None)) if callable(fn) else False
        
        # 3. Registrar auditoría
        if resultado:
            datos_viejos = {"stock": stock_anterior, "stock_minimo": stock_min_anterior}
            datos_nuevos = {"stock": stock_abs, "stock_minimo": stock_minimo}
            
            self._registrar_auditoria(
                id_usuario=id_usuario,
                accion="AJUSTE_STOCK_MANUAL",
                tabla_afectada="Inventario",
                id_registro=id_producto,
                datos_anteriores=datos_viejos,
                datos_nuevos=datos_nuevos
            )
        
        return resultado

    def obtener_stock_bajo(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_stock_bajo", None)
        return list(fn() or []) if callable(fn) else []

    # ---------- Bajas ----------
    def eliminar_producto(self, id_producto: int, id_usuario: int | None = None) -> bool:
        fn = getattr(DB, "eliminar_producto", None)
        if not callable(fn):
            raise RuntimeError("DB.eliminar_producto no está implementado.")
        
        # 1. Obtener datos anteriores
        producto_anterior = self.buscar_producto_por_id(id_producto)
        
        # 2. Eliminar
        resultado = bool(fn(id_producto))
        
        # 3. Registrar auditoría
        if resultado:
            self._registrar_auditoria(
                id_usuario=id_usuario,
                accion="DESACTIVAR_PRODUCTO",
                tabla_afectada="Producto",
                id_registro=id_producto,
                datos_anteriores={"nombre": producto_anterior.get("nombre"), "activo": True},
                datos_nuevos={"activo": False}
            )
        return resultado

    # ---------- Proveedores y Compras ----------
    
    def obtener_proveedores(self, incluir_inactivos: bool = False) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_proveedores", None)
        return list(fn(incluir_inactivos) or []) if callable(fn) else []
    def insertar_proveedor(self, nombre: str, empresa: str, telefono: str, email: str) -> int | None:
        fn = getattr(DB, "insertar_proveedor", None)
        return fn(nombre, empresa, telefono, email) if callable(fn) else None
    def actualizar_proveedor(self, id_proveedor: int, nombre: str, empresa: str, telefono: str, email: str) -> bool:
        fn = getattr(DB, "actualizar_proveedor", None)
        return bool(fn(id_proveedor, nombre, empresa, telefono, email)) if callable(fn) else False
    def obtener_proveedor_para_editar(self, id_proveedor: int) -> dict | None:
        fn = getattr(DB, "obtener_proveedor_completo", None)
        return fn(id_proveedor) if callable(fn) else None
    def eliminar_proveedor_logico(self, id_proveedor: int) -> bool:
        fn = getattr(DB, "eliminar_proveedor_logico", None)
        return bool(fn(id_proveedor)) if callable(fn) else False
    def obtener_productos_por_proveedor(self, id_proveedor: int) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_productos_por_proveedor", None)
        return list(fn(id_proveedor) or []) if callable(fn) else []
    def obtener_productos_sin_asignar(self, id_proveedor: int) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_productos_sin_asignar", None)
        return list(fn(id_proveedor) or []) if callable(fn) else []
    def asignar_producto_a_proveedor(self, id_proveedor: int, id_producto: int) -> bool:
        fn = getattr(DB, "asignar_producto_a_proveedor", None)
        return bool(fn(id_proveedor, id_producto)) if callable(fn) else False
    def quitar_producto_a_proveedor(self, id_proveedor: int, id_producto: int) -> bool:
        fn = getattr(DB, "quitar_producto_a_proveedor", None)
        return bool(fn(id_proveedor, id_producto)) if callable(fn) else False
    def insertar_compra(self, id_usuario: int, id_proveedor: int) -> int | None:
        fn = getattr(DB, "insertar_compra", None)
        return fn(id_usuario, id_proveedor) if callable(fn) else None
    def insertar_detalle_compra(self, id_compra: int, id_producto: int, cantidad: float, precio_costo: float) -> bool:
        fn = getattr(DB, "insertar_detalle_compra", None)
        return bool(fn(id_compra, id_producto, cantidad, precio_costo)) if callable(fn) else False
    
    # ... (Resto de las secciones (Historiales, CC, Usuarios, Reportes) sin cambios) ...
    # ---------- Historiales (Venta/Compra) ----------
    def obtener_ventas_maestro(
        self, 
        fecha_desde: Optional[str], 
        fecha_hasta: Optional[str], 
        id_cliente: Optional[int], 
        id_vendedor: Optional[int]
    ) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_ventas_maestro", None)
        return list(fn(fecha_desde, fecha_hasta, id_cliente, id_vendedor) or []) if callable(fn) else []
    def obtener_venta_detalle(self, id_venta: int) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_venta_detalle", None)
        return list(fn(id_venta) or []) if callable(fn) else []
    def obtener_compras_maestro(
        self, 
        fecha_desde: Optional[str], 
        fecha_hasta: Optional[str], 
        id_proveedor: Optional[int]
    ) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_compras_maestro", None)
        return list(fn(fecha_desde, fecha_hasta, id_proveedor) or []) if callable(fn) else []
    def obtener_compra_detalle(self, id_compra: int) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_compra_detalle", None)
        return list(fn(id_compra) or []) if callable(fn) else []
    # ---------- Cuenta Corriente ----------
    def obtener_clientes_con_deuda(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_clientes_con_deuda", None)
        return list(fn() or []) if callable(fn) else []
    def crear_cuenta_corriente_si_no_existe(self, id_cliente: int) -> bool:
        fn = getattr(DB, "crear_cuenta_corriente_si_no_existe", None)
        return bool(fn(id_cliente)) if callable(fn) else False
    def obtener_cuenta_por_cliente(self, id_cliente: int) -> dict | None:
        fn = getattr(DB, "obtener_cuenta_por_cliente", None)
        return fn(id_cliente) if callable(fn) else None
    def registrar_pago_cuenta_corriente(self, id_cuenta: int, monto: float, metodo: str, id_usuario: int) -> bool:
        fn = getattr(DB, "registrar_pago_cuenta_corriente", None)
        return bool(fn(id_cuenta, monto, metodo, id_usuario)) if callable(fn) else False
    # ---------- Gestión de Usuarios ----------
    def obtener_usuarios_con_rol(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_usuarios_con_rol", None)
        return list(fn() or []) if callable(fn) else []
    def obtener_roles(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_roles", None)
        return list(fn() or []) if callable(fn) else []
    def crear_usuario(self, nombre: str, password_plana: str, id_rol: int) -> int | None:
        fn = getattr(DB, "crear_usuario", None)
        return fn(nombre, password_plana, id_rol) if callable(fn) else None
    def actualizar_rol_usuario(self, id_usuario: int, id_rol_nuevo: int) -> bool:
        fn = getattr(DB, "actualizar_rol_usuario", None)
        return bool(fn(id_usuario, id_rol_nuevo)) if callable(fn) else False
    def resetear_password_usuario(self, id_usuario: int, password_plana_nueva: str) -> bool:
        fn = getattr(DB, "resetear_password_usuario", None)
        return bool(fn(id_usuario, password_plana_nueva)) if callable(fn) else False
    def desactivar_usuario(self, id_usuario: int) -> bool:
        fn = getattr(DB, "desactivar_usuario", None)
        return bool(fn(id_usuario)) if callable(fn) else False
    # ---------- Reportes ----------
    def obtener_vendedores(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_vendedores", None)
        return list(fn() or []) if callable(fn) else []
    def reporte_ventas_por_vendedor(self, desde: str, hasta: str, id_vendedor: int | None = None) -> list[dict[str, Any]]:
        fn = getattr(DB, "reporte_ventas_por_vendedor", None)
        return list(fn(desde, hasta, id_vendedor) or []) if callable(fn) else []
    def obtener_ventas_diarias(self, desde: str | None = None, hasta: str | None = None) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_ventas_diarias", None)
        return list(fn(desde, hasta) or []) if callable(fn) else []
