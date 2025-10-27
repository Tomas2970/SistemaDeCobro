# app/database/backend_adapter.py
from __future__ import annotations
from typing import Any, Optional

try:
    from app.database import DB
except Exception as e:
    raise ImportError("No se pudo importar app.database.DB.") from e


class BackendAdapter:
    # ---------- Auth ----------
    def verificar_contraseña(self, usuario: str, contraseña: str) -> dict | None:
        return DB.verificar_contraseña(usuario, contraseña)

    # ---------- Clientes ----------
    def insertar_cliente(self, nombre: str, direccion: str, telefono: str, email: str) -> int | None:
        return DB.insertar_cliente(nombre, direccion, telefono, email)

    def listar_clientes(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_clientes", None)
        return list(fn() or []) if callable(fn) else []

    def buscar_cliente_por_nombre(self, patron: str) -> list[dict[str, Any]]:
        fn = getattr(DB, "buscar_cliente_por_nombre", None)
        return list(fn(patron) or []) if callable(fn) else []

    # ---------- Ventas ----------
    def insertar_venta(self, id_usuario: int, id_cliente: int | None = None) -> int | None:
        return DB.insertar_venta(id_usuario, None if id_cliente in (None, 0) else id_cliente)

    def insertar_detalle_venta(self, id_venta: int, id_producto: int, cantidad: int, precio_unitario: float) -> bool:
        return DB.insertar_detalle_venta(id_venta, id_producto, cantidad, precio_unitario)

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
    ) -> int | None:
        pid = DB.crear_producto_completo(nombre, precio, categoria_id, stock_inicial, stock_minimo)
        if pid and codigo_barras:
            fn = getattr(DB, "actualizar_codigo_barras", None)
            if callable(fn):
                try: fn(pid, codigo_barras)
                except Exception: pass
        return pid

    def actualizar_producto(
        self,
        id_producto: int,
        nombre: Optional[str] = None,
        id_categoria: Optional[int] = None,
        precio: Optional[float] = None,
        codigo_barras: Optional[str] = None,
    ) -> bool:
        fn = getattr(DB, "actualizar_producto", None)
        return bool(fn(id_producto, nombre, precio, id_categoria, codigo_barras)) if callable(fn) else False

    # ---------- Stock & mínimo ----------
    def obtener_stock(self, id_producto: int) -> int:
        fn = getattr(DB, "obtener_stock_por_producto", None)
        return int(fn(id_producto)) if callable(fn) else 0

    def obtener_stock_minimo(self, id_producto: int) -> int:
        fn = getattr(DB, "obtener_stock_minimo", None)
        return int(fn(id_producto)) if callable(fn) else 0

    def actualizar_inventario_absoluto(self, id_producto: int, stock_abs: int, stock_minimo: Optional[int]) -> bool:
        fn = getattr(DB, "actualizar_inventario_absoluto", None)
        return bool(fn(id_producto, int(stock_abs), int(stock_minimo) if stock_minimo is not None else None)) if callable(fn) else False

    # ---------- Bajas ----------
    def eliminar_producto(self, id_producto: int) -> bool:
        fn = getattr(DB, "eliminar_producto", None)
        if not callable(fn):
            raise RuntimeError("DB.eliminar_producto no está implementado.")
        return bool(fn(id_producto))

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
