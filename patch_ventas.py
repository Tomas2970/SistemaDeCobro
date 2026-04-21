import re
import os

filepath = r"d:\Documentos\GitHub\SistemaDeCobro\app\frontend\interfaz_venta.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Reemplazamos la definición UI de ui_venta desde "def ui_venta" hasta la LÓGICA
# Encontramos la función ui_venta(parent...
ui_start = content.find("def ui_venta(parent: tk.Misc, backend, usuario: dict) -> None:")
logic_start = content.find("# ================================================================\n    # LÓGICA - 🔥 BÚSQUEDA DINÁMICA CON POPUP FLOTANTE")

ui_nueva = """def ui_venta(parent: tk.Misc, backend, usuario: dict) -> None:
    import customtkinter as ctk

    for w in parent.winfo_children():
        if isinstance(w, ctk.CTkToplevel) and w.title() == "Punto de Venta - Supermercado Don Atilio":
            w.lift()
            w.focus_force()
            return

    win = ctk.CTkToplevel(parent)
    win.title("Punto de Venta - Supermercado Don Atilio")
    try: win.state('zoomed')
    except: win.geometry("1100x750")
    
    col_bg = "#f3f4f6" if ctk.get_appearance_mode() == "Light" else "#111827"
    col_card = "#ffffff" if ctk.get_appearance_mode() == "Light" else "#1f2937"
    col_border = "#e5e7eb" if ctk.get_appearance_mode() == "Light" else "#374151"
    font_title = ("Segoe UI", 15, "bold")
    font_normal = ("Segoe UI", 14)
    font_big = ("Segoe UI", 24, "bold")
    
    win.configure(fg_color=col_bg)

    # VALIDADORES
    def validar_len_30(t): return len(t) <= 30
    def validar_cantidad(t):
        if t == "": return True
        if len(t) > 5: return False
        import re
        return bool(re.match(r'^[0-9]{0,4}[.,]?[0-9]{0,3}$', t))
    
    vc_30 = (win.register(validar_len_30), '%P')
    vc_cantidad = (win.register(validar_cantidad), '%P')

    items = []
    cliente_sel = None
    total_venta = 0.0 

    # ==================================
    # ESTRUCTURA LAYOUT CTK
    # ==================================
    frm_header = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_width=1, border_color=col_border)
    frm_header.pack(fill="x", padx=25, pady=(25, 10))

    frm_inputs = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_width=1, border_color=col_border)
    frm_inputs.pack(fill="x", padx=25, pady=10)
    
    frm_footer = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_width=1, border_color=col_border)
    frm_footer.pack(side="bottom", fill="x", padx=25, pady=(10, 25))
    
    frm_lista = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_width=1, border_color=col_border)
    frm_lista.pack(fill="both", expand=True, padx=25, pady=10)

    # 1. HEADER CLIENTE
    ctk.CTkLabel(frm_header, text="👤 Cliente Actual:", font=font_title, text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white").pack(side="left", padx=20, pady=20)
    
    lbl_cliente = tk.Label(frm_header, text="(Consumidor Final)", bg=col_card, font=("Segoe UI", 12), fg="#6b7280")
    lbl_cliente.pack(side="left")
    
    def abrir_selector_cliente():
        nonlocal cliente_sel
        popup = tk.Toplevel(win)
        popup.title("Seleccionar Cliente")
        popup.geometry("700x550")
        popup.config(bg="#f4f4f8")
        
        frm_bus = tk.Frame(popup, bg="#f4f4f8", pady=10)
        frm_bus.pack(fill=tk.X, padx=15)
        tk.Label(frm_bus, text="🔎 Buscar cliente:", bg="#f4f4f8", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        var_bus = tk.StringVar()
        ent_bus = tk.Entry(frm_bus, textvariable=var_bus, font=("Segoe UI", 10), width=40)
        ent_bus.pack(side=tk.LEFT, padx=10)
        ent_bus.focus_set()
        
        frm_tree = tk.Frame(popup, bg="#f4f4f8")
        frm_tree.pack(fill=tk.BOTH, expand=True, padx=15)
        
        cols = ("ID", "Nombre", "DNI")
        tree_c = ttk.Treeview(frm_tree, columns=cols, show="headings", height=12)
        tree_c.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sc_c = ttk.Scrollbar(frm_tree, orient="vertical", command=tree_c.yview)
        sc_c.pack(side=tk.RIGHT, fill=tk.Y)
        tree_c.configure(yscrollcommand=sc_c.set)
        
        tree_c.heading("ID", text="ID"); tree_c.heading("Nombre", text="Nombre"); tree_c.heading("DNI", text="DNI")
        tree_c.column("ID", width=60); tree_c.column("Nombre", width=350); tree_c.column("DNI", width=150)
        
        todos_clis = backend.listar_clientes()
        
        def filtrar(*_):
            for i in tree_c.get_children(): tree_c.delete(i)
            q = var_bus.get().lower()
            for c in todos_clis:
                dni = c.get('dni') or "-"
                if q in c['nombre'].lower() or q in str(dni):
                    tree_c.insert("", tk.END, values=(c['id_cliente'], c['nombre'], dni))
            hijos = tree_c.get_children()
            if hijos: tree_c.selection_set(hijos[0])
        var_bus.trace_add("write", filtrar)
        filtrar()
        
        def seleccionar(event=None):
            nonlocal cliente_sel
            sel = tree_c.selection()
            if not sel: return
            cid = int(tree_c.item(sel[0], "values")[0])
            cliente_sel = next((c for c in todos_clis if c['id_cliente'] == cid), None)
            _upd_cliente()
            popup.destroy()
        
        tree_c.bind("<Double-1>", seleccionar)
        tree_c.bind("<Return>", seleccionar)
        
        fr_btns = tk.Frame(popup, bg="#f4f4f8", pady=15)
        fr_btns.pack(fill=tk.X)
        def limpiar_cliente():
            nonlocal cliente_sel
            cliente_sel = None
            _upd_cliente()
            popup.destroy()
        
        tk.Button(fr_btns, text="✓ Seleccionar", bg="#10b981", fg="white", command=seleccionar).pack(side=tk.LEFT, padx=5)
        def abrir_nuevo_cliente():
            if ui_crear_cliente:
                ui_crear_cliente(popup, backend)
                nonlocal todos_clis
                todos_clis = backend.listar_clientes()
                filtrar()
        tk.Button(fr_btns, text="➕ Nuevo", bg="#3b82f6", fg="white", command=abrir_nuevo_cliente).pack(side=tk.LEFT, padx=5)
        tk.Button(fr_btns, text="Consumidor Final", bg="#6b7280", fg="white", command=limpiar_cliente).pack(side=tk.LEFT, padx=5)
        
        configurar_navegacion_ventana(popup)
        popup.after(100, lambda: ent_bus.focus_set())
        popup.grab_set()

    def quitar_cliente():
        nonlocal cliente_sel
        cliente_sel = None
        _upd_cliente()

    def _upd_cliente():
        if cliente_sel:
            lbl_cliente.configure(text=f"{cliente_sel.get('nombre','')} (ID: {cliente_sel.get('id_cliente','')})", fg="#1f2937" if ctk.get_appearance_mode()=="Light" else "white", font=("Segoe UI", 12, "bold"))
        else:
            lbl_cliente.configure(text="(Consumidor Final)", fg="#6b7280", font=("Segoe UI", 12, "normal"))

    # Botones cliente
    ctk.CTkButton(frm_header, text="🔍 Cambiar", font=font_title, fg_color="#3b82f6", width=120, height=45, command=abrir_selector_cliente).pack(side="right", padx=(10, 20))
    btn_no_cli = ctk.CTkButton(frm_header, text="❌ Quitar", font=font_normal, fg_color="#ef4444", width=80, height=45, command=quitar_cliente)
    btn_no_cli.pack(side="right")

    # 2. INPUTS
    ctk.CTkLabel(frm_inputs, text="Cant.", font=font_title, text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white").pack(side="left", padx=(20, 10), pady=20)
    
    # Usamos tk.Entry puro para Cantidad porque CTkEntry tiene un bug feo de validación keystroke y focus en viejas lib.
    # Pero lo metemos en un frame simulado de CTk para que se vea lindo.
    frm_cant_border = ctk.CTkFrame(frm_inputs, fg_color="#f3f4f6", width=80, height=45, corner_radius=6)
    frm_cant_border.pack(side="left")
    frm_cant_border.pack_propagate(False)
    entry_cantidad = tk.Entry(frm_cant_border, font=font_big, justify="center", validate="key", validatecommand=vc_cantidad, bd=0, bg="#f3f4f6")
    entry_cantidad.insert(0, "1")
    entry_cantidad.pack(expand=True, fill="both", padx=2, pady=2)
    
    ctk.CTkLabel(frm_inputs, text="Código o Producto:", font=font_title, text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white").pack(side="left", padx=(30, 10))
    
    frm_prod_border = ctk.CTkFrame(frm_inputs, fg_color="#f3f4f6", height=45, corner_radius=6)
    frm_prod_border.pack(side="left", fill="x", expand=True)
    frm_prod_border.pack_propagate(False)
    entry_producto = tk.Entry(frm_prod_border, font=font_normal, validate="key", validatecommand=vc_30, bd=0, bg="#f3f4f6")
    entry_producto.pack(expand=True, fill="both", padx=10, pady=2)
    
    popup_sugerencias = None
    listbox_sugerencias = None
    sugerencias_activas = []
    _debounce_id = None
    
    btn_agregar = ctk.CTkButton(frm_inputs, text="+ Agregar", font=font_title, fg_color="#10b981", hover_color="#059669", width=120, height=45)
    btn_agregar.pack(side="left", padx=20)

    # 3. LISTA
    style = ttk.Style(win)
    style.theme_use('clam')
    style.configure("Modern.Treeview", background="white", foreground="#1f2937", rowheight=50, font=('Segoe UI', 13), borderwidth=0)
    style.configure("Modern.Treeview.Heading", background="#f8fafc", foreground="#475569", font=('Segoe UI', 12, 'bold'), borderwidth=0, padding=12)
    style.map('Modern.Treeview', background=[('selected', '#eff6ff')], foreground=[('selected', '#1e40af')])
    
    cols = ("ID", "Producto", "Precio", "Cant", "Subtotal")
    tree = ttk.Treeview(frm_lista, columns=cols, show="headings", style="Modern.Treeview")
    tree.column("ID", width=60, anchor="center")
    tree.column("Producto", width=500, anchor="w")
    tree.column("Precio", width=150, anchor="e")
    tree.column("Cant", width=100, anchor="center")
    tree.column("Subtotal", width=150, anchor="e")
    
    tree.heading("ID", text="ID")
    tree.heading("Producto", text="DESCRIPCIÓN")
    tree.heading("Precio", text="PRECIO UNIT.")
    tree.heading("Cant", text="CANT.")
    tree.heading("Subtotal", text="SUBTOTAL")
    
    vsb = ttk.Scrollbar(frm_lista, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    vsb.pack(side="right", fill="y", pady=5)

    # 4. FOOTER
    btn_cancelar = ctk.CTkButton(frm_footer, text="🗑️ Cancelar", fg_color="#ef4444", hover_color="#dc2626", font=font_title, width=150, height=55)
    btn_cancelar.pack(side="left", padx=20, pady=20)

    btn_quitar = ctk.CTkButton(frm_footer, text="➖ Quitar Ítem", fg_color="#f59e0b", hover_color="#d97706", font=font_title, width=150, height=55)
    btn_quitar.pack(side="left", padx=(0, 20), pady=20)

    btn_confirmar = ctk.CTkButton(frm_footer, text="💳 COBRAR (F12)", fg_color="#10b981", hover_color="#059669", font=font_big, width=250, height=65)
    btn_confirmar.pack(side="right", padx=20, pady=20)

    lbl_total_monto = ctk.CTkLabel(frm_footer, text="$ 0.00", font=("Segoe UI", 48, "bold"), text_color="#111827" if ctk.get_appearance_mode()=="Light" else "white")
    lbl_total_monto.pack(side="right", padx=30)
    
    ctk.CTkLabel(frm_footer, text="TOTAL:", font=("Segoe UI", 18, "bold"), text_color="#6b7280").pack(side="right", padx=0)

    """

content_nuevo = content[:ui_start] + ui_nueva + "\n    " + content[logic_start:]
content_nuevo = content_nuevo.replace("lbl_total_monto.config", "lbl_total_monto.configure")
content_nuevo = content_nuevo.replace("btn_confirmar.config", "btn_confirmar.configure")
content_nuevo = content_nuevo.replace("btn_cancelar.config", "btn_cancelar.configure")
content_nuevo = content_nuevo.replace("btn_quitar.config", "btn_quitar.configure")
content_nuevo = content_nuevo.replace("btn_agregar.config", "btn_agregar.configure")
content_nuevo = content_nuevo.replace("win.bind(\"<F5>\"", "win.bind(\"<F12>\"") 
# Aseguramos compatibilidad tkinter Entry vs CTkEntry: como usé tk.Entry embebido en ctk.CTkFrame, el logic anda perfecto.

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content_nuevo)
print("PATCH EJECUTADO")
