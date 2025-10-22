# ==========================================
# app/frontend/interfaz_productos.py  (REEMPLAZAR COMPLETO)
# ==========================================
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox

def ui_productos(parent: tk.Misc, backend, usuario: dict) -> None:
    win = tk.Toplevel(parent)
    win.title("🧰 Productos (ABM)")
    win.geometry("820x520")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    notebook = ttk.Notebook(win); notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    # ---------- Agregar producto ----------
    tab_add = tk.Frame(notebook, bg="#f4f4f8"); notebook.add(tab_add, text="Agregar")

    row = 0
    def add_row(lbl, widget):
        nonlocal row
        tk.Label(tab_add, text=lbl, bg="#f4f4f8").grid(row=row, column=0, sticky="e", padx=8, pady=6)
        widget.grid(row=row, column=1, sticky="w")
        row += 1

    var_nombre = tk.StringVar(); add_row("Nombre:", tk.Entry(tab_add, textvariable=var_nombre, width=34))

    combo_cat = ttk.Combobox(tab_add, state="readonly", width=32); add_row("Categoría:", combo_cat)

    var_precio = tk.StringVar(value="0.00"); add_row("Precio:", tk.Entry(tab_add, textvariable=var_precio, width=12))

    var_stock_ini = tk.StringVar(value="0"); add_row("Stock inicial:", tk.Entry(tab_add, textvariable=var_stock_ini, width=8))

    var_stock_min = tk.StringVar(value="10"); add_row("Stock mínimo:", tk.Entry(tab_add, textvariable=var_stock_min, width=8))

    var_cod = tk.StringVar(); add_row("Código de barras (op.):", tk.Entry(tab_add, textvariable=var_cod, width=34))

    def cargar_categorias():
        cats = backend.obtener_categorias() or []
        nombres = ["(Sin categoría)"]; ids = [None]
        for c in cats:
            nombres.append(str(c.get("nombre") or c.get("categoria") or ""))
            ids.append(int(c.get("id_categoria") or c.get("id") or 0) or None)
        combo_cat["values"] = nombres; combo_cat.ids = ids  # type: ignore
        combo_cat.current(0)

    def _id_categoria_sel():
        idx = combo_cat.current()
        return getattr(combo_cat, "ids", [None])[idx] if idx is not None and idx >= 0 else None  # type: ignore

    def guardar():
        try:
            nombre = var_nombre.get().strip()
            if not nombre:
                messagebox.showwarning("Validación", "El nombre es obligatorio."); return
            id_cat = _id_categoria_sel()
            precio = float((var_precio.get() or "0").replace(",", "."))
            stock_ini = int(var_stock_ini.get() or "0")
            stock_min = int(var_stock_min.get() or "10")
            codigo = var_cod.get().strip() or None

            if codigo:
                # Tu DB.py no guarda código en crear_producto_completo; solo advertimos
                messagebox.showinfo("Aviso", "El código de barras será ignorado en este flujo (tu DB.py no lo recibe).")

            prod_id = backend.crear_producto_completo(
                nombre=nombre,
                categoria_id=id_cat,
                codigo_barras=codigo,
                precio=precio,
                stock_inicial=stock_ini,
                stock_minimo=stock_min,
            )
            if prod_id:
                messagebox.showinfo("OK", f"Producto creado (ID {prod_id}).")
                var_nombre.set(""); var_precio.set("0.00"); var_stock_ini.set("0"); var_stock_min.set("10"); var_cod.set("")
                if combo_cat["values"]: combo_cat.current(0)
            else:
                messagebox.showerror("Error", "No se pudo crear el producto.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear producto:\n{e}")

    tk.Button(tab_add, text="💾 Guardar", bg="#4CAF50", fg="white", width=14, command=guardar)\
        .grid(row=row, column=0, columnspan=2, pady=10)

    cargar_categorias()

    # ---------- Actualizar stock (valor absoluto) ----------
    tab_st = tk.Frame(notebook, bg="#f4f4f8"); notebook.add(tab_st, text="Stock")

    tk.Label(tab_st, text="Producto (ID):", bg="#f4f4f8").grid(row=0, column=0, padx=8, pady=8, sticky="e")
    var_id = tk.StringVar(); tk.Entry(tab_st, textvariable=var_id, width=8).grid(row=0, column=1, sticky="w")

    tk.Label(tab_st, text="Nuevo stock (absoluto):", bg="#f4f4f8").grid(row=0, column=2, padx=8, pady=8, sticky="e")
    var_nuevo = tk.StringVar(value="0"); tk.Entry(tab_st, textvariable=var_nuevo, width=10).grid(row=0, column=3, sticky="w")

    def aplicar():
        try:
            pid = int(var_id.get())
            nuevo = int(var_nuevo.get())
        except Exception:
            messagebox.showerror("Validación", "Ingrese ID y stock válidos."); return
        ok = backend.actualizar_stock(pid, nuevo)  # adapter convierte a delta
        if ok:
            messagebox.showinfo("OK", "Stock actualizado.")
        else:
            messagebox.showerror("Error", "No se pudo actualizar el stock.")

    tk.Button(tab_st, text="✅ Aplicar", bg="#4CAF50", fg="white", command=aplicar)\
        .grid(row=0, column=4, padx=10, pady=8)