# app/frontend/interfaz_compra.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
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
    win.geometry("1050x650") # Altura ajustada para evitar que la barra de Windows tape contenido
    win.config(bg="#f4f4f8")
    
    style = ttk.Style()
    style.theme_use('clam')
    
    style.configure("Modern.Treeview",
                    background="#ffffff",
                    foreground="#1f2937",
                    rowheight=32,
                    fieldbackground="#ffffff",
                    borderwidth=0,
                    font=('Segoe UI', 10))
    
    style.configure("Modern.Treeview.Heading",
                    background="#f3f4f6",
                    foreground="#374151",
                    relief="flat",
                    borderwidth=1,
                    font=('Segoe UI', 10, 'bold'))
    
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

    def quitar_producto_seleccionado(event=None):
        sel = tree.selection()
        if not sel: return
        indices = sorted([int(i) for i in sel], reverse=True)
        for idx in indices:
            if 0 <= idx < len(carrito):
                carrito.pop(idx)
        repintar_tabla()

    # =================================================================
    # 1. SECCIÓN SUPERIOR: PROVEEDOR
    # =================================================================
    frame_top = tk.Frame(win, bg="#ffffff", pady=10, padx=15)
    frame_top.pack(fill=tk.X, padx=10, pady=(8, 5))

    tk.Label(frame_top, text="Proveedor:", bg="#ffffff", font=("Segoe UI", 11, "bold"), fg="#1f2937").pack(side=tk.LEFT)
    lbl_proveedor = tk.Label(frame_top, text="(Ninguno seleccionado)", fg="#6b7280", bg="#ffffff", font=("Segoe UI", 11), padx=10)
    lbl_proveedor.pack(side=tk.LEFT, padx=10)

    def seleccionar_proveedor():
        nonlocal proveedor_sel
        popup = tk.Toplevel(win)
        popup.title("Seleccionar Proveedor")
        popup.geometry("800x580") # Altura para que se vean los botones
        popup.config(bg="#f4f4f8")
        
        frm_busqueda = tk.Frame(popup, bg="#f4f4f8", pady=10)
        frm_busqueda.pack(fill=tk.X, padx=10)
        
        tk.Label(frm_busqueda, text="🔎 Buscar:", font=("Segoe UI", 10, "bold"), bg="#f4f4f8").pack(side=tk.LEFT, padx=5)
        var_buscar = tk.StringVar()
        entry_buscar = tk.Entry(frm_busqueda, textvariable=var_buscar, font=("Segoe UI", 10), width=45)
        entry_buscar.pack(side=tk.LEFT, padx=5)
        entry_buscar.focus_set()
        
        frm_lista = tk.Frame(popup, bg="#f4f4f8")
        frm_lista.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 🔥 COLUMNA VENDEDOR ELIMINADA
        cols_sel = ("ID", "Empresa", "CUIT")
        tree_provs = ttk.Treeview(frm_lista, columns=cols_sel, show="headings", height=12, style="Modern.Treeview")
        tree_provs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scroll = ttk.Scrollbar(frm_lista, orient="vertical", command=tree_provs.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree_provs.configure(yscrollcommand=scroll.set)
        
        for c in cols_sel: tree_provs.heading(c, text=c)
        tree_provs.column("ID", width=0, minwidth=0, stretch=False)
        tree_provs.column("Empresa", width=350)
        tree_provs.column("CUIT", width=150, anchor="center")

        provs = backend.obtener_proveedores(incluir_inactivos=False)

        def filtrar_proveedores(*args):
            for i in tree_provs.get_children(): tree_provs.delete(i)
            q = var_buscar.get().strip().lower()
            for p in provs:
                emp = p.get('empresa') or 'Sin Empresa'
                cuit = p.get('cuit') or '-'
                if q in emp.lower() or q in cuit.lower():
                    tree_provs.insert("", tk.END, values=(p['id_proveedor'], emp, cuit))
            hijos = tree_provs.get_children()
            if hijos: tree_provs.selection_set(hijos[0])

        var_buscar.trace_add("write", filtrar_proveedores)
        filtrar_proveedores()
        
        def confirmar(event=None):
            nonlocal proveedor_sel
            sel = tree_provs.selection()
            if not sel: return
            vals = tree_provs.item(sel[0], "values")
            prov_data = next((p for p in provs if p['id_proveedor'] == int(vals[0])), None)
            if not prov_data: return
            proveedor_sel = prov_data
            # 🔥 Mostrar solo nombre de la empresa
            lbl_proveedor.config(text=f"{prov_data.get('empresa')}", 
                               fg="#1f2937", font=("Segoe UI", 11, "bold"))
            btn_add_prod.config(state="normal") 
            popup.destroy()

        tree_provs.bind("<Double-1>", confirmar)
        tree_provs.bind("<Return>", confirmar)
        
        frm_botones = tk.Frame(popup, bg="#f4f4f8", pady=20)
        frm_botones.pack(fill=tk.X)
        tk.Button(frm_botones, text="✓ Seleccionar", command=confirmar, bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=25, pady=10).pack(side=tk.LEFT, padx=(250, 10))
        tk.Button(frm_botones, text="Cancelar", command=popup.destroy, bg="#6b7280", fg="white", font=("Segoe UI", 10), relief="flat", padx=20, pady=10).pack(side=tk.LEFT)
        configurar_navegacion_ventana(popup)

    tk.Button(frame_top, text="🔍 Buscar Proveedor", command=seleccionar_proveedor, bg="#3b82f6", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=8).pack(side=tk.LEFT)

    # =================================================================
    # 2. GRILLA PRINCIPAL
    # =================================================================
    frame_grilla = tk.Frame(win, bg="#f4f4f8")
    frame_grilla.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    cols = ("ID", "Producto", "Cantidad", "Costo Unit.", "Subtotal", "Precio Venta Nuevo")
    tree = ttk.Treeview(frame_grilla, columns=cols, show="headings", style="Modern.Treeview")
    
    tree.column("ID", width=0, minwidth=0, stretch=False)
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

    tree.bind("<Delete>", quitar_producto_seleccionado)

    frame_totales = tk.Frame(win, bg="#f4f4f8")
    frame_totales.pack(fill=tk.X, padx=20, pady=5)
    lbl_total = tk.Label(frame_totales, text="TOTAL: $ 0.00", font=("Segoe UI", 16, "bold"), bg="#f4f4f8", fg="#dc2626")
    lbl_total.pack(side=tk.RIGHT)

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
        except: return
        col_map = {'#3': 'cant', '#4': 'costo', '#6': 'precio_venta'}
        if col_id not in col_map: return
        campo = col_map[col_id]
        try:
            x, y, w, h = tree.bbox(row_id, col_id)
            if w == 0: return 
        except: return

        entry = EntryDecimal(tree, font=("Segoe UI", 10))
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, str(item[campo]))
        entry.select_range(0, tk.END)
        entry.focus_set()

        def confirmar_y_saltar(e=None):
            try:
                val = float(entry.get().replace(",", "."))
                if val < 0: raise ValueError
                item[campo] = val
                if campo == 'costo':
                    item['precio_venta'] = val * (1 + item.get('margen', 30.0)/100)
                entry.destroy()
                repintar_tabla()
                orden = ['#3', '#4', '#6']
                try:
                    curr_idx = orden.index(col_id)
                    if curr_idx < len(orden) - 1:
                        win.after(10, lambda: editar_celda(row_id, orden[curr_idx + 1]))
                    elif int(row_id) + 1 < len(carrito):
                        win.after(10, lambda: editar_celda(str(int(row_id) + 1), '#3'))
                except: pass
            except:
                entry.focus_set()

        entry.bind("<Return>", confirmar_y_saltar)
        entry.bind("<Tab>", confirmar_y_saltar)
        entry.bind("<Escape>", lambda e: entry.destroy())
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    tree.bind("<Double-1>", lambda e: tree.identify("region", e.x, e.y) == "cell" and editar_celda(tree.identify_row(e.y), tree.identify_column(e.x)))

    def abrir_selector_producto():
        if not proveedor_sel: return
        popup = Toplevel(win)
        popup.title("Agregar Producto al Carrito")
        popup.geometry("650x580") # Altura para botones
        popup.config(bg="#f4f4f8")
        
        frm_bus = tk.Frame(popup, bg="#f4f4f8", pady=10)
        frm_bus.pack(fill=tk.X, padx=15)
        tk.Label(frm_bus, text="🔎 Buscar producto:", bg="#f4f4f8", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        var_bus = tk.StringVar()
        ent_bus = tk.Entry(frm_bus, textvariable=var_bus, font=("Segoe UI", 10), width=40)
        ent_bus.pack(side=tk.LEFT, padx=10)
        ent_bus.focus_set()

        frm_tree = tk.Frame(popup, bg="#f4f4f8")
        frm_tree.pack(fill=tk.BOTH, expand=True, padx=15)
        
        cols_p = ("ID", "Nombre", "Stock Actual")
        tree_p = ttk.Treeview(frm_tree, columns=cols_p, show="headings", height=12, style="Modern.Treeview")
        tree_p.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sc_p = ttk.Scrollbar(frm_tree, orient="vertical", command=tree_p.yview)
        sc_p.pack(side=tk.RIGHT, fill=tk.Y)
        tree_p.configure(yscrollcommand=sc_p.set)

        for c in cols_p: tree_p.heading(c, text=c)
        tree_p.column("ID", width=0, minwidth=0, stretch=False)
        tree_p.column("Nombre", width=350)
        tree_p.column("Stock Actual", width=100, anchor="center")
        
        todos_prods = backend.obtener_productos_por_proveedor(proveedor_sel['id_proveedor'])
        
        def filtrar(*_):
            for i in tree_p.get_children(): tree_p.delete(i)
            q = var_bus.get().lower()
            for p in todos_prods:
                if q in p['nombre'].lower() or q in str(p['id_producto']):
                    tree_p.insert("", tk.END, values=(p['id_producto'], p['nombre'], f"{float(p.get('stock', 0)):.2f}"))
        
        var_bus.trace_add("write", filtrar); filtrar()

        def agregar_al_carrito(event=None):
            sel = tree_p.selection()
            if not sel: return
            vals = tree_p.item(sel[0], "values")
            pid = int(vals[0])
            prod_full = backend.buscar_producto_por_id(pid)
            if not prod_full: return
            
            id_cat = prod_full.get('id_categoria')
            margen = obtener_margen(id_cat)
            carrito.append({'id': pid, 'nombre': prod_full['nombre'], 'cant': 1.0, 'costo': 1.0, 'margen': margen, 'precio_venta': 1.0 * (1 + margen/100)})
            repintar_tabla(); popup.destroy()
            win.after(100, lambda: editar_celda(str(len(carrito)-1), '#3'))

        tree_p.bind("<Double-1>", agregar_al_carrito)
        tree_p.bind("<Return>", agregar_al_carrito)

        fr_btns = tk.Frame(popup, bg="#f4f4f8", pady=15)
        fr_btns.pack(fill=tk.X)
        tk.Button(fr_btns, text="+ Agregar al Carrito", bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=25, pady=10, command=agregar_al_carrito).pack(pady=5)
        configurar_navegacion_ventana(popup)

    # =================================================================
    # FOOTER
    # =================================================================
    frame_footer = tk.Frame(win, bg="#ffffff", pady=10)
    frame_footer.pack(fill=tk.X, side=tk.BOTTOM)
    
    inner_footer = tk.Frame(frame_footer, bg="#ffffff")
    inner_footer.pack(fill=tk.X, padx=20)

    btn_add_prod = tk.Button(inner_footer, text="+ Agregar Producto", command=abrir_selector_producto, bg="#3b82f6", fg="white", font=("Segoe UI", 10, "bold"), state="disabled", relief="flat", padx=20, pady=8)
    btn_add_prod.pack(side=tk.LEFT)

    tk.Button(inner_footer, text="🗑️ Quitar Item", command=quitar_producto_seleccionado, bg="#f3f4f6", fg="#ef4444", font=("Segoe UI", 9, "bold"), relief="flat", padx=15, pady=8).pack(side=tk.LEFT, padx=10)
    
    tk.Button(inner_footer, text="Cancelar", command=win.destroy, bg="#6b7280", fg="white", font=("Segoe UI", 10), relief="flat", padx=15, pady=8).pack(side=tk.LEFT, padx=5)

    def pedir_medio_pago():
        dialog = tk.Toplevel(win)
        dialog.title("Confirmar Compra")
        dialog.geometry("400x320")
        dialog.config(bg="#f4f4f8")
        dialog.resizable(False, False)
        dialog.transient(win); dialog.grab_set()
        
        seleccion = {"valor": None}
        total_pago = sum(item['cant'] * item['costo'] for item in carrito)

        tk.Label(dialog, text="Finalizar Compra", font=("Segoe UI", 14, "bold"), bg="#f4f4f8").pack(pady=(15,5))
        tk.Label(dialog, text=f"Total: $ {total_pago:,.2f}", font=("Segoe UI", 12, "bold"), fg="#10b981", bg="#f4f4f8").pack(pady=5)
        
        frm_btns = tk.Frame(dialog, bg="#f4f4f8")
        frm_btns.pack(fill="x", padx=40)

        def set_pago(tipo): seleccion["valor"] = tipo; dialog.destroy()

        opts = [("💵 Efectivo", "efectivo", "#dcfce7", "#065f46"), 
                ("🏦 Transferencia/Tarjeta", "transferencia", "#dbeafe", "#1e3a8a"),
                ("📋 Cuenta Corriente", "cuenta_corriente", "#fee2e2", "#991b1b")]
        
        for txt, val, bgc, fgc in opts:
            tk.Button(frm_btns, text=txt, bg=bgc, fg=fgc, command=lambda v=val: set_pago(v), font=("Segoe UI", 10), width=30, relief="flat", pady=8).pack(pady=3)

        tk.Button(dialog, text="Cancelar", command=dialog.destroy, bg="#6b7280", fg="white", relief="flat", padx=15, pady=8).pack(pady=10)
        win.wait_window(dialog); return seleccion["valor"]

    def guardar_compra():
        if not proveedor_sel or not carrito: return
        medio = pedir_medio_pago()
        if not medio: return
        try:
            id_compra = backend.insertar_compra(usuario['id_usuario'], proveedor_sel['id_proveedor'], carrito, medio_pago=medio)
            if id_compra:
                for item in carrito: backend.actualizar_precio_producto(item['id'], item['precio_venta'], id_usuario=usuario['id_usuario'])
                messagebox.showinfo("Éxito", "Compra registrada correctamente.")
                stock_events.notificar_cambio_stock(); win.destroy()
        except ValueError as ve:
            if "CAJA_CERRADA" in str(ve):
                messagebox.showerror(
                    "⚠️ Caja Cerrada", 
                    "No se puede procesar la compra porque la caja está cerrada.\n\n"
                    "Por favor, abra la caja antes de continuar.", 
                    parent=win
                )
            else:
                messagebox.showerror("Error", str(ve), parent=win)
        except Exception as e: 
            messagebox.showerror("Error", str(e), parent=win)

    tk.Button(inner_footer, text="✓ CONFIRMAR COMPRA", command=guardar_compra, bg="#10b981", fg="white", font=("Segoe UI", 11, "bold"), relief="flat", padx=25, pady=10).pack(side=tk.RIGHT)

    win.bind("<F2>", lambda e: btn_add_prod.invoke())
    configurar_navegacion_ventana(win, confirmar_cierre=True)
    win.grab_set()