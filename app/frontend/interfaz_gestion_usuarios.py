
# ARCHIVO 1: interfaz_gestion_usuarios.py
# ============================================
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

    var_mostrar_inactivos = tk.BooleanVar(value=False)

    def cargar_datos():
        for i in tree.get_children(): tree.delete(i)
        try:
            users = backend.obtener_usuarios_con_rol()
            mostrar_todos = var_mostrar_inactivos.get()

            for u in users:
                es_activo = u.get('activo')
                if not mostrar_todos and not es_activo:
                    continue

                activo_txt = "SI" if es_activo else "NO"
                tree.insert("", tk.END, values=[
                    u.get('id_usuario'),
                    u.get('nombre'),
                    u.get('rol_nombre'),
                    activo_txt
                ])
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar: {e}", parent=win)

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

    def on_doble_click(event): abrir_editar()
    tree.bind("<Double-1>", on_doble_click)

    def desactivar():
        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        
        if usuario_actual and str(usuario_actual.get('id_usuario')) == str(item[0]):
            messagebox.showerror("Error", "No puedes desactivar tu propio usuario.", parent=win)
            return
            
        if item[3] == 'NO': return

        if messagebox.askyesno("Confirmar", f"¿Desactivar usuario '{item[1]}'?"):
            if backend.desactivar_usuario(int(item[0])):
                messagebox.showinfo("Éxito", "Usuario desactivado.", parent=win)
                cargar_datos()
            else: messagebox.showerror("Error", "No se pudo desactivar.", parent=win)

    def activar_usuario():
        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        if item[3] == 'SI': return

        if messagebox.askyesno("Confirmar", f"¿Activar usuario '{item[1]}'?"):
            if backend.activar_usuario(int(item[0])):
                messagebox.showinfo("Éxito", "Usuario activado.", parent=win)
                cargar_datos()
            else: messagebox.showerror("Error", "No se pudo activar.", parent=win)

    # 🔥 FRAME DE BOTONES MODERNO
    frame_botones = tk.Frame(win, bg="#f4f4f8")
    frame_botones.pack(pady=15, fill="x", padx=20)

    frame_acciones = tk.Frame(frame_botones, bg="#f4f4f8")
    frame_acciones.pack(side=tk.LEFT)

    tk.Button(
        frame_acciones, text="➕ Crear Usuario", command=accion_nuevo, 
        bg="#16a34a", fg="white", font=("Segoe UI", 10, "bold"), 
        relief="flat", padx=15, pady=8, cursor="hand2"
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        frame_acciones, text="🗑️ Desactivar", command=desactivar, 
        bg="#dc2626", fg="white", font=("Segoe UI", 9), 
        relief="flat", padx=12, pady=7, cursor="hand2"
    ).pack(side=tk.LEFT, padx=5)

    # 🔥 Botón Activar CONDICIONAL
    btn_activar = tk.Button(
        frame_acciones, text="✅ Activar", command=activar_usuario, 
        bg="#0ea5e9", fg="white", font=("Segoe UI", 9), 
        relief="flat", padx=12, pady=7, cursor="hand2"
    )

    def toggle_mostrar_inactivos():
        cargar_datos()
        if var_mostrar_inactivos.get():
            btn_activar.pack(side=tk.LEFT, padx=5)
        else:
            btn_activar.pack_forget()

    frame_filtros = tk.Frame(frame_botones, bg="#f4f4f8")
    frame_filtros.pack(side=tk.LEFT, padx=30)

    tk.Checkbutton(
        frame_filtros, text="Ver Inactivos", variable=var_mostrar_inactivos, 
        bg="#f4f4f8", font=("Segoe UI", 9), command=toggle_mostrar_inactivos
    ).pack(side=tk.LEFT)

    tk.Button(
        frame_botones, text="Cerrar", command=win.destroy, 
        bg="#64748b", fg="white", font=("Segoe UI", 9), 
        relief="flat", padx=15, pady=7, cursor="hand2"
    ).pack(side=tk.RIGHT)

    cargar_datos()
    configurar_navegacion_ventana(win)
    win.grab_set()
