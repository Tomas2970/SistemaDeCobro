# app/frontend/interfaz_crear_proveedor.py
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
import re

from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana

# Validaciones simples
def validar_email(e): return "@" in e

# Importamos la pantalla de asignación
try:
    from app.frontend.interfaz_asignar_productos import ui_asignar_productos
except ImportError:
    ui_asignar_productos = None

def ui_crear_proveedor(parent: tk.Misc, backend, id_proveedor_a_editar: Optional[int] = None):
    
    win = tk.Toplevel(parent)
    win.geometry("500x360")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    modo_edicion = id_proveedor_a_editar is not None
    current_id_proveedor = id_proveedor_a_editar
    datos_prov = {}

    if modo_edicion:
        win.title("Editar Proveedor")
        try:
            datos_prov = backend.obtener_proveedor_para_editar(id_proveedor_a_editar) or {}
        except Exception as e:
            messagebox.showerror("Error", f"Error carga: {e}", parent=win)
            win.destroy()
            return
    else:
        win.title("Crear Nuevo Proveedor")

    frame = tk.Frame(win, bg="#f4f4f8")
    frame.pack(padx=30, pady=20, fill="both", expand=True)
    
    row = 0
    def add_field(label, widget):
        nonlocal row
        tk.Label(frame, text=label, bg="#f4f4f8", anchor="e").grid(row=row, column=0, sticky="e", pady=8, padx=5)
        widget.grid(row=row, column=1, sticky="w", pady=8, padx=5)
        row += 1

    # 1. Nombre
    var_nombre = tk.StringVar(value=datos_prov.get('nombre', ''))
    ent_nombre = tk.Entry(frame, textvariable=var_nombre, width=35)
    add_field("Nombre (*):", ent_nombre)
    
    # 2. Empresa
    var_empresa = tk.StringVar(value=datos_prov.get('empresa', ''))
    ent_empresa = tk.Entry(frame, textvariable=var_empresa, width=35)
    add_field("Empresa:", ent_empresa)
    
    # 3. Teléfono (Validación visual mientras escribes)
    var_tel = tk.StringVar(value=datos_prov.get('telefono', ''))
    
    def validar_input_tel(texto):
        # Solo permite números, guiones, espacios y paréntesis
        return bool(re.match(r'^[0-9\-\s\+\(\)]*$', texto)) or texto == ""

    vcmd = (win.register(validar_input_tel), '%P')
    ent_tel = tk.Entry(frame, textvariable=var_tel, width=35, validate="key", validatecommand=vcmd)
    add_field("Teléfono:", ent_tel)
    
    # 4. Email
    var_email = tk.StringVar(value=datos_prov.get('email', ''))
    ent_email = tk.Entry(frame, textvariable=var_email, width=35)
    add_field("Email:", ent_email)
    
    def guardar_y_continuar():
        nonlocal current_id_proveedor
        
        nombre = var_nombre.get().strip()
        empresa = var_empresa.get().strip()
        telefono = var_tel.get().strip()
        email = var_email.get().strip()

        # --- VALIDACIONES DE NEGOCIO ---
        
        # 1. Nombre: Obligatorio y NO solo números
        if not nombre:
            messagebox.showwarning("Error", "El Nombre es obligatorio.", parent=win)
            ent_nombre.focus_set()
            return
        if nombre.isdigit():
            messagebox.showwarning("Error", "El Nombre no puede ser solo números. Escriba letras.", parent=win)
            ent_nombre.focus_set()
            return

        # 2. Empresa: NO solo números
        if empresa and empresa.isdigit():
            messagebox.showwarning("Error", "La Empresa no puede ser solo números.", parent=win)
            ent_empresa.focus_set()
            return

        # 3. Teléfono: NO debe tener letras (por si pegaron texto)
        # Buscamos si hay alguna letra [a-zA-Z]
        if re.search(r'[a-zA-Z]', telefono):
            messagebox.showwarning("Error", "El teléfono no debe contener letras.", parent=win)
            ent_tel.focus_set()
            return

        # 4. Email: Formato
        if email and not validar_email(email):
            messagebox.showwarning("Error", "El formato del Email es incorrecto (falta @).", parent=win)
            ent_email.focus_set()
            return
        
        try:
            if current_id_proveedor:
                # Editar
                ok = backend.actualizar_proveedor(current_id_proveedor, nombre, empresa, telefono, email)
                if not ok:
                    messagebox.showerror("Error", "No se pudieron guardar los cambios.")
                    return
            else:
                # Crear
                new_id = backend.insertar_proveedor(nombre, empresa, telefono, email)
                if not new_id:
                    messagebox.showerror("Error", "No se pudo crear (verifique que no exista ya).")
                    return
                current_id_proveedor = new_id

            # Cerrar y abrir asignación
            win.destroy()
            if ui_asignar_productos:
                ui_asignar_productos(parent, backend, current_id_proveedor, nombre)
            else:
                messagebox.showinfo("Guardado", "Proveedor guardado exitosamente.")

        except Exception as e:
            messagebox.showerror("Error de Sistema", f"Ocurrió un error técnico:\n{e}")

    # --- Botones ---
    btn_frame = tk.Frame(win, bg="#f4f4f8")
    btn_frame.pack(pady=20)
    
    texto_btn = "💾 Guardar y Asignar Productos" if not modo_edicion else "💾 Guardar Cambios y Gestionar Productos"
    
    tk.Button(btn_frame, text=texto_btn, command=guardar_y_continuar, 
              bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"), padx=20).pack(side=tk.LEFT, padx=10)

    tk.Button(btn_frame, text="Cancelar", command=win.destroy, 
              bg="#f44336", fg="white", font=("Segoe UI", 10), padx=10).pack(side=tk.LEFT, padx=10)

    configurar_navegacion_ventana(win)
    win.after(50, lambda: ent_nombre.focus_set())
    win.grab_set()
    win.transient(parent)