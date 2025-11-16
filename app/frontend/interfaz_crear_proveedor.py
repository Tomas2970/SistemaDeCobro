# app/frontend/interfaz_crear_proveedor.py
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from typing import Optional

# ¡NUEVO! Importar navegación por teclado
try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    print("ADVERTENCIA: navegacion_teclado_comun.py no encontrado")
    def configurar_navegacion_ventana(win, confirmar_cierre=False):
        pass

def ui_crear_proveedor(parent: tk.Misc, backend, id_proveedor_a_editar: Optional[int] = None):
    """
    Abre una ventana emergente para CREAR o EDITAR un proveedor.
    """
    win = tk.Toplevel(parent)
    win.geometry("450x260")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

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
        datos_prov = {}

    frame = tk.Frame(win, bg="#f4f4f8")
    frame.pack(padx=20, pady=20, fill="both", expand=True)
    
    tk.Label(frame, text="Nombre (*):", bg="#f4f4f8").grid(row=0, column=0, sticky="e", pady=5, padx=5)
    var_nombre = tk.StringVar()
    ent_nombre = tk.Entry(frame, textvariable=var_nombre, width=40)
    ent_nombre.grid(row=0, column=1, pady=5)
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
    
    def guardar():
        nombre = var_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Campo obligatorio", "El 'Nombre' es obligatorio.", parent=win)
            return
        
        try:
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
            
            else:
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

    btn_frame = tk.Frame(frame, bg="#f4f4f8")
    btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
    
    btn_guardar = tk.Button(btn_frame, text="Guardar", command=guardar, bg="#4CAF50", fg="white", width=15)
    btn_guardar.pack(side=tk.LEFT, padx=10)
    
    btn_cancelar = tk.Button(btn_frame, text="Cancelar", command=win.destroy, bg="#f44336", fg="white", width=15)
    btn_cancelar.pack(side=tk.LEFT, padx=10)

    # ¡NUEVO! Aplicar navegación por teclado
    configurar_navegacion_ventana(win)
    
    # ¡NUEVO! Foco inicial en campo nombre
    win.after(50, lambda: ent_nombre.focus_set())
    
    win.grab_set()
    win.transient(parent)