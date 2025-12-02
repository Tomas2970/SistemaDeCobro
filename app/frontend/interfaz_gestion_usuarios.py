# app/frontend/interfaz_gestion_usuarios.py
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
    win.geometry("900x500")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    frame_lista = tk.Frame(win, bg="#f4f4f8")
    frame_lista.pack(pady=20, padx=20, fill="both", expand=True)

    cols = ["ID", "Nombre", "Rol", "Activo"]
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", height=15)
    tree.pack(side="left", fill="both", expand=True)
    
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    ys.pack(side="right", fill="y")
    tree.configure(yscrollcommand=ys.set)
    
    for c in cols: tree.heading(c, text=c)
    tree.column("ID", width=50, anchor="center")
    tree.column("Nombre", width=200)
    tree.column("Rol", width=150)
    tree.column("Activo", width=80, anchor="center")

    def cargar_datos():
        for i in tree.get_children(): tree.delete(i)
        try:
            users = backend.obtener_usuarios_con_rol()
            for u in users:
                activo = "SI" if u.get('activo') else "NO"
                tree.insert("", tk.END, values=[
                    u.get('id_usuario'),
                    u.get('nombre'),
                    u.get('rol_nombre'),
                    activo
                ])
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar: {e}", parent=win)

    # --- Acciones ---
    def accion_nuevo():
        ui_crear_usuario(win, backend)
        win.after(1500, cargar_datos) 

    # 🔥 FUNCIÓN DE EDITAR RECUPERADA
    def abrir_editar():
        sel = tree.selection()
        if not sel: 
            messagebox.showwarning("Atención", "Seleccione un usuario para editar.", parent=win)
            return
        item = tree.item(sel[0], "values")
        
        # Abrimos la ventana de crear usuario en modo edición (pasando ID)
        ui_crear_usuario(win, backend, id_usuario_a_editar=int(item[0]))
        # Recargamos lista luego
        win.after(1000, cargar_datos)

    # 🔥 DOBLE CLICK RECUPERADO
    def on_doble_click(event):
        abrir_editar()

    tree.bind("<Double-1>", on_doble_click)

    def desactivar():
        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        # Evitar auto-desactivación
        if usuario_actual and str(usuario_actual.get('id_usuario')) == str(item[0]):
            messagebox.showerror("Error", "No puedes desactivar tu propio usuario.", parent=win)
            return

        if messagebox.askyesno("Confirmar", f"¿Desactivar usuario '{item[1]}'?", parent=win):
            if backend.desactivar_usuario(int(item[0])):
                messagebox.showinfo("Éxito", "Usuario desactivado.", parent=win)
                cargar_datos()
            else:
                messagebox.showerror("Error", "No se pudo desactivar.", parent=win)

    frame_botones = tk.Frame(win, bg="#f4f4f8")
    frame_botones.pack(pady=15, fill="x")

    tk.Button(frame_botones, text="+ Crear Usuario", command=accion_nuevo, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=20)
    
    # 🔥 BOTÓN EDITAR RECUPERADO
    tk.Button(frame_botones, text="✎ Editar", command=abrir_editar, bg="#FFC107").pack(side=tk.LEFT, padx=5)
    
    tk.Button(frame_botones, text="Desactivar Seleccionado", command=desactivar, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
    tk.Button(frame_botones, text="Cerrar", command=win.destroy, bg="#607D8B", fg="white").pack(side=tk.RIGHT, padx=20)

    cargar_datos()
    configurar_navegacion_ventana(win)
    win.grab_set()