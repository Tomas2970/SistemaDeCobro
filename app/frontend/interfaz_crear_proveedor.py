# app/frontend/interfaz_crear_proveedor.py
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from typing import Optional

def ui_crear_proveedor(parent: tk.Misc, backend, id_proveedor_a_editar: Optional[int] = None):
    """
    Abre una ventana emergente para CREAR o EDITAR un proveedor.
    """
    win = tk.Toplevel(parent)
    win.geometry("450x260") # <-- Más corta, sin "Contacto"
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # --- ¡NUEVO! Lógica de Edición ---
    modo_edicion = id_proveedor_a_editar is not None
    
    if modo_edicion:
        win.title("Editar Proveedor")
        try:
            datos_prov = backend.obtener_proveedor_para_editar(id_proveedor_a_editar)
            if not datos_prov:
                messagebox.showerror("Error", "No se pudieron cargar los datos del proveedor.", parent=win)
                win.destroy()
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {e}", parent=win)
            win.destroy()
            return
    else:
        win.title("Crear Nuevo Proveedor")
        datos_prov = {} # Vacío si es nuevo
    # --- FIN LÓGICA EDICIÓN ---

    frame = tk.Frame(win, bg="#f4f4f8")
    frame.pack(padx=20, pady=20, fill="both", expand=True)
    
    # --- Widgets ---
    tk.Label(frame, text="Nombre (*):", bg="#f4f4f8").grid(row=0, column=0, sticky="e", pady=5, padx=5)
    var_nombre = tk.StringVar()
    tk.Entry(frame, textvariable=var_nombre, width=40).grid(row=0, column=1, pady=5)
    var_nombre.set(datos_prov.get('nombre', ''))
    
    tk.Label(frame, text="Empresa:", bg="#f4f4f8").grid(row=1, column=0, sticky="e", pady=5, padx=5)
    var_empresa = tk.StringVar()
    tk.Entry(frame, textvariable=var_empresa, width=40).grid(row=1, column=1, pady=5)
    var_empresa.set(datos_prov.get('empresa', ''))
    
    tk.Label(frame, text="Teléfono:", bg="#f4f4f8").grid(row=2, column=0, sticky="e", pady=5, padx=5)
    var_tel = tk.StringVar()
    tk.Entry(frame, textvariable=var_tel, width=40).grid(row=2, column=1, pady=5)
    var_tel.set(datos_prov.get('telefono', ''))
    
    tk.Label(frame, text="Email:", bg="#f4f4f8").grid(row=3, column=0, sticky="e", pady=5, padx=5)
    var_email = tk.StringVar()
    tk.Entry(frame, textvariable=var_email, width=40).grid(row=3, column=1, pady=5)
    var_email.set(datos_prov.get('email', ''))
    
    # (Campo "Contacto" eliminado)
    
    # --- Guardar ---
    def guardar():
        nombre = var_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Campo obligatorio", "El 'Nombre' es obligatorio.", parent=win)
            return
        
        try:
            # --- ¡NUEVO! Lógica para guardar o actualizar ---
            if modo_edicion:
                exito = backend.actualizar_proveedor(
                    id_proveedor=id_proveedor_a_editar,
                    nombre=nombre,
                    empresa=var_empresa.get().strip(),
                    telefono=var_tel.get().strip(),
                    email=var_email.get().strip()
                )
                if exito:
                    messagebox.showinfo("Éxito", f"Proveedor '{nombre}' actualizado.", parent=win)
                    win.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo actualizar el proveedor.", parent=win)
            
            else: # Modo Creación
                nuevo_id = backend.insertar_proveedor(
                    nombre=nombre,
                    empresa=var_empresa.get().strip(),
                    telefono=var_tel.get().strip(),
                    email=var_email.get().strip()
                )
                if nuevo_id:
                    messagebox.showinfo("Éxito", f"Proveedor '{nombre}' creado con ID {nuevo_id}.", parent=win)
                    win.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo crear el proveedor.", parent=win)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}", parent=win)

    # --- Botones ---
    btn_frame = tk.Frame(frame, bg="#f4f4f8")
    btn_frame.grid(row=4, column=0, columnspan=2, pady=20) # Fila cambiada a 4
    
    tk.Button(btn_frame, text="Guardar", command=guardar, bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="Cancelar", command=win.destroy, bg="#f44336", fg="white", width=15).pack(side=tk.LEFT, padx=10)

    win.grab_set()
    win.transient(parent)