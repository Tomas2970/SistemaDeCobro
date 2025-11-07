# app/frontend/interfaz_gestion_proveedores.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from app.frontend.interfaz_crear_proveedor import ui_crear_proveedor
# --- ¡NUEVO! Importamos la nueva pantalla ---
try:
    from app.frontend.interfaz_asignar_productos import ui_asignar_productos
except ImportError:
    ui_asignar_productos = None
    print("Advertencia: No se encontró 'interfaz_asignar_productos.py'.")

def ui_gestion_proveedores(parent: tk.Misc, backend):
    win = tk.Toplevel(parent)
    win.title("Gestión de Proveedores")
    win.geometry("900x500")
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
    tree.column("Teléfono", width=100)
    tree.column("Email", width=180)
    tree.column("Activo", width=60, anchor="center")

    var_mostrar_inactivos = tk.BooleanVar(value=False)

    def cargar_datos():
        for i in tree.get_children():
            tree.delete(i)
        
        try:
            incluir_inactivos = var_mostrar_inactivos.get()
            proveedores = backend.obtener_proveedores(incluir_inactivos=incluir_inactivos)
            
            for p in proveedores:
                estado = "SI" if p.get('activo') else "NO"
                tree.insert("", tk.END, values=[
                    p.get('id_proveedor', ''),
                    p.get('nombre', ''),
                    p.get('empresa', ''),
                    p.get('telefono', ''),
                    p.get('email', ''),
                    estado
                ])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar proveedores:\n{e}", parent=win)

    frame_botones = tk.Frame(win, bg="#f4f4f8")
    frame_botones.pack(pady=10, fill="x")

    def abrir_editar_proveedor():
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un proveedor de la lista.", parent=win)
            return
            
        item = tree.item(seleccion[0], "values")
        id_prov = item[0]
        
        ui_crear_proveedor(win, backend, id_proveedor_a_editar=int(id_prov))
        
        cargar_datos()
    
    # --- ¡NUEVA FUNCIÓN! ---
    def abrir_asignar_productos():
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un proveedor de la lista.", parent=win)
            return
            
        if not callable(ui_asignar_productos):
            messagebox.showerror("Error", "No se encontró el archivo 'interfaz_asignar_productos.py'.", parent=win)
            return
            
        item = tree.item(seleccion[0], "values")
        id_prov = int(item[0])
        nombre_prov = str(item[1])
        
        # Llama a la nueva pantalla
        ui_asignar_productos(win, backend, id_prov, nombre_prov)
    # --- FIN NUEVA FUNCIÓN ---

    def desactivar_proveedor():
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un proveedor de la lista.", parent=win)
            return
            
        item = tree.item(seleccion[0], "values")
        id_prov = item[0]
        nombre_prov = item[1]
        
        if not messagebox.askyesno("Confirmar", f"¿Está seguro de que desea DESACTIVAR a '{nombre_prov}' (ID: {id_prov})?", parent=win):
            return
            
        try:
            if backend.eliminar_proveedor_logico(int(id_prov)):
                messagebox.showinfo("Éxito", "Proveedor desactivado.", parent=win)
                cargar_datos()
            else:
                messagebox.showerror("Error", "No se pudo desactivar el proveedor.", parent=win)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}", parent=win)

    tk.Button(frame_botones, text="↻ Recargar Lista", command=cargar_datos, bg="#03A9F4", fg="white", width=15).pack(side=tk.LEFT, padx=(20, 10))
    
    tk.Button(frame_botones, text="✎ Editar Seleccionado", command=abrir_editar_proveedor, bg="#FFC107", fg="black", width=18).pack(side=tk.LEFT, padx=10)
    
    # --- ¡NUEVO BOTÓN! ---
    tk.Button(frame_botones, text="Asignar Productos", command=abrir_asignar_productos, bg="#7c3aed", fg="white", width=18).pack(side=tk.LEFT, padx=10)
    # --- FIN NUEVO BOTÓN ---
    
    tk.Button(frame_botones, text="Desactivar Seleccionado", command=desactivar_proveedor, bg="#f44336", fg="white", width=20).pack(side=tk.LEFT, padx=10)
    
    chk_inactivos = tk.Checkbutton(
        frame_botones, 
        text="Mostrar desactivados", 
        variable=var_mostrar_inactivos, 
        onvalue=True, 
        offvalue=False,
        bg="#f4f4f8",
        command=cargar_datos
    )
    chk_inactivos.pack(side=tk.LEFT, padx=20)
    
    tk.Button(frame_botones, text="Cerrar", command=win.destroy, bg="#607D8B", fg="white", width=15).pack(side=tk.RIGHT, padx=20)

    cargar_datos()
    win.grab_set()
    win.transient(parent)