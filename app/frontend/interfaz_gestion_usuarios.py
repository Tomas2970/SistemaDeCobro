# app/frontend/interfaz_gestion_usuarios.py
# 🔥 MANTENIENDO TU DISEÑO ORIGINAL Y TUS FUNCIONES (DOBLE CLIC, BUSCADOR, ETC)

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from app.frontend.interfaz_crear_usuario import ui_crear_usuario

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

def ui_gestion_usuarios(parent: tk.Misc, backend, usuario_actual: dict = None):
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
    win.title("Gestión de Usuarios")
    win.geometry("1150x680") 
    win.configure(fg_color=col_bg)
    win.resizable(False, False)

    # BARRA DE BÚSQUEDA
    frame_busqueda = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
    frame_busqueda.pack(pady=(20, 5), padx=25, fill="x")
    
    ctk.CTkLabel(frame_busqueda, text="🔍 Buscar Usuario:", font=("Segoe UI", 13, "bold"), text_color=col_text).pack(side="left", padx=15, pady=15)
    var_busqueda = tk.StringVar()
    entry_busqueda = ctk.CTkEntry(frame_busqueda, textvariable=var_busqueda, font=("Segoe UI", 13), width=350, height=40, placeholder_text="Nombre de usuario o rol...")
    entry_busqueda.pack(side="left", padx=10, pady=15)

    # TREEVIEW
    frame_lista = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
    frame_lista.pack(pady=10, padx=25, fill="both", expand=True)

    cols = ["ID", "Nombre", "Rol", "Fecha Creación", "Último Acceso", "Activo"]
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", height=8, style="Modern.Treeview")
    tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    ys.pack(side="right", fill="y")
    tree.configure(yscrollcommand=ys.set)
    
    for c in cols: tree.heading(c, text=c)
    
    tree.column("ID", width=0, stretch=False)
    tree.column("Nombre", width=200)
    tree.column("Rol", width=150)
    tree.column("Fecha Creación", width=180, anchor="center")
    tree.column("Último Acceso", width=180, anchor="center")
    tree.column("Activo", width=80, anchor="center")
    tree.configure(displaycolumns=[c for c in cols if c != "ID"])

    tree.tag_configure("activo", foreground="#16a34a")
    tree.tag_configure("inactivo", foreground="#dc2626")
    tree.tag_configure("sin_acceso", foreground="#9ca3af")

    var_mostrar_inactivos = tk.BooleanVar(value=False)
    todos_usuarios = []

    # FUNCIÓN DE FORMATEO (La que tenías vos)
    def formatear_fecha(fecha_obj):
        if not fecha_obj or str(fecha_obj) in ["None", "-", ""]:
            return "-"
        try:
            from datetime import datetime
            if isinstance(fecha_obj, datetime):
                return fecha_obj.strftime("%d/%m/%Y %H:%M")
            fecha_str = str(fecha_obj)
            if "T" in fecha_str:
                dt = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(fecha_str[:19], "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return str(fecha_obj)[:16]

    def cargar_datos():
        nonlocal todos_usuarios
        for i in tree.get_children(): 
            tree.delete(i)
        
        try:
            # 🔥 CORRECCIÓN CLAVE: Usamos backend.obtener_usuarios_con_rol(backend) 
            # para pasarle la instancia que pide tu nueva función del DB.py
            users = backend.obtener_usuarios_con_rol()
            
            mostrar_todos = var_mostrar_inactivos.get()
            todos_usuarios = users

            for u in users:
                es_activo = u.get('activo')
                if not mostrar_todos and not es_activo:
                    continue

                activo_txt = "✓ SI" if es_activo else "✗ NO"
                fecha_creacion = formatear_fecha(u.get('fecha_creacion'))
                ultimo_acceso = formatear_fecha(u.get('ultimo_acceso'))
                
                tag = "activo" if es_activo else "inactivo"
                if es_activo and ultimo_acceso == "-": tag = "sin_acceso"
                
                tree.insert("", tk.END, values=[
                    u.get('id_usuario'),
                    u.get('nombre'),
                    u.get('rol_nombre'),
                    fecha_creacion if fecha_creacion != "-" else "No disponible",
                    ultimo_acceso if ultimo_acceso != "-" else "Nunca",
                    activo_txt
                ], tags=(tag,))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar: {e}", parent=win)

    # LÓGICA DE FILTRADO (La que tenías vos)
    def filtrar_lista(*args):
        query = var_busqueda.get().lower().strip()
        for i in tree.get_children(): tree.delete(i)
        for u in todos_usuarios:
            if query in str(u.get('nombre', '')).lower() or query in str(u.get('rol_nombre', '')).lower():
                es_activo = u.get('activo')
                if not var_mostrar_inactivos.get() and not es_activo: continue
                tree.insert("", tk.END, values=[
                    u.get('id_usuario'), u.get('nombre'), u.get('rol_nombre'),
                    formatear_fecha(u.get('fecha_creacion')), formatear_fecha(u.get('ultimo_acceso')),
                    "✓ SI" if es_activo else "✗ NO"
                ])

    var_busqueda.trace_add("write", filtrar_lista)

    # FUNCIONES DE BOTONES
    def recargar_lista_callback():
        win.after(100, cargar_datos)
        
    def accion_nuevo():
        ui_crear_usuario(win, backend, callback_on_save=recargar_lista_callback)

    def abrir_editar():
        sel = tree.selection()
        if not sel: 
            messagebox.showwarning("Atención", "Seleccione un usuario.", parent=win)
            return
        item = tree.item(sel[0], "values")
        ui_crear_usuario(win, backend, id_usuario_a_editar=int(item[0]), callback_on_save=recargar_lista_callback)

    # 🔥 RECUPERADO: TU FUNCIÓN DE DOBLE CLIC
    tree.bind("<Double-1>", lambda e: abrir_editar())

    # FRAME DE BOTONES
    frame_botones = ctk.CTkFrame(win, fg_color="transparent")
    frame_botones.pack(pady=(5, 20), fill="x", padx=25)

    ctk.CTkButton(frame_botones, text="➕ Crear Usuario", command=accion_nuevo, fg_color="#16a34a", hover_color="#15803d", font=("Segoe UI", 12, "bold"), width=150, height=45).pack(side=tk.LEFT, padx=10)
    
    def accion_desactivar():
        sel = tree.selection()
        if not sel: 
            messagebox.showwarning("Atención", "Seleccione un usuario.", parent=win)
            return
        item = tree.item(sel[0], "values")
        if messagebox.askyesno("Confirmar", f"¿Desactivar al usuario {item[1]}?", parent=win):
            try:
                if backend.desactivar_usuario(int(item[0])):
                    cargar_datos()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)

    ctk.CTkButton(frame_botones, text="🗑️ Desactivar", command=accion_desactivar, fg_color="#dc2626", hover_color="#b91c1c", font=("Segoe UI", 12, "bold"), width=130, height=45).pack(side=tk.LEFT, padx=5)
    
    # CHECKBOX Y CERRAR
    ctk.CTkCheckBox(frame_botones, text="Inactivos", variable=var_mostrar_inactivos, font=("Segoe UI", 11), command=cargar_datos, width=100).pack(side=tk.LEFT, padx=10)
    
    ctk.CTkButton(frame_botones, text="Cerrar", command=win.destroy, fg_color="#4b5563", hover_color="#374151", font=("Segoe UI", 12, "bold"), width=100, height=45).pack(side=tk.RIGHT, padx=10)

    cargar_datos()
    entry_busqueda.focus_set()
    configurar_navegacion_ventana(win)
    win.grab_set()
    win.transient(parent)