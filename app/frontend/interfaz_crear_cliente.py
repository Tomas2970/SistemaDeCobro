# app/frontend/interfaz_crear_cliente.py
import tkinter as tk
from tkinter import messagebox, Toplevel

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

# === VALIDADORES ORIGINALES ===
def validar_solo_letras(texto):
    if texto == "": return True
    import unicodedata
    for c in texto:
        if c.isspace(): continue
        normalized = unicodedata.normalize('NFD', c)
        if any(char.isalpha() for char in normalized) or c in 'ñÑ': continue
        return False
    return True

def validar_dni(texto):
    return (len(texto) <= 8 and texto.isdigit()) or texto == ""

def validar_telefono(texto):
    return (len(texto) <= 10 and texto.isdigit()) or texto == ""

def validar_decimal(texto):
    if texto == "": return True
    import re
    return bool(re.match(r'^[0-9]*[.,]?[0-9]*$', texto))

# === LÓGICA DE COLOREO Y MENSAJES REFINADA ===
def validar_y_colorear(entry, tipo_validacion, label_feedback=None):
    valor = entry.get().strip()
    valido, mensaje = False, ""
    
    if tipo_validacion == 'nombre':
        if len(valor) == 0: 
            valido, mensaje = False, "⚠️ Obligatorio"
        elif len(valor) < 3: 
            # Ya no cuenta letras, solo indica que es obligatorio hasta cumplir el mínimo
            valido, mensaje = False, "⚠️ Obligatorio"
        else: 
            valido, mensaje = True, "✓ Válido"
        
    elif tipo_validacion == 'dni':
        if len(valor) == 0: 
            # Estado inicial neutro
            valido, mensaje = False, "⚠️ Obligatorio"
        elif 7 <= len(valor) <= 8: 
            valido, mensaje = True, "✓ Válido"
        else: 
            valido, mensaje = False, "❌ DNI Inválido"
            
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

    # Aplicar colores: Blanco si está vacío, Verde si es válido, Rojo si hay error real
    if valor == "":
        entry.config(bg="#ffffff")
    else:
        entry.config(bg="#d1fae5" if valido else "#fee2e2")
    
    if label_feedback:
        label_feedback.config(text=mensaje, fg="#059669" if valido else ("#6b7280" if "Opcional" in mensaje or "Obligatorio" in mensaje else "#dc2626"))

def ui_crear_cliente(parent, backend, id_cliente_a_editar=None):
    win = Toplevel(parent)
    win.title("Editar Cliente" if id_cliente_a_editar else "Nuevo Cliente")
    win.geometry("630x560") 
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    var_nombre, var_dni, var_tel = tk.StringVar(), tk.StringVar(), tk.StringVar()
    var_email, var_dir, var_limite = tk.StringVar(), tk.StringVar(), tk.StringVar(value="50000.00")

    if id_cliente_a_editar:
        cli = backend.obtener_cliente_para_editar(id_cliente_a_editar)
        if cli:
            def _limpiar(val):
                """Convierte None o la cadena 'None' a vacío."""
                if val is None or str(val).strip().lower() == 'none':
                    return ''
                return str(val)
            var_nombre.set(_limpiar(cli.get('nombre')))
            var_dni.set(_limpiar(cli.get('dni')))
            var_tel.set(_limpiar(cli.get('telefono')))
            var_email.set(_limpiar(cli.get('email')))
            var_dir.set(_limpiar(cli.get('direccion')))
            var_limite.set(_limpiar(cli.get('limite_credito')) or '50000.00')

    frm = tk.Frame(win, bg="#f4f4f8", padx=20, pady=20)
    frm.pack(fill="both", expand=True)

    fila = 1
    def crear_campo(label, var, val_teclado, tipo_val, obligatorio=True):
        nonlocal fila
        tk.Label(frm, text=f"{label} {'(*)' if obligatorio else ''}", bg="#f4f4f8", anchor="w", width=16).grid(row=fila, column=0, sticky="w", pady=5)
        e = tk.Entry(frm, textvariable=var, width=28, font=("Segoe UI", 10), validate="key", validatecommand=val_teclado)
        e.grid(row=fila, column=1, sticky="w", pady=5, padx=5)
        
        lbl_fb = tk.Label(frm, text="", bg="#f4f4f8", font=("Segoe UI", 9), width=25, anchor="w")
        lbl_fb.grid(row=fila, column=2, sticky="w")
        
        # Seteo inicial de "Opcional" para Dirección si está vacía
        if label == "Dirección" and not var.get():
            lbl_fb.config(text="⚪ Opcional", fg="#6b7280")

        if tipo_val:
            e.bind('<KeyRelease>', lambda ev: validar_y_colorear(e, tipo_val, lbl_fb))
            validar_y_colorear(e, tipo_val, lbl_fb)
            
        fila += 1
        return e

    vc_letras = (win.register(validar_solo_letras), '%P')
    vc_dni = (win.register(validar_dni), '%P')
    vc_tel = (win.register(validar_telefono), '%P')
    vc_decimal = (win.register(validar_decimal), '%P')

    crear_campo("Nombre Completo", var_nombre, vc_letras, 'nombre')
    crear_campo("DNI", var_dni, vc_dni, 'dni')
    crear_campo("Teléfono", var_tel, vc_tel, 'telefono', False)
    crear_campo("Email", var_email, (win.register(lambda t: True), '%P'), 'email', False)
    
    # 🔥 Ahora Dirección muestra "Opcional" igual que los otros
    crear_campo("Dirección", var_dir, (win.register(lambda t: True), '%P'), None, False)
    
    crear_campo("Límite Crédito", var_limite, vc_decimal, 'monto')

    def guardar():
        nom = var_nombre.get().strip()
        dni = var_dni.get().strip()
        limite_str = var_limite.get().strip()
        
        # Validaciones específicas
        if not nom or len(nom) < 3:
            messagebox.showwarning("Campo requerido", "El Nombre Completo debe tener al menos 3 caracteres.", parent=win)
            return
        if len(dni) < 7:
            messagebox.showwarning("Campo requerido", "El DNI debe tener entre 7 y 8 dígitos.", parent=win)
            return
        if not limite_str:
            messagebox.showwarning("Campo requerido", "Debe ingresar un Límite de Crédito.", parent=win)
            return

        # Validar teléfono si fue ingresado parcialmente
        tel = var_tel.get().strip()
        if tel and len(tel) < 10:
            messagebox.showwarning("Teléfono inválido", f"El teléfono tiene {len(tel)} dígitos. Debe tener 10 o dejarlo vacío.", parent=win)
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

    btn_frm = tk.Frame(win, bg="#f4f4f8", pady=15)
    btn_frm.pack(fill="x")
    tk.Button(btn_frm, text="💾 Guardar", command=guardar, bg="#16a34a", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=25, pady=10).pack(side="left", padx=30)
    tk.Button(btn_frm, text="Cancelar", command=win.destroy, bg="#6b7280", fg="white", relief="flat", padx=20, pady=10).pack(side="right", padx=30)

    configurar_navegacion_ventana(win)
    win.grab_set()
    return win