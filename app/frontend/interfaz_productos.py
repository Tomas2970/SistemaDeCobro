# app/frontend/interfaz_productos.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

def ui_productos(parent: tk.Misc, backend, usuario: dict) -> None:
    win = tk.Toplevel(parent)
    win.title("🧰 Productos (Alta / Edición / Stock)")
    win.geometry("900x600")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # ---------- Alerta de stock bajo al abrir ----------
    try:
        bajos = backend.obtener_stock_bajo()
        if bajos:
            # mostrás un resumen (primeros 10)
            líneas = []
            for r in bajos[:10]:
                líneas.append(f"[{r.get('id_producto')}] {r.get('nombre')} · stk {r.get('cantidad')} / min {r.get('stock_minimo')}")
            resto = max(0, len(bajos) - 10)
            msg = "Productos con stock bajo:\n" + "\n".join(líneas)
            if resto:
                msg += f"\n... y {resto} más."
            messagebox.showwarning("Stock bajo", msg, parent=win)
    except Exception:
        pass

    frm = tk.Frame(win, bg="#f4f4f8"); frm.pack(fill=tk.X, padx=16, pady=12)

    tk.Label(frm, text="Código de barras o ID:", bg="#f4f4f8").grid(row=0, column=0, sticky="e", padx=6)
    var_token = tk.StringVar()
    tk.Entry(frm, textvariable=var_token, width=24).grid(row=0, column=1, sticky="w")
    tk.Button(frm, text="🔎 Buscar", width=12, command=lambda: cargar_por_token()).grid(row=0, column=2, padx=(12,4))
    tk.Button(frm, text="Nuevo", width=10, command=lambda: limpiar_form()).grid(row=0, column=3, padx=4)

    body = tk.Frame(win, bg="#f4f4f8"); body.pack(fill=tk.X, padx=16, pady=8)
    row = 0
    def add_row(lbl: str, widget):
        nonlocal row
        tk.Label(body, text=lbl, bg="#f4f4f8").grid(row=row, column=0, sticky="e", padx=8, pady=6)
        widget.grid(row=row, column=1, sticky="w"); row += 1

    var_id = tk.StringVar(); add_row("ID (solo lectura):", tk.Entry(body, textvariable=var_id, width=10, state="readonly"))
    var_nombre = tk.StringVar(); add_row("Nombre:", tk.Entry(body, textvariable=var_nombre, width=36))
    combo_cat = ttk.Combobox(body, state="readonly", width=34); add_row("Categoría:", combo_cat)
    var_precio = tk.StringVar(value="0.00"); add_row("Precio:", tk.Entry(body, textvariable=var_precio, width=12))
    var_cod = tk.StringVar(); add_row("Código de barras:", tk.Entry(body, textvariable=var_cod, width=36))
    var_stock = tk.StringVar(value="0"); add_row("Stock (absoluto):", tk.Entry(body, textvariable=var_stock, width=8))
    var_stock_min = tk.StringVar(value="10"); add_row("Stock mínimo:", tk.Entry(body, textvariable=var_stock_min, width=8))

    actions = tk.Frame(win, bg="#f4f4f8"); actions.pack(fill=tk.X, padx=16, pady=10)
    btn_guardar = tk.Button(actions, text="💾 Guardar (crear/editar)", bg="#4CAF50", fg="white", width=22, command=lambda: guardar())
    btn_guardar.pack(side=tk.LEFT, padx=6)
    btn_limpiar = tk.Button(actions, text="Limpiar", width=12, command=lambda: limpiar_form())
    btn_limpiar.pack(side=tk.LEFT, padx=6)
    btn_eliminar = tk.Button(actions, text="🗑 Eliminar", bg="#ef4444", fg="white", width=12, command=lambda: on_eliminar())
    btn_eliminar.pack(side=tk.LEFT, padx=6)

    # ---------- categorías ----------
    def cargar_categorias():
        cats = backend.obtener_categorias() or []
        nombres = ["(Sin categoría)"]; ids = [None]
        for c in cats:
            nombres.append(str(c.get("nombre") or c.get("categoria") or ""))
            ids.append(int(c.get("id_categoria") or c.get("id") or 0) or None)
        combo_cat["values"] = nombres; combo_cat.ids = ids  # type: ignore
        combo_cat.current(0)

    def _id_categoria_sel() -> Optional[int]:
        idx = combo_cat.current()
        return getattr(combo_cat, "ids", [None])[idx] if idx is not None and idx >= 0 else None  # type: ignore

    # ---------- helpers ----------
    def limpiar_form():
        var_id.set(""); var_nombre.set(""); var_precio.set("0.00"); var_cod.set(""); var_stock.set("0"); var_stock_min.set("10"); var_token.set("")
        if combo_cat["values"]: combo_cat.current(0)

    def _resolver_producto(token: str) -> dict | None:
        token = token.strip()
        if not token: return None
        if token.isdigit():
            prod = backend.buscar_producto_por_id(int(token))
            if prod: return prod
        prod = backend.buscar_producto_por_codigo_barras(token)
        if prod: return prod
        res = backend.buscar_producto_por_nombre(token) or []
        return res[0] if res else None

    def _norm(prod: dict) -> dict:
        return {
            "id": prod.get("id_producto") or prod.get("id") or "",
            "nombre": prod.get("nombre") or "",
            "categoria": prod.get("categoria") or prod.get("nombre_categoria") or "",
            "id_categoria": prod.get("id_categoria") or prod.get("categoria_id") or None,
            "precio": float(prod.get("precio") or 0.0),
            "codigo": prod.get("codigo_barras") or prod.get("codigo") or "",
            "stock": int(prod.get("stock") or prod.get("cantidad") or 0),
            "stock_minimo": int(prod.get("stock_minimo") or 0),
        }

    def cargar_por_token():
        token = var_token.get().strip()
        prod = _resolver_producto(token)
        if not prod:
            messagebox.showinfo("Sin resultados", "No se encontró el producto."); return
        n = _norm(prod)
        var_id.set(n["id"]); var_nombre.set(n["nombre"]); var_precio.set(f"{n['precio']:.2f}")
        var_cod.set(n["codigo"])
        try:
            sid = int(n["id"])
            var_stock.set(str(backend.obtener_stock(sid)))
            var_stock_min.set(str(backend.obtener_stock_minimo(sid)))
        except Exception:
            var_stock.set(str(n["stock"]))
            var_stock_min.set(str(n["stock_minimo"]))
        ids = getattr(combo_cat, "ids", [None])  # type: ignore
        if n["id_categoria"] and n["id_categoria"] in ids:
            combo_cat.current(ids.index(n["id_categoria"]))
        else:
            names = list(combo_cat["values"])
            combo_cat.current(names.index(n["categoria"]) if n["categoria"] in names else 0)

    def _validar_dup_codigo(codigo: str, except_id: Optional[int]) -> bool:
        if not codigo: return True
        prod = backend.buscar_producto_por_codigo_barras(codigo)
        if not prod: return True
        pid = int(prod.get("id_producto") or prod.get("id") or 0)
        return except_id is not None and pid == except_id

    # ---------- guardar ----------
    def guardar():
        try:
            nombre = var_nombre.get().strip()
            if not nombre:
                messagebox.showwarning("Validación", "El nombre es obligatorio."); return
            id_cat = _id_categoria_sel()
            precio = float((var_precio.get() or "0").replace(",", "."))
            codigo = (var_cod.get() or "").strip() or None
            stock_abs = int(var_stock.get() or "0")
            stock_min = int(var_stock_min.get() or "0")
        except Exception:
            messagebox.showerror("Validación", "Revisá precio/stock/stock mínimo."); return

        pid = int(var_id.get()) if var_id.get().isdigit() else None
        if not _validar_dup_codigo(codigo or "", pid):
            messagebox.showerror("Código duplicado", "El código de barras ya existe en otro producto."); return

        if pid is None:
            nuevo_id = backend.crear_producto_completo(
                nombre=nombre, categoria_id=id_cat, codigo_barras=codigo,
                precio=precio, stock_inicial=stock_abs, stock_minimo=stock_min
            )
            if nuevo_id:
                var_id.set(str(nuevo_id))
                messagebox.showinfo("OK", f"Producto creado (ID {nuevo_id}).")
                if stock_abs <= stock_min:
                    messagebox.showwarning("Stock bajo", "El stock inicial es menor o igual al mínimo.")
            else:
                messagebox.showerror("Error", "No se pudo crear el producto.")
            return

        ok = backend.actualizar_producto(
            id_producto=pid, nombre=nombre, id_categoria=id_cat, precio=precio, codigo_barras=codigo
        )
        if not ok:
            messagebox.showerror("Error", "No se pudieron guardar los cambios del producto."); return

        if not backend.actualizar_inventario_absoluto(pid, stock_abs, stock_min):
            messagebox.showwarning("Stock", "Se guardaron datos, pero no se pudo actualizar inventario.")
        else:
            if stock_abs <= stock_min:
                messagebox.showwarning("Stock bajo", "El stock quedó por debajo (o igual) al mínimo.")
            messagebox.showinfo("OK", "Producto actualizado.")

    # ---------- eliminar ----------
    def on_eliminar():
        pid_txt = var_id.get().strip()
        if not pid_txt.isdigit():
            messagebox.showwarning("Atención", "Primero cargá un producto existente."); return
        pid = int(pid_txt)
        if not messagebox.askyesno("Confirmar", f"¿Eliminar el producto ID {pid}? Esta acción no se puede deshacer."):
            return
        try:
            if backend.eliminar_producto(pid):
                messagebox.showinfo("OK", f"Producto ID {pid} eliminado.")
                limpiar_form()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el producto (¿FK RESTRICT en ventas/compras?).")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el producto:\n{e}")

    cargar_categorias()
    win.grab_set()
