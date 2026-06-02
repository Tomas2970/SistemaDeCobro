# app/frontend/autorizacion.py
# ============================================
# Módulo centralizado de autorización de supervisor/admin
# Patrón "Supervisor Override" para acciones restringidas
# ============================================
import tkinter as tk
from tkinter import messagebox

try:
    from app.frontend.theme_config import get_color, preparar_ventana, centrar_y_mostrar_ventana
except ImportError:
    def get_color(k): return "#000000"
    def preparar_ventana(w): pass
    def centrar_y_mostrar_ventana(w): pass


def solicitar_autorizacion_supervisor(parent, backend, usuario_actual, callback_exito=None):
    """
    Muestra un popup pidiendo credenciales de administrador.
    Si las credenciales son válidas y corresponden a un admin (id_rol=1),
    ejecuta callback_exito(supervisor_dict).
    
    Usado como patrón "Supervisor Override" en todo el sistema:
    el vendedor puede solicitar una acción restringida, pero un admin
    debe autorizar ingresando sus credenciales.
    """
    import customtkinter as ctk
    popup = ctk.CTkToplevel(parent)
    popup.title("🔓 Autorización")
    popup.geometry("400x350")
    preparar_ventana(popup)
    popup.resizable(False, False)
    popup.transient(parent)
    
    frm_main = ctk.CTkFrame(popup, fg_color=get_color("bg_surface"), corner_radius=15)
    frm_main.pack(fill="both", expand=True, padx=20, pady=20)
    
    ctk.CTkLabel(frm_main, text="Autorización de Administrador", 
                 font=("Segoe UI", 16, "bold"), text_color=get_color("text_primary")).pack(pady=(20, 15))
    
    ctk.CTkLabel(frm_main, text="Usuario:", font=("Segoe UI", 12), text_color=get_color("text_secondary")).pack(anchor="w", padx=50)
    entry_user = ctk.CTkEntry(frm_main, font=("Segoe UI", 13), width=250, height=40, placeholder_text="Nombre de usuario")
    entry_user.pack(pady=(2, 10))
    entry_user.focus_set()
    
    ctk.CTkLabel(frm_main, text="Contraseña:", font=("Segoe UI", 12), text_color=get_color("text_secondary")).pack(anchor="w", padx=50)
    entry_pass = ctk.CTkEntry(frm_main, show="●", font=("Segoe UI", 13), width=250, height=40, placeholder_text="••••••••")
    entry_pass.pack(pady=(2, 25))
    
    def validar():
        u_nom = entry_user.get().strip()
        u_pass = entry_pass.get().strip()
        
        if not u_nom or not u_pass:
            messagebox.showwarning("Atención", "Ingrese credenciales", parent=popup)
            return
        
        try:
            supervisor = backend.verificar_contraseña(u_nom, u_pass)
            if supervisor and supervisor.get('id_rol') == 1:
                popup.grab_release()
                popup.destroy()
                if callback_exito:
                    parent.after(100, lambda: callback_exito(supervisor))
            else:
                messagebox.showerror("Error", "No autorizado.", parent=popup)
                entry_pass.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Fallo: {e}", parent=popup)
    
    frm_btns = ctk.CTkFrame(popup, fg_color="transparent")
    frm_btns.pack(pady=(0, 20))
    
    ctk.CTkButton(frm_btns, text="✓ Autorizar", fg_color=get_color("button_primary"), hover_color=get_color("button_primary_hover"),
                  font=("Segoe UI", 12, "bold"), width=140, height=40, command=validar).pack(side="left", padx=10)
    
    ctk.CTkButton(frm_btns, text="Cancelar", fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"),
                  font=("Segoe UI", 12), width=100, height=40, command=popup.destroy).pack(side="left", padx=10)

    entry_pass.bind("<Return>", lambda e: validar())
    centrar_y_mostrar_ventana(popup)
    popup.grab_set()
