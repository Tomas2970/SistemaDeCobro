# app/frontend/interfaz_productos.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Any, Dict
try:
    from app.frontend.stock_alerts import show_low_stock_alert
except ImportError:
    def show_low_stock_alert(*args, **kwargs):
        print("Advertencia: Módulo 'stock_alerts' no encontrado.")

def ui_productos(
    parent: tk.Misc, 
    backend, 
    usuario: dict, # <-- ¡Ya recibimos el 'usuario' aquí!
    id_producto_a_cargar: int | None = None
) -> None:
    
    win = tk.Toplevel(parent)
    win.title("🧰 Productos (Alta / Edición / Stock)")
    win.geometry("520x480")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    main_frame = tk.Frame(win, bg="#f4f4f8")
    main_frame.pack(expand=True, fill=tk.BOTH, pady=10, padx=20)

    # ---------- Header búsqueda ----------
    frm_busqueda = tk.Frame(main_frame, bg="#f4f4f8")
    frm_busqueda.pack(fill=tk.X, pady=(5, 15)) 
    
    tk.Label(frm_busqueda, text="ID / Código / Nombre:", bg="#f4f4f8").pack(side=tk.LEFT, padx=(0, 6))
    var_token = tk.StringVar()
    tk.Entry(frm_busqueda, textvariable=var_token, width=24).pack(side=tk.LEFT)
    tk.Button(frm_busqueda, text="🔎 Buscar", width=8, command=lambda: cargar_por_token()).pack(side=tk.LEFT, padx=(6,2))
    tk.Button(frm_busqueda, text="Nuevo", width=7, command=lambda: limpiar_form()).pack(side=tk.LEFT, padx=2)

    # --- Frame para el formulario, centrado ---
    body = tk.Frame(main_frame, bg="#f4f4f8")
    body.pack(fill=tk.X, pady=8) 
    
    body.columnconfigure(0, weight=1, uniform='lbl') # Etiqueta
    body.columnconfigure(1, weight=3, uniform='ent') # Entrada

    row = 0
    def add_row(lbl: str, widget):
        nonlocal row
        tk.Label(body, text=lbl, bg="#f4f4f8").grid(row=row, column=0, sticky="e", padx=8, pady=6)
        widget.grid(row=row, column=1, sticky="w", padx=8, pady=6)
        row += 1

    var_id = tk.StringVar(); add_row("ID (solo lectura):", tk.Entry(body, textvariable=var_id, width=12, state="readonly"))
    var_nombre = tk.StringVar(); add_row("Nombre:", tk.Entry(body, textvariable=var_nombre, width=40))
    combo_cat = ttk.Combobox(body, state="readonly", width=38); add_row("Categoría:", combo_cat)
    var_precio = tk.StringVar(value="0.00"); add_row("Precio:", tk.Entry(body, textvariable=var_precio, width=14))
    
    var_es_pesable = tk.BooleanVar(value=False)
    chk_pesable = tk.Checkbutton(body, text="Es pesable (se vende por Kg/Lt)", variable=var_es_pesable, bg="#f4f4f8")
    add_row("Tipo de Venta:", chk_pesable)
    
    var_cod = tk.StringVar(); add_row("Código de barras:", tk.Entry(body, textvariable=var_cod, width=40))
    var_stock = tk.StringVar(value="0"); add_row("Stock (Kg / Unid):", tk.Entry(body, textvariable=var_stock, width=10))
    var_stock_min = tk.StringVar(value="10"); add_row("Stock mínimo:", tk.Entry(body, textvariable=var_stock_min, width=10))

    # --- Frame de acciones centrado ---
    actions = tk.Frame(main_frame, bg="#f4f4f8")
    actions.pack(pady=10, fill=tk.X, expand=True) 
    
    btn_container = tk.Frame(actions, bg="#f4f4f8")
    btn_container.pack() 

    btn_guardar = tk.Button(btn_container, text="💾 Guardar (crear/editar)", bg="#4CAF50", fg="white", width=22, command=lambda: guardar())
    btn_guardar.pack(side=tk.LEFT, padx=10) 
    
    btn_desactivar = tk.Button(btn_container, text="🗑 Desactivar", bg="#f44336", fg="white", width=18, command=lambda: desactivar())
    btn_desactivar.pack(side=tk.LEFT, padx=10)

    # ---------- helpers ----------
    def _norm(prod: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": prod.get("id_producto") or prod.get("id"),
            "nombre": prod.get("nombre") or "",
            "codigo": prod.get("codigo_barras") or prod.get("codigo") or "",
            "precio": float(prod.get("precio") or 0.0),
            "es_pesable": bool(prod.get("es_pesable") or False), 
            "stock": float(prod.get("stock") or 0.0), 
            "stock_minimo": int(prod.get("stock_minimo") or 0),
            "categoria": prod.get("categoria") or prod.get("nombre_categoria") or "",
            "id_categoria": prod.get("id_categoria") or prod.get("categoria_id") or None,
        }

    def cargar_categorias():
        cats = backend.obtener_categorias() or []
        nombres = ["(Sin categoría)"]
        ids = [None]
        for c in cats:
            nombres.append(str(c.get("nombre") or c.get("categoria") or ""))
            ids.append(int(c.get("id_categoria") or 0))
            
        combo_cat["values"] = nombres
        combo_cat.ids = ids  # type: ignore
        combo_cat.current(0)

    def _resolver_producto(token: str):
        token = token.strip()
        if not token: return None
        if token.isdigit():
            p = backend.buscar_producto_por_id(int(token))
            if p: return p
        
        fn_cod = getattr(backend, "buscar_producto_por_codigo_barras", None)
        if callable(fn_cod):
            p = fn_cod(token)
            if p: return p
            
        res = backend.buscar_producto_por_nombre(token) or []
        return res[0] if res else None

    def limpiar_form():
        var_id.set(""); var_nombre.set(""); var_precio.set("0.00"); var_cod.set("")
        var_stock.set("0"); var_stock_min.set("10")
        var_es_pesable.set(False) 
        if combo_cat["values"]: combo_cat.current(0)
        var_token.set("")

    def cargar_por_token():
        token = var_token.get().strip()
        if not token:
            messagebox.showinfo("Búsqueda", "Ingrese un ID, código o nombre para buscar.", parent=win)
            return
            
        prod = _resolver_producto(token)
        if not prod:
            messagebox.showinfo("Sin resultados", "No se encontró el producto.", parent=win); return
        
        n = _norm(prod)
        var_id.set("" if n["id"] in (None, "", "None") else str(n["id"]))
        var_nombre.set(n["nombre"]); var_precio.set(f"{n['precio']:.2f}")
        var_cod.set(n["codigo"])
        var_es_pesable.set(n["es_pesable"]) 
        
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
        prod = None
        fn = getattr(backend, "buscar_producto_por_codigo_barras", None)
        if callable(fn):
            try:
                prod = fn(codigo)
            except Exception:
                pass
        if not prod: return True
        pid = int(prod.get("id_producto") or prod.get("id") or 0)
        return except_id is not None and pid == except_id

    def guardar():
        # --- ¡MODIFICACIÓN! Obtener id_usuario para auditoría ---
        id_user = usuario.get("id_usuario")
        
        try:
            nombre = var_nombre.get().strip()
            if not nombre:
                messagebox.showwarning("Validación", "El nombre es obligatorio.", parent=win); return
            
            ids_meta = getattr(combo_cat, "ids", [None])  # type: ignore
            id_cat = ids_meta[combo_cat.current()] if ids_meta and combo_cat.current() >= 0 else None
            
            precio = float(var_precio.get().replace(",", "."))
            if precio < 0: raise ValueError("Precio negativo")
            
            stock_abs = float(var_stock.get().replace(",", ".")) 
            stock_min = int(var_stock_min.get().strip() or "0")
            codigo = (var_cod.get().strip() or None)
            es_pesable = var_es_pesable.get() 

        except Exception as e:
            messagebox.showwarning("Validación", f"Verifique los datos (precio/stock). Error: {e}", parent=win); return

        pid = int(var_id.get()) if var_id.get().isdigit() else None
        
        if not _validar_dup_codigo(codigo, pid):
            messagebox.showwarning("Código", "El código de barras ya existe en otro producto.", parent=win); return

        if pid is None:
            try:
                nuevo_id = backend.crear_producto_completo(
                    nombre=nombre,
                    categoria_id=id_cat,
                    codigo_barras=codigo,
                    precio=precio,
                    stock_inicial=stock_abs,
                    stock_minimo=stock_min,
                    es_pesable=es_pesable,
                    id_usuario=id_user # <-- Pasa el usuario
                )
                if nuevo_id:
                    var_id.set(str(nuevo_id))
                    messagebox.showinfo("OK", f"Producto creado (ID {nuevo_id}).", parent=win)
                else:
                    messagebox.showerror("Error", "No se pudo crear el producto.", parent=win)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear:\n{e}", parent=win)

        else:
            try:
                ok_prod = backend.actualizar_producto(
                    id_producto=pid,
                    nombre=nombre,
                    id_categoria=id_cat,
                    precio=precio,
                    codigo_barras=codigo,
                    es_pesable=es_pesable,
                    id_usuario=id_user # <-- Pasa el usuario
                )
                
                ok_inv = backend.actualizar_inventario_absoluto(
                    id_producto=pid,
                    stock_abs=stock_abs,
                    stock_minimo=stock_min,
                    id_usuario=id_user # <-- Pasa el usuario
                )
                
                if ok_prod and ok_inv:
                    messagebox.showinfo("OK", "Producto actualizado correctamente.", parent=win)
                elif not ok_prod:
                     messagebox.showerror("Error", "No se pudieron guardar los cambios del producto.", parent=win)
                else:
                    messagebox.showwarning("Atención", "Se guardaron los datos del producto, pero falló la actualización del stock.", parent=win)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar:\s{e}", parent=win)

    def desactivar():
        pid_txt = var_id.get().strip()
        if not pid_txt.isdigit():
            messagebox.showwarning("Desactivar", "No hay un producto cargado.", parent=win); return
        
        pid = int(pid_txt)
        if not messagebox.askyesno("Confirmar", f"¿Desactivar el producto ID {pid}?\nEl producto ya no aparecerá en ventas o inventario.", parent=win):
            return
        try:
            # --- ¡MODIFICACIÓN! Pasa el id_usuario ---
            id_user = usuario.get("id_usuario")
            if backend.eliminar_producto(pid, id_usuario=id_user):
            # --- FIN MODIFICACIÓN ---
                messagebox.showinfo("OK", "Producto desactivado.", parent=win)
                limpiar_form()
            else:
                 messagebox.showerror("Error", "No se pudo desactivar el producto.", parent=win)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo desactivar:\n{e}", parent=win)

    def cargar_producto_inicial():
        if id_producto_a_cargar:
            var_token.set(str(id_producto_a_cargar))
            cargar_por_token()
    
    # Boot
    cargar_categorias()
    win.after(10, cargar_producto_inicial) 
    win.grab_set()