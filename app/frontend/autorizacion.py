# app/frontend/autorizacion.py
# ============================================
# Módulo centralizado de autorización HÍBRIDO (Remoto + Físico)
# Patrón "Supervisor Override" para acciones restringidas
# ============================================
import tkinter as tk
import logging
from app.frontend import custom_dialogs as messagebox

logger = logging.getLogger(__name__)

try:
    from app.frontend.theme_config import get_color, preparar_ventana, centrar_y_mostrar_ventana
except ImportError:
    def get_color(k): return "#000000"
    def preparar_ventana(w): pass
    def centrar_y_mostrar_ventana(w): pass


# =========================================================
# LÓGICA DE INTERFAZ
# =========================================================
def solicitar_autorizacion_supervisor(parent, backend, usuario_actual, callback_exito=None, roles_permitidos=(1, 3), 
                                      tipo_operacion="Operación Restringida", motivo="Autorización de supervisor requerida"):
    """
    Muestra el modal de autorización presencial.
    """
    import customtkinter as ctk
    
    popup = ctk.CTkToplevel(parent)
    popup.title("🔓 Autorización Requerida")
    popup.geometry("400x320")
    preparar_ventana(popup)
    popup.resizable(False, False)
    popup.transient(parent)
    
    frm_main = ctk.CTkFrame(popup, fg_color=get_color("bg_surface"), corner_radius=15)
    frm_main.pack(fill="both", expand=True, padx=20, pady=20)
    
    ctk.CTkLabel(frm_main, text="Autorización Presencial Requerida", 
                 font=("Segoe UI", 16, "bold"), text_color=get_color("text_primary")).pack(pady=(20, 15))
    
    # --- SECCIÓN FÍSICA ---
    ctk.CTkLabel(frm_main, text="Credencial o Usuario Administrador/Supervisor:", font=("Segoe UI", 12), text_color=get_color("text_secondary")).pack(anchor="w", padx=40)
    entry_user = ctk.CTkEntry(frm_main, font=("Segoe UI", 13), width=280, height=35, placeholder_text="Escanee o escriba...")
    entry_user.pack(pady=(2, 10))
    entry_user.focus_set()
    
    ctk.CTkLabel(frm_main, text="Contraseña / PIN:", font=("Segoe UI", 12), text_color=get_color("text_secondary")).pack(anchor="w", padx=40)
    entry_pass = ctk.CTkEntry(frm_main, show="●", font=("Segoe UI", 13), width=280, height=35, placeholder_text="••••••••")
    entry_pass.pack(pady=(2, 20))
    
    # --- LÓGICA DE CONTROL ---
    def procesar_aprobacion_local(autorizador):
        popup.grab_release()
        popup.destroy()
        if callback_exito:
            parent.after(100, lambda: callback_exito(autorizador))

    def validar_usuario_o_codigo(event=None):
        u_nom = entry_user.get().strip()
        if not u_nom: return
        try:
            autorizador = backend.buscar_usuario_por_codigo(u_nom)
            if autorizador and autorizador.get('id_rol') in roles_permitidos:
                procesar_aprobacion_local(autorizador)
                return
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al buscar código: {e}", parent=popup)
        entry_pass.focus_set()

    def validar_local():
        u_nom = entry_user.get().strip()
        u_pass = entry_pass.get().strip()
        
        from app.frontend.validaciones_ui import ValidadorFormulario
        ok, msg = ValidadorFormulario.validar_campos({
            'Usuario / Credencial': (u_nom, None, True),
            'Contraseña / PIN': (u_pass, None, True)
        })
        if not ok:
            messagebox.showwarning("Atención", msg, parent=popup)
            return
        try:
            autorizador = backend.verificar_contraseña(u_nom, u_pass)
            if autorizador and autorizador.get('id_rol') in roles_permitidos:
                procesar_aprobacion_local(autorizador)
            else:
                messagebox.showerror("Error", "Permisos insuficientes o credenciales incorrectas.", parent=popup)
                entry_pass.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Fallo de validación: {e}", parent=popup)
    
    # --- BOTONES ---
    frm_btns = ctk.CTkFrame(popup, fg_color="transparent")
    frm_btns.pack(pady=(0, 15))
    
    ctk.CTkButton(frm_btns, text="✓ Aprobar", fg_color=get_color("button_primary"), hover_color=get_color("button_primary_hover"),
                  font=("Segoe UI", 12, "bold"), width=140, height=40, command=validar_local).pack(side="left", padx=10)
    
    def cancelar():
        popup.destroy()

    ctk.CTkButton(frm_btns, text="Cancelar Solicitud", fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"),
                  font=("Segoe UI", 12), width=130, height=40, command=cancelar).pack(side="left", padx=10)

    # --- BINDINGS Y ARRANQUE ---
    entry_user.bind("<Return>", validar_usuario_o_codigo)
    entry_pass.bind("<Return>", lambda e: validar_local())
    
    centrar_y_mostrar_ventana(popup)
    popup.grab_set()
