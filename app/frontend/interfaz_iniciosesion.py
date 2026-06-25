import customtkinter as ctk
from app.frontend import custom_dialogs as messagebox
from app.frontend.custom_dialogs import mostrar_confirmacion, mostrar_advertencia, mostrar_error
import logging
from app.frontend.navegacion_teclado_comun import configurar_navegacion_teclado

logger = logging.getLogger(__name__)

def ui_login(parent, backend):
    win = parent
    win.title("Inicio de Sesión - Supermercado Don Atilio")
    
    try:
        win.state('normal') # DESHACER LA MAXIMIZACIÓN DEL MENÚ
    except Exception: pass
    
    win.update_idletasks()
    ancho, alto = 850, 520
    x = (win.winfo_screenwidth() - ancho) // 2
    y = (win.winfo_screenheight() - alto) // 2
    win.geometry(f"{ancho}x{alto}+{x}+{y}")
    win.resizable(False, False)
    
    colores_bg = "#ffffff" if ctk.get_appearance_mode() == "Light" else "#2b2b2b"
    usuario_logeado = None

    # Frame Izquierdo
    left_frame = ctk.CTkFrame(win, fg_color="#3b82f6", width=350, corner_radius=0)
    left_frame.pack(side="left", fill="y")
    left_frame.pack_propagate(False)
    
    ctk.CTkLabel(left_frame, text="🛒", font=("Segoe UI", 72), text_color="white").pack(pady=(120, 10))
    ctk.CTkLabel(left_frame, text="Sistema de Cobros", font=("Segoe UI", 20, "bold"), text_color="white").pack()
    ctk.CTkLabel(left_frame, text="Supermercado\nDon Atilio", font=("Segoe UI", 14), text_color="white").pack(pady=10)

    # Frame Derecho
    right_frame = ctk.CTkFrame(win, fg_color=colores_bg, corner_radius=0)
    right_frame.pack(side="right", fill="both", expand=True)

    card = ctk.CTkFrame(right_frame, fg_color=colores_bg, border_width=0)
    card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.75, relheight=0.85)

    ctk.CTkLabel(card, text="¡Bienvenido!", font=("Segoe UI", 24, "bold")).pack(pady=(30, 5))
    ctk.CTkLabel(card, text="Ingresa tus credenciales para continuar", font=("Segoe UI", 12)).pack(pady=(0, 25))

    ctk.CTkLabel(card, text="Usuario", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20)
    entry_usuario = ctk.CTkEntry(card, font=("Segoe UI", 13), border_width=1, corner_radius=6)
    entry_usuario.pack(fill="x", padx=20, pady=(5, 15), ipady=5)

    ctk.CTkLabel(card, text="Contraseña", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20)
    entry_contrasena = ctk.CTkEntry(card, show="•", font=("Segoe UI", 13), border_width=1, corner_radius=6)
    entry_contrasena.pack(fill="x", padx=20, pady=(5, 25), ipady=5)

    def iniciar_sesion(*_):
        nonlocal usuario_logeado
        u = entry_usuario.get().strip()
        p = entry_contrasena.get().strip()
        
        from app.frontend.validaciones_ui import ValidadorFormulario
        ok, msg = ValidadorFormulario.validar_campos({
            'Usuario': (u, None, True),
            'Contraseña': (p, None, True)
        })
        if not ok:
            mostrar_advertencia("Credenciales Requeridas", msg)
            entry_usuario.focus_set()
            return
        
        btn_login.configure(state="disabled", text="Verificando...")
        win.update()
        
        try:
            udb = backend.verificar_contraseña(u, p)
            if udb:
                usuario_logeado = udb
                win.quit()
            else:
                mostrar_error("Acceso Denegado", "El nombre de usuario o la contraseña ingresados son incorrectos.")
                entry_contrasena.delete(0, 'end')
                entry_usuario.focus_set()
                btn_login.configure(state="normal", text="Ingresar al Sistema")
        except Exception as e:
            from app.frontend.manejador_errores import ManejadorErroresUI
            ManejadorErroresUI.manejar_error(e, parent=win, contexto="conexión")
            btn_login.configure(state="normal", text="Ingresar al Sistema")

    def salir(*_):
        if mostrar_confirmacion("Confirmar", "¿Desea salir del sistema?"):
            win.quit()
        
    btn_login = ctk.CTkButton(card, text="Ingresar al Sistema", fg_color="#3b82f6", hover_color="#2563eb", font=("Segoe UI", 13, "bold"), command=iniciar_sesion)
    btn_login.pack(fill="x", padx=20, pady=(0, 10), ipady=5)
    
    btn_salir = ctk.CTkButton(card, text="Salir", fg_color="#ef4444", hover_color="#b91c1c", font=("Segoe UI", 13, "bold"), command=salir)
    btn_salir.pack(fill="x", padx=20, ipady=5)

    configurar_navegacion_teclado(win, [entry_usuario, entry_contrasena, btn_login, btn_salir])
    entry_contrasena.bind("<Return>", iniciar_sesion)
    entry_usuario.focus_set()
    
    win.protocol("WM_DELETE_WINDOW", salir)
    
    win.mainloop()  # Bloquea hasta win.quit()
    
    if win.winfo_exists():
        for widget in win.winfo_children(): widget.destroy()

    return usuario_logeado