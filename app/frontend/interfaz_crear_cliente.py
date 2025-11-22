# app/frontend/interfaz_crear_cliente.py
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional 

# Importamos la navegación por teclado
try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

# Componentes personalizados
try:
    from app.frontend.componentes_ui import EntryNumerico, EntryDecimal
except ImportError:
    # Fallback simple por si acaso
    class EntryNumerico(ttk.Entry):
        def __init__(self, parent, max_chars=None, *args, **kwargs):
            super().__init__(parent, *args, **kwargs)
            self.max_chars = max_chars
    class EntryDecimal(ttk.Entry):
        def __init__(self, parent, *args, **kwargs):
            super().__init__(parent, *args, **kwargs)

# Validaciones
try:
    from app.frontend.validaciones import validar_email
except ImportError:
    def validar_email(email): return True

def ui_crear_cliente(parent: tk.Misc, backend, usuario: dict, id_cliente_a_editar: Optional[int] = None):
    
    win = tk.Toplevel(parent)
    
    modo_edicion = id_cliente_a_editar is not None
    titulo = "Editar Cliente" if modo_edicion else "Crear Cliente"
    win.title(titulo)
    win.geometry("520x420") # Un poco más alta para los radiobuttons
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # Cargar datos si es edición
    datos_cliente = {}
    doc_actual = ""
    
    if modo_edicion:
        try:
            datos_cliente = backend.obtener_cliente_para_editar(id_cliente_a_editar)
            if not datos_cliente:
                messagebox.showerror("Error", "No se pudieron cargar los datos.", parent=win)
                win.destroy()
                return
            doc_actual = datos_cliente.get('dni') or ""
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {e}", parent=win)
            win.destroy()
            return

    # --- Lógica de Documento Dinámico ---
    def al_cambiar_tipo_doc():
        tipo = var_tipo_doc.get()
        if tipo == "DNI":
            lbl_doc.config(text="DNI (8 dígitos) *:")
            entry_dni.max_chars = 8
            # Si hay texto y es muy largo, avisar visualmente o cortar (opcional)
            contenido = entry_dni.get()
            if len(contenido) > 8:
                entry_dni.delete(8, tk.END)
        else:
            lbl_doc.config(text="CUIT (11 dígitos) *:")
            entry_dni.max_chars = 11

    def on_guardar():
        nombre = entry_nombre.get().strip()
        doc_numero = entry_dni.get().strip()
        direccion = entry_direccion.get().strip()
        telefono = entry_telefono.get().strip()
        email = entry_email.get().strip()
        limite_str = entry_limite.get().strip()
        tipo_doc = var_tipo_doc.get()
        
        # 1. Validar Nombre
        if not nombre:
            messagebox.showwarning("Faltan datos", "El campo 'Nombre' es obligatorio.", parent=win)
            entry_nombre.focus_set()
            return
        
        # 2. Validar Documento (DNI o CUIT)
        if not doc_numero:
            messagebox.showwarning("Faltan datos", f"El {tipo_doc} es obligatorio.", parent=win)
            entry_dni.focus_set()
            return
            
        # Validaciones de longitud específicas
        if tipo_doc == "DNI":
            if len(doc_numero) < 7:
                messagebox.showwarning("DNI Inválido", "El DNI debe tener al menos 7 u 8 números.", parent=win)
                entry_dni.focus_set()
                return
        else: # CUIT
            if len(doc_numero) != 11:
                messagebox.showwarning("CUIT Inválido", "El CUIT debe tener exactamente 11 números.", parent=win)
                entry_dni.focus_set()
                return

        # 3. Validar Email
        if email and not validar_email(email):
            messagebox.showwarning("Email inválido", "El correo no es válido.", parent=win)
            entry_email.focus_set()
            return
        
        # 4. Validar Límite
        try:
            limite = float(limite_str.replace(",", ".") or "0")
            if limite < 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Error", "El límite de crédito debe ser positivo.", parent=win)
            entry_limite.focus_set()
            return
        
        # 5. Guardar
        try:
            if modo_edicion:
                exito = backend.actualizar_cliente(
                    id_cliente=id_cliente_a_editar,
                    nombre=nombre,
                    dni=doc_numero, # Guardamos CUIT o DNI en el mismo campo 'dni' de la BD
                    direccion=direccion,
                    telefono=telefono,
                    email=email,
                    limite_credito=limite,
                )
                if exito:
                    messagebox.showinfo("Éxito", "Cliente actualizado.", parent=win)
                    win.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo actualizar.", parent=win)
            else:
                exito = backend.crear_cliente(
                    nombre=nombre,
                    dni=doc_numero,
                    direccion=direccion,
                    telefono=telefono,
                    email=email,
                    limite_credito=limite,
                )
                if exito:
                    messagebox.showinfo("Éxito", "Cliente creado.", parent=win)
                    win.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo crear.", parent=win)
        
        except Exception as e:
            err_msg = str(e)
            if "DNI_DUPLICADO" in err_msg or "Duplicate entry" in err_msg:
                messagebox.showerror("Duplicado", f"Ya existe un cliente con ese {tipo_doc}.", parent=win)
            else:
                messagebox.showerror("Error", f"Ocurrió un error al guardar:\n{e}", parent=win)

    # --- Construcción de la Interfaz ---
    
    frame_form = tk.Frame(win, bg="#f4f4f8")
    frame_form.pack(padx=30, pady=15, fill=tk.X)
    
    current_row = 0
    def add_field(label_widget, widget):
        nonlocal current_row
        label_widget.grid(row=current_row, column=0, sticky="e", padx=5, pady=8)
        widget.grid(row=current_row, column=1, sticky="w", padx=5, pady=8)
        current_row += 1

    # 1. Nombre
    lbl_nom = tk.Label(frame_form, text="Nombre (*):", bg="#f4f4f8", anchor="e")
    entry_nombre = ttk.Entry(frame_form, width=40)
    entry_nombre.insert(0, datos_cliente.get('nombre') or '')
    add_field(lbl_nom, entry_nombre)
    
    # 2. Selector Tipo Documento (Radiobuttons)
    # Determinamos valor inicial: si editamos y tiene 11 chars -> CUIT, sino DNI
    valor_inicial = "CUIT" if len(doc_actual) > 8 else "DNI"
    var_tipo_doc = tk.StringVar(value=valor_inicial)
    
    frame_radios = tk.Frame(frame_form, bg="#f4f4f8")
    
    rb_dni = tk.Radiobutton(frame_radios, text="DNI (Cliente)", variable=var_tipo_doc, 
                            value="DNI", bg="#f4f4f8", command=al_cambiar_tipo_doc)
    rb_cuit = tk.Radiobutton(frame_radios, text="CUIT (Comercio)", variable=var_tipo_doc, 
                             value="CUIT", bg="#f4f4f8", command=al_cambiar_tipo_doc)
    
    rb_dni.pack(side=tk.LEFT, padx=(0, 10))
    rb_cuit.pack(side=tk.LEFT)
    
    lbl_tipo = tk.Label(frame_form, text="Tipo:", bg="#f4f4f8", anchor="e")
    add_field(lbl_tipo, frame_radios)

    # 3. Campo Documento (Numérico dinámico)
    lbl_doc = tk.Label(frame_form, text="DNI (8 dígitos) *:", bg="#f4f4f8", anchor="e")
    entry_dni = EntryNumerico(frame_form, max_chars=8, width=25) 
    entry_dni.insert(0, doc_actual)
    add_field(lbl_doc, entry_dni)
    
    # Ejecutar lógica inicial para setear max_chars correcto según lo que cargamos
    al_cambiar_tipo_doc()
    
    # 4. Dirección
    lbl_dir = tk.Label(frame_form, text="Dirección:", bg="#f4f4f8", anchor="e")
    entry_direccion = ttk.Entry(frame_form, width=40)
    entry_direccion.insert(0, datos_cliente.get('direccion') or '')
    add_field(lbl_dir, entry_direccion)
    
    # 5. Teléfono
    lbl_tel = tk.Label(frame_form, text="Teléfono:", bg="#f4f4f8", anchor="e")
    entry_telefono = ttk.Entry(frame_form, width=40)
    entry_telefono.insert(0, datos_cliente.get('telefono') or '')
    add_field(lbl_tel, entry_telefono)
    
    # 6. Email
    lbl_email = tk.Label(frame_form, text="Email:", bg="#f4f4f8", anchor="e")
    entry_email = ttk.Entry(frame_form, width=40)
    entry_email.insert(0, datos_cliente.get('email') or '')
    add_field(lbl_email, entry_email)

    # 7. Límite Crédito
    lbl_lim = tk.Label(frame_form, text="Límite Crédito ($):", bg="#f4f4f8", anchor="e")
    entry_limite = EntryDecimal(frame_form, width=20)
    limite_val = datos_cliente.get('limite_credito', 50000.00)
    try:
        entry_limite.insert(0, f"{float(limite_val):.2f}")
    except (ValueError, TypeError):
        entry_limite.insert(0, "50000.00")
    add_field(lbl_lim, entry_limite)

    # Botones
    frame_botones = tk.Frame(win, bg="#f4f4f8")
    frame_botones.pack(pady=15)

    tk.Button(
        frame_botones, text="Guardar", bg="#4CAF50", fg="white", width=15, command=on_guardar
    ).pack(side=tk.LEFT, padx=10)

    tk.Button(
        frame_botones, text="Cancelar", bg="#f44336", fg="white", width=15, command=win.destroy
    ).pack(side=tk.LEFT, padx=10)

    configurar_navegacion_ventana(win)
    win.after(50, lambda: entry_nombre.focus_set())
    win.grab_set()
    win.transient(parent)