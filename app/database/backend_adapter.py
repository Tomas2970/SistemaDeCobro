# app/database/backend_adapter.py
from __future__ import annotations
from typing import Any, Optional
import logging
import json

try:
    from app.database import DB
except Exception as e:
    raise ImportError("No se pudo importar app.database.DB.") from e

logger = logging.getLogger(__name__)

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

    # ---------- Clientes (Firmas Actualizadas con CUIT) ----------
    def insertar_cliente(self, nombre: str, dni: str, cuit: str, direccion: str, telefono: str, email: str, limite_credito: float = 50000.00) -> int | None:
        try:
            limite_valido = float(limite_credito)
        except (ValueError, TypeError):
            limite_valido = 50000.00
        # Incluye CUIT
        return DB.insertar_cliente(nombre, dni, cuit, direccion, telefono, email, limite_valido)
    
    def crear_cliente(self, nombre: str, dni: str, cuit: str, direccion: str, telefono: str, email: str, limite_credito: float = 50000.00) -> int | None:
        """Alias usado por la interfaz de registro de clientes."""
        return self.insertar_cliente(nombre, dni, cuit, direccion, telefono, email, limite_credito)

    def actualizar_cliente(self, id_cliente: int, nombre: str, dni: str, cuit: str, direccion: str, telefono: str, email: str, limite_credito: float) -> bool:
        try:
            limite_valido = float(limite_credito)
        except (ValueError, TypeError):
            limite_valido = 0.00
        # Incluye CUIT
        return DB.actualizar_cliente_completo(id_cliente, nombre, dni, cuit, direccion, telefono, email, limite_valido)
        
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
    def activar_cliente_logico(self, id_cliente: int) -> bool:
        fn = getattr(DB, "activar_cliente_logico", None)
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
        tipo_pago: str,
        id_session: int | None = None  # 🔥 NUEVO PARÁMETRO
    ) -> int | None:
        try:
            # La lógica de auditoría de Venta ya está en el Trigger de Inventario,
            # pero podríamos agregar una auditoría de 'ACCIÓN' aquí si quisiéramos.
            return DB.registrar_venta_completa(id_usuario, id_cliente, items, tipo_pago, id_session)
        except Exception as e:
            logger.error(f"Error en registrar_venta_completa: {e}")
            raise 
    
    # ---------- Productos / Categorías ----------
    def crear_categoria(self, nombre: str, margen: float, es_pesable: bool = False) -> bool:
            fn = getattr(DB, "crear_categoria", None)
            return bool(fn(nombre, margen, es_pesable)) if callable(fn) else False

    def obtener_categoria_por_id(self, id_categoria: int) -> dict | None:
        fn = getattr(DB, "obtener_categoria_por_id", None)
        return fn(id_categoria) if callable(fn) else None

    def eliminar_categoria(self, id_categoria: int, id_usuario: int | None = None) -> bool:
        fn = getattr(DB, "eliminar_categoria", None)
        if not fn: return False
        
        # Obtener datos anteriores
        cat_anterior = self.obtener_categoria_por_id(id_categoria)
        
        # Eliminar (desactivar)
        resultado = fn(id_categoria)
        
        # Registrar auditoría
        if resultado and cat_anterior:
            self._registrar_auditoria(
                id_usuario=id_usuario,
                accion="DESACTIVAR_CATEGORIA",
                tabla_afectada="Categoria",
                id_registro=id_categoria,
                datos_anteriores={"nombre": cat_anterior.get("nombre"), "activa": True},
                datos_nuevos={"activa": False}
            )
        return resultado

    def reactivar_categoria(self, id_categoria: int, id_usuario: int | None = None) -> bool:
        fn = getattr(DB, "reactivar_categoria", None)
        if not fn: return False
        
        # Obtener datos anteriores
        cat_anterior = self.obtener_categoria_por_id(id_categoria)
        
        # Reactivar
        resultado = fn(id_categoria)
        
        # Registrar auditoría
        if resultado and cat_anterior:
            self._registrar_auditoria(
                id_usuario=id_usuario,
                accion="REACTIVAR_CATEGORIA",
                tabla_afectada="Categoria",
                id_registro=id_categoria,
                datos_anteriores={"nombre": cat_anterior.get("nombre"), "activa": False},
                datos_nuevos={"activa": True}
            )
        return resultado

    def actualizar_categoria(self, id_categoria: int, nombre: str, margen: float, es_pesable: bool) -> bool:
        fn = getattr(DB, "actualizar_categoria", None)
        return bool(fn(id_categoria, nombre, margen, es_pesable)) if callable(fn) else False

    def obtener_categorias(self, incluir_inactivas: bool = False) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_categorias", None)
        return list(fn(incluir_inactivas) or []) if callable(fn) else []
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
        # app/database/backend_adapter.py (Nueva función)

    def buscar_producto_inteligente(self, token: str) -> dict | None:
        """
        Búsqueda unificada por ID, Código o Nombre. 
        Usada por Venta, Inventario y Productos.
        """
        token = token.strip()
        if not token:
            return None


        if token.isdigit():
            try:
                if len(token) < 16: 
                    prod = self.buscar_producto_por_id(int(token))
                    if prod:
                        return prod
            except Exception:
                pass
        
        prod = self.buscar_producto_por_codigo_barras(token)
        if prod:
            return prod
            
        res = self.buscar_producto_por_nombre(token) or []
        return res[0] if res else None

        
    def crear_producto_completo(
        self,
        nombre: str,
        categoria_id: Optional[int],
        codigo_barras: Optional[str],
        precio: float,
        stock_inicial: int,
        stock_minimo: int = 10,
        es_pesable: bool = False,
        id_usuario: int | None = None
    ) -> int | None:
        # VALIDACIONES DE SEGURIDAD Y NEGOCIO
        if precio < 0:
            raise ValueError("El precio no puede ser negativo.")
            
        if id_usuario is not None:
            usuarios = DB.obtener_usuarios_con_rol()
            user = next((u for u in usuarios if u.get('id_usuario') == id_usuario), None)
            if user and user.get('rol_nombre') == 'vendedor':
                raise PermissionError("Acceso denegado: Los vendedores no tienen permisos para crear productos.")

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
        id_usuario: int | None = None
    ) -> bool:
        # VALIDACIONES DE SEGURIDAD Y NEGOCIO
        if precio is not None and precio < 0:
            raise ValueError("El precio no puede ser negativo.")
            
        if id_usuario is not None:
            usuarios = DB.obtener_usuarios_con_rol()
            user = next((u for u in usuarios if u.get('id_usuario') == id_usuario), None)
            if user and user.get('rol_nombre') == 'vendedor':
                raise PermissionError("Acceso denegado: Los vendedores no tienen permisos para modificar productos.")
                
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

    def actualizar_precio_producto(self, id_producto: int, nuevo_precio: float, id_usuario: int | None = None) -> bool:
        """Actualiza solo el precio de venta (usado desde Compras)."""
        return self.actualizar_producto(id_producto, precio=nuevo_precio, id_usuario=id_usuario)


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

    def registrar_pago_proveedor(self, id_proveedor: int, monto: float, medio: str, id_usuario: int, obs: str) -> bool:
        fn = getattr(DB, "registrar_pago_proveedor", None)
        if callable(fn):
            return fn(id_proveedor, monto, medio, id_usuario, obs)
        return False

    def obtener_proveedores(self, incluir_inactivos: bool = False) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_proveedores", None)
        return list(fn(incluir_inactivos) or []) if callable(fn) else []

    # EN app/database/backend_adapter.py (Línea ~312)
    def insertar_proveedor(self, nombre: str, empresa: str, cuit_empresa: str, dni_vendedor: str, telefono: str, email: str, direccion: str) -> int | None:
        fn = getattr(DB, "insertar_proveedor", None)
        if not callable(fn):
            return None
        return fn(
            nombre=nombre,
            empresa=empresa,
            cuit_empresa=cuit_empresa, # ¡Asegúrate de que este cuit sea el nuevo nombre!
            dni_vendedor=dni_vendedor, # ¡Asegúrate de que este dni sea el nuevo nombre!
            telefono=telefono,
            email=email,
            direccion=direccion
        )

    # EN app/database/backend_adapter.py (Línea ~324)
    def actualizar_proveedor(self, id_proveedor: int, nombre: str, empresa: str, cuit_empresa: str, dni_vendedor: str, telefono: str, email: str, direccion: str) -> bool:
        fn = getattr(DB, "actualizar_proveedor", None)
        if not callable(fn):
            return False
        return bool(fn(
            id_proveedor=id_proveedor,
            nombre=nombre,
            empresa=empresa,
            cuit_empresa=cuit_empresa, # ¡Asegúrate de que este cuit sea el nuevo nombre!
            dni_vendedor=dni_vendedor, # ¡Asegúrate de que este dni sea el nuevo nombre!
            telefono=telefono,
            email=email,
            direccion=direccion
        ))

    def obtener_proveedor_completo(self, id_proveedor: int) -> dict | None:
        fn = getattr(DB, "obtener_proveedor_completo", None)
        return fn(id_proveedor) if callable(fn) else None

    def obtener_proveedor_para_editar(self, id_proveedor: int) -> dict | None:
        fn = getattr(DB, "obtener_proveedor_completo", None)
        return fn(id_proveedor) if callable(fn) else None

    def eliminar_proveedor_logico(self, id_proveedor: int) -> bool:
        fn = getattr(DB, "eliminar_proveedor_logico", None)
        return bool(fn(id_proveedor)) if callable(fn) else False

    def activar_proveedor_logico(self, id_proveedor: int) -> bool:
        fn = getattr(DB, "activar_proveedor_logico", None)
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

    def insertar_compra(self, id_usuario: int, id_proveedor: int, items: list[dict] | None = None, medio_pago: str = 'efectivo') -> int | None:
            """
            Inserta compra permitiendo seleccionar medio de pago.
            """
            fn = getattr(DB, "insertar_compra", None)
            if not callable(fn):
                return None

            try:
                # Llamamos a la nueva firma de DB.insertar_compra
                if items is not None:
                    return fn(id_usuario, id_proveedor, items, medio_pago)
                else:
                    return fn(id_usuario, id_proveedor)
            except TypeError:
                # Fallback por si DB no se actualizó
                if items is not None:
                    return fn(id_usuario, id_proveedor, items)
                return fn(id_usuario, id_proveedor)
        
    def insertar_detalle_compra(self, id_compra: int, id_producto: int, cantidad: float, precio_costo: float) -> bool:
        fn = getattr(DB, "insertar_detalle_compra", None)
        return bool(fn(id_compra, id_producto, cantidad, precio_costo)) if callable(fn) else False
    
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
    
    # ---------- Historial de Pagos ----------
    def obtener_pagos_maestro(
        self,
        fecha_desde: Optional[str],
        fecha_hasta: Optional[str],
        id_cliente: Optional[int],
        id_usuario: Optional[int]
    ) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_pagos_maestro", None)
        return list(fn(fecha_desde, fecha_hasta, id_cliente, id_usuario) or []) if callable(fn) else []
    
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
# EN app/database/backend_adapter.py (Línea ~432)

    def actualizar_rol_usuario(self, id_usuario: int, id_rol_nuevo: int, nuevo_nombre: Optional[str] = None) -> bool:
        
        # 1. Obtener datos anteriores para comparar y auditar si es necesario
        usuarios = DB.obtener_usuarios_con_rol()
        usuario_anterior = next((u for u in usuarios if u.get('id_usuario') == id_usuario), None)

        if not usuario_anterior:
            logger.error(f"Intento de actualizar usuario {id_usuario} que no existe.")
            return False

        rol_anterior = usuario_anterior.get('id_rol')
        nombre_anterior = usuario_anterior.get('nombre')
        
        # Bandera de éxito combinada
        exito_rol = True
        exito_nombre = True

        # 2. Actualizar Rol si es diferente
        if id_rol_nuevo != rol_anterior:
            fn_rol = getattr(DB, "actualizar_rol_usuario", None)
            if callable(fn_rol):
                exito_rol = fn_rol(id_usuario, id_rol_nuevo)
            else:
                exito_rol = False # Fallo si la función no existe

        # 3. Actualizar Nombre si se provee y es diferente
        if nuevo_nombre is not None and nuevo_nombre != nombre_anterior:
            fn_nombre = getattr(DB, "actualizar_nombre_usuario", None)
            if callable(fn_nombre):
                try:
                    exito_nombre = fn_nombre(id_usuario, nuevo_nombre)
                except ValueError as ve: # Captura el NOMBRE_DUPLICADO propagado desde DB.py
                    logger.warning(f"Fallo de integridad al actualizar nombre: {ve}")
                    raise # Re-lanzar para que el frontend lo capture
            else:
                exito_nombre = False
        
        # 4. Auditoría (Opcional, si ambos fueron exitosos)
        if exito_rol and exito_nombre:
            # Recargar datos nuevos para auditoría
            usuario_nuevo = next((u for u in DB.obtener_usuarios_con_rol() if u.get('id_usuario') == id_usuario), {})
            
            datos_anteriores = {'nombre': nombre_anterior, 'id_rol': rol_anterior}
            datos_nuevos = {}
            if nuevo_nombre is not None and nuevo_nombre != nombre_anterior:
                datos_nuevos['nombre'] = nuevo_nombre
            if id_rol_nuevo != rol_anterior:
                datos_nuevos['id_rol'] = id_rol_nuevo

            if datos_nuevos: # Solo auditar si hubo cambios reales
                self._registrar_auditoria(
                    id_usuario=id_usuario,
                    accion="MODIFICAR_USUARIO",
                    tabla_afectada="Usuario",
                    id_registro=id_usuario,
                    datos_anteriores=datos_anteriores,
                    datos_nuevos=datos_nuevos
                )
        
        return exito_rol and exito_nombre

    def resetear_password_usuario(self, id_usuario: int, password_plana_nueva: str) -> bool:
        fn = getattr(DB, "resetear_password_usuario", None)
        return bool(fn(id_usuario, password_plana_nueva)) if callable(fn) else False
    def desactivar_usuario(self, id_usuario: int) -> bool:
        fn = getattr(DB, "desactivar_usuario", None)
        return bool(fn(id_usuario)) if callable(fn) else False
    def activar_usuario(self, id_usuario: int) -> bool:
        fn = getattr(DB, "activar_usuario", None)
        return bool(fn(id_usuario)) if callable(fn) else False
        
    def actualizar_nombre_usuario(self, id_usuario: int, nuevo_nombre: str) -> bool:
        fn = getattr(DB, "actualizar_nombre_usuario", None)
        return bool(fn(id_usuario, nuevo_nombre)) if callable(fn) else False
    
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

# ---------- CAJA (SISTEMA INDIVIDUAL POR USUARIO) ----------
    
    def obtener_session_abierta(self, id_usuario: int) -> dict | None:
        """
        Obtiene la sesión de caja abierta DEL USUARIO ESPECÍFICO.
        Sistema individual: cada usuario tiene su propia caja.
        """
        fn = getattr(DB, "obtener_session_abierta", None)
        if not callable(fn): return None
        
        # Pasar el id_usuario para obtener SU caja
        return fn(id_usuario)
    
    def obtener_session_activa(self) -> dict | None:
        """
        Obtiene cualquier sesión de caja activa (sin filtrar por usuario).
        Usado por el frontend para obtener id_session al registrar ventas.
        """
        fn = getattr(DB, "obtener_session_activa", None)
        if callable(fn):
            return fn()
        # Fallback: obtener la primera sesión abierta
        fn_alt = getattr(DB, "obtener_session_abierta", None)
        if callable(fn_alt):
            return fn_alt(None)  # Sin filtro de usuario
        return None
    
    def abrir_caja_session(self, id_usuario: int, monto_inicial: float) -> bool:
        fn = getattr(DB, "abrir_caja_session", None)
        if not callable(fn): return False
        try:
            return bool(fn(id_usuario, monto_inicial))
        except ValueError as e:
            # Re-lanzar errores de validación (ej: "Usuario ya tiene caja abierta")
            raise
    
    def registrar_movimiento_manual(self, id_session: int, tipo: str, monto: float, motivo: str, descripcion: str, id_usuario: int) -> bool:
        fn = getattr(DB, "registrar_movimiento_manual", None)
        return bool(fn(id_session, tipo, monto, motivo, descripcion, id_usuario)) if callable(fn) else False
    
    def obtener_resumen_cierre(self, id_session: int) -> dict:
        fn = getattr(DB, "obtener_resumen_cierre", None)
        return fn(id_session) if callable(fn) else {}
    
    def cerrar_caja_session(self, id_session: int, id_usuario_cierre: int, efectivo_esperado: float, efectivo_contado: float, diferencia: float, obs: str) -> bool:
        fn = getattr(DB, "cerrar_caja_session", None)
        return bool(fn(id_session, id_usuario_cierre, efectivo_esperado, efectivo_contado, diferencia, obs)) if callable(fn) else False
    
    # --- REPORTES DE CAJA ---
    def obtener_resumen_diario(self, fecha: str | None = None) -> dict:
        """
        Obtiene resumen de ventas del día por categoría y método de pago.
        Si fecha es None, usa hoy.
        """
        fn = getattr(DB, "obtener_resumen_diario", None)
        return fn(fecha) if callable(fn) else {}
    
    def obtener_historial_movimientos_caja(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        tipo: str | None = None,
        motivo: str | None = None,
        id_usuario: int | None = None
    ) -> list[dict]:
        """
        Obtiene historial de movimientos de caja con filtros.
        """
        fn = getattr(DB, "obtener_historial_movimientos_caja", None)
        return list(fn(fecha_desde, fecha_hasta, tipo, motivo, id_usuario) or []) if callable(fn) else []