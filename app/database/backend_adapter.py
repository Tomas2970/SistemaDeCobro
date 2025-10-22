# ==========================================
# app/database/backend_adapter.py  (REEMPLAZAR COMPLETO)
# ==========================================
from __future__ import annotations
from typing import Any, Optional

try:
    from app.database import DB
except Exception as e:
    raise ImportError(
        "No se pudo importar app.database.DB. Verifica que DB.py esté en app/database/ "
        "y que ejecutes desde la raíz del proyecto."
    ) from e


class BackendAdapter:
    # ---------- Auth ----------
    def verificar_contraseña(self, usuario: str, contraseña: str) -> dict | None:
        return DB.verificar_contraseña(usuario, contraseña)

    # ---------- Clientes ----------
    def insertar_cliente(self, nombre: str, direccion: str, telefono: str, email: str) -> int | None:
        return DB.insertar_cliente(nombre, direccion, telefono, email)

    def listar_clientes(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_clientes", None)
        res = fn() if callable(fn) else []
        return list(res) if res else []

    def buscar_cliente_por_nombre(self, patron: str) -> list[dict[str, Any]]:
        fn = getattr(DB, "buscar_cliente_por_nombre", None)
        if callable(fn):
            res = fn(patron)
            return list(res) if res else []
        p = patron.lower()
        return [c for c in self.listar_clientes() if p in str(c.get("nombre", "")).lower()]

    def buscar_cliente_por_dni(self, dni: str) -> dict | None:
        fn = getattr(DB, "buscar_cliente_por_dni", None)
        if callable(fn):
            return fn(dni)
        for c in self.listar_clientes():
            if str(c.get("dni", "")) == str(dni):
                return c
        return None

    # ---------- Ventas ----------
    def insertar_venta(self, id_usuario: int, id_cliente: int | None = None) -> int | None:
        cid = None if (id_cliente in (None, 0)) else id_cliente  # FK opcional => NULL
        return DB.insertar_venta(id_usuario, cid)

    def insertar_detalle_venta(self, id_venta: int, id_producto: int, cantidad: int, precio_unitario: float) -> bool:
        return DB.insertar_detalle_venta(id_venta, id_producto, cantidad, precio_unitario)

    # ---------- Productos / Categorías ----------
    def obtener_categorias(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_categorias", None)
        res = fn() if callable(fn) else []
        return list(res) if res else []

    def obtener_productos(self) -> list[dict[str, Any]]:
        # Nota: DB.obtener_productos NO trae stock. Para grilla completa usá obtener_productos_full().
        res = DB.obtener_productos()
        return list(res) if res else []

    def obtener_productos_full(self) -> list[dict[str, Any]]:
        """
        Lista de productos con categoría y stock.
        Usa DB.buscar_producto_por_nombre("") que hace JOIN con Inventario.
        """
        fn = getattr(DB, "buscar_producto_por_nombre", None)
        if callable(fn):
            return list(fn("")) or []
        # Fallback: sin stock; evita romper
        return self.obtener_productos()

    def obtener_inventario(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_inventario", None)
        return list(fn()) if callable(fn) else []

    def buscar_producto_por_nombre(self, patron: str) -> list[dict[str, Any]]:
        res = DB.buscar_producto_por_nombre(patron)
        return list(res) if res else []

    def buscar_producto_por_codigo_barras(self, codigo: str) -> dict | None:
        fn = getattr(DB, "buscar_producto_por_codigo_barras", None)
        return fn(codigo) if callable(fn) else None

    def crear_producto_completo(
        self,
        nombre: str,
        categoria_id: Optional[int],
        codigo_barras: Optional[str],
        precio: float,
        stock_inicial: int,
        stock_minimo: int = 10,
    ) -> int | None:
        """
        Mapeo a DB.crear_producto_completo(nombre, precio, id_categoria, stock_inicial, stock_minimo).
        (Tu DB.py no acepta código de barras aquí; si lo ingresan, solo se advierte en la UI.)
        """
        fn_full = getattr(DB, "crear_producto_completo", None)
        if not callable(fn_full):
            # Si no existe, último recurso: insertar_producto + intentar crear inventario vía actualizar_stock (fallará si no hay fila en Inventario)
            fn_ins = getattr(DB, "insertar_producto", None)
            if not callable(fn_ins):
                return None
            prod_id = fn_ins(nombre, precio, categoria_id)
            # Intentar setear stock inicial como delta
            fn_upd = getattr(DB, "actualizar_stock", None)
            if callable(fn_upd) and prod_id:
                try:
                    fn_upd(prod_id, stock_inicial)
                except Exception:
                    pass
            return prod_id

        # Llamada exacta según tu DB.py
        return fn_full(nombre, precio, categoria_id, stock_inicial, stock_minimo)

    def insertar_producto(
        self,
        nombre: str,
        categoria_id: Optional[int],
        codigo_barras: Optional[str],
        precio: float,
        stock_inicial: int,
        stock_minimo: int = 10,
    ) -> int | None:
        """
        Para tu DB.py conviene SIEMPRE usar crear_producto_completo() (crea fila de Inventario).
        Este método sólo redirige al anterior para mantener compatibilidad con la UI.
        """
        return self.crear_producto_completo(
            nombre=nombre,
            categoria_id=categoria_id,
            codigo_barras=codigo_barras,
            precio=precio,
            stock_inicial=stock_inicial,
            stock_minimo=stock_minimo,
        )

    def _stock_actual(self, id_producto: int) -> Optional[int]:
        inv = self.obtener_inventario()  # [{id_producto, cantidad, ...}]
        for fila in inv:
            if int(fila.get("id_producto", -1)) == int(id_producto):
                return int(fila.get("cantidad", 0))
        # Si no vino de inventario, intentamos por nombre (JOIN)
        prods = self.obtener_productos_full()
        for p in prods:
            if int(p.get("id_producto", -1)) == int(id_producto):
                return int(p.get("stock", 0) or 0)
        return None

    def actualizar_stock(self, id_producto: int, nuevo_stock: int) -> bool:
        """
        Tu DB.actualizar_stock(id, cantidad) espera un **delta**.
        Este adapter convierte de absoluto→delta leyendo el stock actual.
        """
        fn = getattr(DB, "actualizar_stock", None)
        if not callable(fn):
            raise RuntimeError("DB.actualizar_stock no disponible.")

        actual = self._stock_actual(id_producto)
        if actual is None:
            # Si no hay fila aún, intentamos sumarle todo como delta
            delta = int(nuevo_stock)
        else:
            delta = int(nuevo_stock) - int(actual)

        try:
            return bool(fn(id_producto, delta))
        except Exception:
            # Último intento: algunos backends aceptan (id, delta, True/False)
            try:
                return bool(fn(id_producto, delta, True))
            except Exception:
                return False

    # ---------- Reportes ----------
    def obtener_ventas_diarias(self, desde: str | None = None, hasta: str | None = None) -> list[dict[str, Any]]:
        return list(DB.obtener_ventas_diarias(desde, hasta))

    def obtener_vendedores(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_vendedores", None)
        if not callable(fn):
            return []
        res = fn()
        return list(res) if res else []

    def reporte_ventas_por_vendedor(self, desde: str, hasta: str, id_vendedor: int | None = None) -> list[dict[str, Any]]:
        fn = getattr(DB, "reporte_ventas_por_vendedor", None)
        if not callable(fn):
            return []
        return list(fn(desde, hasta, id_vendedor))

