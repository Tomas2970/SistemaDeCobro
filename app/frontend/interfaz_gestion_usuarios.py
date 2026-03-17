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
    win = tk.Toplevel(parent)
    win.title("Gestión de Usuarios")
    win.geometry("1150x680") 
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # ESTILOS MODERNOS (Los que vos definiste)
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
    
    style.map("Modern.Treeview.Heading",
              background=[('active', '#e5e7eb')])

    # BARRA DE BÚSQUEDA
    frame_busqueda = tk.Frame(win, bg="#f4f4f8")
    frame_busqueda.pack(pady=(15,0), padx=20, fill="x")
    
    tk.Label(frame_busqueda, text="🔍", bg="#f4f4f8", font=("Segoe UI", 14)).pack(side=tk.LEFT)
    tk.Label(frame_busqueda, text="Buscar:", bg="#f4f4f8", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(5,10))
    var_busqueda = tk.StringVar()
    entry_busqueda = tk.Entry(frame_busqueda, textvariable=var_busqueda, width=35, font=("Segoe UI", 10))
    entry_busqueda.pack(side=tk.LEFT)

    # TREEVIEW
    frame_lista = tk.Frame(win, bg="#f4f4f8")
    frame_lista.pack(pady=10, padx=20, fill="both", expand=True)

    cols = ["ID", "Nombre", "Rol", "Fecha Creación", "Último Acceso", "Activo"]
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", height=12, style="Modern.Treeview")
    tree.pack(side="left", fill="both", expand=True)
    
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    ys.pack(side="right", fill="y")
    tree.configure(yscrollcommand=ys.set)
    
    for c in cols: tree.heading(c, text=c)
    
    tree.column("ID", width=0, minwidth=0, stretch=False)
    tree.column("Nombre", width=200)
    tree.column("Rol", width=150)
    tree.column("Fecha Creación", width=180, anchor="center")
    tree.column("Último Acceso", width=180, anchor="center")
    tree.column("Activo", width=80, anchor="center")

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

    # FRAME DE BOTONES (TU LAYOUT ORIGINAL)
    frame_botones = tk.Frame(win, bg="#f4f4f8", height=80)
    frame_botones.pack(pady=15, fill="x", padx=20)
    frame_botones.pack_propagate(False)

    frame_acciones = tk.Frame(frame_botones, bg="#f4f4f8")
    frame_acciones.pack(side=tk.LEFT, anchor="w")

    tk.Button(frame_acciones, text="➕ Crear Usuario", command=accion_nuevo, bg="#16a34a", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=10).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_acciones, text="🗑️ Desactivar", command=lambda: messagebox.showinfo("Info", "Funcionalidad de desactivar"), bg="#dc2626", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=10).pack(side=tk.LEFT, padx=5)

    # CHECKBOX Y CERRAR
    tk.Checkbutton(frame_botones, text="Ver Inactivos", variable=var_mostrar_inactivos, bg="#f4f4f8", command=cargar_datos).pack(side=tk.LEFT, padx=20)
    tk.Button(frame_botones, text="Cerrar", command=win.destroy, bg="#64748b", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=10).pack(side=tk.RIGHT)

    cargar_datos()
    entry_busqueda.focus_set()
    configurar_navegacion_ventana(win)
    win.grab_set()
    win.transient(parent)