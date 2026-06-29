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
            from app.frontend.validaciones_ui import ValidadoresTeclado
            return len(txt) <= 15 and ValidadoresTeclado.decimal(txt)
        vcmd_num = (tree.register(_validar_numerico), '%P')
        entry = tk.Entry(tree, font=("Segoe UI", 11), bg=col_input_bg, fg=col_input_fg, bd=0, insertbackground=col_input_fg, justify="right",
                         validate="key", validatecommand=vcmd_num)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, str(item[campo]))
        entry.select_range(0, tk.END)
        entry.focus_set()

        def confirmar_y_saltar(e=None):
            if not entry.winfo_exists(): return
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
                if entry.winfo_exists():
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

        def set_pago(tipo): 
            if tipo == "efectivo":
                pedir_monto_parcial()
            else:
                seleccion["valor"] = (tipo, 0.0)
                dialog.destroy()
                
        def pedir_monto_parcial():
            frm_btns.pack_forget()
            frm_parcial = ctk.CTkFrame(dialog, fg_color="transparent")
            frm_parcial.pack(fill="x", padx=40, pady=10)
            
            ctk.CTkLabel(frm_parcial, text="¿Cuánto va a abonar en efectivo?", font=("Segoe UI", 14), text_color=col_text).pack(pady=5)
            ent_monto = ctk.CTkEntry(frm_parcial, font=("Segoe UI", 16), justify="center")
            ent_monto.pack(fill="x", pady=10)
            ent_monto.insert(0, str(total_pago))
            ent_monto.focus_set()
            
            def confirmar_parcial(event=None):
                try:
                    m = float(ent_monto.get().replace(',', '.'))
                    if m < 0: raise ValueError
                    seleccion["valor"] = ("efectivo", m)
                    dialog.destroy()
                except ValueError:
                    messagebox.showerror("Error", "Ingrese un monto válido", parent=dialog)
            
            ent_monto.bind("<Return>", confirmar_parcial)
            ctk.CTkButton(frm_parcial, text="Confirmar", command=confirmar_parcial, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 14, "bold"), height=40).pack(pady=10, fill="x")
            
            btn_cancel.configure(text="Volver", command=lambda: [frm_parcial.pack_forget(), frm_btns.pack(fill="x", padx=40, pady=10), btn_cancel.configure(text="Cancelar", command=dialog.destroy)])

        opts = [("💵 Efectivo", "efectivo", "#dcfce7", "#065f46", "#bbf7d0"), 
                ("🏦 Transferencia/Tarjeta", "transferencia", "#dbeafe", "#1e3a8a", "#bfdbfe"),
                ("📋 Cuenta Corriente", "cuenta_corriente", "#fee2e2", "#991b1b", "#fecaca")]
        
        for txt, val, bgc, fgc, hov in opts:
            ctk.CTkButton(frm_btns, text=txt, fg_color=bgc, hover_color=hov, text_color=fgc, command=lambda v=val: set_pago(v), font=("Segoe UI", 14, "bold"), height=45).pack(pady=5, fill="x")

        btn_cancel = ctk.CTkButton(dialog, text="Cancelar", command=dialog.destroy, fg_color="#ef4444", hover_color="#dc2626", font=("Segoe UI", 13, "bold"), height=40)
        btn_cancel.pack(pady=15)
        win.wait_window(dialog); return seleccion["valor"]

    def _pedir_revision_precios(items_con_cambio: list[dict]) -> list[int]:
        """
        Muestra un diálogo donde el usuario ve Precio Actual → Precio Nuevo
        y elige qué productos actualizar. Devuelve lista de id_producto confirmados.
        """
        if not items_con_cambio:
            return []

        rev = ctk.CTkToplevel(win)
        rev.title("Revisión de Precios de Venta")
        rev.geometry("720x480")
        rev.configure(fg_color=col_bg)
        rev.resizable(False, False)
        rev.transient(win)
        rev.grab_set()

        ctk.CTkLabel(rev, text="📋 Revisión de Precios de Venta",
                     font=("Segoe UI", 17, "bold"), text_color=col_text).pack(pady=(20, 4))
        ctk.CTkLabel(rev, text="Seleccioná los productos cuyo precio de venta deseas actualizar.",
                     font=("Segoe UI", 11), text_color="#9ca3af").pack(pady=(0, 12))

        frm_tabla = ctk.CTkFrame(rev, fg_color=col_card, corner_radius=10,
                                  border_color=col_border, border_width=1)
        frm_tabla.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Encabezado
        hdr = ctk.CTkFrame(frm_tabla, fg_color="#1e3a8a", corner_radius=6)
        hdr.pack(fill="x", padx=8, pady=(8, 4))
        for txt, w in [("✓", 40), ("Producto", 220), ("Precio Actual", 110), ("Precio Nuevo", 110), ("Δ", 70)]:
            ctk.CTkLabel(hdr, text=txt, font=("Segoe UI", 11, "bold"),
                         text_color="white", width=w, anchor="w").pack(side="left", padx=4, pady=6)

        checks: list[tuple[tk.BooleanVar, int]] = []  # (var, id_producto)

        scroll_frame = ctk.CTkScrollableFrame(frm_tabla, fg_color="transparent", height=250)
        scroll_frame.pack(fill="both", expand=True, padx=8, pady=4)

        for it in items_con_cambio:
            var = tk.BooleanVar(value=True)  # marcado por defecto
            checks.append((var, it['id']))
            delta = it['precio_venta'] - it['precio_actual']
            color_delta = "#4ade80" if delta >= 0 else "#f87171"
            signo = "+" if delta >= 0 else ""

            fila = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            fila.pack(fill="x", pady=2)

            ctk.CTkCheckBox(fila, text="", variable=var, width=40,
                             fg_color="#10b981", hover_color="#059669").pack(side="left", padx=4)
            ctk.CTkLabel(fila, text=it['nombre'], font=("Segoe UI", 12),
                          text_color=col_text, width=220, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(fila, text=f"$ {it['precio_actual']:,.2f}",
                          font=("Segoe UI", 12), text_color="#9ca3af",
                          width=110, anchor="e").pack(side="left", padx=4)
            ctk.CTkLabel(fila, text=f"$ {it['precio_venta']:,.2f}",
                          font=("Segoe UI", 12, "bold"), text_color=col_text,
                          width=110, anchor="e").pack(side="left", padx=4)
            ctk.CTkLabel(fila, text=f"{signo}{delta:,.2f}",
                          font=("Segoe UI", 11, "bold"), text_color=color_delta,
                          width=70, anchor="e").pack(side="left", padx=4)

        resultado = {"ids": []}

        frm_btns = ctk.CTkFrame(rev, fg_color="transparent")
        frm_btns.pack(fill="x", padx=20, pady=(0, 16))

        def btn_todos():
            for v, _ in checks: v.set(True)

        def btn_ninguno():
            for v, _ in checks: v.set(False)

        def confirmar():
            resultado["ids"] = [pid for v, pid in checks if v.get()]
            rev.destroy()

        def omitir():
            resultado["ids"] = []
            rev.destroy()

        ctk.CTkButton(frm_btns, text="☑ Todos", command=btn_todos,
                       fg_color="#374151", hover_color="#4b5563",
                       font=("Segoe UI", 11), width=90, height=35).pack(side="left", padx=4)
        ctk.CTkButton(frm_btns, text="☐ Ninguno", command=btn_ninguno,
                       fg_color="#374151", hover_color="#4b5563",
                       font=("Segoe UI", 11), width=90, height=35).pack(side="left", padx=4)
        ctk.CTkButton(frm_btns, text="⏭ Omitir precios", command=omitir,
                       fg_color="#6b7280", hover_color="#4b5563",
                       font=("Segoe UI", 11, "bold"), width=130, height=35).pack(side="left", padx=10)
        ctk.CTkButton(frm_btns, text="✓ Aplicar selección", command=confirmar,
                       fg_color="#10b981", hover_color="#059669",
                       font=("Segoe UI", 13, "bold"), width=180, height=40).pack(side="right", padx=4)

        win.wait_window(rev)
        return resultado["ids"]

    def guardar_compra():
        from app.database.permisos import tiene_permiso
        if not tiene_permiso(usuario, 'registrar_compras'):
            messagebox.showwarning("Acceso Denegado", "No tienes permisos para registrar compras.", parent=win)
            return

        if not proveedor_sel or not carrito: 
            messagebox.showwarning("Aviso", "Añada productos al carrito antes de confirmar.", parent=win)
            return
        res_pago = pedir_medio_pago()
        if not res_pago: return
        medio, monto_ef = res_pago
        
        try:
            res = backend.registrar_compra_mixta(
                usuario['id_usuario'],
                proveedor_sel['id_proveedor'],
                carrito,
                medio_real=medio,
                monto_efectivo=monto_ef,
                usuario_actual=usuario
            )
            
            id_compra = res.get("id_compra")
            pago_exitoso = res.get("pago_exitoso")
            mensaje_error = res.get("mensaje_error_pago")
            
            if id_compra:
                # Construir lista de productos con cambio de precio para revisión
                items_revision = []
                for item in carrito:
                    try:
                        prod = backend.buscar_producto_por_id(item['id'])
                        if prod:
                            precio_actual = float(prod.get('precio_venta') or prod.get('precio') or 0.0)
                        else:
                            precio_actual = 0.0
                    except Exception:
                        precio_actual = 0.0
                    precio_nuevo = round(item['precio_venta'], 2)
                    if abs(precio_nuevo - precio_actual) > 0.01:
                        items_revision.append({
                            'id': item['id'],
                            'nombre': item['nombre'],
                            'precio_actual': precio_actual,
                            'precio_venta': precio_nuevo
                        })

                # Mostrar diálogo de revisión solo si hay cambios
                ids_a_actualizar = _pedir_revision_precios(items_revision) if items_revision else []

                for id_prod in ids_a_actualizar:
                    nuevo_precio = next((i['precio_venta'] for i in items_revision if i['id'] == id_prod), None)
                    if nuevo_precio is not None:
                        backend.actualizar_precio_producto(id_prod, nuevo_precio, id_usuario=usuario['id_usuario'])

                if not pago_exitoso and mensaje_error:
                    messagebox.showwarning("Pago Fallido", f"La compra se registró correctamente (Deuda), pero el pago falló:\n\n{mensaje_error}", parent=win)
                else:
                    messagebox.showinfo("Éxito", f"Compra #{id_compra} registrada correctamente.", parent=win)
                
                carrito.clear()
                proveedor_sel.clear()
                lbl_proveedor.configure(text="(Ninguno seleccionado)", text_color="#6b7280")
                repintar_tabla()
                stock_events.notificar_cambio_stock(); win.destroy()
            else:
                messagebox.showerror("Error", "No se pudo registrar la compra.", parent=win)
                
        except PermissionError as pe:
            messagebox.showerror("Acceso Denegado", str(pe), parent=win)
        except ValueError as ve:
            if "CAJA_CERRADA" in str(ve) or "TESORERIA_CERRADA" in str(ve):
                messagebox.showerror(
                    "⚠️ Caja Cerrada", 
                    "No se puede procesar el pago porque la caja está cerrada.\n\n"
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