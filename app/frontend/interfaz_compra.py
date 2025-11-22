# app/frontend/interfaz_compra.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Listbox
from typing import Any

try:
    from app.frontend.componentes_ui import EntryDecimal
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass
    class EntryDecimal(tk.Entry): pass

try:
    from app.frontend.stock_event_manager import stock_events
except ImportError:
    class DummyStockEvents:
        def notificar_cambio_stock(self): pass
    stock_events = DummyStockEvents()

def ui_compra(parent: tk.Misc, backend, usuario: dict):
    
    win = tk.Toplevel(parent)
    win.title("Registrar Compra (Entrada de Mercadería)")
    win.geometry("1050x700") 
    win.config(bg="#f4f4f8")
    
    proveedor_sel: dict | None = None
    carrito: list[dict] = [] 
    
    try:
        categorias_cache = backend.obtener_categorias()
    except:
        categorias_cache = []

    def obtener_margen(id_cat):
        for c in categorias_cache:
            if c['id_categoria'] == id_cat:
                return float(c.get('margen_ganancia', 30.0))
        return 30.0

    # =================================================================
    # 1. SECCIÓN SUPERIOR: PROVEEDOR
    # =================================================================
    frame_top = tk.Frame(win, bg="#f4f4f8", pady=15)
    frame_top.pack(fill=tk.X, padx=20)

    tk.Label(frame_top, text="Proveedor:", bg="#f4f4f8", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
    lbl_proveedor = tk.Label(frame_top, text="(Ninguno seleccionado)", fg="#0369a1", bg="#e0f2fe", font=("Segoe UI", 11), padx=10)
    lbl_proveedor.pack(side=tk.LEFT, padx=10)

    def seleccionar_proveedor():
        nonlocal proveedor_sel
        popup = Toplevel(win)
        popup.title("Seleccionar Proveedor")
        popup.geometry("500x400")
        
        lst = Listbox(popup, font=("Segoe UI", 10))
        lst.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        provs = backend.obtener_proveedores()
        for p in provs:
            estado = "" if p['activo'] else " (Inactivo)"
            lst.insert(tk.END, f"{p['id_proveedor']} - {p['nombre']}{estado}")
            
        def confirmar():
            nonlocal proveedor_sel
            sel = lst.curselection()
            if not sel: return
            idx = sel[0]
            prov_data = provs[idx]
            if not prov_data['activo']:
                messagebox.showwarning("Atención", "No se puede registrar compras a un proveedor inactivo.", parent=popup)
                return

            proveedor_sel = prov_data
            lbl_proveedor.config(text=proveedor_sel['nombre'])
            btn_add_prod.config(state="normal") 
            popup.destroy()

        lst.bind("<Double-1>", lambda e: confirmar())
        lst.bind("<Return>", lambda e: confirmar())

        tk.Button(popup, text="Seleccionar", command=confirmar, bg="#4CAF50", fg="white").pack(pady=10)
        configurar_navegacion_ventana(popup)

    tk.Button(frame_top, text="Buscar...", command=seleccionar_proveedor).pack(side=tk.LEFT)
    # SE ELIMINÓ EL BOTÓN DE CREAR NUEVO PROVEEDOR

    # =================================================================
    # 2. GRILLA
    # =================================================================
    frame_grilla = tk.Frame(win, bg="#f4f4f8")
    frame_grilla.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

    cols = ("ID", "Producto", "Cantidad", "Costo Unit.", "Subtotal", "Precio Venta Nuevo")
    tree = ttk.Treeview(frame_grilla, columns=cols, show="headings")
    
    tree.column("ID", width=50, anchor="center")
    tree.column("Producto", width=300)
    tree.column("Cantidad", width=80, anchor="e")    
    tree.column("Costo Unit.", width=100, anchor="e") 
    tree.column("Subtotal", width=100, anchor="e")
    tree.column("Precio Venta Nuevo", width=120, anchor="e") 

    for c in cols: tree.heading(c, text=c)

    vsb = ttk.Scrollbar(frame_grilla, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)

    frame_totales = tk.Frame(win, bg="#f4f4f8")
    frame_totales.pack(fill=tk.X, padx=20, pady=5)
    lbl_total = tk.Label(frame_totales, text="TOTAL: $ 0.00", font=("Segoe UI", 16, "bold"), bg="#f4f4f8", fg="#dc2626")
    lbl_total.pack(side=tk.RIGHT)

    # Lógica de Edición
    def repintar_tabla():
        for i in tree.get_children(): tree.delete(i)
        total_gral = 0.0
        for idx, item in enumerate(carrito):
            subtotal = item['cant'] * item['costo']
            total_gral += subtotal
            cant_str = f"{item['cant']:.3f}" if item['cant'] % 1 != 0 else f"{int(item['cant'])}"
            tree.insert("", tk.END, iid=str(idx), values=(
                item['id'], item['nombre'], cant_str,
                f"$ {item['costo']:.2f}", f"$ {subtotal:.2f}", f"$ {item['precio_venta']:.2f}"
            ))
        lbl_total.config(text=f"TOTAL: $ {total_gral:,.2f}")

    def editar_celda(row_id, col_id):
        try:
            idx = int(row_id)
            item = carrito[idx]
        except (ValueError, IndexError): return

        col_map = {'#3': 'cant', '#4': 'costo', '#6': 'precio_venta'}
        if col_id not in col_map: return

        campo = col_map[col_id]
        try:
            x, y, w, h = tree.bbox(row_id, col_id)
            if w == 0: return 
        except Exception: return

        valor_actual = item[campo]
        entry = EntryDecimal(tree)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, str(valor_actual))
        entry.select_range(0, tk.END)
        entry.focus_set()

        def confirmar_y_saltar(e=None):
            try:
                val = float(entry.get())
                if val < 0: raise ValueError
                item[campo] = val
                
                if campo == 'costo':
                    margen = item.get('margen', 30.0)
                    item['precio_venta'] = val * (1 + margen/100)

                entry.destroy()
                repintar_tabla()
                
                orden = ['#3', '#4', '#6']
                try:
                    curr_idx = orden.index(col_id)
                    if curr_idx < len(orden) - 1:
                        next_col = orden[curr_idx + 1]
                        win.after(10, lambda: editar_celda(row_id, next_col))
                    else:
                        next_row_idx = int(row_id) + 1
                        if next_row_idx < len(carrito):
                            win.after(10, lambda: editar_celda(str(next_row_idx), '#3'))
                except ValueError: pass

            except ValueError:
                messagebox.showwarning("Error", "Valor inválido")
                entry.focus_set()

        entry.bind("<Return>", confirmar_y_saltar)
        entry.bind("<Tab>", confirmar_y_saltar)
        entry.bind("<Escape>", lambda e: entry.destroy())
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    def on_click(event):
        region = tree.identify("region", event.x, event.y)
        if region == "cell":
            col = tree.identify_column(event.x)
            row = tree.identify_row(event.y)
            if row: editar_celda(row, col)

    tree.bind("<Double-1>", on_click)

    # Lógica de Agregar Producto
    def abrir_selector_producto():
        if not proveedor_sel: return
        popup = Toplevel(win)
        popup.title("Agregar Producto al Carrito")
        popup.geometry("500x450")
        
        tk.Label(popup, text="Buscar en productos de este proveedor:", bg="#f4f4f8").pack(pady=5)
        var_bus = tk.StringVar()
        ent_bus = tk.Entry(popup, textvariable=var_bus)
        ent_bus.pack(fill=tk.X, padx=10)
        ent_bus.focus_set()

        lst = Listbox(popup, height=15)
        lst.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        todos_prods = backend.obtener_productos_por_proveedor(proveedor_sel['id_proveedor'])
        
        def filtrar(*_):
            lst.delete(0, tk.END)
            q = var_bus.get().lower()
            for p in todos_prods:
                txt = f"{p['id_producto']} | {p['nombre']}"
                if q in txt.lower(): lst.insert(tk.END, txt)
        var_bus.trace_add("write", filtrar)
        filtrar()

        def agregar_al_carrito():
            sel = lst.curselection()
            if not sel: return
            linea = lst.get(sel[0])
            pid = int(linea.split("|")[0].strip())
            
            prod_full = backend.buscar_producto_por_id(pid)
            if not prod_full: return

            id_cat = prod_full.get('id_categoria')
            margen = obtener_margen(id_cat)
            
            nuevo_item = {
                'id': pid, 'nombre': prod_full['nombre'],
                'cant': 1.0, 'costo': 1.0, 'margen': margen,
                'precio_venta': 1.0 * (1 + margen/100)
            }
            carrito.append(nuevo_item)
            repintar_tabla()
            popup.destroy()
            
            new_idx = str(len(carrito) - 1)
            win.after(100, lambda: editar_celda(new_idx, '#3'))

        lst.bind("<Double-1>", lambda e: agregar_al_carrito())
        lst.bind("<Return>", lambda e: agregar_al_carrito())

        fr_btns = tk.Frame(popup, bg="#f4f4f8", pady=10)
        fr_btns.pack(fill=tk.X)
        tk.Button(fr_btns, text="Agregar al Carrito (Enter)", bg="#2196F3", fg="white", 
                  command=agregar_al_carrito, width=25).pack()
        
        configurar_navegacion_ventana(popup)

    # Footer
    frame_footer = tk.Frame(win, bg="#e5e7eb", height=60)
    frame_footer.pack(fill=tk.X, side=tk.BOTTOM)
    
    inner_footer = tk.Frame(frame_footer, bg="#e5e7eb")
    inner_footer.pack(fill=tk.X, padx=20, pady=15)

    btn_add_prod = tk.Button(inner_footer, text="+ Agregar Producto (F2)", command=abrir_selector_producto, 
                             bg="#03A9F4", fg="white", font=("Segoe UI", 10, "bold"), state="disabled", padx=15, pady=5)
    btn_add_prod.pack(side=tk.LEFT)
    
    tk.Button(inner_footer, text="Cancelar", command=win.destroy, 
              bg="#f44336", fg="white", font=("Segoe UI", 10), padx=10, pady=5).pack(side=tk.LEFT, padx=15)

    def guardar_compra():
        if not proveedor_sel: return
        if not carrito: 
            messagebox.showerror("Error", "Carrito vacío")
            return
        try:
            id_compra = backend.insertar_compra(usuario['id_usuario'], proveedor_sel['id_proveedor'])
            if not id_compra: raise Exception("Error DB")
            for item in carrito:
                backend.insertar_detalle_compra(id_compra, item['id'], item['cant'], item['costo'])
                backend.actualizar_precio_producto(item['id'], item['precio_venta'], id_usuario=usuario['id_usuario'])
            messagebox.showinfo("Éxito", "Compra registrada.")
            stock_events.notificar_cambio_stock()
            win.destroy()
        except Exception as e: messagebox.showerror("Error", str(e))

    tk.Button(inner_footer, text="CONFIRMAR COMPRA", command=guardar_compra, 
              bg="#16a34a", fg="white", font=("Segoe UI", 11, "bold"), padx=20, pady=5).pack(side=tk.RIGHT)

    win.bind("<F2>", lambda e: btn_add_prod.invoke())
    configurar_navegacion_ventana(win, confirmar_cierre=True)
    win.grab_set()