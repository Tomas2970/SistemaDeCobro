import re
import os

filepath = r"d:\Documentos\GitHub\SistemaDeCobro\app\frontend\interfaz_inventario.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

init_start = content.find("    def __init__(self, parent: tk.Misc, backend, usuario: dict):")
init_end = content.find("    def _on_close(self):")

nuevo_init = """    def __init__(self, parent: tk.Misc, backend, usuario: dict):
        import customtkinter as ctk
        self.backend = backend
        self.usuario = usuario
        self.win = ctk.CTkToplevel(parent)
        self.win.title("📦 Gestión de Inventario")
        self.win.geometry("1100x750")
        try: self.win.state('zoomed')
        except: pass
        self.can_ajustar_manual = puede_ajustar_inventario_manual(usuario)
        
        self.win.configure(fg_color="#f3f4f6" if ctk.get_appearance_mode()=="Light" else "#111827")
        
        self.productos_cache = []
        self.cat_map = {}
        self.var_filtrar_stock_bajo = tk.BooleanVar(value=False)

        style = ttk.Style(self.win)
        style.theme_use('clam')
        style.configure("Modern.Treeview", background="white", foreground="#1f2937", rowheight=45, font=('Segoe UI', 13), borderwidth=0)
        style.configure("Modern.Treeview.Heading", background="#f8fafc", foreground="#475569", font=('Segoe UI', 12, 'bold'), borderwidth=0, padding=12)
        style.map('Modern.Treeview', background=[('selected', '#eff6ff')], foreground=[('selected', '#1e40af')])

        self._crear_widgets()
        self._cargar_categorias_para_filtro()
        self.cargar_todo()

        stock_events.suscribir(self.cargar_todo)
        
        configurar_navegacion_ventana(self.win)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self.win.grab_set()
        self.win.after(100, lambda: self.entry_busqueda.focus_set())

"""

widgets_start = content.find("    def _crear_widgets(self):")
widgets_end = content.find("    def _cargar_categorias_para_filtro(self):")

nuevo_widgets = """    def _crear_widgets(self):
        import customtkinter as ctk
        col_card = "#ffffff" if ctk.get_appearance_mode()=="Light" else "#1f2937"
        col_border = "#e5e7eb" if ctk.get_appearance_mode()=="Light" else "#374151"
        font_title = ("Segoe UI", 15, "bold")
        font_normal = ("Segoe UI", 14)

        frm_header = ctk.CTkFrame(self.win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
        frm_header.pack(fill="x", padx=25, pady=(25, 10))
        
        ctk.CTkLabel(frm_header, text="🔍 Buscar Producto:", font=font_title, text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white").pack(side="left", padx=(20, 10), pady=20)
        self.var_busqueda = tk.StringVar()
        
        frm_bus_border = ctk.CTkFrame(frm_header, fg_color="#f3f4f6", height=45, width=300, corner_radius=6)
        frm_bus_border.pack(side="left", padx=5)
        frm_bus_border.pack_propagate(False)
        self.entry_busqueda = tk.Entry(frm_bus_border, textvariable=self.var_busqueda, font=font_normal, bd=0, bg="#f3f4f6")
        self.entry_busqueda.pack(expand=True, fill="both", padx=10, pady=2)
        self.var_busqueda.trace_add("write", self._filtrar_lista) 
        
        ctk.CTkLabel(frm_header, text="Categoría:", font=font_title, text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white").pack(side="left", padx=(30, 10))
        self.cb_categoria = ctk.CTkOptionMenu(frm_header, font=font_normal, fg_color="#f3f4f6", button_color="#e5e7eb", button_hover_color="#d1d5db", text_color="#1f2937", command=self._filtrar_lista, width=200, height=45)
        self.cb_categoria.pack(side="left", padx=5)
        
        ctk.CTkSwitch(frm_header, text="Stock Bajo / Crítico", variable=self.var_filtrar_stock_bajo, command=self._filtrar_lista, font=font_title, progress_color="#ef4444").pack(side="left", padx=40)
        
        ctk.CTkButton(frm_header, text="📊 Exportar CSV", font=("Segoe UI", 14, "bold"), fg_color="#f59e0b", hover_color="#d97706", width=160, height=45, command=self._exportar_csv).pack(side="right", padx=20)
        
        # 3. Footer (Empacado antes para anclar al fondo)
        frm_footer = ctk.CTkFrame(self.win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
        frm_footer.pack(fill="x", side="bottom", padx=25, pady=(10, 25))
        
        ctk.CTkButton(frm_footer, text="➕ Agregar / Editar Producto", font=("Segoe UI", 16, "bold"), fg_color="#10b981", hover_color="#059669", width=250, height=60, command=lambda: self._abrir_abm_productos(None)).pack(side="left", padx=20, pady=20)
        ctk.CTkButton(frm_footer, text="Cerrar", font=("Segoe UI", 15, "bold"), fg_color="#6b7280", hover_color="#4b5563", width=150, height=55, command=self.win.destroy).pack(side="right", padx=20, pady=20)

        # 2. Tabla (Treeview)
        frm_lista = ctk.CTkFrame(self.win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
        frm_lista.pack(fill="both", expand=True, padx=25, pady=10)
        
        cols = ("ID", "Nombre", "Categoría", "Stock", "Stock Min.", "Precio Venta")
        self.tree = ttk.Treeview(frm_lista, columns=cols, show="headings", style="Modern.Treeview")
        
        ys = ttk.Scrollbar(frm_lista, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ys.set)
        
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("ID", width=80, anchor="center")
        self.tree.column("Nombre", width=450)
        self.tree.column("Categoría", width=200)
        self.tree.column("Stock", width=120, anchor="center")
        self.tree.column("Stock Min.", width=120, anchor="center")
        self.tree.column("Precio Venta", width=150, anchor="e")

        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        ys.pack(side="right", fill="y", pady=5)

        self.tree.tag_configure('bajo', background='#fee2e2', foreground='#991b1b')
        self.tree.bind("<Double-1>", self._on_doble_clic)

"""

cat_start = content.find("    def _cargar_categorias_para_filtro(self):")
cat_end = content.find("    def cargar_todo(self):")

nuevo_cat = """    def _cargar_categorias_para_filtro(self):
        try:
            cats = self.backend.obtener_categorias()
            self.cat_map = {c['nombre']: c['id_categoria'] for c in cats}
            valores = ["(Todas)"] + list(self.cat_map.keys())
            self.cb_categoria.configure(values=valores)
            if valores: self.cb_categoria.set(valores[0])
        except Exception as e:
            pass

"""

if init_start != -1 and widgets_start != -1 and cat_start != -1:
    content_nuevo = content[:init_start] + nuevo_init + content[init_end:widgets_start] + nuevo_widgets + nuevo_cat + content[cat_end:]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content_nuevo)
    print("INVENTARIO PARCHEADO")
else:
    print("FALLO: No se encontraron los bloques")
