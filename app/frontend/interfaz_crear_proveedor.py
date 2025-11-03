# app/frontend/interfaz_crear_proveedor.py
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox

def ui_crear_proveedor(parent: tk.Misc, backend):
    """
    Abre una ventana emergente para crear un nuevo proveedor.
    """
    win = tk.Toplevel(parent)
    win.title("Crear Nuevo Proveedor")
    win.geometry("450x300")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    frame = tk.Frame(win, bg="#f4f4f8")
    frame.pack(padx=20, pady=20, fill="both", expand=True)
    
    # --- Widgets ---
    tk.Label(frame, text="Nombre (*):", bg="#f4f4f8").grid(row=0, column=0, sticky="e", pady=5, padx=5)
    var_nombre = tk.StringVar()
    tk.Entry(frame, textvariable=var_nombre, width=40).grid(row=0, column=1, pady=5)
    
    # --- ¡CAMBIADO! ---
    tk.Label(frame, text="Empresa:", bg="#f4f4f8").grid(row=1, column=0, sticky="e", pady=5, padx=5)
    var_empresa = tk.StringVar()
    tk.Entry(frame, textvariable=var_empresa, width=40).grid(row=1, column=1, pady=5)
    
    tk.Label(frame, text="Teléfono:", bg="#f4f4f8").grid(row=2, column=0, sticky="e", pady=5, padx=5)
    var_tel = tk.StringVar()
    tk.Entry(frame, textvariable=var_tel, width=40).grid(row=2, column=1, pady=5)
    
    tk.Label(frame, text="Email:", bg="#f4f4f8").grid(row=3, column=0, sticky="e", pady=5, padx=5)
    var_email = tk.StringVar()
    tk.Entry(frame, textvariable=var_email, width=40).grid(row=3, column=1, pady=5)
    
    tk.Label(frame, text="Contacto:", bg="#f4f4f8").grid(row=4, column=0, sticky="e", pady=5, padx=5)
    var_contacto = tk.StringVar()
    tk.Entry(frame, textvariable=var_contacto, width=40).grid(row=4, column=1, pady=5)
    
    # --- Guardar ---
    def guardar():
        nombre = var_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Campo obligatorio", "El 'Nombre' es obligatorio.", parent=win)
            return
        
        try:
            # --- ¡MODIFICADO! ---
            nuevo_id = backend.insertar_proveedor(
                nombre=nombre,
                empresa=var_empresa.get().strip(), # <-- CAMBIADO
                telefono=var_tel.get().strip(),
                email=var_email.get().strip(),
                contacto=var_contacto.get().strip()
            )
            if nuevo_id:
                messagebox.showinfo("Éxito", f"Proveedor '{nombre}' creado con ID {nuevo_id}.", parent=win)
                win.destroy() # Cierra la ventana emergente al guardar
            else:
                messagebox.showerror("Error", "No se pudo crear el proveedor.", parent=win)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}", parent=win)

    # --- Botones ---
    btn_frame = tk.Frame(frame, bg="#f4f4f8")
    btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
    
    tk.Button(btn_frame, text="Guardar", command=guardar, bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="Cancelar", command=win.destroy, bg="#f44336", fg="white", width=15).pack(side=tk.LEFT, padx=10)

    # Asegura que esta ventana se mantenga al frente
    win.grab_set()
    win.transient(parent)