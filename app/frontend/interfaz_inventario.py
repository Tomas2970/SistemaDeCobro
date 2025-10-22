# ==========================================
# app/frontend/interfaz_inventario.py  (REEMPLAZAR COMPLETO)
# ==========================================
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any

def ui_inventario(parent: tk.Misc, backend, usuario: dict) -> None:
    win = tk.Toplevel(parent)
    win.title("Interfaz de Inventario")
    win.geometry("860x560")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    frm = tk.Frame(win, bg="#f4f4f8"); frm.pack(fill=tk.X, padx=16, pady=12)

    tk.Label(frm, text="Nombre:", bg="#f4f4f8").grid(row=0, column=0, sticky="e", padx=6)
    var_nombre = tk.StringVar()
    tk.Entry(frm, textvariable=var_nombre, width=28).grid(row=0, column=1, sticky="w")

    tk.Label(frm, text="Categoría:", bg="#f4f4f8").grid(row=0, column=2, sticky="e", padx=(20,6))
    combo_cat = ttk.Combobox(frm, state="readonly", width=24); combo_cat.grid(row=0, column=3, sticky="w")

    tk.Button(frm, text="🔎 Buscar", width=12, command=lambda: buscar()).grid(row=0, column=4, padx=(20,6))
    tk.Button(frm, text="Limpiar", width=10, command=lambda: limpiar()).grid(row=0, column=5, padx=6)
    tk.Button(frm, text="↻ Recargar", width=12, command=lambda: cargar_todo()).grid(row=0, column=6, padx=6)

    cols = ["ID", "Nombre", "Categoría", "Stock", "Precio"]
    tree = ttk.Treeview(win, columns=cols, show="headings")
    tree.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4,12))
    for c in cols:
        tree.heading(c, text=c)
    tree.column("ID", width=70, anchor="center")
    tree.column("Nombre", width=300)
    tree.column("Categoría", width=200)
    tree.column("Stock", width=90, anchor="e")
    tree.column("Precio", width=100, anchor="e")

    yscroll = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
    tree.configure(yscroll=yscroll.set)
    yscroll.place(in_=tree, relx=1.0, rely=0, relheight=1.0, x=-2)

    def _norm(prod: dict) -> dict:
        # buscar_producto_por_nombre("") devuelve: p.*, categoria, stock
        return {
            "ID": prod.get("id_producto") or prod.get("id") or "",
            "Nombre": prod.get("nombre") or "",
            "Categoría": prod.get("categoria") or prod.get("nombre_categoria") or "",
            "Stock": prod.get("stock") or prod.get("cantidad") or 0,
            "Precio": prod.get("precio") or 0.0,
        }

    def _paint(filas: list[dict]) -> None:
        for i in tree.get_children():
            tree.delete(i)
        for p in filas:
            n = _norm(p)
            tree.insert("", tk.END, values=[n[c] for c in cols])

    def cargar_categorias() -> None:
        try:
            cats = backend.obtener_categorias() or []
            nombres = ["(Todas)"]
            for c in cats:
                nombres.append(str(c.get("nombre") or c.get("categoria") or ""))
            combo_cat["values"] = nombres
            combo_cat.current(0)
        except Exception as e:
            combo_cat["values"] = ["(Todas)"]; combo_cat.current(0)
            messagebox.showwarning("Categorías", f"No se pudieron cargar categorías:\n{e}")

    def cargar_todo() -> None:
        try:
            prods = backend.obtener_productos_full()  # ← con stock y categoría
            _paint(prods)
        except Exception as e:
            messagebox.showerror("Inventario", f"No se pudieron cargar productos:\n{e}")

    def buscar() -> None:
        nombre = var_nombre.get().strip().lower()
        cat = combo_cat.get().strip()
        try:
            prods = backend.obtener_productos_full()
            if nombre:
                prods = [p for p in prods if nombre in str(p.get("nombre","")).lower()]
            if cat and not cat.startswith("("):
                prods = [p for p in prods if str(p.get("categoria") or p.get("nombre_categoria") or "").lower() == cat.lower()]
            _paint(prods)
        except Exception as e:
            messagebox.showerror("Búsqueda", f"Error al filtrar:\n{e}")

    def limpiar() -> None:
        var_nombre.set("")
        if combo_cat["values"]:
            combo_cat.current(0)
        cargar_todo()

    cargar_categorias()
    cargar_todo()
    win.grab_set()
