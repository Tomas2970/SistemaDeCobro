# app/frontend/interfaz_crear_proveedor.py
from __future__ import annotations
import tkinter as tk
from app.frontend import custom_dialogs as messagebox
from typing import Optional
import customtkinter as ctk
from app.frontend.validaciones_ui import (
    ValidadorFormulario,
    conectar_validacion_ctk,
    registrar_validadores_teclado_ctk,
)

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
# 🗃️ INTERFAZ PRINCIPAL
# ============================================================================
def ui_crear_proveedor(
    parent: tk.Misc,
    backend,
    id_proveedor_a_editar: Optional[int] = None,
    callback_on_save: Optional[callable] = None,
    usuario_actual: dict | None = None
):
    col_bg      = "#f3f4f6" if ctk.get_appearance_mode() == "Light" else "#111827"
    col_card    = "#ffffff" if ctk.get_appearance_mode() == "Light" else "#1f2937"
    col_border  = "#e5e7eb" if ctk.get_appearance_mode() == "Light" else "#374151"
    col_input   = "#f9fafb" if ctk.get_appearance_mode() == "Light" else "#374151"

    win = ctk.CTkToplevel(parent)
    preparar_ventana(win)
    win.geometry("720x650")
    win.resizable(False, False)
    win.title("Editar Empresa" if id_proveedor_a_editar else "Nueva Empresa Proveedora")

    datos_prov: dict = {}
    if id_proveedor_a_editar:
        try:
            datos_prov = backend.obtener_proveedor_completo(id_proveedor_a_editar) or {}
        except Exception:
            datos_prov = {}

    def _limpiar(val):
        if val is None or str(val).strip().lower() == 'none':
            return ''
        return str(val)

    var_empresa   = tk.StringVar(value=_limpiar(datos_prov.get('empresa')))
    var_cuit      = tk.StringVar(value=_limpiar(datos_prov.get('cuit')))
    var_tel       = tk.StringVar(value=_limpiar(datos_prov.get('telefono')))
    var_email     = tk.StringVar(value=_limpiar(datos_prov.get('email')))
    var_direccion = tk.StringVar(value=_limpiar(datos_prov.get('direccion')))

    # Botones al fondo (empacados PRIMERO para que tkinter les reserve espacio)
    btn_frm = ctk.CTkFrame(win, fg_color="transparent")
    btn_frm.pack(fill="x", side="bottom", pady=(5, 20), padx=25)

    ctk.CTkButton(
        btn_frm, text="Cancelar", command=win.destroy,
        fg_color="#ef4444", hover_color="#dc2626",
        font=("Segoe UI", 15, "bold"), width=150, height=55
    ).pack(side="left")
    ctk.CTkButton(
        btn_frm, text="💾 Guardar Empresa", command=lambda: guardar(),
        fg_color="#10b981", hover_color="#059669",
        font=("Segoe UI", 18, "bold"), width=250, height=55
    ).pack(side="right")

    # Card principal
    frm = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10,
                       border_color=col_border, border_width=1)
    frm.pack(fill="both", expand=True, padx=25, pady=(25, 10))

    ctk.CTkLabel(
        frm, text="Datos de la Empresa",
        font=("Segoe UI", 20, "bold"),
        text_color="#1f2937" if col_bg == "#f3f4f6" else "white"
    ).grid(row=0, column=0, columnspan=3, pady=(15, 25), sticky="w", padx=20)

    fila = 1

    def crear_campo(label, var, tipo_val, obligatorio=True):
        """Crea una fila label + CTkEntry (dentro de CTkFrame borde) + label feedback."""
        nonlocal fila
        ctk.CTkLabel(
            frm,
            text=f"{label} {'(*)' if obligatorio else ''}",
            font=("Segoe UI", 14, "bold"),
            text_color="#374151" if col_bg == "#f3f4f6" else "#9ca3af",
            anchor="w"
        ).grid(row=fila, column=0, sticky="w", pady=10, padx=(20, 10))

        frm_input = ctk.CTkFrame(frm, fg_color=col_input, corner_radius=8, border_width=0)
        frm_input.grid(row=fila, column=1, sticky="w", pady=10, padx=5)
        e = ctk.CTkEntry(
            frm_input, textvariable=var,
            font=("Segoe UI", 13), width=280, height=45,
            fg_color="transparent", border_width=0
        )
        e.pack(padx=2, pady=2)

        lbl_fb = ctk.CTkLabel(frm, text="", font=("Segoe UI", 13, "bold"), width=120, anchor="w")
        lbl_fb.grid(row=fila, column=2, sticky="w", padx=10)

        if tipo_val:
            conectar_validacion_ctk(e, lbl_fb, tipo_val, win)
        else:
            # Dirección: opcional sin validación lógica
            lbl_fb.configure(text="⚪ Opcional", text_color="#6b7280")
            e.bind('<KeyRelease>', lambda ev: lbl_fb.configure(
                text="✓ Válido" if e.get().strip() else "⚪ Opcional",
                text_color="#10b981" if e.get().strip() else "#6b7280"
            ))

        fila += 1
        return e

    crear_campo("Nombre Empresa", var_empresa,   'nombre_empresa',      True)
    crear_campo("CUIT Empresa",   var_cuit,      'cuit_obligatorio',    True)
    crear_campo("Teléfono",        var_tel,       'telefono_obligatorio', True)
    crear_campo("Email",           var_email,     'email',               False)
    crear_campo("Dirección",       var_direccion, None,                  False)

    def guardar():
        # ── Validación centralizada ──────────────────────────────────────────
        campos = {
            'Nombre Empresa': (var_empresa.get(), 'nombre_empresa',      True),
            'CUIT':           (var_cuit.get(),    'cuit_obligatorio',    True),
            'Teléfono':        (var_tel.get(),     'telefono_obligatorio', True),
            'Email':           (var_email.get(),   'email',               False),
        }
        ok, msg = ValidadorFormulario.validar_campos(campos)
        if not ok:
            messagebox.showwarning("Campo inválido", msg, parent=win)
            return

        try:
            p = {
                'empresa':   var_empresa.get().strip(),
                'cuit':      var_cuit.get().strip(),
                'telefono':  var_tel.get().strip(),
                'email':     var_email.get().strip(),
                'direccion': var_direccion.get().strip(),
            }
            if id_proveedor_a_editar:
                backend.actualizar_proveedor(
                    id_proveedor_a_editar,
                    p['empresa'], p['empresa'], p['cuit'], '',
                    p['telefono'], p['email'], p['direccion'],
                    id_usuario_admin=usuario_actual['id_usuario'] if usuario_actual else None,
                    usuario_actual=usuario_actual
                )
            else:
                backend.insertar_proveedor(
                    p['empresa'], p['empresa'], p['cuit'], '',
                    p['telefono'], p['email'], p['direccion'],
                    id_usuario_admin=usuario_actual['id_usuario'] if usuario_actual else None,
                    usuario_actual=usuario_actual
                )

            messagebox.showinfo("Éxito", "Proveedor guardado correctamente.", parent=win)
            if callback_on_save:
                callback_on_save()
            win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}", parent=win)

    configurar_navegacion_ventana(win)
    win.transient(parent)
    centrar_y_mostrar_ventana(win)
    win.grab_set()