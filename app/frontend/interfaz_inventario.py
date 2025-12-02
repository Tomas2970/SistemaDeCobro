# ============================================
# app/frontend/interfaz_inventario.py
# ============================================
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Dict, List
import csv
import logging
from datetime import datetime

from app.frontend.interfaz_productos import ui_productos
from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana

try:
    from app.frontend.stock_alerts import show_low_stock_alert
except ImportError:
    def show_low_stock_alert(*args, **kwargs):
        print("Advertencia: Módulo 'stock_alerts' no encontrado.")

# Sistema de notificación de cambios de stock (si existe)
try:
    from app.frontend.stock_event_manager import stock_events
except ImportError:
    print("ADVERTENCIA: No se pudo importar stock_event_manager")
    class DummyStockEvents:
        def notificar_cambio_stock(self):
            pass
    stock_events = DummyStockEvents()

logger = logging.getLogger(__name__)


def ui_inventario(parent: tk.Misc, backend, usuario: dict) -> None:
    """
    Interfaz de Inventario.
    - Filtrar por texto (nombre, código, ID).
    - Filtrar por categoría.
    - Ver stock bajo.
    - Exportar vista actual a CSV.
    - Doble clic → abre ABM Productos.
    """
    # Ventana principal
    win = tk.Toplevel(parent)
    win.title("Inventario de Productos")
    win.geometry("1000x580")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # ============================
    # Frame 1: Filtros y búsqueda
    # ============================
    frm_filtros = tk.Frame(win, bg="#f4f4f8")
    frm_filtros.pack(fill=tk.X, padx=16, pady=(12, 4))

    tk.Label(frm_filtros, text="Nombre / Código / ID:", bg="#f4f4f8").grid(
        row=0, column=0, sticky="e", padx=6
    )
    var_query = tk.StringVar()
    ent_q = tk.Entry(frm_filtros, textvariable=var_query, width=34)
    ent_q.grid(row=0, column=1, sticky="w")

    tk.Label(frm_filtros, text="Categoría:", bg="#f4f4f8").grid(
        row=0, column=2, sticky="e", padx=(20, 6)
    )
    combo_cat = ttk.Combobox(frm_filtros, state="readonly", width=24)
    combo_cat.grid(row=0, column=3, sticky="w")

    btn_buscar = tk.Button(
        frm_filtros,
        text="🔎 Buscar",
        width=12,
        command=lambda: buscar()
    )
    btn_buscar.grid(row=0, column=4, padx=(20, 6))

    btn_limpiar = tk.Button(
        frm_filtros,
        text="Limpiar",
        width=10,
        command=lambda: limpiar()
    )
    btn_limpiar.grid(row=0, column=5, padx=6)

    # ============================
    # Frame 2: Botones de acción
    # ============================
    frm_botones = tk.Frame(win, bg="#f4f4f8")
    frm_botones.pack(fill=tk.X, padx=16, pady=(0, 12))

    btn_stock_bajo = tk.Button(
        frm_botones,
        text="Ver Stock Bajo",
        width=16,
        command=lambda: mostrar_stock_bajo(),
        bg="#f4a261",
        fg="black"
    )
    btn_stock_bajo.pack(side=tk.LEFT, padx=0)

    btn_exportar = tk.Button(
        frm_botones,
        text="Exportar Vista...",
        width=16,
        command=lambda: exportar_vista_csv(),
        bg="#16a34a",
        fg="white"
    )
    btn_exportar.pack(side=tk.LEFT, padx=10)

    btn_cerrar = tk.Button(
        frm_botones,
        text="Cerrar",
        width=10,
        command=win.destroy,
        bg="#ef4444",
        fg="white"
    )
    btn_cerrar.pack(side=tk.RIGHT, padx=0)

    # ============================
    # Frame 3: Tabla de inventario
    # ============================
    cols = ["ID", "Código", "Nombre", "Categoría", "Stock", "Precio"]
    tree = ttk.Treeview(win, columns=cols, show="headings")
    tree.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))

    for c in cols:
        tree.heading(c, text=c)

    tree.column("ID", width=70, anchor="center")
    tree.column("Código", width=160, anchor="center")
    tree.column("Nombre", width=320, anchor="w")
    tree.column("Categoría", width=220, anchor="w")
    
    # CORRECCIÓN: Usamos 'center' para evitar que se corten los números con el borde
    tree.column("Stock", width=100, anchor="center")
    tree.column("Precio", width=100, anchor="center")

    yscroll = ttk.Scrollbar(tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=yscroll.set)
    yscroll.pack(side=tk.RIGHT, fill=tk.Y)

    # ====================================
    # Funciones de normalización de datos
    # ====================================
    def _get_id(p: Dict[str, Any]) -> int | None:
        return p.get("id_producto") or p.get("id")

    def _get_barcode(p: Dict[str, Any]) -> str:
        return str(p.get("codigo_barras") or p.get("codigo") or "")

    def _get_nombre(p: Dict[str, Any]) -> str:
        return str(p.get("nombre") or "")

    def _get_categoria(p: Dict[str, Any]) -> str:
        return str(p.get("categoria") or p.get("nombre_categoria") or "")

    def _get_stock(p: Dict[str, Any]) -> float:
        try:
            return float(p.get("stock") or p.get("cantidad") or 0.0)
        except Exception:
            return 0.0

    def _get_precio(p: Dict[str, Any]) -> float:
        try:
            return float(p.get("precio") or 0.0)
        except Exception:
            return 0.0

    def _norm(prod: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ID": _get_id(prod) or "",
            "Código": _get_barcode(prod),
            "Nombre": _get_nombre(prod),
            "Categoría": _get_categoria(prod),
            "Stock": _get_stock(prod),
            "Precio": _get_precio(prod),
            "es_pesable": bool(prod.get("es_pesable") or False),
        }

    def _paint(filas: List[Dict[str, Any]]) -> None:
        for i in tree.get_children():
            tree.delete(i)
        for p in filas:
            n = _norm(p)
            # CORRECCIÓN: Al usar 'center', ya no necesitamos el espacio extra
            tree.insert(
                "",
                tk.END,
                values=(
                    n["ID"],
                    n["Código"],
                    n["Nombre"],
                    n["Categoría"],
                    f"{n['Stock']:.2f}",
                    f"{n['Precio']:.2f}",
                ),
            )

    # ============================
    # Carga de datos desde backend
    # ============================
    def cargar_categorias() -> None:
        try:
            cats = backend.obtener_categorias() or []
            nombres = ["(Todas)"] + [
                str(c.get("nombre") or c.get("categoria") or "") for c in cats
            ]
            combo_cat["values"] = nombres
            combo_cat.current(0)
        except Exception as e:
            combo_cat["values"] = ["(Todas)"]
            combo_cat.current(0)
            messagebox.showwarning(
                "Categorías",
                f"No se pudieron cargar categorías:\n{e}",
                parent=win,
            )

    def cargar_todo() -> None:
        try:
            prods = backend.obtener_productos_full()
            _paint(prods)
        except Exception as e:
            messagebox.showerror(
                "Inventario",
                f"Error al cargar inventario:\n{e}",
                parent=win,
            )

    # ============================
    # Búsqueda
    # ============================
    def _resolver_busqueda(q: str) -> List[Dict[str, Any]]:
        q = q.strip()
        if not q:
            return backend.obtener_productos_full() or []

        # Si es número → probamos ID
        if q.isdigit():
            try:
                pid = int(q)
                if hasattr(backend, "buscar_producto_por_id"):
                    res = backend.buscar_producto_por_id(pid)
                    if res:
                        return [res]
            except Exception:
                pass

        # Si el backend soporta búsqueda por nombre
        if hasattr(backend, "buscar_producto_por_nombre"):
            return backend.buscar_producto_por_nombre(q) or []

        # Fallback
        return backend.obtener_productos_full() or []

    def buscar() -> None:
        try:
            q = var_query.get()
            categoria = combo_cat.get()
            filas = _resolver_busqueda(q)

            if categoria and categoria != "(Todas)":
                filas = [p for p in filas if _get_categoria(p) == categoria]

            _paint(filas)
        except Exception as e:
            messagebox.showerror(
                "Búsqueda",
                f"Error en la búsqueda:\n{e}",
                parent=win,
            )

    def limpiar() -> None:
        var_query.set("")
        if combo_cat["values"]:
            combo_cat.current(0)
        cargar_todo()

    ent_q.bind("<Return>", lambda e: buscar())

    # ============================
    # Stock bajo
    # ============================
    def mostrar_stock_bajo():
        try:
            if hasattr(backend, "obtener_stock_bajo"):
                bajos = backend.obtener_stock_bajo()
            else:
                messagebox.showerror(
                    "Error",
                    "La función 'obtener_stock_bajo' no existe en el backend.",
                    parent=win,
                )
                return

            if not bajos:
                messagebox.showinfo(
                    "Stock OK",
                    "No se encontraron productos con stock bajo.",
                    parent=win,
                )
                return

            _paint(bajos)
        except Exception as e:
            logger.error(f"[stock_alerts] show_low_stock_alert error: {e}")
            messagebox.showerror(
                "Error",
                f"No se pudo obtener el stock bajo:\n{e}",
                parent=win,
            )

    # ============================
    # Exportar vista actual a CSV
    # ============================
    def exportar_vista_csv():
        try:
            if not tree.get_children():
                messagebox.showinfo(
                    "Nada que exportar",
                    "La tabla de inventario está vacía.",
                    parent=win,
                )
                return

            hoy = datetime.now().strftime("%d-%m-%Y")
            default_filename = f"reporte_inventario_{hoy}.csv"

            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[
                    ("Archivo CSV (delimitado por punto y coma)", "*.csv"),
                    ("Todos los archivos", "*.*"),
                ],
                initialfile=default_filename,
                title="Guardar como CSV",
            )

            if not filepath:
                return

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(cols)
                for item_id in tree.get_children():
                    row = tree.item(item_id, "values")
                    # Limpieza estándar
                    clean_row = [str(x).strip() for x in row]
                    writer.writerow(clean_row)

            messagebox.showinfo(
                "Exportado",
                f"Archivo guardado en:\n{filepath}",
                parent=win,
            )
        except Exception as e:
            messagebox.showerror(
                "Exportar",
                f"No se pudo exportar el archivo:\n{e}",
                parent=win,
            )

    # ============================
    # Doble clic → abrir ABM productos
    # ============================
    def on_doble_clic(event):
        sel = tree.selection()
        if not sel:
            return
        item = sel[0]
        vals = tree.item(item, "values")
        if not vals:
            return
        try:
            id_prod = int(vals[0])
        except Exception:
            messagebox.showwarning(
                "ABM Productos",
                "No se pudo determinar el ID del producto.",
                parent=win,
            )
            return
        try:
            ui_productos(
                parent=win,
                backend=backend,
                usuario=usuario,
                id_producto_a_cargar=id_prod,
            )
            win.after(100, cargar_todo)
        except Exception as e:
            messagebox.showerror(
                "ABM Productos",
                f"No se pudo abrir el ABM de productos:\n{e}",
                parent=win,
            )

    tree.bind("<Double-1>", on_doble_clic)

    # ============================
    # Boot / inicio
    # ============================
    cargar_categorias()
    cargar_todo()
    configurar_navegacion_ventana(win)

    # 🔴 Foco inicial para que TAB y flechas ya trabajen sobre Inventario
    def _enfocar_inicial():
        try:
            win.focus_force()   # la ventana recibe el foco del teclado
            ent_q.focus_set()   # el cursor queda en el cuadro de búsqueda
        except Exception:
            pass

    win.after(50, _enfocar_inicial)
    win.grab_set()