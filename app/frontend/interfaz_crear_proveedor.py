# app/frontend/interfaz_crear_proveedor.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from app.frontend import custom_dialogs as messagebox
from typing import Optional
import re
import customtkinter as ctk

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

try:
    from app.frontend.theme_config import preparar_ventana, centrar_y_mostrar_ventana
except ImportError:
    def preparar_ventana(w): pass
    def centrar_y_mostrar_ventana(w): pass

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
    
    # Color del borde del frame padre (mismo estilo que crear_cliente)
    frm_border = entry.master
    col_input = "#f9fafb" if ctk.get_appearance_mode() == "Light" else "#374151"
    if valor == "":
        if valido:
            frm_border.configure(border_width=0, fg_color=col_input)
        else:
            frm_border.configure(border_width=2, border_color="#ef4444", fg_color=col_input)
    else:
        frm_border.configure(border_width=2, border_color="#10b981" if valido else "#ef4444", fg_color=col_input)
    
    # Actualizar label de feedback
    if label_feedback:
        if "Opcional" in mensaje or "Obligatorio" in mensaje:
            color = "#9ca3af" if "Opcional" in mensaje else "#6b7280"
        else:
            color = "#10b981" if valido else "#ef4444"
        label_feedback.configure(text=mensaje, text_color=color)
    return valido

# ============================================================================
# 🗃️ INTERFAZ PRINCIPAL
# ============================================================================
def ui_crear_proveedor(parent: tk.Misc, backend, id_proveedor_a_editar: Optional[int] = None, callback_on_save: Optional[callable] = None):
    col_bg = "#f3f4f6" if ctk.get_appearance_mode() == "Light" else "#111827"
    col_card = "#ffffff" if ctk.get_appearance_mode() == "Light" else "#1f2937"
    col_border = "#e5e7eb" if ctk.get_appearance_mode() == "Light" else "#374151"
    col_input_bg = "#f9fafb" if ctk.get_appearance_mode() == "Light" else "#374151"
    col_input_fg = "#1f2937" if ctk.get_appearance_mode() == "Light" else "#f9fafb"

    win = ctk.CTkToplevel(parent)
    preparar_ventana(win)
    win.geometry("720x650")
    win.resizable(False, False)
    win.title("Editar Empresa" if id_proveedor_a_editar else "Nueva Empresa Proveedora")

    datos_prov = {}
    if id_proveedor_a_editar:
        try:
            datos_prov = backend.obtener_proveedor_completo(id_proveedor_a_editar) or {}
        except: datos_prov = {}

    def _limpiar(val):
        if val is None or str(val).strip().lower() == 'none':
            return ''
        return str(val)


    var_empresa = tk.StringVar(value=_limpiar(datos_prov.get('empresa')))
    var_cuit = tk.StringVar(value=_limpiar(datos_prov.get('cuit')))
    var_tel = tk.StringVar(value=_limpiar(datos_prov.get('telefono')))
    var_email = tk.StringVar(value=_limpiar(datos_prov.get('email')))
    var_direccion = tk.StringVar(value=_limpiar(datos_prov.get('direccion')))

    # Botones al fondo (empacados PRIMERO para que tkinter les reserve espacio)
    btn_frm = ctk.CTkFrame(win, fg_color="transparent")
    btn_frm.pack(fill="x", side="bottom", pady=(5, 20), padx=25)
    
    ctk.CTkButton(btn_frm, text="Cancelar", command=win.destroy, fg_color="#ef4444", hover_color="#dc2626", 
                  font=("Segoe UI", 15, "bold"), width=150, height=55).pack(side="left")
    ctk.CTkButton(btn_frm, text="💾 Guardar Empresa", command=lambda: guardar(), fg_color="#10b981", hover_color="#059669", 
                  font=("Segoe UI", 18, "bold"), width=250, height=55).pack(side="right")

    # Card principal con título (mismo estilo que crear_cliente)
    frm = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
    frm.pack(fill="both", expand=True, padx=25, pady=(25, 10))

    ctk.CTkLabel(frm, text="Datos de la Empresa", font=("Segoe UI", 20, "bold"), 
                 text_color="#1f2937" if col_bg == "#f3f4f6" else "white").grid(
        row=0, column=0, columnspan=3, pady=(15, 25), sticky="w", padx=20)

    fila = 1
    def crear_campo(label, var, val_teclado, tipo_val, obligatorio=True):
        nonlocal fila
        ctk.CTkLabel(frm, text=f"{label} {'(*)' if obligatorio else ''}", 
                     font=("Segoe UI", 14, "bold"), 
                     text_color="#374151" if col_bg == "#f3f4f6" else "#9ca3af", 
                     anchor="w").grid(row=fila, column=0, sticky="w", pady=10, padx=(20, 10))
        
        frm_input = ctk.CTkFrame(frm, fg_color=col_input_bg, corner_radius=8, border_width=0)
        frm_input.grid(row=fila, column=1, sticky="w", pady=10, padx=5)
        e = ctk.CTkEntry(frm_input, textvariable=var, font=("Segoe UI", 13), width=280, height=45,
                         fg_color="transparent", border_width=0)
        e.configure(validate="key", validatecommand=(win.register(val_teclado), '%P'))
        e.pack(padx=2, pady=2)
        
        lbl_fb = ctk.CTkLabel(frm, text="", font=("Segoe UI", 13, "bold"), width=120, anchor="w")
        lbl_fb.grid(row=fila, column=2, sticky="w", padx=10)
        
        if label == "Dirección" and not var.get():
            lbl_fb.configure(text="⚪ Opcional", text_color="#6b7280")

        if tipo_val:
            e.bind('<KeyRelease>', lambda ev: validar_y_colorear(e, tipo_val, lbl_fb))
            validar_y_colorear(e, tipo_val, lbl_fb)
        else:
            def _colorear_opcional(e_evt=None, ent=e, lbl=lbl_fb):
                val = ent.get().strip()
                if val:
                    lbl.configure(text="✓ Válido", text_color="#10b981")
                else:
                    lbl.configure(text="⚪ Opcional", text_color="#6b7280")
            e.bind('<KeyRelease>', _colorear_opcional)
            _colorear_opcional()
        
        fila += 1
        return e


    ent_emp = crear_campo("Nombre Empresa", var_empresa, lambda t: len(t) < 50, 'empresa')
    ent_cuit = crear_campo("CUIT Empresa", var_cuit, validar_cuit, 'cuit')
    ent_tel = crear_campo("Teléfono", var_tel, validar_telefono, 'telefono', True)
    ent_ema = crear_campo("Email", var_email, lambda t: True, 'email', False)
    ent_dir = crear_campo("Dirección", var_direccion, lambda t: True, None, False)

    def guardar():
        empresa = var_empresa.get().strip()
        cuit = var_cuit.get().strip()
        tel = var_tel.get().strip()
        
        if len(empresa) < 3:
            messagebox.showwarning("Campo requerido", "El Nombre de la empresa debe tener al menos 3 caracteres.", parent=win)
            return
        if len(cuit) != 11:
            messagebox.showwarning("Campo requerido", f"El CUIT debe tener exactamente 11 dígitos (tiene {len(cuit)}).", parent=win)
            return
        if len(tel) != 10:
            messagebox.showwarning("Campo requerido", f"El Teléfono debe tener exactamente 10 dígitos (tiene {len(tel)}).", parent=win)
            return

        v1 = validar_y_colorear(ent_emp, 'empresa')
        v2 = validar_y_colorear(ent_cuit, 'cuit')
        v3 = validar_y_colorear(ent_tel, 'telefono')
        if not (v1 and v2 and v3): 
            messagebox.showwarning("Atención", "Revisá los campos obligatorios resaltados.", parent=win)
            return
            
        try:
            p = {
                'empresa': var_empresa.get().strip(),
                'cuit': var_cuit.get().strip(),
                'telefono': var_tel.get().strip(),
                'email': var_email.get().strip(),
                'direccion': var_direccion.get().strip()
            }
            if not p['empresa'] or not p['cuit']:
                messagebox.showwarning("Campo requerido", "Nombre Empresa y CUIT son obligatorios.", parent=win)
                return

            if id_proveedor_a_editar:
                backend.actualizar_proveedor(
                    id_proveedor_a_editar, 
                    p['empresa'], p['empresa'], p['cuit'], '', p['telefono'], p['email'], p['direccion']
                )
            else:
                backend.insertar_proveedor(
                    p['empresa'], p['empresa'], p['cuit'], '', p['telefono'], p['email'], p['direccion']
                )
            
            messagebox.showinfo("Éxito", "Proveedor guardado correctamente.", parent=win)
            if callback_on_save: callback_on_save()
            win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}", parent=win)

    # (Botones ya empacados arriba antes del card principal)

    configurar_navegacion_ventana(win)
    win.transient(parent)
    centrar_y_mostrar_ventana(win)
    win.grab_set()
    ent_emp.focus_set()