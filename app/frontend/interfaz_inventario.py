# ============================================
# app/frontend/interfaz_inventario.py
# (¡CORREGIDO EL CRASH DE on_doble_clic!)
# ============================================
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List

from app.frontend.interfaz_productos import ui_productos
try:
    from app.frontend.stock_alerts import show_low_stock_alert
except ImportError:
    def show_low_stock_alert(*args, **kwargs): 
        print("Advertencia: Módulo 'stock_alerts' no encontrado.")
        messagebox.showwarning("Error", "Módulo 'stock_alerts.py' no encontrado.")


def ui_inventario(parent: tk.Misc, backend, usuario: dict) -> None:
    win = tk.Toplevel(parent)
    win.title("Interfaz de Inventario")
    win.geometry("980x580")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # Alerta de stock movida aquí
    show_low_stock_alert(parent=win, backend=backend)

    frm = tk.Frame(win, bg="#f4f4f8"); frm.pack(fill=tk.X, padx=16, pady=12)

    tk.Label(frm, text="Nombre / Código / ID:", bg="#f4f4f8").grid(row=0, column=0, sticky="e", padx=6)
    var_query = tk.StringVar(); ent_q = tk.Entry(frm, textvariable=var_query, width=34)
    ent_q.grid(row=0, column=1, sticky="w")

    tk.Label(frm, text="Categoría:", bg="#f4f4f8").grid(row=0, column=2, sticky="e", padx=(20,6))
    combo_cat = ttk.Combobox(frm, state="readonly", width=24); combo_cat.grid(row=0, column=3, sticky="w")

    tk.Button(frm, text="🔎 Buscar", width=12, command=lambda: buscar()).grid(row=0, column=4, padx=(20,6))
    tk.Button(frm, text="Limpiar", width=10, command=lambda: limpiar()).grid(row=0, column=5, padx=6)
    tk.Button(frm, text="↻ Recargar", width=12, command=lambda: cargar_todo()).grid(row=0, column=6, padx=6)

    cols = ["ID", "Código", "Nombre", "Categoría", "Stock", "Precio"]
    tree = ttk.Treeview(win, columns=cols, show="headings")
    tree.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4,12))
    for c in cols: tree.heading(c, text=c)
    tree.column("ID", width=70, anchor="center")
    tree.column("Código", width=160, anchor="center")
    tree.column("Nombre", width=320)
    tree.column("Categoría", width=200)
    tree.column("Stock", width=90, anchor="e")
    tree.column("Precio", width=110, anchor="e")

    yscroll = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
    tree.configure(yscroll=yscroll.set); yscroll.place(in_=tree, relx=1.0, rely=0, relheight=1.0, x=-2)
    
    # (El .bind() se movió al final del archivo, después de la definición)

    # ---------------- Utils de normalización ----------------
    def _get_barcode(p: Dict[str, Any]) -> str:
        for k in ("codigo_barras", "codigo", "cod_barras", "codigo_barra", "barcode", "cb"):
            v = p.get(k)
            if v not in (None, ""):
                return str(v)
        return ""

    def _get_id(p: Dict[str, Any]) -> Any:
        return p.get("id_producto") or p.get("id")

    def _get_nombre(p: Dict[str, Any]) -> str:
        return str(p.get("nombre") or "")

    def _get_categoria(p: Dict[str, Any]) -> str:
        return str(p.get("categoria") or p.get("nombre_categoria") or "")

    def _get_stock(p: Dict[str, Any]) -> int:
        try: return int(p.get("stock") or p.get("cantidad") or 0)
        except Exception: return 0

    def _get_precio(p: Dict[str, Any]) -> float:
        try: return float(p.get("precio") or 0.0)
        except Exception: return 0.0

    def _norm(prod: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ID": _get_id(prod) or "",
            "Código": _get_barcode(prod),
            "Nombre": _get_nombre(prod),
            "Categoría": _get_categoria(prod),
            "Stock": _get_stock(prod),
            "Precio": _get_precio(prod),
        }

    def _paint(filas: List[Dict[str, Any]]) -> None:
        for i in tree.get_children(): tree.delete(i)
        for p in filas:
            n = _norm(p)
            tree.insert("", tk.END, values=[n[c] for c in cols])

    # ---------------- Carga de datos ----------------
    def cargar_categorias() -> None:
        try:
            cats = backend.obtener_categorias() or []
            nombres = ["(Todas)"] + [str(c.get("nombre") or c.get("categoria") or "") for c in cats]
            combo_cat["values"] = nombres; combo_cat.current(0)
        except Exception as e:
            combo_cat["values"] = ["(Todas)"]; combo_cat.current(0)
            messagebox.showwarning("Categorías", f"No se pudieron cargar categorías:\n{e}")

    def cargar_todo() -> None:
        try:
            prods = backend.obtener_productos_full()
            _paint(prods)
        except Exception as e:
            messagebox.showerror("Inventario", f"Error al cargar inventario:\n{e}")

    # ---------------- Búsqueda mejorada ----------------
    def _resolver_busqueda(q: str) -> List[Dict[str, Any]]:
        q = q.strip()
        if not q:
            return backend.obtener_productos_full() or []

        if q.isdigit():
            try:
                rid = int(q)
                if hasattr(backend, "buscar_producto_por_id"):
                    p = backend.buscar_producto_por_id(rid)
                    if p: return [p]
            except Exception:
                pass

        buscar_cb = None
        for name in ("buscar_producto_por_codigo_barras", "buscar_producto_por_codigo"):
            if hasattr(backend, name):
                buscar_cb = getattr(backend, name); break
        if callable(buscar_cb):
            try:
                p = buscar_cb(q)
                if p: return [p]
            except Exception:
                pass

        try:
            return backend.buscar_producto_por_nombre(q) or []
        except Exception:
            return []

    def _aplicar_filtro_categoria(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not combo_cat["values"]:
            return rows
        cat = combo_cat.get().strip()
        if not cat or cat.startswith("("):
            return rows
        wanted = cat.lower()
        out = []
        for p in rows:
            if _get_categoria(p).lower() == wanted:
                out.append(p)
        return out

    def buscar() -> None:
        try:
            q = var_query.get()
            rows = _resolver_busqueda(q)
            rows = _aplicar_filtro_categoria(rows)
            _paint(rows)
        except Exception as e:
            messagebox.showerror("Búsqueda", f"Error al filtrar:\n{e}")

    def limpiar() -> None:
        var_query.set("")
        if combo_cat["values"]: combo_cat.current(0)
        cargar_todo()

    ent_q.bind("<Return>", lambda e: buscar())

    # --- ¡CORRECCIÓN! Definición de la función movida aquí (antes de ser usada) ---
    def on_doble_clic(event=None):
        seleccion = tree.selection()
        if not seleccion:
            return 
        
        item_seleccionado = seleccion[0]
        try:
            id_producto = int(tree.item(item_seleccionado, "values")[0])
            if id_producto:
                ui_productos(
                    parent=win, 
                    backend=backend, 
                    usuario=usuario, 
                    id_producto_a_cargar=id_producto
                )
            else:
                messagebox.showinfo("Info", "Este producto no tiene un ID válido.", parent=win)
        except Exception as e:
            print(f"Error al abrir ABM en doble clic: {e}")
            messagebox.showwarning("Error", "No se pudo obtener el ID del producto.", parent=win)

    # --- ¡CORRECCIÓN! El .bind() se mueve al final ---
    tree.bind("<Double-1>", on_doble_clic)

    # Boot
    cargar_categorias()
    cargar_todo()
    win.grab_set()