# app/frontend/interfaz_crear_cliente.py
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

# === VALIDADORES ORIGINALES ===
def validar_solo_letras(texto):
    if texto == "": return True
    if len(texto) > 50: return False
    import unicodedata
    for c in texto:
        if c.isspace(): continue
        normalized = unicodedata.normalize('NFD', c)
        if any(char.isalpha() for char in normalized) or c in 'ñÑ': continue
        return False
    return True

def validar_dni(texto): return (len(texto) <= 8 and texto.isdigit()) or texto == ""
def validar_telefono(texto): return (len(texto) <= 10 and texto.isdigit()) or texto == ""
def validar_decimal(texto):
    if texto == "": return True
    import re
    return bool(re.match(r'^[0-9]*[.,]?[0-9]*$', texto))

# === LÓGICA DE COLOREO ===
def validar_y_colorear(entry, tipo_validacion, label_feedback=None):
    valor = entry.get().strip()
    valido, mensaje = False, ""
    
    if tipo_validacion == 'nombre':
        if len(valor) == 0: valido, mensaje = False, "⚠️ Obligatorio"
        elif len(valor) < 3: valido, mensaje = False, "⚠️ Obligatorio"
        else: valido, mensaje = True, "✓ Válido"
    elif tipo_validacion == 'dni':
        if len(valor) == 0: valido, mensaje = False, "⚠️ Obligatorio"
        elif 7 <= len(valor) <= 8: valido, mensaje = True, "✓ Válido"
        else: valido, mensaje = False, "❌ DNI Inválido"
    elif tipo_validacion == 'telefono':
        if len(valor) == 0: valido, mensaje = True, "⚪ Opcional"
        elif len(valor) == 10: valido, mensaje = True, "✓ Válido"
        else: valido, mensaje = False, f"❌ Faltan {10-len(valor)} nros"
    elif tipo_validacion == 'email':
        if len(valor) == 0: valido, mensaje = True, "⚪ Opcional"
        else:
            if "@" not in valor: valido, mensaje = False, "❌ Falta @"
            elif "." not in valor.split("@")[-1]: valido, mensaje = False, "❌ Falta dominio"
            else:
                import re
                patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                valido = bool(re.match(patron, valor))
                mensaje = "✓ Válido" if valido else "❌ Formato incorrecto"
    elif tipo_validacion == 'monto':
        if len(valor) == 0: valido, mensaje = False, "⚠️ Obligatorio"
        else:
            try:
                m = float(valor.replace(',', '.'))
                if m >= 0: valido, mensaje = True, "✓ Válido"
                else: valido, mensaje = False, "❌ Debe ser > 0"
            except: valido, mensaje = False, "❌ Número inválido"

    # Color entry
    frm_border = entry.master
    # Obtener el color desde el CTkFrame padre o hardcodear si es necesario
    col_input = "#f9fafb" if ctk.get_appearance_mode() == "Light" else "#374151"
    if valor == "": 
        frm_border.configure(border_width=0, fg_color=col_input)
    else: 
        frm_border.configure(border_width=2, border_color="#10b981" if valido else "#ef4444", fg_color=col_input)
    
    # Color label feedback CTk
    if label_feedback:
        if "Opcional" in mensaje or "Obligatorio" in mensaje:
            color = "#9ca3af" if "Opcional" in mensaje else "#6b7280" # Gris un poco mas claro para opcional
        else:
            color = "#10b981" if valido else "#ef4444"
        label_feedback.configure(text=mensaje, text_color=color)

def ui_crear_cliente(parent, backend, id_cliente_a_editar=None):
    win = ctk.CTkToplevel(parent)
    win.title("Editar Cliente" if id_cliente_a_editar else "Nuevo Cliente")
    win.geometry("720x620") 
    col_bg = "#f3f4f6" if ctk.get_appearance_mode()=="Light" else "#111827"
    col_card = "#ffffff" if ctk.get_appearance_mode()=="Light" else "#1f2937"
    win.configure(fg_color=col_bg)
    win.resizable(False, False)

    col_input_bg = "#f9fafb" if ctk.get_appearance_mode() == "Light" else "#374151"
    col_input_fg = "#1f2937" if ctk.get_appearance_mode() == "Light" else "#f9fafb"

    var_nombre, var_dni, var_tel = tk.StringVar(), tk.StringVar(), tk.StringVar()
    var_email, var_dir, var_limite = tk.StringVar(), tk.StringVar(), tk.StringVar(value="50000.00")

    if id_cliente_a_editar:
        cli = backend.obtener_cliente_para_editar(id_cliente_a_editar)
        if cli:
            def _limpiar(val):
                if val is None or str(val).strip().lower() == 'none': return ''
                return str(val)
            var_nombre.set(_limpiar(cli.get('nombre')))
            var_dni.set(_limpiar(cli.get('dni')))
            var_tel.set(_limpiar(cli.get('telefono')))
            var_email.set(_limpiar(cli.get('email')))
            var_dir.set(_limpiar(cli.get('direccion')))
            var_limite.set(_limpiar(cli.get('limite_credito')) or '50000.00')

    frm = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_color="#e5e7eb" if col_bg=="#f3f4f6" else "#374151", border_width=1)
    frm.pack(fill="both", expand=True, padx=25, pady=25)

    ctk.CTkLabel(frm, text="Datos del Cliente", font=("Segoe UI", 20, "bold"), text_color="#1f2937" if col_bg=="#f3f4f6" else "white").grid(row=0, column=0, columnspan=3, pady=(15, 25), sticky="w", padx=20)

    fila = 1
    def crear_campo(label, var, val_teclado, tipo_val, obligatorio=True):
        nonlocal fila
        ctk.CTkLabel(frm, text=f"{label} {'(*)' if obligatorio else ''}", font=("Segoe UI", 14, "bold"), text_color="#374151" if col_bg=="#f3f4f6" else "#9ca3af", anchor="w").grid(row=fila, column=0, sticky="w", pady=10, padx=(20, 10))
        
        e = ctk.CTkEntry(frm, textvariable=var, font=("Segoe UI", 13), width=280, height=45)
        if val_teclado:
            e.configure(validate="key", validatecommand=val_teclado)
        e.grid(row=fila, column=1, sticky="w", pady=10, padx=5)
        
        lbl_fb = ctk.CTkLabel(frm, text="", font=("Segoe UI", 13, "bold"), width=120, anchor="w")
        lbl_fb.grid(row=fila, column=2, sticky="w", padx=10)
        
        if label == "Dirección" and not var.get():
            lbl_fb.configure(text="⚪ Opcional", text_color="#6b7280")

        if tipo_val:
            e.bind('<KeyRelease>', lambda ev: validar_y_colorear(e, tipo_val, lbl_fb))
            validar_y_colorear(e, tipo_val, lbl_fb)
            
        fila += 1
        return e

    vc_letras = (win.register(validar_solo_letras), '%P')
    vc_dni = (win.register(validar_dni), '%P')
    vc_tel = (win.register(validar_telefono), '%P')
    vc_decimal = (win.register(validar_decimal), '%P')

    crear_campo("Nombre", var_nombre, vc_letras, 'nombre')
    crear_campo("DNI", var_dni, vc_dni, 'dni')
    crear_campo("Teléfono", var_tel, vc_tel, 'telefono', False)
    crear_campo("Correo Electrónico", var_email, (win.register(lambda t: True), '%P'), 'email', False)
    crear_campo("Dirección", var_dir, (win.register(lambda t: True), '%P'), None, False)
    crear_campo("Límite Crédito ($)", var_limite, vc_decimal, 'monto')

    def guardar():
        nom = var_nombre.get().strip()
        dni = var_dni.get().strip()
        limite_str = var_limite.get().strip()
        
        if not nom or len(nom) < 3:
            messagebox.showwarning("Campo requerido", "El Nombre debe tener al menos 3 caracteres.", parent=win)
            return
        if len(dni) < 7 or len(dni) > 8:
            messagebox.showwarning("Campo requerido", "El DNI debe tener 7 u 8 dígitos.", parent=win)
            return
        if not limite_str:
            messagebox.showwarning("Campo requerido", "Debe ingresar un Límite de Crédito.", parent=win)
            return

        tel = var_tel.get().strip()
        if tel and len(tel) < 10:
            messagebox.showwarning("Teléfono inválido", f"El teléfono tiene {len(tel)} dígitos. Debe tener 10 o dejarlo vacío.", parent=win)
            return

        import re
        email = var_email.get().strip()
        if email:
            patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(patron, email):
                messagebox.showwarning("Email inválido", "El email ingresado no tiene un formato válido.", parent=win)
                return

        try:
            limite = float(limite_str.replace(',', '.'))
            if id_cliente_a_editar:
                ok = backend.actualizar_cliente(id_cliente_a_editar, nom, dni, dni, var_dir.get(), var_tel.get(), var_email.get(), limite)
            else:
                ok = backend.crear_cliente(nom, dni, dni, var_dir.get(), var_tel.get(), var_email.get(), limite)
            
            if ok:
                messagebox.showinfo("Éxito", "Guardado correctamente", parent=win)
                win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}", parent=win)

    btn_frm = ctk.CTkFrame(win, fg_color="transparent")
    btn_frm.pack(fill="x", side="bottom", pady=(5, 20), padx=25)
    
    ctk.CTkButton(btn_frm, text="Cancelar", command=win.destroy, fg_color="#ef4444", hover_color="#dc2626", font=("Segoe UI", 15, "bold"), width=150, height=55).pack(side="left")
    ctk.CTkButton(btn_frm, text="💾 Guardar Cliente", command=guardar, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 18, "bold"), width=250, height=55).pack(side="right")

    configurar_navegacion_ventana(win)
    win.grab_set()
    return win