# app/frontend/interfaz_gestion_proveedores.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, Toplevel
from app.frontend import custom_dialogs as messagebox
from app.frontend.interfaz_crear_proveedor import ui_crear_proveedor

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
    from app.frontend.componentes_ui import EntryDecimal
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass
    EntryDecimal = None  # Se resolverá al importar ctk dentro de la función

try:
    from app.frontend.interfaz_asignar_productos import ui_asignar_productos
except ImportError:
    ui_asignar_productos = None

try:
    from app.frontend.theme_config import preparar_ventana, centrar_y_mostrar_ventana
except ImportError:
    def preparar_ventana(w): pass
    def centrar_y_mostrar_ventana(w): pass

def _fmt_mon(val):
    try: return f"$ {float(val):,.2f}"
    except: return "$ 0.00"

def ui_gestion_proveedores(parent: tk.Misc, backend, usuario_actual: dict = None): 
    import customtkinter as ctk
    from app.frontend.theme_config import get_color, configurar_estilo_treeview
    
    # 🔥 CARGA DE ESTILOS Y COLORES
    configurar_estilo_treeview()
    col_bg = get_color("bg_root")
    col_card = get_color("bg_surface")
    col_text = get_color("text_primary")
    col_input_bg = "#374151"
    col_input_fg = "#ffffff"
    col_border = "#2d3748"

    win = ctk.CTkToplevel(parent)
    preparar_ventana(win)
    win.title("Gestión de Empresas Proveedoras")
    win.geometry("1280x650") 
    win.resizable(True, True)
    win.minsize(950, 550)

    # --- BARRA DE BÚSQUEDA ---
    frame_busqueda = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
    frame_busqueda.pack(pady=(20,5), padx=25, fill="x")
    
    ctk.CTkLabel(frame_busqueda, text="🔍 Buscar Empresa/CUIT:", font=("Segoe UI", 13, "bold"), text_color=col_text).pack(side="left", padx=15, pady=15)
    var_busqueda = tk.StringVar()
    
    entry_busqueda = ctk.CTkEntry(frame_busqueda, textvariable=var_busqueda, font=("Segoe UI", 12), width=350, height=38, placeholder_text="Empresa o CUIT...")
    entry_busqueda.pack(side="left", padx=10, pady=15)

    # --- FRAME DE BOTONES (Empacado al fondo primero para evitar que se achique) ---
    frame_botones = ctk.CTkFrame(win, fg_color="transparent")
    frame_botones.pack(side=tk.BOTTOM, pady=(0, 20), fill="x", padx=25)

    frame_lista = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
    frame_lista.pack(pady=10, padx=25, fill="both", expand=True)

    # 🔥 COLUMNAS FILTRADAS: Solo datos de Empresa
    cols = ["ID", "Empresa", "CUIT", "Teléfono", "Email", "Dirección", "Saldo", "Activo"]
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", height=7, style="Modern.Treeview")
    
    ys = ctk.CTkScrollbar(frame_lista, command=tree.yview)
    ys.pack(side="right", fill="y", padx=(0, 5), pady=5)
    tree.configure(yscrollcommand=ys.set)
    tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    
    for c in cols: tree.heading(c, text=c)
    
    tree.column("ID", width=0, minwidth=0, stretch=False)
    tree.configure(displaycolumns=[c for c in cols if c != "ID"])
    tree.column("Empresa", width=200, minwidth=180, stretch=True) 
    tree.column("CUIT", width=115, minwidth=110, stretch=False)
    tree.column("Teléfono", width=105, minwidth=100, stretch=False)
    tree.column("Email", width=170, minwidth=150, stretch=True)
    tree.column("Dirección", width=160, minwidth=140, stretch=True)
    tree.column("Saldo", width=130, minwidth=120, stretch=False)
    tree.column("Activo", width=80, minwidth=75, stretch=False)
    
    tree.tag_configure("deuda", foreground="#f87171")
    tree.tag_configure("favor", foreground="#4ade80")
    tree.tag_configure("cero", foreground="#f9fafb")

    var_mostrar_inactivos = tk.BooleanVar(value=False)
    todos_proveedores = []

    def cargar_datos():
        nonlocal todos_proveedores
        if not win.winfo_exists():
            return
        try:
            incluir_inactivos = var_mostrar_inactivos.get()
            todos_proveedores = backend.obtener_proveedores(incluir_inactivos=incluir_inactivos)
            todos_proveedores.sort(key=lambda x: float(x.get('saldo', 0.0)))
            filtrar_lista()
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando: {e}", parent=win)
            
    def filtrar_lista(*args):
        if not win.winfo_exists():
            return
        query = var_busqueda.get().lower().strip()
        for i in tree.get_children(): tree.delete(i)
        
        for p in todos_proveedores:
            empresa = str(p.get('empresa', '')).lower()
            cuit = str(p.get('cuit', '')).lower()
            
            if query in empresa or query in cuit:
                estado = "SI" if p.get('activo') else "NO"
                saldo = float(p.get('saldo', 0.0))
                
                tag = "cero"
                if saldo < -0.01: tag = "deuda"
                elif saldo > 0.01: tag = "favor"
                
                saldo_vis = f"- $ {abs(saldo):,.2f}" if saldo < 0 else f"+ $ {saldo:,.2f}"
                if abs(saldo) < 0.01: saldo_vis = "$ 0.00"

                tree.insert("", tk.END, values=[
                    p.get('id_proveedor', ''), 
                    p.get('empresa', ''),
                    p.get('cuit', '-'),
                    p.get('telefono', ''), 
                    p.get('email', ''), 
                    p.get('direccion', '-'),
                    saldo_vis, 
                    estado
                ], tags=(tag,))

    var_busqueda.trace_add("write", filtrar_lista)

    def recargar_lista_callback():
        win.after(100, cargar_datos)

    def accion_nuevo():
        ui_crear_proveedor(win, backend, callback_on_save=recargar_lista_callback)

    def abrir_editar_proveedor():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una empresa.", parent=win)
            return
        item = tree.item(sel[0], "values")
        ui_crear_proveedor(win, backend, id_proveedor_a_editar=int(item[0]), callback_on_save=recargar_lista_callback)
    
    tree.bind("<Double-1>", lambda e: abrir_editar_proveedor())
    
    def abrir_pagar_deuda():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una empresa.", parent=win)
            return
        item_vals = tree.item(sel[0], "values")
        id_prov = int(item_vals[0])
        nombre_empresa = item_vals[1]
        
        pop = ctk.CTkToplevel(win)
        preparar_ventana(pop)
        pop.title(f"Registrar Pago a {nombre_empresa}")
        pop.geometry("400x450")
        pop.transient(win)
        
        ctk.CTkLabel(pop, text=f"Empresa: {nombre_empresa}", font=("Segoe UI", 14, "bold")).pack(pady=20)
        ctk.CTkLabel(pop, text="Monto a abonar ($):", font=("Segoe UI", 12)).pack(pady=2)
        _EntryDecimal = EntryDecimal if EntryDecimal else ctk.CTkEntry
        ent_monto = _EntryDecimal(pop, font=("Segoe UI", 14), width=180, height=40, justify="center")
        ent_monto.pack(pady=5)
        ent_monto.focus_set()
        
        ctk.CTkLabel(pop, text="Medio de Pago:", font=("Segoe UI", 12)).pack(pady=(10, 2))
        cb_medio = ctk.CTkOptionMenu(pop, values=["efectivo", "transferencia", "cheque"], width=180, height=35)
        cb_medio.set("efectivo")
        cb_medio.pack(pady=5)
        
        ctk.CTkLabel(pop, text="Observación:", font=("Segoe UI", 12)).pack(pady=(10, 2))
        ent_obs = ctk.CTkEntry(pop, width=250, height=35, placeholder_text="Opcional...")
        ent_obs.pack(pady=5)
        
        def confirmar_pago():
            try:
                monto = float(ent_monto.get())
                if monto <= 0: raise ValueError("Monto debe ser positivo")
                uid = usuario_actual['id_usuario'] if usuario_actual else 1
                backend.registrar_pago_proveedor(id_prov, monto, cb_medio.get(), uid, ent_obs.get())
                messagebox.showinfo("Éxito", "Pago registrado.", parent=pop)
                pop.destroy()
                cargar_datos()
            except ValueError as ve:
                if "CAJA_CERRADA" in str(ve):
                    messagebox.showerror(
                        "⚠️ Caja Cerrada", 
                        "No se puede procesar el pago porque la caja está cerrada.\n\n"
                        "Por favor, abra la caja antes de continuar.", 
                        parent=pop
                    )
                else:
                    messagebox.showerror("Error", str(ve), parent=pop)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=pop)
                
        ctk.CTkButton(pop, text="✓ CONFIRMAR PAGO", command=confirmar_pago, fg_color="#10b981", hover_color="#059669", 
                      font=("Segoe UI", 13, "bold"), height=45).pack(pady=20, padx=40, fill="x")
        configurar_navegacion_ventana(pop)
        centrar_y_mostrar_ventana(pop)
        pop.grab_set()

    def abrir_asignar_productos():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una empresa.", parent=win)
            return
        item = tree.item(sel[0], "values")
        if ui_asignar_productos:
            ui_asignar_productos(win, backend, int(item[0]), str(item[1]))

    def desactivar_proveedor():
        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        if messagebox.askyesno("Confirmar", f"¿Desactivar la empresa '{item[1]}'?", parent=win):
            try:
                if backend.eliminar_proveedor_logico(int(item[0])):
                    cargar_datos()
            except Exception as e:
                messagebox.showerror("Error", f"{e}", parent=win)

    def activar_proveedor():
        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        if messagebox.askyesno("Confirmar", f"¿Activar la empresa '{item[1]}'?", parent=win):
            try:
                if backend.activar_proveedor_logico(int(item[0])):
                    cargar_datos()
            except Exception as e:
                messagebox.showerror("Error", f"{e}", parent=win)



    ctk.CTkButton(frame_botones, text="➕ Nueva Empresa", command=accion_nuevo, fg_color="#16a34a", hover_color="#15803d", font=("Segoe UI", 13, "bold"), width=160, height=45).pack(side=tk.LEFT, padx=10)
    ctk.CTkButton(frame_botones, text="💳 PAGAR", command=abrir_pagar_deuda, fg_color="#0ea5e9", hover_color="#0284c7", font=("Segoe UI", 13, "bold"), width=120, height=45).pack(side=tk.LEFT, padx=5)
    ctk.CTkButton(frame_botones, text="📦 Productos", command=abrir_asignar_productos, fg_color="#7c3aed", hover_color="#6d28d9", font=("Segoe UI", 13), width=120, height=45).pack(side=tk.LEFT, padx=5)
    
    # CHECKBOX, LIMPIAR Y CERRAR
    ctk.CTkCheckBox(frame_botones, text="Ver Inactivas", variable=var_mostrar_inactivos, font=("Segoe UI", 12), command=cargar_datos).pack(side=tk.LEFT, padx=15)

    def limpiar_filtros():
        var_busqueda.set('')
        if var_mostrar_inactivos.get():
            var_mostrar_inactivos.set(False)
        cargar_datos()

    ctk.CTkButton(frame_botones, text="🧹 Limpiar", command=limpiar_filtros, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 11, "bold"), width=100, height=35).pack(side=tk.LEFT, padx=10)
    
    ctk.CTkButton(frame_botones, text="Cerrar", command=win.destroy, fg_color="#4b5563", hover_color="#374151", font=("Segoe UI", 13, "bold"), width=110, height=45).pack(side=tk.RIGHT, padx=10)

    cargar_datos()
    entry_busqueda.focus_set()
    configurar_navegacion_ventana(win)
    win.transient(parent)
    centrar_y_mostrar_ventana(win)
    win.grab_set()