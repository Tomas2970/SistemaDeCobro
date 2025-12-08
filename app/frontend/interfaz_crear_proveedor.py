# app/frontend/interfaz_crear_proveedor.py
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
import re
from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana

def validar_email(e): return "@" in e

try:
    from app.frontend.interfaz_asignar_productos import ui_asignar_productos
except ImportError:
    ui_asignar_productos = None

def ui_crear_proveedor(parent: tk.Misc, backend, id_proveedor_a_editar: Optional[int] = None, callback_on_save: Optional[callable] = None):
    
    win = tk.Toplevel(parent)
    win.geometry("550x550") 
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # --- Validadores ---
    def check_dni(t):
        # DNI: máximo 8 dígitos
        if len(t) > 8: return False
        return t.isdigit() or t == ""
    
    def check_cuit(t):
        # CUIT: máximo 11 dígitos
        if len(t) > 11: return False
        return t.isdigit() or t == ""
    
    def check_telefono(t):
        # Teléfono: máximo 20 dígitos
        if len(t) > 20: return False
        return t.isdigit() or t == ""

    vc_dni = (win.register(check_dni), '%P')
    vc_cuit = (win.register(check_cuit), '%P')
    vc_tel = (win.register(check_telefono), '%P')

    modo_edicion = id_proveedor_a_editar is not None
    current_id_proveedor = id_proveedor_a_editar
    datos_prov = {}

    if modo_edicion:
        win.title("Editar Proveedor")
        try:
            datos_prov = backend.obtener_proveedor_completo(id_proveedor_a_editar) or {}
        except Exception: pass
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

    var_nombre = tk.StringVar(value=datos_prov.get('nombre', ''))
    ent_nombre = tk.Entry(frame, textvariable=var_nombre, width=35)
    add_field("Nombre Vendedor (*):", ent_nombre)
    
    var_dni = tk.StringVar(value=datos_prov.get('dni', ''))
    ent_dni = tk.Entry(frame, textvariable=var_dni, width=35, validate="key", validatecommand=vc_dni)
    add_field("DNI Vendedor (*):", ent_dni)

    var_empresa = tk.StringVar(value=datos_prov.get('empresa', ''))
    ent_empresa = tk.Entry(frame, textvariable=var_empresa, width=35)
    add_field("Nombre Empresa (*):", ent_empresa)

    var_cuit = tk.StringVar(value=datos_prov.get('cuit', ''))
    ent_cuit = tk.Entry(frame, textvariable=var_cuit, width=35, validate="key", validatecommand=vc_cuit)
    add_field("CUIT Empresa (*):", ent_cuit)
    
    var_tel = tk.StringVar(value=datos_prov.get('telefono', ''))
    ent_tel = tk.Entry(frame, textvariable=var_tel, width=35, validate="key", validatecommand=vc_tel) 
    add_field("Teléfono:", ent_tel)
    
    var_email = tk.StringVar(value=datos_prov.get('email', ''))
    ent_email = tk.Entry(frame, textvariable=var_email, width=35)
    add_field("Email:", ent_email)

    var_direccion = tk.StringVar(value=datos_prov.get('direccion', ''))
    ent_direccion = tk.Entry(frame, textvariable=var_direccion, width=35)
    add_field("Dirección:", ent_direccion)
    
    var_asignar = tk.BooleanVar(value=False)
    chk_asignar = tk.Checkbutton(frame, text="Asignar productos ahora", variable=var_asignar, bg="#f4f4f8")
    chk_asignar.grid(row=row, column=1, sticky="w", pady=10, padx=5)
    row += 1
    
    def guardar_y_continuar():
        nonlocal current_id_proveedor
        nombre = var_nombre.get().strip()
        empresa = var_empresa.get().strip()
        dni = var_dni.get().strip()
        cuit = var_cuit.get().strip()
        telefono = var_tel.get().strip()
        email = var_email.get().strip()
        direccion = var_direccion.get().strip()
        
        redirigir_asignacion = var_asignar.get() and ui_asignar_productos

        # 🔥 VALIDACIONES DE OBLIGATORIEDAD Y FORMATO ESTRICTO
        if not nombre: return messagebox.showwarning("Error", "Nombre Vendedor obligatorio.", parent=win)
        if not empresa: return messagebox.showwarning("Error", "Nombre Empresa obligatorio.", parent=win)
        
        if not dni: return messagebox.showwarning("Error", "DNI Vendedor obligatorio.", parent=win)
        if len(dni) not in [7, 8]: return messagebox.showwarning("Error", "El DNI debe tener 7 u 8 dígitos.", parent=win)
        
        if not cuit: return messagebox.showwarning("Error", "CUIT Empresa obligatorio.", parent=win)
        if len(cuit) != 11: return messagebox.showwarning("Error", "El CUIT debe tener 11 dígitos.", parent=win)

        if email and not validar_email(email): return messagebox.showwarning("Error", "Email inválido.", parent=win)
        
        try:
            if current_id_proveedor:
                ok = backend.actualizar_proveedor(
                    current_id_proveedor, nombre, empresa, cuit, dni, telefono, email, direccion
                ) 
                if not ok: return messagebox.showerror("Error", "No se pudieron guardar los cambios.")
            else:
                new_id = backend.insertar_proveedor(
                    nombre, empresa, cuit, dni, telefono, email, direccion
                )
                if not new_id: return messagebox.showerror("Error", "No se pudo crear.")
                current_id_proveedor = new_id

            win.destroy()
            
            if callback_on_save: callback_on_save()
            if redirigir_asignacion:
                ui_asignar_productos(parent, backend, current_id_proveedor, nombre)
            else:
                messagebox.showinfo("Guardado", "Proveedor guardado exitosamente.")

        except ValueError as ve:
            msg = str(ve)
            if "DNI_DUPLICADO" in msg:
                messagebox.showerror("DNI Repetido", f"El DNI {dni} ya existe.", parent=win)
            elif "EMAIL_DUPLICADO" in msg:
                messagebox.showerror("Email Repetido", f"El email {email} ya existe.", parent=win)
            else:
                messagebox.showerror("Error Validación", msg, parent=win)
        except Exception as e:
            error_msg = str(e)
            if "1062" in error_msg:
                 messagebox.showerror("Error de Duplicado", "DNI o Email duplicado detectado.", parent=win)
            else:
                messagebox.showerror("Error Sistema", f"Ocurrió un error:\n{e}", parent=win)

    btn_frame = tk.Frame(win, bg="#f4f4f8")
    btn_frame.pack(pady=20)
    
    texto_btn = "💾 Guardar Cambios" 
    tk.Button(btn_frame, text=texto_btn, command=guardar_y_continuar, 
              bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"), padx=20).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="Cancelar", command=win.destroy, 
              bg="#f44336", fg="white", font=("Segoe UI", 10), padx=10).pack(side=tk.LEFT, padx=10)

    configurar_navegacion_ventana(win)
    win.after(50, lambda: ent_nombre.focus_set())
    win.grab_set()