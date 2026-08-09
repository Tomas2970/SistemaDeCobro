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
    def verificar_contraseña(self, usuario: str, contraseña: str, ignorar_sesion: bool = False) -> dict | None:
        return DB.verificar_contraseña(usuario, contraseña, ignorar_sesion=ignorar_sesion)

    def buscar_usuario_por_codigo(self, codigo_barras: str) -> dict | None:
        fn = getattr(DB, "buscar_usuario_por_codigo", None)
        return fn(codigo_barras) if callable(fn) else None

    def cerrar_sesion_usuario(self, id_usuario: int) -> bool:
        return DB.cerrar_sesion_usuario(id_usuario)

    def forzar_cierre_sesion(self, id_usuario: int) -> bool:
        return DB.forzar_cierre_sesion(id_usuario)

    def obtener_usuario_por_id(self, id_usuario: int) -> dict | None:
        fn = getattr(DB, "obtener_usuario_por_id", None)
        return fn(id_usuario) if callable(fn) else None

    # ---------- Clientes (Firmas Actualizadas con CUIT) ----------
    def crear_cliente(self, nombre: str, dni: str, cuit: str, direccion: str, telefono: str, email: str, limite_credito: float = 50000.00, id_usuario_admin: int | None = None) -> int | None:
        try:
            limite_valido = float(limite_credito)
        except (ValueError, TypeError):
            limite_valido = 50000.00
        # Incluye CUIT
        nuevo_id = DB.crear_cliente(nombre, dni, cuit, direccion, telefono, email, limite_valido)
        if nuevo_id:
            self._registrar_auditoria(
                id_usuario=id_usuario_admin,
                accion="CREAR_CLIENTE",
                tabla_afectada="Cliente",
                id_registro=nuevo_id,
                datos_nuevos={"nombre": nombre, "limite_credito": limite_valido}
            )
        return nuevo_id
    
    def insertar_cliente(self, nombre: str, dni: str, cuit: str, direccion: str, telefono: str, email: str, limite_credito: float = 50000.00, id_usuario_admin: int | None = None) -> int | None:
        """DEPRECATED: Alias de compatibilidad de interfaz → delega a crear_cliente()."""
        return self.crear_cliente(nombre, dni, cuit, direccion, telefono, email, limite_credito, id_usuario_admin=id_usuario_admin)

    def actualizar_cliente(self, id_cliente: int, nombre: str, dni: str, cuit: str, direccion: str, telefono: str, email: str, limite_credito: float, id_usuario_admin: int | None = None) -> bool:
        try:
            limite_valido = float(limite_credito)
        except (ValueError, TypeError):
            limite_valido = 0.00
            
        cliente_anterior = self.obtener_cliente_para_editar(id_cliente)
        
        # Incluye CUIT
        resultado = DB.actualizar_cliente_completo(id_cliente, nombre, dni, cuit, direccion, telefono, email, limite_valido)
        if resultado and cliente_anterior:
            limite_anterior = cliente_anterior.get("limite_credito", 0.0)
            if float(limite_anterior) != limite_valido:
                self._registrar_auditoria(
                    id_usuario=id_usuario_admin,
                    accion="MODIFICAR_LIMITE_CREDITO_CLIENTE",
                    tabla_afectada="Cliente",
                    id_registro=id_cliente,
                    datos_anteriores={"limite_credito": float(limite_anterior)},
                    datos_nuevos={"limite_credito": limite_valido}
                )
        return resultado
        
    def obtener_clientes(self, incluir_inactivos: bool = False) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_clientes", None)
        return list(fn(incluir_inactivos) or []) if callable(fn) else []

    def listar_clientes(self, incluir_inactivos: bool = False) -> list[dict[str, Any]]:
        """DEPRECATED: Usar obtener_clientes()."""
        return self.obtener_clientes(incluir_inactivos)

    def obtener_clientes_con_saldos(self, incluir_inactivos: bool = False) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_clientes_con_saldos", None)
        return list(fn(incluir_inactivos) or []) if callable(fn) else []

    def listar_clientes_con_saldos(self, incluir_inactivos: bool = False) -> list[dict[str, Any]]:
        """DEPRECATED: Usar obtener_clientes_con_saldos()."""
        return self.obtener_clientes_con_saldos(incluir_inactivos)

    def obtener_cliente_completo(self, id_cliente: int) -> dict | None:
        fn = getattr(DB, "obtener_cliente_completo", None)
        return fn(id_cliente) if callable(fn) else None

    def obtener_cliente_para_editar(self, id_cliente: int) -> dict | None:
        """DEPRECATED: Usar obtener_cliente_completo()."""
        return self.obtener_cliente_completo(id_cliente)

    def buscar_cliente_por_nombre(self, patron: str) -> list[dict[str, Any]]:
        fn = getattr(DB, "buscar_cliente_por_nombre", None)
        return list(fn(patron) or []) if callable(fn) else []

    def buscar_cliente_por_dni(self, dni: str) -> dict | None:
        fn = getattr(DB, "buscar_cliente_por_dni", None)
        return fn(dni) if callable(fn) else None

    def eliminar_cliente_logico(self, id_cliente: int, id_usuario_admin: int | None = None) -> bool:
        fn = getattr(DB, "eliminar_cliente_logico", None)
        resultado = bool(fn(id_cliente)) if callable(fn) else False
        if resultado:
            self._registrar_auditoria(
                id_usuario=id_usuario_admin,
                accion="DESACTIVAR_CLIENTE",
                tabla_afectada="Cliente",
                id_registro=id_cliente,
                datos_anteriores={"activo": True},
                datos_nuevos={"activo": False}
            )
        return resultado
        
    def activar_cliente_logico(self, id_cliente: int, id_usuario_admin: int | None = None) -> bool:
        fn = getattr(DB, "activar_cliente_logico", None)
        resultado = bool(fn(id_cliente)) if callable(fn) else False
        if resultado:
            self._registrar_auditoria(
                id_usuario=id_usuario_admin,
                accion="REACTIVAR_CLIENTE",
                tabla_afectada="Cliente",
                id_registro=id_cliente,
                datos_anteriores={"activo": False},
                datos_nuevos={"activo": True}
            )
        return resultado

    # ---------- Ventas ----------

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
    def obtener_productos(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_productos", None)
        return list(fn() or []) if callable(fn) else []

    def obtener_productos_full(self) -> list[dict[str, Any]]:
        """DEPRECATED: Alias de conveniencia. Usar obtener_productos()."""
        return self.obtener_productos()
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
        
    def actualizar_inventario_absoluto(
        self,
        id_producto: int,
        stock_abs: float,
        stock_minimo: Optional[int],
        id_usuario: int | None = None,
        motivo: str = ""
    ) -> bool:
        """Establece el stock de un producto a un valor absoluto.

        Args:
            id_producto: ID del producto a actualizar.
            stock_abs: Nuevo valor de stock (valor absoluto, no delta).
            stock_minimo: Nuevo stock mínimo. Si es None, no se modifica.
            id_usuario: ID del usuario que realiza el ajuste (para auditoría).
            motivo: Razón del ajuste (obligatorio desde el módulo de ajuste manual;
                    puede quedar vacío cuando se llama desde el ABM de productos).
        """
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
            if motivo:
                datos_nuevos["motivo"] = motivo

            self._registrar_auditoria(
                id_usuario=id_usuario,
                accion="AJUSTE_STOCK_MANUAL",
                tabla_afectada="Inventario",
                id_registro=id_producto,
                datos_anteriores=datos_viejos,
                datos_nuevos=datos_nuevos
            )

            # 4. Insertar fila en AuditoriaInventario (cierra el hueco de trazabilidad)
            try:
                fn_inv = getattr(DB, "registrar_auditoria_inventario", None)
                if callable(fn_inv):
                    fn_inv(
                        id_producto=id_producto,
                        cantidad_anterior=stock_anterior,
                        cantidad_nueva=float(stock_abs),
                        tipo_movimiento="ajuste_manual",
                        id_referencia=None,
                        id_usuario=id_usuario,
                        observaciones=motivo or None
                    )
            except Exception as e:
                logger.warning(f"No se pudo insertar en AuditoriaInventario: {e}")

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

    def registrar_pago_proveedor(self, id_proveedor: int, monto: float, medio: str, id_usuario: int, obs: str,
                                   usuario_actual: dict | None = None) -> bool:
        from app.database.permisos import tiene_permiso
        if usuario_actual and not tiene_permiso(usuario_actual, 'registrar_pagos_proveedores'):
            raise PermissionError("Sin permiso: registrar_pagos_proveedores")
        fn = getattr(DB, "registrar_pago_proveedor", None)
        if callable(fn):
            return fn(id_proveedor, monto, medio, id_usuario, obs)
        return False

    def obtener_proveedores(self, incluir_inactivos: bool = False) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_proveedores", None)
        return list(fn(incluir_inactivos) or []) if callable(fn) else []

    def crear_proveedor(self, nombre: str, empresa: str, cuit_empresa: str, dni_vendedor: str, telefono: str,
                            email: str, direccion: str,
                            id_usuario_admin: int | None = None,
                            usuario_actual: dict | None = None) -> int | None:
        from app.database.permisos import tiene_permiso
        if usuario_actual and not tiene_permiso(usuario_actual, 'crear_proveedores'):
            raise PermissionError("Sin permiso: crear_proveedores")
        fn = getattr(DB, "crear_proveedor", None)
        if not callable(fn):
            return None
        nuevo_id = fn(
            nombre=nombre,
            empresa=empresa,
            cuit_empresa=cuit_empresa,
            dni_vendedor=dni_vendedor,
            telefono=telefono,
            email=email,
            direccion=direccion
        )
        if nuevo_id:
            self._registrar_auditoria(
                id_usuario=id_usuario_admin,
                accion="CREAR_PROVEEDOR",
                tabla_afectada="Proveedor",
                id_registro=nuevo_id,
                datos_nuevos={"empresa": empresa, "cuit_empresa": cuit_empresa}
            )
        return nuevo_id

    def insertar_proveedor(self, nombre: str, empresa: str, cuit_empresa: str, dni_vendedor: str, telefono: str,
                            email: str, direccion: str,
                            id_usuario_admin: int | None = None,
                            usuario_actual: dict | None = None) -> int | None:
        """DEPRECATED: Usar crear_proveedor()."""
        return self.crear_proveedor(nombre, empresa, cuit_empresa, dni_vendedor, telefono, email, direccion, id_usuario_admin, usuario_actual)

    def actualizar_proveedor(self, id_proveedor: int, nombre: str, empresa: str, cuit_empresa: str,
                              dni_vendedor: str, telefono: str, email: str, direccion: str,
                              id_usuario_admin: int | None = None,
                              usuario_actual: dict | None = None) -> bool:
        from app.database.permisos import tiene_permiso
        if usuario_actual and not tiene_permiso(usuario_actual, 'editar_proveedores'):
            raise PermissionError("Sin permiso: editar_proveedores")
        fn = getattr(DB, "actualizar_proveedor", None)
        if not callable(fn):
            return False
        resultado = bool(fn(
            id_proveedor=id_proveedor,
            nombre=nombre,
            empresa=empresa,
            cuit_empresa=cuit_empresa,
            dni_vendedor=dni_vendedor,
            telefono=telefono,
            email=email,
            direccion=direccion
        ))
        if resultado:
            self._registrar_auditoria(
                id_usuario=id_usuario_admin,
                accion="EDITAR_PROVEEDOR",
                tabla_afectada="Proveedor",
                id_registro=id_proveedor,
                datos_nuevos={"empresa": empresa, "cuit_empresa": cuit_empresa}
            )
        return resultado

    def obtener_proveedor_completo(self, id_proveedor: int) -> dict | None:
        fn = getattr(DB, "obtener_proveedor_completo", None)
        return fn(id_proveedor) if callable(fn) else None

    def obtener_proveedor_para_editar(self, id_proveedor: int) -> dict | None:
        """DEPRECATED: Alias de compatibilidad → delega a obtener_proveedor_completo()."""
        return self.obtener_proveedor_completo(id_proveedor)

    def eliminar_proveedor_logico(self, id_proveedor: int, id_usuario_admin: int | None = None) -> bool:
        fn = getattr(DB, "eliminar_proveedor_logico", None)
        resultado = bool(fn(id_proveedor)) if callable(fn) else False
        if resultado:
            self._registrar_auditoria(
                id_usuario=id_usuario_admin,
                accion="DESACTIVAR_PROVEEDOR",
                tabla_afectada="Proveedor",
                id_registro=id_proveedor,
                datos_anteriores={"activo": True},
                datos_nuevos={"activo": False}
            )
        return resultado

    def activar_proveedor_logico(self, id_proveedor: int, id_usuario_admin: int | None = None) -> bool:
        fn = getattr(DB, "activar_proveedor_logico", None)
        resultado = bool(fn(id_proveedor)) if callable(fn) else False
        if resultado:
            self._registrar_auditoria(
                id_usuario=id_usuario_admin,
                accion="REACTIVAR_PROVEEDOR",
                tabla_afectada="Proveedor",
                id_registro=id_proveedor,
                datos_anteriores={"activo": False},
                datos_nuevos={"activo": True}
            )
        return resultado

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

    def registrar_compra(self, id_usuario: int, id_proveedor: int, items: list[dict] | None = None,
                         medio_pago: str = 'efectivo',
                         usuario_actual: dict | None = None) -> int | None:
        """
        Registra compra permitiendo seleccionar medio de pago.
        """
        from app.database.permisos import tiene_permiso
        if usuario_actual and not tiene_permiso(usuario_actual, 'registrar_compras'):
            raise PermissionError("Sin permiso: registrar_compras")
        fn = getattr(DB, "registrar_compra", None)
        if not callable(fn):
            return None

        try:
            # Llamamos a la nueva firma de DB.registrar_compra
            if items is not None:
                return fn(id_usuario, id_proveedor, items, medio_pago)
            else:
                return fn(id_usuario, id_proveedor)
        except TypeError as te:
            # Fallback solo si es un error de firma de función
            if "positional" in str(te) or "keyword" in str(te) or "argument" in str(te):
                if items is not None:
                    return fn(id_usuario, id_proveedor, items)
                return fn(id_usuario, id_proveedor)
            raise

    def insertar_compra(self, id_usuario: int, id_proveedor: int, items: list[dict] | None = None,
                         medio_pago: str = 'efectivo',
                         usuario_actual: dict | None = None) -> int | None:
        """DEPRECATED: Usar registrar_compra()."""
        return self.registrar_compra(id_usuario, id_proveedor, items, medio_pago, usuario_actual)

    def registrar_compra_mixta(self, id_usuario: int, id_proveedor: int, items: list[dict], medio_real: str, monto_efectivo: float = 0.0, usuario_actual: dict | None = None) -> dict:
        """
        Registra compra según el medio real:
        - efectivo: genera deuda (cuenta_corriente) e intenta saldarla.
        - tarjeta/transferencia: registra pago instantáneo no-efectivo sin deuda.
        - cuenta_corriente: registra deuda pura sin pago.
        """
        total_compra = sum(float(item['cant']) * float(item['costo']) for item in items)
        
        if medio_real in ['tarjeta', 'transferencia', 'cheque']:
            # Pago instantáneo no-efectivo, NO es deuda.
            id_compra = self.registrar_compra(id_usuario, id_proveedor, items, medio_pago=medio_real, usuario_actual=usuario_actual)
            return {"id_compra": id_compra, "pago_exitoso": True, "mensaje_error_pago": None}
            
        elif medio_real == 'cuenta_corriente':
            # Deuda pura, sin pago inicial
            id_compra = self.registrar_compra(id_usuario, id_proveedor, items, medio_pago='cuenta_corriente', usuario_actual=usuario_actual)
            return {"id_compra": id_compra, "pago_exitoso": True, "mensaje_error_pago": None}
            
        elif medio_real == 'efectivo':
            # Si no envían monto parcial, se asume pago total
            if monto_efectivo <= 0:
                monto_efectivo = total_compra
            elif monto_efectivo > total_compra:
                raise ValueError("El monto en efectivo no puede superar el total de la compra.")
                
            # 1. Registrar deuda para dejar la traza
            id_compra = self.registrar_compra(id_usuario, id_proveedor, items, medio_pago='cuenta_corriente', usuario_actual=usuario_actual)
            
            pago_exitoso = False
            mensaje_error_pago = None
            
            # 2. Intentar pagar con efectivo
            try:
                self.registrar_pago_proveedor(id_proveedor, monto_efectivo, 'efectivo', id_usuario, obs=f"Pago por compra #{id_compra}", usuario_actual=usuario_actual)
                pago_exitoso = True
            except ValueError as ve:
                mensaje_error_pago = str(ve)
            except Exception as e:
                mensaje_error_pago = str(e)
                
            return {
                "id_compra": id_compra,
                "pago_exitoso": pago_exitoso,
                "mensaje_error_pago": mensaje_error_pago
            }
        else:
            raise ValueError(f"Medio de pago no soportado: {medio_real}")


    # ---------- Historiales (Venta/Compra) ----------
    def contar_ventas_maestro(
        self, 
        fecha_desde: Optional[str], 
        fecha_hasta: Optional[str], 
        id_cliente: Optional[int], 
        id_vendedor: Optional[int]
    ) -> int:
        fn = getattr(DB, "contar_ventas_maestro", None)
        return int(fn(fecha_desde, fecha_hasta, id_cliente, id_vendedor)) if callable(fn) else 0

    def obtener_ventas_maestro(
        self, 
        fecha_desde: Optional[str], 
        fecha_hasta: Optional[str], 
        id_cliente: Optional[int], 
        id_vendedor: Optional[int],
        limit: Optional[int] = None,
        offset: Optional[int] = 0
    ) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_ventas_maestro", None)
        return list(fn(fecha_desde, fecha_hasta, id_cliente, id_vendedor, limit, offset) or []) if callable(fn) else []
    def obtener_venta_detalle(self, id_venta: int) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_venta_detalle", None)
        return list(fn(id_venta) or []) if callable(fn) else []

    def anular_venta(self, id_venta: int, id_usuario: int, motivo: str | None = None) -> bool:
        """
        Anula una venta de forma atómica: cambia el estado a 'cancelada',
        restituye stock y revierte la cuenta corriente si corresponde.

        Raises:
            ValueError: Si la venta ya está anulada o no está completada.
            Exception: Error de base de datos.
            PermissionError: Si un vendedor intenta anular una venta.
        """
        from app.database import DB
        usuarios = DB.obtener_usuarios_con_rol()
        user = next((u for u in usuarios if u.get('id_usuario') == id_usuario), None)
        if user and user.get('rol_nombre') == 'vendedor':
            raise PermissionError("No tienes permisos para anular ventas.")

        fn = getattr(DB, "anular_venta", None)
        if not callable(fn):
            raise RuntimeError("DB.anular_venta no está implementado.")
        return bool(fn(id_venta, id_usuario, motivo))

    def anular_compra(self, id_compra: int, id_usuario: int, motivo: str | None = None) -> bool:
        """
        Anula una compra de forma atómica: cambia el estado a 'cancelada',
        restituye stock y revierte el pago/cuenta corriente si corresponde.

        Raises:
            ValueError: Si la compra ya está anulada o no hay caja.
            Exception: Error de base de datos.
            PermissionError: Si un vendedor intenta anular una compra.
        """
        from app.database import DB
        usuarios = DB.obtener_usuarios_con_rol()
        user = next((u for u in usuarios if u.get('id_usuario') == id_usuario), None)
        if user and user.get('rol_nombre') == 'vendedor':
            raise PermissionError("No tienes permisos para anular compras.")

        fn = getattr(DB, "anular_compra", None)
        if not callable(fn):
            raise RuntimeError("DB.anular_compra no está implementado.")
        return bool(fn(id_compra, id_usuario, motivo))

    def contar_compras_maestro(
        self, 
        fecha_desde: Optional[str], 
        fecha_hasta: Optional[str], 
        id_proveedor: Optional[int]
    ) -> int:
        fn = getattr(DB, "contar_compras_maestro", None)
        return int(fn(fecha_desde, fecha_hasta, id_proveedor)) if callable(fn) else 0

    def obtener_compras_maestro(
        self, 
        fecha_desde: Optional[str], 
        fecha_hasta: Optional[str], 
        id_proveedor: Optional[int],
        limit: Optional[int] = None,
        offset: Optional[int] = 0
    ) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_compras_maestro", None)
        return list(fn(fecha_desde, fecha_hasta, id_proveedor, limit, offset) or []) if callable(fn) else []

    def obtener_compra_detalle(self, id_compra: int) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_compra_detalle", None)
        return list(fn(id_compra) or []) if callable(fn) else []

    
    # ---------- Historial de Pagos ----------
    def contar_pagos_maestro(
        self,
        fecha_desde: Optional[str],
        fecha_hasta: Optional[str],
        id_cliente: Optional[int],
        id_usuario: Optional[int]
    ) -> int:
        fn = getattr(DB, "contar_pagos_maestro", None)
        return int(fn(fecha_desde, fecha_hasta, id_cliente, id_usuario)) if callable(fn) else 0

    def obtener_pagos_maestro(
        self,
        fecha_desde: Optional[str],
        fecha_hasta: Optional[str],
        id_cliente: Optional[int],
        id_usuario: Optional[int],
        limit: Optional[int] = None,
        offset: Optional[int] = 0
    ) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_pagos_maestro", None)
        return list(fn(fecha_desde, fecha_hasta, id_cliente, id_usuario, limit, offset) or []) if callable(fn) else []
    
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
    def crear_usuario(self, nombre: str, password_plana: str, id_rol: int, codigo_barras: Optional[str] = None, id_usuario_admin: int | None = None) -> int | None:
        fn = getattr(DB, "crear_usuario", None)
        nuevo_id = fn(nombre, password_plana, id_rol, codigo_barras=codigo_barras) if callable(fn) else None
        if nuevo_id:
            self._registrar_auditoria(
                id_usuario=id_usuario_admin,
                accion="CREAR_USUARIO",
                tabla_afectada="Usuario",
                id_registro=nuevo_id,
                datos_nuevos={"nombre": nombre, "id_rol": id_rol, "codigo_barras": codigo_barras}
            )
        return nuevo_id
# EN app/database/backend_adapter.py (Línea ~432)

    def actualizar_rol_usuario(self, id_usuario: int, id_rol_nuevo: int, nuevo_nombre: Optional[str] = None, codigo_barras: Optional[str] = None) -> bool:
        
        # 1. Obtener datos anteriores para comparar y auditar si es necesario
        usuarios = DB.obtener_usuarios_con_rol()
        usuario_anterior = next((u for u in usuarios if u.get('id_usuario') == id_usuario), None)

        if not usuario_anterior:
            logger.error(f"Intento de actualizar usuario {id_usuario} que no existe.")
            return False

        rol_anterior = usuario_anterior.get('id_rol')
        nombre_anterior = usuario_anterior.get('nombre')
        codigo_barras_anterior = usuario_anterior.get('codigo_barras')
        
        # Bandera de éxito combinada
        exito_rol = True
        exito_nombre = True

        # 2. Actualizar Rol si es diferente (o si hay codigo de barras)
        if id_rol_nuevo != rol_anterior or codigo_barras != codigo_barras_anterior:
            fn_rol = getattr(DB, "actualizar_rol_usuario", None)
            if callable(fn_rol):
                # La función en DB.py acepta nuevo_nombre y codigo_barras. 
                # Solo le pasamos codigo_barras aquí, ya que el nombre se maneja abajo.
                exito_rol = fn_rol(id_usuario, id_rol_nuevo, codigo_barras=codigo_barras)
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
            
            datos_anteriores = {'nombre': nombre_anterior, 'id_rol': rol_anterior, 'codigo_barras': codigo_barras_anterior}
            datos_nuevos = {}
            if nuevo_nombre is not None and nuevo_nombre != nombre_anterior:
                datos_nuevos['nombre'] = nuevo_nombre
            if id_rol_nuevo != rol_anterior:
                datos_nuevos['id_rol'] = id_rol_nuevo
            if codigo_barras != codigo_barras_anterior:
                datos_nuevos['codigo_barras'] = codigo_barras

            if datos_nuevos: # Solo auditar si hubo cambios reales
                self._registrar_auditoria(
                    id_usuario=id_usuario,
                    accion="MODIFICAR_USUARIO",
                    tabla_afectada="Usuario",
                    id_registro=id_usuario,
                    datos_anteriores=datos_anteriores,
                    datos_nuevos=datos_nuevos
                )

            # Si el rol cambió, enviar un broadcast para forzar el cierre de sesión remotamente
            if id_rol_nuevo != rol_anterior:
                try:
                    self.enviar_mensaje_broadcast("SYS:FORCE_LOGOUT", 1, "usuario", id_usuario)
                except Exception as e:
                    logger.error(f"Error enviando broadcast de cierre de sesión: {e}")
        
        return exito_rol and exito_nombre

    def resetear_password_usuario(self, id_usuario: int, password_plana_nueva: str, id_usuario_admin: int | None = None) -> bool:
        fn = getattr(DB, "resetear_password_usuario", None)
        resultado = bool(fn(id_usuario, password_plana_nueva)) if callable(fn) else False
        if resultado:
            self._registrar_auditoria(
                id_usuario=id_usuario_admin,
                accion="RESETEAR_PASSWORD",
                tabla_afectada="Usuario",
                id_registro=id_usuario,
                datos_nuevos={"password_reseteada": True}
            )
        return resultado

    def desactivar_usuario(self, id_usuario: int, id_usuario_admin: int | None = None) -> bool:
        fn = getattr(DB, "desactivar_usuario", None)
        resultado = bool(fn(id_usuario)) if callable(fn) else False
        if resultado:
            self._registrar_auditoria(
                id_usuario=id_usuario_admin,
                accion="DESACTIVAR_USUARIO",
                tabla_afectada="Usuario",
                id_registro=id_usuario,
                datos_anteriores={"activo": True},
                datos_nuevos={"activo": False}
            )
        return resultado

    def activar_usuario(self, id_usuario: int, id_usuario_admin: int | None = None) -> bool:
        fn = getattr(DB, "activar_usuario", None)
        resultado = bool(fn(id_usuario)) if callable(fn) else False
        if resultado:
            self._registrar_auditoria(
                id_usuario=id_usuario_admin,
                accion="REACTIVAR_USUARIO",
                tabla_afectada="Usuario",
                id_registro=id_usuario,
                datos_anteriores={"activo": False},
                datos_nuevos={"activo": True}
            )
        return resultado
        
    def actualizar_nombre_usuario(self, id_usuario: int, nuevo_nombre: str) -> bool:
        fn = getattr(DB, "actualizar_nombre_usuario", None)
        return bool(fn(id_usuario, nuevo_nombre)) if callable(fn) else False
    
    # ---------- Reportes ----------
    def obtener_vendedores(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_vendedores", None)
        return list(fn() or []) if callable(fn) else []

    def obtener_compradores(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_compradores", None)
        return list(fn() or []) if callable(fn) else []

    def obtener_usuarios_operativos(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_usuarios_operativos", None)
        return list(fn() or []) if callable(fn) else []
    def reporte_ventas_por_vendedor(self, desde: str, hasta: str, id_vendedor: int | None = None) -> list[dict[str, Any]]:
        fn = getattr(DB, "reporte_ventas_por_vendedor", None)
        return list(fn(desde, hasta, id_vendedor) or []) if callable(fn) else []
    def obtener_ventas_diarias(self, desde: str | None = None, hasta: str | None = None) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_ventas_diarias", None)
        return list(fn(desde, hasta) or []) if callable(fn) else []

    def obtener_productos_mas_vendidos(self, fecha_desde: str, fecha_hasta: str, limite: int = 5) -> list[dict[str, Any]]:
        """Retorna los productos más vendidos en el rango de fechas indicado."""
        fn = getattr(DB, "obtener_productos_mas_vendidos", None)
        return list(fn(fecha_desde, fecha_hasta, limite) or []) if callable(fn) else []

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

    def obtener_tesoreria_activa(self) -> dict | None:
        """Obtiene la sesión de Tesorería activa (única)."""
        fn = getattr(DB, "obtener_tesoreria_activa", None)
        return fn() if callable(fn) else None
        
    def obtener_session_por_id(self, id_session: int) -> dict | None:
        """Obtiene una sesión por su ID"""
        fn = getattr(DB, "obtener_session_por_id", None)
        return fn(id_session) if callable(fn) else None
    
    def abrir_caja_session(self, id_usuario: int, monto_inicial: float, tipo_caja: str = 'turno') -> bool:
        fn = getattr(DB, "abrir_caja_session", None)
        if not callable(fn): return False
        try:
            return bool(fn(id_usuario, monto_inicial, tipo_caja))
        except ValueError as e:
            # Re-lanzar errores de validación (ej: "Usuario ya tiene caja abierta" o "Tesorería ya abierta")
            raise
    
    def registrar_movimiento_manual(self, id_session: int, tipo: str, monto: float, motivo: str, descripcion: str, id_usuario: int) -> bool:
        fn = getattr(DB, "registrar_movimiento_manual", None)
        return bool(fn(id_session, tipo, monto, motivo, descripcion, id_usuario)) if callable(fn) else False
    
    def transferir_entre_cajas(self, origen: int, destino: int, monto: float, id_usuario: int, motivo_salida: str, motivo_entrada: str, obs: str, id_autorizador: int = None) -> bool:
        fn = getattr(DB, "transferir_entre_cajas", None)
        return bool(fn(origen, destino, monto, id_usuario, motivo_salida, motivo_entrada, obs, id_autorizador)) if callable(fn) else False
    
    def obtener_resumen_cierre(self, id_session: int) -> dict:
        fn = getattr(DB, "obtener_resumen_cierre", None)
        return fn(id_session) if callable(fn) else {}
    
    def cerrar_caja_session(self, id_session: int, id_usuario_cierre: int, efectivo_esperado: float, efectivo_contado: float, diferencia: float, obs: str) -> bool:
        fn = getattr(DB, "cerrar_caja_session", None)
        return bool(fn(id_session, id_usuario_cierre, efectivo_esperado, efectivo_contado, diferencia, obs)) if callable(fn) else False

    def cerrar_caja_por_supervisor(self, id_session: int, id_supervisor: int, obs: str = "Cierre Forzado por Supervisor") -> bool:
        fn = getattr(DB, "cerrar_caja_por_supervisor", None)
        return bool(fn(id_session, id_supervisor, obs)) if callable(fn) else False

    def registrar_ingreso_capital(self, monto: float, observacion: str, id_usuario: int) -> bool:
        fn = getattr(DB, "registrar_ingreso_capital", None)
        return bool(fn(monto, observacion, id_usuario)) if callable(fn) else False

    # ---------- Auditoría (Bitácora) ----------
    def contar_bitacora_acciones(self, fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None, id_usuario: Optional[int] = None, accion: Optional[str] = None) -> int:
        fn = getattr(DB, "contar_bitacora_acciones", None)
        return int(fn(fecha_desde, fecha_hasta, id_usuario, accion)) if callable(fn) else 0

    def obtener_bitacora_acciones(self, fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None, id_usuario: Optional[int] = None, accion: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = 0) -> list[dict]:
        fn = getattr(DB, "obtener_bitacora_acciones", None)
        return list(fn(fecha_desde, fecha_hasta, id_usuario, accion, limit, offset) or []) if callable(fn) else []
    
    # --- REPORTES DE CAJA ---
    def obtener_resumen_diario(self, fecha: str | None = None) -> dict:
        """
        Obtiene resumen de ventas del día por categoría y método de pago.
        Si fecha es None, usa hoy.
        """
        fn = getattr(DB, "obtener_resumen_diario", None)
        return fn(fecha) if callable(fn) else {}
    
    def contar_historial_movimientos_caja(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        tipo: str | None = None,
        motivo: str | None = None,
        id_usuario: int | None = None,
        id_session: int | None = None,
        tipo_caja: str | None = None
    ) -> int:
        fn = getattr(DB, "contar_historial_movimientos_caja", None)
        return int(fn(fecha_desde, fecha_hasta, tipo, motivo, id_usuario, id_session, tipo_caja)) if callable(fn) else 0

    def obtener_historial_movimientos_caja(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        tipo: str | None = None,
        motivo: str | None = None,
        id_usuario: int | None = None,
        id_session: int | None = None,
        tipo_caja: str | None = None,
        limit: int | None = None,
        offset: int = 0
    ) -> list[dict]:
        """
        Obtiene historial de movimientos de caja con filtros.
        """
        fn = getattr(DB, "obtener_historial_movimientos_caja", None)
        return list(fn(fecha_desde, fecha_hasta, tipo, motivo, id_usuario, id_session, tipo_caja, limit, offset) or []) if callable(fn) else []

    def obtener_sesiones_abiertas_con_totales(self, tipo_caja: str = None) -> list[dict[str, Any]]:
        """Retorna todas las sesiones de caja abiertas con sus totales acumulados."""
        fn = getattr(DB, "obtener_sesiones_abiertas_con_totales", None)
        return list(fn(tipo_caja) or []) if callable(fn) else []

    def obtener_kpis_admin(self) -> dict[str, Any]:
        """Obtiene los KPIs globales del día para el dashboard del administrador."""
        fn = getattr(DB, "obtener_kpis_admin", None)
        return fn() if callable(fn) else {'ventas_dia': 0.0, 'tickets': 0, 'efectivo_total': 0.0}

    def obtener_feed_eventos(self, limit: int = 30, id_usuario: int | None = None) -> list[dict]:
        """Obtiene el log de eventos para el Live Feed del dashboard admin."""
        fn = getattr(DB, "obtener_feed_eventos", None)
        return list(fn(limit, id_usuario) or []) if callable(fn) else []

    def obtener_usuarios_actividad_hoy(self) -> list[dict]:
        """Obtiene la lista de usuarios con actividad el día de hoy para el filtro del Live Feed."""
        fn = getattr(DB, "obtener_usuarios_actividad_hoy", None)
        return list(fn() or []) if callable(fn) else []

    # ---------- Broadcast ----------

    def obtener_usuarios_activos_para_broadcast(self, excluir_id: int | None = None) -> list[dict]:
        """
        Obtiene usuarios activos para poblar el selector de destinatario en el broadcast.
        Excluye opcionalmente al admin emisor.
        """
        fn = getattr(DB, "obtener_usuarios_con_rol", None)
        if not callable(fn):
            return []
        usuarios = list(fn() or [])
        if excluir_id is not None:
            usuarios = [u for u in usuarios if u.get("id_usuario") != excluir_id]
        return [{"id_usuario": u["id_usuario"], "nombre": u["nombre"]} for u in usuarios if u.get("activo", True)]

    def enviar_mensaje_broadcast(
        self,
        contenido: str,
        id_admin: int,
        destinatario_tipo: str = "todos",
        destinatario_id: int | None = None,
    ) -> bool:
        """
        Inserta un mensaje broadcast en la tabla mensajes_broadcast.
        Delega a DB.enviar_mensaje_broadcast().
        Retorna True si el mensaje fue insertado, False en caso de error.
        """
        fn = getattr(DB, "enviar_mensaje_broadcast", None)
        if callable(fn):
            return bool(fn(contenido, id_admin, destinatario_tipo, destinatario_id))
        logger.error("enviar_mensaje_broadcast: función no disponible en DB.py")
        return False

    def obtener_mensajes_no_leidos(
        self,
        id_rol: int,
        id_usuario: int,
        excluir_id_admin: int | None = None,
        ultimo_id: int = 0,
    ) -> list[dict]:
        """
        Devuelve los mensajes broadcast con id_mensaje > ultimo_id para el usuario dado.

        El parámetro ultimo_id actúa como cursor local del cliente: solo se retornan
        mensajes nuevos desde la última verificación, sin modificar la BD.
        Si excluir_id_admin se proporciona, se omiten los mensajes enviados por ese
        admin (evita que el administrador reciba sus propios broadcasts).
        """
        fn = getattr(DB, "obtener_mensajes_broadcast_no_leidos", None)
        if callable(fn):
            return list(fn(id_rol, id_usuario, excluir_id_admin, ultimo_id) or [])
        return []

    def marcar_mensajes_leidos(self, ids: list[int]) -> bool:
        """Marca como leídos los mensajes broadcast con los ids indicados.

        Nota: Este método queda disponible por compatibilidad pero ya no se invoca
        en el ciclo de polling (v2). El estado de lectura ahora se gestiona con
        un cursor local en memoria en `broadcast_manager.py`.
        """
        fn = getattr(DB, "marcar_mensajes_broadcast_leidos", None)
        if callable(fn):
            return bool(fn(ids))
        return False

    def obtener_ultimo_id_broadcast(self) -> int:
        """
        Devuelve el id_mensaje más alto en mensajes_broadcast.

        Usado al iniciar el polling para fijar el cursor del cliente y evitar
        que se re-entreguen mensajes históricos al iniciar sesión.
        """
        fn = getattr(DB, "obtener_ultimo_id_broadcast", None)
        if callable(fn):
            return int(fn() or 0)
        return 0
    # ---------- Tesorería ----------
    def obtener_tesoreria_hoy(self) -> dict | None:
        conn = None
        try:
            conn = DB.conectar()
            cur = conn.cursor(dictionary=True)
            return DB.obtener_tesoreria_hoy(cur)
        except Exception as e:
            logger.error(f"Error en obtener_tesoreria_hoy: {e}")
            return None
        finally:
            if conn: conn.close()
            
    def crear_tesoreria_hoy(self, id_usuario: int) -> dict | None:
        conn = None
        try:
            conn = DB.conectar()
            cur = conn.cursor(dictionary=True)
            conn.start_transaction()
            res = DB.crear_tesoreria_hoy(cur, id_usuario)
            conn.commit()
            return res
        except Exception as e:
            if conn: conn.rollback()
            logger.error(f"Error en crear_tesoreria_hoy: {e}")
            return None
        finally:
            if conn: conn.close()
            
    def obtener_o_crear_tesoreria_hoy(self, id_usuario: int) -> dict | None:
        conn = None
        try:
            conn = DB.conectar()
            cur = conn.cursor(dictionary=True)
            conn.start_transaction()
            res = DB.obtener_o_crear_tesoreria_hoy(cur, id_usuario)
            conn.commit()
            return res
        except Exception as e:
            if conn: conn.rollback()
            logger.error(f"Error en obtener_o_crear_tesoreria_hoy: {e}")
            return None
        finally:
            if conn: conn.close()
