# app/frontend/interfaz_crear_proveedor.py
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
import re

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

# ============================================================================
# 🔒 VALIDADORES DE TECLADO
# ============================================================================
def validar_cuit(texto):
    if len(texto) > 11: return False
    return texto.isdigit() or texto == ""

def validar_telefono(texto):
    if len(texto) > 10: return False
    return texto.isdigit() or texto == ""

# ============================================================================
# 🎨 VALIDACIÓN VISUAL UNIFICADA
# ============================================================================
def validar_y_colorear(entry, tipo_validacion, label_feedback=None):
    valor = entry.get().strip()
    valido, mensaje = False, ""
    
    if tipo_validacion == 'empresa':
        if len(valor) < 3: 
            valido, mensaje = False, "⚠️ Obligatorio"
        else: 
            valido, mensaje = True, "✓ Válido"
            
    elif tipo_validacion == 'cuit':
        if len(valor) == 0:
            valido, mensaje = False, "⚠️ Obligatorio"
        elif len(valor) == 11: 
            valido, mensaje = True, "✓ Válido"
        else: 
            valido, mensaje = False, "❌ CUIT Inválido"
            
    elif tipo_validacion == 'telefono':
        # 🔥 AHORA ES OBLIGATORIO (Igual que DNI/Nombre)
        if len(valor) == 0: 
            valido, mensaje = False, "⚠️ Obligatorio"
        elif len(valor) == 10: 
            valido, mensaje = True, "✓ Válido"
        else: 
            valido, mensaje = False, f"❌ Faltan {10-len(valor)} nros"
            
    elif tipo_validacion == 'email':
        if len(valor) == 0: 
            valido, mensaje = True, "⚪ Opcional"
        else:
            if "@" not in valor: 
                valido, mensaje = False, "❌ Falta @"
            elif "." not in valor.split("@")[-1]: 
                valido, mensaje = False, "❌ Falta dominio"
            else:
                patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                valido = bool(re.match(patron, valor))
                mensaje = "✓ Válido" if valido else "❌ Formato incorrecto"
    
    # Aplicar colores de fondo
    if valor == "":
        entry.config(bg="#ffffff")
    else:
        entry.config(bg="#d1fae5" if valido else "#fee2e2")
    
    # Actualizar label de feedback
    if label_feedback:
        label_feedback.config(
            text=mensaje, 
            fg="#059669" if valido else ("#6b7280" if "Opcional" in mensaje or "Obligatorio" in mensaje else "#dc2626")
        )
    return valido

# ============================================================================
# 🗃️ INTERFAZ PRINCIPAL
# ============================================================================
def ui_crear_proveedor(parent: tk.Misc, backend, id_proveedor_a_editar: Optional[int] = None, callback_on_save: Optional[callable] = None):
    win = tk.Toplevel(parent)
    win.geometry("630x480") 
    win.config(bg="#f4f4f8")
    win.resizable(False, False)
    win.title("Editar Empresa" if id_proveedor_a_editar else "Nueva Empresa Proveedora")

    datos_prov = {}
    if id_proveedor_a_editar:
        try:
            datos_prov = backend.obtener_proveedor_completo(id_proveedor_a_editar) or {}
        except: datos_prov = {}

    def _limpiar(val):
        """Convierte None o la cadena 'None' a vacío."""
        if val is None or str(val).strip().lower() == 'none':
            return ''
        return str(val)

    var_empresa = tk.StringVar(value=_limpiar(datos_prov.get('empresa')))
    var_cuit = tk.StringVar(value=_limpiar(datos_prov.get('cuit')))
    var_tel = tk.StringVar(value=_limpiar(datos_prov.get('telefono')))
    var_email = tk.StringVar(value=_limpiar(datos_prov.get('email')))
    var_direccion = tk.StringVar(value=_limpiar(datos_prov.get('direccion')))

    frame = tk.Frame(win, bg="#f4f4f8", padx=20, pady=20)
    frame.pack(fill="both", expand=True)

    fila = 1
    def crear_fila(label, var, val_teclado, tipo_val, obligatorio=True):
        nonlocal fila
        tk.Label(frame, text=f"{label} {'(*)' if obligatorio else ''}:", 
                 bg="#f4f4f8", font=("Segoe UI", 9), width=16, anchor="w").grid(row=fila, column=0, sticky="w", pady=5)
        
        ent = tk.Entry(frame, textvariable=var, width=28, font=("Segoe UI", 10), 
                       validate="key", validatecommand=(win.register(val_teclado), '%P'))
        ent.grid(row=fila, column=1, sticky="w", pady=5, padx=5)
        
        lbl_fb = tk.Label(frame, text="", bg="#f4f4f8", font=("Segoe UI", 9), width=25, anchor="w")
        lbl_fb.grid(row=fila, column=2, sticky="w")
        
        if tipo_val:
            ent.bind('<KeyRelease>', lambda e: validar_y_colorear(ent, tipo_val, lbl_fb))
            validar_y_colorear(ent, tipo_val, lbl_fb)
        else:
            # Campo opcional sin tipo de validación (ej: Dirección)
            # Mostrar "Opcional" si vacío, verde si tiene contenido
            def _colorear_opcional(e=None):
                val = ent.get().strip()
                if val:
                    ent.config(bg="#d1fae5")
                    lbl_fb.config(text="✓ Válido", fg="#059669")
                else:
                    ent.config(bg="#ffffff")
                    lbl_fb.config(text="⚪ Opcional", fg="#6b7280")
            ent.bind('<KeyRelease>', _colorear_opcional)
            _colorear_opcional()
        
        fila += 1
        return ent

    crear_fila("Nombre", var_empresa, lambda t: len(t) < 50, 'empresa')
    crear_fila("CUIT", var_cuit, validar_cuit, 'cuit')
    # 🔥 Teléfono ahora es obligatorio (*)
    crear_fila("Teléfono", var_tel, validar_telefono, 'telefono', True)
    crear_fila("Email", var_email, lambda t: True, 'email', False)
    crear_fila("Dirección", var_direccion, lambda t: True, None, False)

    def guardar():
        empresa = var_empresa.get().strip()
        cuit = var_cuit.get().strip()
        tel = var_tel.get().strip()
        
        # Validaciones específicas
        if len(empresa) < 3:
            messagebox.showwarning("Campo requerido", "El Nombre de la empresa debe tener al menos 3 caracteres.", parent=win)
            return
        if len(cuit) != 11:
            messagebox.showwarning("Campo requerido", f"El CUIT debe tener exactamente 11 dígitos (tiene {len(cuit)}).", parent=win)
            return
        if len(tel) != 10:
            messagebox.showwarning("Campo requerido", f"El Teléfono debe tener exactamente 10 dígitos (tiene {len(tel)}).", parent=win)
            return

        # Validar email si fue ingresado
        import re
        email = var_email.get().strip()
        if email:
            patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(patron, email):
                messagebox.showwarning("Email inválido", "El email ingresado no tiene un formato válido (ej: nombre@dominio.com).", parent=win)
                return

        try:
            dni_db = cuit 
            if id_proveedor_a_editar:
                ok = backend.actualizar_proveedor(id_proveedor_a_editar, empresa, empresa, cuit, dni_db, tel, var_email.get(), var_direccion.get())
            else:
                ok = backend.insertar_proveedor(empresa, empresa, cuit, dni_db, tel, var_email.get(), var_direccion.get())
            
            if ok:
                if callback_on_save: callback_on_save()
                win.destroy()
                messagebox.showinfo("Éxito", "Guardado correctamente.")
        except Exception as e: 
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    btn_frame = tk.Frame(win, bg="#f4f4f8", pady=15)
    btn_frame.pack(fill="x")
    tk.Button(btn_frame, text="💾 GUARDAR", command=guardar, bg="#16a34a", fg="white", 
              font=("Segoe UI", 10, "bold"), relief="flat", padx=30, pady=8).pack(side="left", padx=30)
    tk.Button(btn_frame, text="Cancelar", command=win.destroy, bg="#6b7280", fg="white", 
              relief="flat", padx=20, pady=8).pack(side="right", padx=30)

    configurar_navegacion_ventana(win)
    win.grab_set()