# app/frontend/interfaz_crear_cliente.py
import tkinter as tk
from app.frontend import custom_dialogs as messagebox
import customtkinter as ctk
from app.frontend.validaciones_ui import (
    ValidadoresTeclado,
    ValidadoresVisuales,
    ValidadorFormulario,
    conectar_validacion_ctk,
    registrar_validadores_teclado_ctk,
)

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass


def ui_crear_cliente(parent, backend, id_cliente_a_editar=None, callback_on_save=None):
    win = ctk.CTkToplevel(parent)
    from app.frontend.theme_config import preparar_ventana, centrar_y_mostrar_ventana
    preparar_ventana(win)
    win.title("Editar Cliente" if id_cliente_a_editar else "Nuevo Cliente")
    win.geometry("720x620")
    col_bg = "#f3f4f6" if ctk.get_appearance_mode() == "Light" else "#111827"
    col_card = "#ffffff" if ctk.get_appearance_mode() == "Light" else "#1f2937"
    win.configure(fg_color=col_bg)
    win.resizable(False, False)

    var_nombre = tk.StringVar()
    var_dni    = tk.StringVar()
    var_tel    = tk.StringVar()
    var_email  = tk.StringVar()
    var_dir    = tk.StringVar()
    var_limite = tk.StringVar(value="50000.00")

    if id_cliente_a_editar:
        cli = backend.obtener_cliente_para_editar(id_cliente_a_editar)
        if cli:
            def _limpiar(val):
                if val is None or str(val).strip().lower() == 'none':
                    return ''
                return str(val)
            var_nombre.set(_limpiar(cli.get('nombre')))
            var_dni.set(_limpiar(cli.get('dni')))
            var_tel.set(_limpiar(cli.get('telefono')))
            var_email.set(_limpiar(cli.get('email')))
            var_dir.set(_limpiar(cli.get('direccion')))
            var_limite.set(_limpiar(cli.get('limite_credito')) or '50000.00')

    frm = ctk.CTkFrame(
        win, fg_color=col_card, corner_radius=10,
        border_color="#e5e7eb" if col_bg == "#f3f4f6" else "#374151",
        border_width=1
    )
    frm.pack(fill="both", expand=True, padx=25, pady=25)

    ctk.CTkLabel(
        frm, text="Datos del Cliente",
        font=("Segoe UI", 20, "bold"),
        text_color="#1f2937" if col_bg == "#f3f4f6" else "white"
    ).grid(row=0, column=0, columnspan=3, pady=(15, 25), sticky="w", padx=20)

    fila = 1

    def crear_campo(label, var, tipo_val, obligatorio=True):
        """Crea una fila label + CTkEntry + CTkLabel de feedback usando validaciones_ui."""
        nonlocal fila
        ctk.CTkLabel(
            frm, text=f"{label} {'(*)' if obligatorio else ''}",
            font=("Segoe UI", 14, "bold"),
            text_color="#374151" if col_bg == "#f3f4f6" else "#9ca3af",
            anchor="w"
        ).grid(row=fila, column=0, sticky="w", pady=10, padx=(20, 10))

        e = ctk.CTkEntry(frm, textvariable=var, font=("Segoe UI", 13), width=280, height=45)
        e.grid(row=fila, column=1, sticky="w", pady=10, padx=5)

        lbl_fb = ctk.CTkLabel(frm, text="", font=("Segoe UI", 13, "bold"), width=120, anchor="w")
        lbl_fb.grid(row=fila, column=2, sticky="w", padx=10)

        if label == "Dirección":
            # Dirección no tiene validación lógica, solo feedback estático opcional
            lbl_fb.configure(text="⚪ Opcional", text_color="#6b7280")
            e.bind('<KeyRelease>', lambda ev: lbl_fb.configure(
                text="✓ Válido" if e.get().strip() else "⚪ Opcional",
                text_color="#10b981" if e.get().strip() else "#6b7280"
            ))
        elif tipo_val:
            conectar_validacion_ctk(e, lbl_fb, tipo_val, win)

        fila += 1
        return e

    ent_nombre = crear_campo("Nombre",              var_nombre, 'nombre')
    ent_dni    = crear_campo("DNI",                 var_dni,    'dni')
    ent_tel    = crear_campo("Teléfono",             var_tel,    'telefono',  False)
    ent_email  = crear_campo("Correo Electrónico",  var_email,  'email',     False)
    _          = crear_campo("Dirección",           var_dir,    None,        False)
    ent_limite = crear_campo("Límite Crédito ($)",  var_limite, 'monto')

    def guardar():
        # ── Validación centralizada con ValidadorFormulario ──────────────────
        campos = {
            'Nombre':           (var_nombre.get(), 'nombre',   True),
            'DNI':              (var_dni.get(),    'dni',      True),
            'Límite de Crédito':(var_limite.get(), 'monto',    True),
            'Teléfono':         (var_tel.get(),    'telefono', False),
            'Email':            (var_email.get(),  'email',    False),
        }
        ok, msg = ValidadorFormulario.validar_campos(campos)
        if not ok:
            messagebox.showwarning("Campo inválido", msg, parent=win)
            return

        try:
            limite = float(var_limite.get().strip().replace(',', '.'))
            if id_cliente_a_editar:
                resultado = backend.actualizar_cliente(
                    id_cliente_a_editar,
                    var_nombre.get().strip(), var_dni.get().strip(), "",
                    var_dir.get().strip(), var_tel.get().strip(),
                    var_email.get().strip(), limite
                )
            else:
                resultado = backend.crear_cliente(
                    var_nombre.get().strip(), var_dni.get().strip(), "",
                    var_dir.get().strip(), var_tel.get().strip(),
                    var_email.get().strip(), limite
                )

            if resultado:
                messagebox.showinfo("Éxito", "Guardado correctamente", parent=win)
                win.destroy()
                if callback_on_save:
                    try:
                        callback_on_save(resultado if not id_cliente_a_editar else id_cliente_a_editar)
                    except TypeError:
                        callback_on_save()
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}", parent=win)

    btn_frm = ctk.CTkFrame(win, fg_color="transparent")
    btn_frm.pack(fill="x", side="bottom", pady=(5, 20), padx=25)

    ctk.CTkButton(
        btn_frm, text="Cancelar", command=win.destroy,
        fg_color="#ef4444", hover_color="#dc2626",
        font=("Segoe UI", 15, "bold"), width=150, height=55
    ).pack(side="left")
    ctk.CTkButton(
        btn_frm, text="💾 Guardar Cliente", command=guardar,
        fg_color="#10b981", hover_color="#059669",
        font=("Segoe UI", 18, "bold"), width=250, height=55
    ).pack(side="right")

    configurar_navegacion_ventana(win)
    centrar_y_mostrar_ventana(win)
    win.grab_set()
    return win