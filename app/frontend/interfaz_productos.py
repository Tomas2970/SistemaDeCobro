# app/frontend/interfaz_productos.py
from __future__ import annotations
import tkinter as tk
from app.frontend import custom_dialogs as messagebox
import re
import customtkinter as ctk
import tkinter.ttk as ttk

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

try:
    from app.frontend.theme_config import preparar_ventana, centrar_y_mostrar_ventana
except ImportError:
    def preparar_ventana(w): pass
    def centrar_y_mostrar_ventana(w): pass

try:
    from app.frontend.custom_dialogs import mostrar_toast_centrado
except ImportError:
    def mostrar_toast_centrado(parent, mensaje, **kwargs):
        messagebox.showinfo("Notificación", mensaje, parent=parent)


from app.frontend.stock_event_manager import stock_events

def ui_productos(parent: tk.Misc, backend, usuario: dict, id_producto_a_cargar: int | None = None, callback_on_save=None) -> None:
    win = ctk.CTkToplevel(parent)
    preparar_ventana(win)
    win.title("Gestión de Productos (ABM)")
    win.geometry("680x680")
    col_bg = "#f3f4f6" if ctk.get_appearance_mode()=="Light" else "#111827"
    col_card = "#ffffff" if ctk.get_appearance_mode()=="Light" else "#1f2937"
    col_border = "#e5e7eb" if ctk.get_appearance_mode()=="Light" else "#374151"
    
    col_input_bg = "#f9fafb" if ctk.get_appearance_mode() == "Light" else "#374151"
    col_input_fg = "#1f2937" if ctk.get_appearance_mode() == "Light" else "#f9fafb"
    col_text = "#374151" if ctk.get_appearance_mode()=="Light" else "white"
    
    win.resizable(True, True)

    def validar_len_30(t): return len(t) <= 30
    def validar_len_60(t): return len(t) <= 60
    
    def validar_decimal(t):
        from app.frontend.validaciones_ui import ValidadoresTeclado
        return len(t) <= 10 and ValidadoresTeclado.decimal(t)
        
    def validar_entero(t):
        from app.frontend.validaciones_ui import ValidadoresTeclado
        return len(t) <= 10 and ValidadoresTeclado.solo_numeros(t)

    vc_30 = (win.register(validar_len_30), '%P')
    vc_60 = (win.register(validar_len_60), '%P')
    vc_dec = (win.register(validar_decimal), '%P')
    vc_int = (win.register(validar_entero), '%P')

    frm_busqueda = ctk.CTkFrame(win, fg_color=col_card, corner_radius=8, border_color=col_border, border_width=1)
    frm_busqueda.pack(fill="x", padx=15, pady=(15, 5)) 
    
    ctk.CTkLabel(frm_busqueda, text="🔍 Buscar (ID/Cód/Nom):", font=("Segoe UI", 13, "bold"), text_color=col_text).pack(side="left", padx=10, pady=10)
    var_token = tk.StringVar()
    ent_busqueda = ctk.CTkEntry(frm_busqueda, textvariable=var_token, font=("Segoe UI", 12), height=35, width=220)
    ent_busqueda.configure(validate="key", validatecommand=vc_30)
    ent_busqueda.pack(side="left", padx=10, pady=10)
    
    body = ctk.CTkFrame(win, fg_color=col_card, corner_radius=8, border_color=col_border, border_width=1)
    body.pack(fill="both", expand=True, padx=15, pady=5)
    body.columnconfigure(1, weight=1)

    row = 0
    def add_row(lbl: str, widget, pady=6):
        nonlocal row
        if lbl:
            ctk.CTkLabel(body, text=lbl, font=("Segoe UI", 12, "bold"), text_color=col_text).grid(row=row, column=0, sticky="e", padx=(15, 10), pady=pady)
        widget.grid(row=row, column=1, sticky="w", padx=10, pady=pady)
        row += 1

    var_id = tk.StringVar()
    
    var_nombre = tk.StringVar()
    ent_nombre = ctk.CTkEntry(body, textvariable=var_nombre, font=("Segoe UI", 12), width=400, height=36)
    ent_nombre.configure(validate="key", validatecommand=vc_60)
    add_row("Nombre del Producto:", ent_nombre, pady=(15, 6))
    
    combo_cat = ctk.CTkOptionMenu(body, width=400, height=36, font=("Segoe UI", 12), fg_color=col_input_bg, text_color=col_input_fg, button_color="#4b5563", button_hover_color="#374151")
    add_row("Categoría:", combo_cat)
    combo_cat.ids = []
    
    var_precio = tk.StringVar(value="0.00")
    ent_precio = ctk.CTkEntry(body, textvariable=var_precio, font=("Segoe UI", 12), width=150, height=36, justify="left")
    ent_precio.configure(validate="key", validatecommand=vc_dec)
    add_row("Precio Venta ($):", ent_precio)
    
    var_es_pesable = tk.BooleanVar(value=False)
    chk_pesable = ctk.CTkSwitch(body, text="Es pesable (kg)", variable=var_es_pesable, font=("Segoe UI", 12), progress_color="#3b82f6")
    add_row("", chk_pesable)
    
    categorias_data = []
    cat_map = {}
    
    def cargar_categorias_memoria():
        nonlocal categorias_data, cat_map
        categorias_data = backend.obtener_categorias()
        cat_map = {c['nombre']: c for c in categorias_data}
        nombres = [c['nombre'] for c in categorias_data]
        if nombres:
            combo_cat.configure(values=nombres)
            combo_cat.set(nombres[0])
        combo_cat.ids = [c['id_categoria'] for c in categorias_data]

    def al_cambiar_categoria(val=None, from_load=False):
        nombre_cat = combo_cat.get()
        datos_cat = cat_map.get(nombre_cat)
        if datos_cat:
            es_pesable_default = bool(datos_cat.get('es_pesable_default', False))
            if not from_load:
                var_es_pesable.set(es_pesable_default)
            if es_pesable_default:
                chk_pesable.configure(state="normal", text="Es pesable (kg)")
            else:
                chk_pesable.configure(state="disabled", text="Es pesable (Bloqueado)")
        else:
            chk_pesable.configure(state="normal", text="Es pesable (kg)")

    combo_cat.configure(command=al_cambiar_categoria)

    var_cod = tk.StringVar()
    ent_cod = ctk.CTkEntry(body, textvariable=var_cod, font=("Segoe UI", 12), width=400, height=36)
    ent_cod.configure(validate="key", validatecommand=vc_30)
    add_row("Código de Barras:", ent_cod)
    
    var_stock = tk.StringVar(value="0")
    ent_stock = ctk.CTkEntry(body, textvariable=var_stock, font=("Segoe UI", 12), width=150, height=36, justify="left")
    ent_stock.configure(validate="key", validatecommand=vc_dec)
    add_row("Stock Actual:", ent_stock)
    
    var_stock_min = tk.StringVar(value="5")
    ent_stock_min = ctk.CTkEntry(body, textvariable=var_stock_min, font=("Segoe UI", 12), width=150, height=36, justify="left")
    ent_stock_min.configure(validate="key", validatecommand=vc_int)
    add_row("Stock Mínimo:", ent_stock_min)

    var_asignar_prov = tk.BooleanVar(value=False)
    chk_asignar = ctk.CTkSwitch(body, text="Asignar a empresas proveedoras al guardar", variable=var_asignar_prov, font=("Segoe UI", 12, "bold"), progress_color="#10b981")
    chk_asignar.grid(row=row, column=1, sticky="w", padx=10, pady=(15, 10))
    row += 1

    def abrir_popup_asignacion(pid, nombre_prod):
        pop = ctk.CTkToplevel(win)
        preparar_ventana(pop)
        pop.title(f"Asignar Empresas - {nombre_prod}")
        pop.geometry("600x500") 
        
        frm_bus = ctk.CTkFrame(pop, fg_color=col_card, corner_radius=8, border_color=col_border, border_width=1)
        frm_bus.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(frm_bus, text="🔎 Buscar Empresa:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(15, 10), pady=10)
        var_filtro = tk.StringVar()
        ent_filtro = ctk.CTkEntry(frm_bus, textvariable=var_filtro, font=("Segoe UI", 12), width=250, height=35, placeholder_text="Filtrar...")
        ent_filtro.pack(side="left", padx=5)
        ent_filtro.focus_set()
        
        # --- Botones al fondo (se empaquetan ANTES del tree para reservar espacio) ---
        fr_btns = ctk.CTkFrame(pop, fg_color="transparent")
        fr_btns.pack(fill="x", side="bottom", padx=15, pady=(5, 15))
        
        all_provs = backend.obtener_proveedores()
        proveedores_seleccionados = set() 
        
        def guardar_asignaciones():
            if not proveedores_seleccionados:
                messagebox.showwarning("Atención", "Seleccione al menos una empresa.", parent=pop)
                return
            count = 0
            for p_id in proveedores_seleccionados:
                if backend.asignar_producto_a_proveedor(p_id, pid): count += 1
            messagebox.showinfo("Listo", f"Vinculado a {count} empresa(s).", parent=pop)
            pop.destroy()
        
        ctk.CTkButton(fr_btns, text="Cancelar", command=pop.destroy, fg_color="#ef4444", hover_color="#dc2626", font=("Segoe UI", 12, "bold"), width=120, height=40).pack(side="left", padx=10)
        ctk.CTkButton(fr_btns, text="✓ Guardar Asignación", command=guardar_asignaciones, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 13, "bold"), width=180, height=40).pack(side="right", padx=10)
        
        # --- Tree (se empaqueta DESPUÉS de los botones para que ocupe el espacio restante) ---
        frm_tree = ctk.CTkFrame(pop, fg_color=col_card, corner_radius=8, border_color=col_border, border_width=1)
        frm_tree.pack(fill="both", expand=True, padx=15, pady=10)
        try:
            from app.frontend.theme_config import configurar_estilo_treeview
            configurar_estilo_treeview()
        except ImportError:
            pass
        
        cols = ("ID", "Empresa", "CUIT")
        tree_p = ttk.Treeview(frm_tree, columns=cols, show="headings", style="Modern.Treeview")
        
        sc_p = ctk.CTkScrollbar(frm_tree, command=tree_p.yview)
        sc_p.pack(side="right", fill="y", padx=(0, 5), pady=5)
        tree_p.configure(yscrollcommand=sc_p.set)
        
        tree_p.heading("ID", text="ID")
        tree_p.heading("Empresa", text="Empresa")
        tree_p.heading("CUIT", text="CUIT")
        tree_p.column("ID", width=0, stretch=False)
        tree_p.column("Empresa", width=250)
        tree_p.column("CUIT", width=120, anchor="center")
        
        tree_p.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        tree_p.tag_configure('seleccionado', background='#dbeafe', foreground='#1e40af')
        
        def filtrar_lista(*args):
            for i in tree_p.get_children(): 
                tree_p.delete(i)
            query = var_filtro.get().lower()
            for p in all_provs:
                if not p.get('activo', True): continue
                empresa = p.get('empresa', '')
                cuit = p.get('cuit') or "-"
                if query in empresa.lower() or query in str(cuit):
                    tag = 'seleccionado' if p['id_proveedor'] in proveedores_seleccionados else ''
                    prefijo = "✓ " if p['id_proveedor'] in proveedores_seleccionados else ""
                    tree_p.insert("", tk.END, values=(p['id_proveedor'], f"{prefijo}{empresa}", cuit), tags=(tag,))
        
        var_filtro.trace_add("write", filtrar_lista)
        filtrar_lista()
        
        def toggle_seleccion(event=None):
            sel = tree_p.selection()
            if not sel: return
            p_id = int(tree_p.item(sel[0], "values")[0])
            if p_id in proveedores_seleccionados: proveedores_seleccionados.remove(p_id)
            else: proveedores_seleccionados.add(p_id)
            filtrar_lista()
        
        tree_p.bind("<Button-1>", lambda e: win.after(10, toggle_seleccion))
        
        configurar_navegacion_ventana(pop)
        centrar_y_mostrar_ventana(pop)
        pop.grab_set()
        win.wait_window(pop)

    actions = ctk.CTkFrame(win, fg_color="transparent")
    actions.pack(fill="x", side="bottom", padx=15, pady=(5, 15)) 
    
    def limpiar():
        var_id.set(""); var_nombre.set(""); var_precio.set("0.00")
        var_stock.set("0"); var_stock_min.set("5"); var_cod.set("")
        var_es_pesable.set(False); chk_pesable.configure(state="normal") 
        var_asignar_prov.set(False)
        valores = combo_cat.cget("values")
        if valores and isinstance(valores, list) and len(valores) > 0:
            combo_cat.set(valores[0])
            al_cambiar_categoria(None, from_load=False)
        ent_nombre.focus_set()

    def buscar():
        token = var_token.get().strip()
        if not token: return
        prod = backend.buscar_producto_por_codigo_barras(token) or \
               backend.buscar_producto_por_id(token) or \
               (backend.buscar_producto_por_nombre(token)[0] if backend.buscar_producto_por_nombre(token) else None)
        if prod:
            var_id.set(str(prod.get('id_producto')))
            var_nombre.set(prod.get('nombre'))
            var_precio.set(f"{float(prod.get('precio')): .2f}")
            stock_val = float(prod.get('stock'))
            es_pesable = bool(prod.get('es_pesable'))
            var_stock.set(f"{int(stock_val)}" if not es_pesable else f"{stock_val:.3f}")
            var_stock_min.set(str(prod.get('stock_minimo')))
            var_cod.set(prod.get('codigo_barras') or "")
            var_es_pesable.set(es_pesable)
            cat_name = prod.get('nombre_categoria')
            valores = combo_cat.cget("values")
            if valores and cat_name in valores:
                combo_cat.set(cat_name)
                al_cambiar_categoria(None, from_load=True) 
        else: messagebox.showinfo("Info", "No encontrado.", parent=win)

    def guardar():
        try:
            nombre = var_nombre.get().strip()
            precio = float(var_precio.get() or 0)
            stock = float(var_stock.get() or 0)
            minimo = int(var_stock_min.get() or 0)
            codigo = var_cod.get().strip() or None

            from app.frontend.validaciones_ui import ValidadorFormulario
            ok, msg = ValidadorFormulario.validar_campos({
                'Nombre del Producto': (nombre, 'nombre_empresa', True),
                'Precio Venta': (str(precio), 'monto', True)
            })
            if not ok:
                messagebox.showwarning("Campo inválido", msg, parent=win)
                return
            
            cat_actual = combo_cat.get()
            valores = combo_cat.cget("values") or []
            if cat_actual not in valores:
                messagebox.showwarning("Campo requerido", "Debe seleccionar una categoría.", parent=win)
                return
            idx = valores.index(cat_actual)

            cat_id = combo_cat.ids[idx]
            pid = int(var_id.get()) if var_id.get().isdigit() else None
            es_creacion = (pid is None)

            if pid:
                backend.actualizar_producto(
                    id_producto=pid, 
                    nombre=nombre, 
                    id_categoria=cat_id, 
                    precio=precio, 
                    codigo_barras=codigo, 
                    es_pesable=var_es_pesable.get(), 
                    id_usuario=usuario.get('id_usuario')
                )
                backend.actualizar_inventario_absoluto(pid, stock, minimo, usuario.get('id_usuario'))
                res_id = pid
            else:
                res_id = backend.crear_producto_completo(nombre, cat_id, codigo, precio, stock, minimo, var_es_pesable.get(), usuario.get('id_usuario'))

            if not res_id:
                messagebox.showerror("Error", "No se pudo guardar el producto.", parent=win)
                return

            mostrar_toast_centrado(win, f"✅ Producto '{nombre}' guardado correctamente.")
            stock_events.notificar_cambio_stock()
            if res_id and var_asignar_prov.get(): abrir_popup_asignacion(res_id, nombre)
            if es_creacion: limpiar()
            if callback_on_save: callback_on_save()
        except Exception as e: messagebox.showerror("Error", str(e), parent=win)
            
    ctk.CTkButton(frm_busqueda, text="🔍 Buscar", command=buscar, font=("Segoe UI", 12, "bold"), width=100, height=35).pack(side="left", padx=10)
    ctk.CTkButton(frm_busqueda, text="Nuevo", command=limpiar, fg_color="#6b7280", font=("Segoe UI", 12, "bold"), width=100, height=35).pack(side="left", padx=5)
    
    ctk.CTkButton(actions, text="Cancelar", command=win.destroy, fg_color="#ef4444", hover_color="#dc2626", font=("Segoe UI", 13, "bold"), width=150, height=45).pack(side="left", padx=10)
    ctk.CTkButton(actions, text="✓ Guardar", command=guardar, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 15, "bold"), width=200, height=45).pack(side="right", padx=10)

    cargar_categorias_memoria()
    if id_producto_a_cargar: var_token.set(str(id_producto_a_cargar)); buscar()
    else: al_cambiar_categoria(None)
    configurar_navegacion_ventana(win, confirmar_cierre=False)
    centrar_y_mostrar_ventana(win)
    win.grab_set()