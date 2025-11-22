# app/frontend/interfaz_gestion_proveedores.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from app.frontend.interfaz_crear_proveedor import ui_crear_proveedor

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

try:
    from app.frontend.interfaz_asignar_productos import ui_asignar_productos
except ImportError:
    ui_asignar_productos = None

def ui_gestion_proveedores(parent: tk.Misc, backend):
    win = tk.Toplevel(parent)
    win.title("Gestión de Proveedores")
    win.geometry("950x550") # Un poco más ancho
    win.config(bg="#f4f4f8")
    win.resizable(False, False)
    
    frame_lista = tk.Frame(win, bg="#f4f4f8")
    frame_lista.pack(pady=20, padx=20, fill="both", expand=True)

    cols = ["ID", "Nombre", "Empresa", "Teléfono", "Email", "Activo"]
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", height=15)
    tree.pack(side="left", fill="both", expand=True)
    
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    ys.pack(side="right", fill="y")
    tree.configure(yscrollcommand=ys.set)
    
    for c in cols: tree.heading(c, text=c)
    tree.column("ID", width=50, anchor="center")
    tree.column("Nombre", width=180)
    tree.column("Empresa", width=150)
    tree.column("Teléfono", width=120)
    tree.column("Email", width=180)
    tree.column("Activo", width=60, anchor="center")

    var_mostrar_inactivos = tk.BooleanVar(value=False)

    def cargar_datos():
        for i in tree.get_children(): tree.delete(i)
        try:
            incluir_inactivos = var_mostrar_inactivos.get()
            proveedores = backend.obtener_proveedores(incluir_inactivos=incluir_inactivos)
            for p in proveedores:
                estado = "SI" if p.get('activo') else "NO"
                tree.insert("", tk.END, values=[
                    p.get('id_proveedor', ''), p.get('nombre', ''), p.get('empresa', ''),
                    p.get('telefono', ''), p.get('email', ''), estado
                ])
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando: {e}", parent=win)

    frame_botones = tk.Frame(win, bg="#f4f4f8")
    frame_botones.pack(pady=15, fill="x")

    # --- ACCIONES ---
    def accion_nuevo():
        ui_crear_proveedor(win, backend)
        # Al volver, recargamos
        win.after(100, cargar_datos)

    def abrir_editar_proveedor():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un proveedor.", parent=win)
            return
        item = tree.item(sel[0], "values")
        ui_crear_proveedor(win, backend, id_proveedor_a_editar=int(item[0]))
        cargar_datos()
    
    def abrir_asignar_productos():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un proveedor.", parent=win)
            return
        if not ui_asignar_productos:
            messagebox.showerror("Error", "Módulo no encontrado.", parent=win)
            return
            
        item = tree.item(sel[0], "values")
        id_prov = int(item[0])
        nombre_prov = str(item[1])
        ui_asignar_productos(win, backend, id_prov, nombre_prov)

    def desactivar_proveedor():
        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        if messagebox.askyesno("Confirmar", f"¿Desactivar a '{item[1]}'?", parent=win):
            try:
                if backend.eliminar_proveedor_logico(int(item[0])):
                    messagebox.showinfo("Éxito", "Desactivado.", parent=win)
                    cargar_datos()
            except Exception as e:
                messagebox.showerror("Error", f"{e}", parent=win)

    # --- BOTONES ORDENADOS ---
    # Izquierda: Acciones principales
    tk.Button(frame_botones, text="+ Nuevo Proveedor", command=accion_nuevo, bg="#4CAF50", fg="white", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=20)
    tk.Button(frame_botones, text="✎ Editar", command=abrir_editar_proveedor, bg="#FFC107").pack(side=tk.LEFT, padx=5)
    tk.Button(frame_botones, text="📦 Productos", command=abrir_asignar_productos, bg="#7c3aed", fg="white").pack(side=tk.LEFT, padx=5)
    
    # Centro: Filtro
    tk.Checkbutton(frame_botones, text="Mostrar inactivos", variable=var_mostrar_inactivos, bg="#f4f4f8", command=cargar_datos).pack(side=tk.LEFT, padx=30)
    
    # Derecha: Borrar y Salir
    tk.Button(frame_botones, text="Cerrar", command=win.destroy, bg="#607D8B", fg="white").pack(side=tk.RIGHT, padx=20)
    tk.Button(frame_botones, text="Desactivar", command=desactivar_proveedor, bg="#f44336", fg="white").pack(side=tk.RIGHT, padx=5)

    cargar_datos()
    configurar_navegacion_ventana(win)
    win.grab_set()
    win.transient(parent)