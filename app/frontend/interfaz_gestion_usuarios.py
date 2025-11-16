# app/frontend/interfaz_gestion_usuarios.py
import tkinter as tk
from tkinter import ttk, messagebox
from app.frontend.interfaz_crear_usuario import ui_crear_editar_usuario

# ¡NUEVO! Importar navegación por teclado
try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    print("ADVERTENCIA: navegacion_teclado_comun.py no encontrado")
    def configurar_navegacion_ventana(win, confirmar_cierre=False):
        pass

def ui_gestion_usuarios(parent: tk.Misc, backend, usuario: dict):
    """
    Pantalla principal para gestionar usuarios (ver, crear, desactivar).
    """
    win = tk.Toplevel(parent)
    win.title("Gestion de Usuarios")
    win.geometry("800x500")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)
    
    frame_lista = tk.Frame(win, bg="#f4f4f8")
    frame_lista.pack(pady=20, padx=20, fill="both", expand=True)

    # --- Treeview (Lista) ---
    cols = ("ID", "Nombre", "Rol", "Activo")
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", height=15)
    tree.pack(side="left", fill="both", expand=True)
    
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    ys.pack(side="right", fill="y")
    tree.configure(yscrollcommand=ys.set)
    
    for c in cols: tree.heading(c, text=c)
    tree.column("ID", width=50, anchor="center")
    tree.column("Nombre", width=200)
    tree.column("Rol", width=150)
    tree.column("Activo", width=60, anchor="center")
    
    # Evento de doble clic para editar
    tree.bind("<Double-1>", lambda e: on_doble_clic())

    # --- Cargar Datos ---
    def cargar_datos():
        for i in tree.get_children():
            tree.delete(i)
        
        try:
            usuarios = backend.obtener_usuarios_con_rol()
            for u in usuarios:
                estado = "SI" if u.get('activo') else "NO"
                tree.insert("", tk.END, values=[
                    u.get('id_usuario', ''),
                    u.get('nombre', ''),
                    u.get('rol_nombre', ''),
                    estado
                ])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los usuarios:\n{e}", parent=win)

    # --- Botones de Acción ---
    frame_botones = tk.Frame(win, bg="#f4f4f8")
    frame_botones.pack(pady=10, fill="x")

    def abrir_crear_usuario():
        ui_crear_editar_usuario(win, backend)
        cargar_datos()

    def on_doble_clic():
        seleccion = tree.selection()
        if not seleccion:
            return
            
        item = tree.item(seleccion[0], "values")
        id_usuario = int(item[0])
        
        try:
            usuarios = backend.obtener_usuarios_con_rol()
            usuario_a_editar = next((u for u in usuarios if u.get('id_usuario') == id_usuario), None)
            
            if usuario_a_editar:
                ui_crear_editar_usuario(win, backend, usuario_a_editar)
                cargar_datos()
            else:
                messagebox.showwarning("Error", "No se encontró el usuario para editar.", parent=win)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la edición:\n{e}", parent=win)

    def desactivar_usuario():
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un usuario de la lista.", parent=win)
            return
            
        item = tree.item(seleccion[0], "values")
        id_usuario = int(item[0])
        nombre_usuario = item[1]
        
        if id_usuario == 1 or nombre_usuario.lower() == 'admin':
            messagebox.showerror("Acción Prohibida", "No se puede desactivar al usuario 'admin' principal.", parent=win)
            return
            
        if not messagebox.askyesno("Confirmar", f"¿Está seguro de que desea DESACTIVAR a '{nombre_usuario}'?\nEl usuario ya no podrá iniciar sesión.", parent=win):
            return
            
        try:
            if backend.desactivar_usuario(id_usuario):
                messagebox.showinfo("Éxito", "Usuario desactivado.", parent=win)
                cargar_datos()
            else:
                messagebox.showerror("Error", "No se pudo desactivar el usuario.", parent=win)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}", parent=win)

    btn_recargar = tk.Button(frame_botones, text="↻ Recargar Lista", command=cargar_datos, bg="#03A9F4", fg="white", width=15)
    btn_recargar.pack(side=tk.LEFT, padx=20)
    
    btn_crear = tk.Button(frame_botones, text="+ Crear Usuario", command=abrir_crear_usuario, bg="#4CAF50", fg="white", width=15)
    btn_crear.pack(side=tk.LEFT, padx=10)
    
    btn_desactivar = tk.Button(frame_botones, text="Desactivar Seleccionado", command=desactivar_usuario, bg="#f44336", fg="white", width=20)
    btn_desactivar.pack(side=tk.LEFT, padx=10)
    
    btn_cerrar = tk.Button(frame_botones, text="Cerrar", command=win.destroy, bg="#607D8B", fg="white", width=15)
    btn_cerrar.pack(side=tk.RIGHT, padx=20)

    # Carga inicial
    cargar_datos()
    
    # ¡NUEVO! Aplicar navegación por teclado
    configurar_navegacion_ventana(win)
    
    # ¡NUEVO! Foco inicial en botón recargar
    win.after(50, lambda: btn_recargar.focus_set())
    
    win.grab_set()
    win.transient(parent)