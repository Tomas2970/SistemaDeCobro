# app/frontend/interfaz_compra.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, Toplevel
from app.frontend import custom_dialogs as messagebox
from typing import Any
import customtkinter as ctk

try:
    from app.frontend.componentes_ui import EntryDecimal
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass
    EntryDecimal = ctk.CTkEntry

try:
    from app.frontend.stock_event_manager import stock_events
except ImportError:
    class DummyStockEvents:
        def notificar_cambio_stock(self): pass
    stock_events = DummyStockEvents()

def ui_compra(parent: tk.Misc, backend, usuario: dict):
    win = ctk.CTkToplevel(parent)
    from app.frontend.theme_config import preparar_ventana, centrar_y_mostrar_ventana
    preparar_ventana(win)
    win.title("Registrar Compra (Entrada de Mercadería)")
    win.geometry("1100x700") 
    
    col_bg = "#f3f4f6" if ctk.get_appearance_mode()=="Light" else "#111827"
    col_card = "#ffffff" if ctk.get_appearance_mode()=="Light" else "#1f2937"
    col_border = "#e5e7eb" if ctk.get_appearance_mode()=="Light" else "#374151"
    col_text = "#374151" if ctk.get_appearance_mode()=="Light" else "white"
    
    col_input_bg = "#f9fafb" if ctk.get_appearance_mode() == "Light" else "#374151"
    col_input_fg = "#1f2937" if ctk.get_appearance_mode() == "Light" else "#f9fafb"
    col_tree_bg = "#ffffff" if ctk.get_appearance_mode() == "Light" else "#1f2937"
    col_tree_fg = "#1f2937" if ctk.get_appearance_mode() == "Light" else "white"
    col_tree_head = "#f3f4f6" if ctk.get_appearance_mode() == "Light" else "#111827"
    
    win.configure(fg_color=col_bg)
    win.resizable(True, True)
    
    from app.frontend.theme_config import configurar_estilo_treeview
    configurar_estilo_treeview()
    
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
    frame_top = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
    frame_top.pack(fill="x", padx=15, pady=(15, 5))

    ctk.CTkLabel(frame_top, text="Proveedor:", font=("Segoe UI", 14, "bold"), text_color=col_text).pack(side="left", padx=(15, 5), pady=15)
    lbl_proveedor = ctk.CTkLabel(frame_top, text="(Ninguno seleccionado)", font=("Segoe UI", 14), text_color="#6b7280")
    lbl_proveedor.pack(side="left", padx=10)

    def seleccionar_proveedor():
        nonlocal proveedor_sel
        popup = ctk.CTkToplevel(win)
        popup.title("Seleccionar Proveedor")
        popup.geometry("800x650") 
        popup.configure(fg_color=col_bg)
        
        var_buscar = tk.StringVar()
        
        frm_busqueda = ctk.CTkFrame(popup, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
        frm_busqueda.pack(fill="x", padx=15, pady=(20, 10))
        
        ctk.CTkLabel(frm_busqueda, text="🔎 Buscar:", font=("Segoe UI", 14, "bold"), text_color=col_text).pack(side="left", padx=(15, 5), pady=15)
        entry_buscar = ctk.CTkEntry(frm_busqueda, textvariable=var_buscar, font=("Segoe UI", 13), width=400, height=40, placeholder_text="Nombre empresa o CUIT...")
        entry_buscar.pack(side="left", padx=10, pady=15)
        entry_buscar.focus_set()
        
        # --- Botones al fondo (empaquetados ANTES del tree para reservar espacio) ---
        frm_botones = ctk.CTkFrame(popup, fg_color="transparent")
        frm_botones.pack(fill="x", side="bottom", padx=15, pady=(10, 20))

        provs = backend.obtener_proveedores(incluir_inactivos=False)

        def confirmar(event=None):
            nonlocal proveedor_sel
            sel = tree_provs.selection()
            if not sel: return
            vals = tree_provs.item(sel[0], "values")
            prov_data = next((p for p in provs if p['id_proveedor'] == int(vals[0])), None)
            if not prov_data: return
            proveedor_sel = prov_data
            lbl_proveedor.configure(text=f"{prov_data.get('empresa')}", text_color=col_text)
            btn_add_prod.configure(state="normal") 
            popup.destroy()

        ctk.CTkButton(frm_botones, text="Cancelar", command=popup.destroy, fg_color="#ef4444", hover_color="#dc2626", font=("Segoe UI", 13, "bold"), width=150, height=45).pack(side="left", padx=10)
        ctk.CTkButton(frm_botones, text="✓ Seleccionar", command=confirmar, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 15, "bold"), width=200, height=45).pack(side="right", padx=10)
        
        # --- Tree (empaquetado DESPUÉS de botones) ---
        frm_lista = ctk.CTkFrame(popup, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
        frm_lista.pack(fill="both", expand=True, padx=15, pady=5)
        
        cols_sel = ("ID", "Empresa", "CUIT")
        tree_provs = ttk.Treeview(frm_lista, columns=cols_sel, show="headings", height=12, style="Compact.Treeview")
        
        scroll = ctk.CTkScrollbar(frm_lista, command=tree_provs.yview)
        scroll.pack(side="right", fill="y", padx=(0, 5), pady=5)
        tree_provs.configure(yscrollcommand=scroll.set)
        tree_provs.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        for c in cols_sel: tree_provs.heading(c, text=c)
        tree_provs.column("ID", width=0, minwidth=0, stretch=False)
        tree_provs.column("Empresa", width=400)
        tree_provs.column("CUIT", width=150, anchor="center")

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

        tree_provs.bind("<Double-1>", confirmar)
        tree_provs.bind("<Return>", confirmar)
        
        configurar_navegacion_ventana(popup)
        popup.grab_set()

    ctk.CTkButton(frame_top, text="🔍 Buscar Proveedor", command=seleccionar_proveedor, font=("Segoe UI", 12, "bold"), width=160, height=35).pack(side="left", padx=15)

    # =================================================================
    # 2. GRILLA PRINCIPAL
    # =================================================================
    frame_grilla = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
    frame_grilla.pack(fill="both", expand=True, padx=15, pady=5)

    cols = ("ID", "Producto", "Cantidad", "Costo Unit.", "Subtotal", "Precio Venta Nuevo")
    tree = ttk.Treeview(frame_grilla, columns=cols, show="headings", style="Compact.Treeview")
    
    tree.column("ID", width=0, minwidth=0, stretch=False)
    tree.configure(displaycolumns=[c for c in cols if c != "ID"])
    tree.column("Producto", width=350)
    tree.column("Cantidad", width=100, anchor="e")    
    tree.column("Costo Unit.", width=120, anchor="e") 
    tree.column("Subtotal", width=120, anchor="e")
    tree.column("Precio Venta Nuevo", width=150, anchor="e") 

    for c in cols: tree.heading(c, text=c)

    vsb = ctk.CTkScrollbar(frame_grilla, command=tree.yview)
    vsb.pack(side="right", fill="y", padx=(0, 5), pady=5)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)

    tree.bind("<Delete>", quitar_producto_seleccionado)

    frame_totales = ctk.CTkFrame(win, fg_color="transparent")
    frame_totales.pack(fill="x", padx=25, pady=5)
    lbl_total = ctk.CTkLabel(frame_totales, text="TOTAL: $ 0.00", font=("Segoe UI", 20, "bold"), text_color="#ef4444")
    lbl_total.pack(side="right")

    def repintar_tabla():
        if not win.winfo_exists():
            return
        try:
            for i in tree.get_children(): tree.delete(i)
        except tk.TclError:
            return
        total_gral = 0.0
        for idx, item in enumerate(carrito):
            subtotal = item['cant'] * item['costo']
            total_gral += subtotal
            cant_str = f"{item['cant']:.3f}" if item['cant'] % 1 != 0 else f"{int(item['cant'])}"
            tree.insert("", tk.END, iid=str(idx), values=(
                item['id'], item['nombre'], cant_str,
                f"$ {item['costo']:.2f}", f"$ {subtotal:.2f}", f"$ {item['precio_venta']:.2f}"
            ))
        lbl_total.configure(text=f"TOTAL: $ {total_gral:,.2f}")

    def editar_celda(row_id, col_id):
        try:
            idx = int(row_id)
            item = carrito[idx]
        except: return
        # Display columns (ID oculta): Producto=#1, Cantidad=#2, Costo Unit.=#3, Subtotal=#4, Precio Venta=#5
        col_map = {'#2': 'cant', '#3': 'costo', '#5': 'precio_venta'}
        if col_id not in col_map: return
        campo = col_map[col_id]
        try:
            x, y, w, h = tree.bbox(row_id, col_id)
            if w == 0: return 
        except: return

        # tk.Entry nativo: CTkEntry no funciona con .place() dentro de ttk.Treeview
        def _validar_numerico(txt):
            if txt == "": return True
            import re
            return bool(re.match(r'^\d{0,10}([.,]\d{0,4})?$', txt))
        vcmd_num = (tree.register(_validar_numerico), '%P')
        entry = tk.Entry(tree, font=("Segoe UI", 11), bg=col_input_bg, fg=col_input_fg, bd=0, insertbackground=col_input_fg, justify="right",
                         validate="key", validatecommand=vcmd_num)
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
                orden = ['#2', '#3', '#5']
                try:
                    curr_idx = orden.index(col_id)
                    if curr_idx < len(orden) - 1:
                        if win.winfo_exists():
                            win.after(10, lambda: editar_celda(row_id, orden[curr_idx + 1]))
                    elif int(row_id) + 1 < len(carrito):
                        if win.winfo_exists():
                            win.after(10, lambda: editar_celda(str(int(row_id) + 1), '#2'))
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
        popup = ctk.CTkToplevel(win)
        popup.title("Agregar Producto al Carrito")
        popup.geometry("700x650") 
        popup.configure(fg_color=col_bg)
        
        var_bus = tk.StringVar()
        
        frm_bus = ctk.CTkFrame(popup, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
        frm_bus.pack(fill="x", padx=15, pady=(20, 10))
        
        ctk.CTkLabel(frm_bus, text="🔎 Buscar producto:", font=("Segoe UI", 14, "bold"), text_color=col_text).pack(side="left", padx=(15, 5), pady=15)
        ent_bus = ctk.CTkEntry(frm_bus, textvariable=var_bus, font=("Segoe UI", 13), width=350, height=40, placeholder_text="Buscar producto...")
        ent_bus.pack(side="left", padx=10, pady=15)
        ent_bus.focus_set()

        # --- Botones al fondo (empaquetados ANTES del tree para reservar espacio) ---
        fr_btns = ctk.CTkFrame(popup, fg_color="transparent")
        fr_btns.pack(fill="x", side="bottom", padx=15, pady=(10, 20))
        
        todos_prods = backend.obtener_productos_por_proveedor(proveedor_sel['id_proveedor'])

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
            if win.winfo_exists():
                win.after(100, lambda: editar_celda(str(len(carrito)-1), '#2'))

        ctk.CTkButton(fr_btns, text="Cancelar", command=popup.destroy, fg_color="#ef4444", hover_color="#dc2626", font=("Segoe UI", 13, "bold"), width=150, height=45).pack(side="left", padx=10)
        ctk.CTkButton(fr_btns, text="+ Agregar al Carrito", command=agregar_al_carrito, fg_color="#3b82f6", hover_color="#2563eb", font=("Segoe UI", 15, "bold"), width=250, height=45).pack(side="right", padx=10)

        # --- Tree (empaquetado DESPUÉS de botones) ---
        frm_tree = ctk.CTkFrame(popup, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
        frm_tree.pack(fill="both", expand=True, padx=15, pady=5)
        
        cols_p = ("ID", "Nombre", "Stock Actual")
        tree_p = ttk.Treeview(frm_tree, columns=cols_p, show="headings", height=12, style="Compact.Treeview")
        
        sc_p = ctk.CTkScrollbar(frm_tree, command=tree_p.yview)
        sc_p.pack(side="right", fill="y", padx=(0, 5), pady=5)
        tree_p.configure(yscrollcommand=sc_p.set)
        tree_p.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        for c in cols_p: tree_p.heading(c, text=c)
        tree_p.column("ID", width=0, minwidth=0, stretch=False)
        tree_p.column("Nombre", width=400)
        tree_p.column("Stock Actual", width=120, anchor="center")

        def filtrar(*_):
            for i in tree_p.get_children(): tree_p.delete(i)
            q = var_bus.get().lower()
            for p in todos_prods:
                if q in p['nombre'].lower() or q in str(p['id_producto']):
                    tree_p.insert("", tk.END, values=(p['id_producto'], p['nombre'], f"{float(p.get('stock', 0)):.2f}"))
            hijos = tree_p.get_children()
            if hijos: tree_p.selection_set(hijos[0])
        
        var_bus.trace_add("write", filtrar); filtrar()

        tree_p.bind("<Double-1>", agregar_al_carrito)
        tree_p.bind("<Return>", agregar_al_carrito)
        
        configurar_navegacion_ventana(popup)
        popup.grab_set()

    # =================================================================
    # FOOTER
    # =================================================================
    frame_footer = ctk.CTkFrame(win, fg_color="transparent")
    frame_footer.pack(fill="x", side="bottom", padx=15, pady=(5, 15))
    
    btn_add_prod = ctk.CTkButton(frame_footer, text="+ Agregar Producto", command=abrir_selector_producto, font=("Segoe UI", 12, "bold"), width=180, height=45, state="disabled")
    btn_add_prod.pack(side="left", padx=10)

    ctk.CTkButton(frame_footer, text="🗑️ Quitar Item", command=quitar_producto_seleccionado, fg_color=col_card, border_color="#ef4444", border_width=1, hover_color="#fee2e2", text_color="#ef4444", font=("Segoe UI", 12, "bold"), width=150, height=45).pack(side="left", padx=5)
    
    ctk.CTkButton(frame_footer, text="✓ CONFIRMAR COMPRA", command=lambda: guardar_compra(), fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 16, "bold"), width=250, height=55).pack(side="right", padx=10)
    ctk.CTkButton(frame_footer, text="Cancelar", command=win.destroy, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 13, "bold"), width=150, height=55).pack(side="right", padx=5)

    def pedir_medio_pago():
        dialog = ctk.CTkToplevel(win)
        dialog.title("Confirmar Compra")
        dialog.geometry("400x350")
        dialog.configure(fg_color=col_bg)
        dialog.resizable(False, False)
        dialog.transient(win); dialog.grab_set()
        
        seleccion = {"valor": None}
        total_pago = sum(item['cant'] * item['costo'] for item in carrito)

        ctk.CTkLabel(dialog, text="Finalizar Compra", font=("Segoe UI", 18, "bold"), text_color=col_text).pack(pady=(25,10))
        ctk.CTkLabel(dialog, text=f"Total: $ {total_pago:,.2f}", font=("Segoe UI", 20, "bold"), text_color="#10b981").pack(pady=10)
        
        frm_btns = ctk.CTkFrame(dialog, fg_color="transparent")
        frm_btns.pack(fill="x", padx=40, pady=10)

        def set_pago(tipo): seleccion["valor"] = tipo; dialog.destroy()

        opts = [("💵 Efectivo", "efectivo", "#dcfce7", "#065f46", "#bbf7d0"), 
                ("🏦 Transferencia/Tarjeta", "transferencia", "#dbeafe", "#1e3a8a", "#bfdbfe"),
                ("📋 Cuenta Corriente", "cuenta_corriente", "#fee2e2", "#991b1b", "#fecaca")]
        
        for txt, val, bgc, fgc, hov in opts:
            ctk.CTkButton(frm_btns, text=txt, fg_color=bgc, hover_color=hov, text_color=fgc, command=lambda v=val: set_pago(v), font=("Segoe UI", 14, "bold"), height=45).pack(pady=5, fill="x")

        ctk.CTkButton(dialog, text="Cancelar", command=dialog.destroy, fg_color="#ef4444", hover_color="#dc2626", font=("Segoe UI", 13, "bold"), height=40).pack(pady=15)
        win.wait_window(dialog); return seleccion["valor"]

    def guardar_compra():
        if not proveedor_sel or not carrito: 
            messagebox.showwarning("Aviso", "Añada productos al carrito antes de confirmar.", parent=win)
            return
        medio = pedir_medio_pago()
        if not medio: return
        try:
            id_compra = backend.insertar_compra(usuario['id_usuario'], proveedor_sel['id_proveedor'], carrito, medio_pago=medio)
            if id_compra:
                for item in carrito: backend.actualizar_precio_producto(item['id'], item['precio_venta'], id_usuario=usuario['id_usuario'])
                messagebox.showinfo("Éxito", "Compra registrada correctamente.", parent=win)
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

    win.bind("<F2>", lambda e: btn_add_prod.invoke())
    configurar_navegacion_ventana(win, confirmar_cierre=False)
    centrar_y_mostrar_ventana(win)
    win.grab_set()