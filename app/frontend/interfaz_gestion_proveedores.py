# app/frontend/interfaz_gestion_proveedores.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox

def ui_gestion_proveedores(parent: tk.Misc, backend):
    """
    Abre una ventana para ver y desactivar proveedores.
    """
    win = tk.Toplevel(parent)
    win.title("Gestión de Proveedores")
    win.geometry("800x500")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)
    
    frame_lista = tk.Frame(win, bg="#f4f4f8")
    frame_lista.pack(pady=20, padx=20, fill="both", expand=True)

    # --- Treeview (Lista) ---
    cols = ["ID", "Nombre", "Empresa", "Teléfono", "Email", "Activo"]
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", height=15)
    tree.pack(side="left", fill="both", expand=True)
    
    # Scrollbar
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    ys.pack(side="right", fill="y")
    tree.configure(yscrollcommand=ys.set)
    
    # Columnas
    for c in cols: tree.heading(c, text=c)
    tree.column("ID", width=50, anchor="center")
    tree.column("Nombre", width=180)
    tree.column("Empresa", width=150)
    tree.column("Teléfono", width=100)
    tree.column("Email", width=180)
    tree.column("Activo", width=60, anchor="center")

    # --- Cargar Datos ---
    def cargar_datos():
        # Limpiar lista
        for i in tree.get_children():
            tree.delete(i)
        
        try:
            # Pedir TODOS (incluyendo inactivos)
            proveedores = backend.obtener_proveedores(incluir_inactivos=True)
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

    # --- Botones de Acción ---
    frame_botones = tk.Frame(win, bg="#f4f4f8")
    frame_botones.pack(pady=10, fill="x")

    def desactivar_proveedor():
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un proveedor de la lista.", parent=win)
            return
            
        item = tree.item(seleccion[0], "values")
        id_prov = item[0]
        nombre_prov = item[1]
        
        if not messagebox.askyesno("Confirmar", f"¿Está seguro de que desea DESACTIVAR a '{nombre_prov}' (ID: {id_prov})?\n\nNo podrá seleccionarlo para futuras compras.", parent=win):
            return
            
        try:
            if backend.eliminar_proveedor_logico(int(id_prov)):
                messagebox.showinfo("Éxito", "Proveedor desactivado.", parent=win)
                cargar_datos() # Recargar la lista para ver el cambio
            else:
                messagebox.showerror("Error", "No se pudo desactivar el proveedor.", parent=win)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}", parent=win)

    tk.Button(frame_botones, text="↻ Recargar Lista", command=cargar_datos, bg="#03A9F4", fg="white", width=15).pack(side=tk.LEFT, padx=20)
    tk.Button(frame_botones, text="Desactivar Seleccionado", command=desactivar_proveedor, bg="#f44336", fg="white", width=20).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_botones, text="Cerrar", command=win.destroy, bg="#607D8B", fg="white", width=15).pack(side=tk.RIGHT, padx=20)

    # Carga inicial
    cargar_datos()
    win.grab_set()
    win.transient(parent)