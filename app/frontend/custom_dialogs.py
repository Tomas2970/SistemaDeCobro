# app/frontend/custom_dialogs.py
import sys
import tkinter as tk
import customtkinter as ctk
from app.frontend.theme_config import obtener_paleta_activa
from app.frontend.componentes_ui import ModernButton

def centrar_dialogo(ventana, parent=None):
    """Calcula la posición geométrica del modal para centrarlo respecto a su padre o a la pantalla."""
    ventana.update_idletasks()
    width = ventana.winfo_reqwidth()
    height = ventana.winfo_reqheight()
    
    # Asegurar dimensiones mínimas aceptables y estilizadas
    width = max(width, 460)
    height = max(height, 220)
    
    if parent and parent.winfo_exists() and parent.winfo_viewable():
        # Centrar sobre la ventana padre activa
        p_width = parent.winfo_width()
        p_height = parent.winfo_height()
        p_x = parent.winfo_x()
        p_y = parent.winfo_y()
        
        x = p_x + (p_width - width) // 2
        y = p_y + (p_height - height) // 2
    else:
        # Centrar en la pantalla principal
        x = (ventana.winfo_screenwidth() - width) // 2
        y = (ventana.winfo_screenheight() - height) // 2
        
    x = max(0, x)
    y = max(0, y)
    ventana.geometry(f"{width}x{height}+{x}+{y}")

class CustomDialog(ctk.CTkToplevel):
    def __init__(self, parent=None, title="Mensaje", message="", dialog_type="info", buttons_type="ok"):
        super().__init__(parent)
        
        # Ocultar la ventana temporalmente para evitar flickering en su posicionamiento
        self.withdraw()
        
        self.title(title)
        self.attributes("-toolwindow", 1)  # Estilo de diálogo compacto en Windows
        self.resizable(False, False)
        
        self.buttons_type = buttons_type
        self.resultado = None
        
        # Configurar la ventana como modal bloqueante
        if parent:
            self.transient(parent)
        self.grab_set()
        self.focus_set()
        
        # Paleta de colores activa (según Light/Dark mode)
        paleta = obtener_paleta_activa()
        
        # Definición de color de acento y tipo de icono según la semántica
        if dialog_type == "error":
            accent_color = paleta["button_danger"]
            icon_text = "❌"
            btn_style = "danger"
        elif dialog_type == "success":
            accent_color = paleta["button_success"]
            icon_text = "✅"
            btn_style = "success"
        elif dialog_type == "warning":
            accent_color = paleta["button_warning"]
            icon_text = "⚠️"
            btn_style = "warning"
        else:  # info
            accent_color = paleta["accent"]
            icon_text = "ℹ️"
            btn_style = "primary"
            
        self.configure(fg_color=paleta["bg_root"])
        
        # Contenedor principal de la tarjeta de diálogo
        main_frame = ctk.CTkFrame(
            self, 
            fg_color=paleta["bg_surface"], 
            corner_radius=12, 
            border_width=1, 
            border_color=paleta["border_color"]
        )
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Barra superior de acento de color
        accent_bar = ctk.CTkFrame(main_frame, height=4, fg_color=accent_color, corner_radius=0)
        accent_bar.pack(fill="x", side="top")
        
        # Contenedor de contenido
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(20, 10))
        
        # Icono de tamaño grande y estilizado
        icon_label = ctk.CTkLabel(content_frame, text=icon_text, font=("Segoe UI", 42))
        icon_label.pack(side="left", anchor="n", padx=(0, 15))
        
        # Bloque de textos
        text_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)
        
        title_label = ctk.CTkLabel(
            text_frame, 
            text=title, 
            font=("Segoe UI", 18, "bold"), 
            text_color=paleta["text_primary"], 
            anchor="w", 
            justify="left"
        )
        title_label.pack(fill="x", pady=(0, 5))
        
        message_label = ctk.CTkLabel(
            text_frame, 
            text=message, 
            font=("Segoe UI", 16), 
            text_color=paleta["text_secondary"], 
            anchor="w", 
            justify="left", 
            wraplength=400
        )
        message_label.pack(fill="both", expand=True)
        
        # Contenedor inferior de botones
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", side="bottom", padx=20, pady=(10, 20))
        
        # Construcción y organización de botones
        if buttons_type == "ok":
            self.btn_ok = ModernButton(
                button_frame, 
                text="Aceptar", 
                command=self.action_ok,
                style_type=btn_style,
                width=100
            )
            self.btn_ok.pack(side="right")
            self.btn_ok.focus_set()
            
            self.bind("<Return>", lambda e: self.action_ok())
            self.bind("<Escape>", lambda e: self.action_ok())
            
        elif buttons_type == "yesno":
            self.btn_yes = ModernButton(
                button_frame, 
                text="Sí", 
                command=self.action_yes,
                style_type="primary",
                width=100
            )
            self.btn_yes.pack(side="right", padx=(10, 0))
            
            self.btn_no = ModernButton(
                button_frame, 
                text="No", 
                command=self.action_no,
                style_type="secondary",
                width=100
            )
            self.btn_no.pack(side="right")
            self.btn_yes.focus_set()
            
            self.bind("<Return>", lambda e: self.action_yes())
            self.bind("<Escape>", lambda e: self.action_no())
            
        elif buttons_type == "okcancel":
            self.btn_ok = ModernButton(
                button_frame, 
                text="Aceptar", 
                command=self.action_ok,
                style_type="primary",
                width=100
            )
            self.btn_ok.pack(side="right", padx=(10, 0))
            
            self.btn_cancel = ModernButton(
                button_frame, 
                text="Cancelar", 
                command=self.action_cancel,
                style_type="secondary",
                width=100
            )
            self.btn_cancel.pack(side="right")
            self.btn_ok.focus_set()
            
            self.bind("<Return>", lambda e: self.action_ok())
            self.bind("<Escape>", lambda e: self.action_cancel())
            
        elif buttons_type == "retrycancel":
            self.btn_retry = ModernButton(
                button_frame, 
                text="Reintentar", 
                command=self.action_retry,
                style_type="primary",
                width=100
            )
            self.btn_retry.pack(side="right", padx=(10, 0))
            
            self.btn_cancel = ModernButton(
                button_frame, 
                text="Cancelar", 
                command=self.action_cancel,
                style_type="secondary",
                width=100
            )
            self.btn_cancel.pack(side="right")
            self.btn_retry.focus_set()
            
            self.bind("<Return>", lambda e: self.action_retry())
            self.bind("<Escape>", lambda e: self.action_cancel())
            
        elif buttons_type == "yesnocancel":
            self.btn_yes = ModernButton(
                button_frame, 
                text="Sí", 
                command=self.action_yes,
                style_type="primary" if dialog_type != "warning" else "warning",
                width=100
            )
            self.btn_yes.pack(side="right", padx=(10, 0))
            
            self.btn_no = ModernButton(
                button_frame, 
                text="No", 
                command=self.action_no,
                style_type="secondary",
                width=100
            )
            self.btn_no.pack(side="right", padx=(10, 0))
            
            self.btn_cancel = ModernButton(
                button_frame, 
                text="Cancelar", 
                command=self.action_cancel,
                style_type="danger",
                width=100
            )
            self.btn_cancel.pack(side="right")
            self.btn_yes.focus_set()
            
            self.bind("<Return>", lambda e: self.action_yes())
            self.bind("<Escape>", lambda e: self.action_cancel())
            
        # Manejar el evento de cierre desde la barra superior de OS
        self.protocol("WM_DELETE_WINDOW", self.action_close)
        
        # Centrar y mostrar
        centrar_dialogo(self, parent)
        self.deiconify()
        
    def action_ok(self):
        self.resultado = True
        self.destroy()
        
    def action_yes(self):
        self.resultado = True
        self.destroy()
        
    def action_no(self):
        self.resultado = False
        self.destroy()
        
    def action_retry(self):
        self.resultado = True
        self.destroy()
        
    def action_cancel(self):
        if self.buttons_type == "yesnocancel":
            self.resultado = None
        else:
            self.resultado = False
        self.destroy()
        
    def action_close(self):
        if self.buttons_type == "yesnocancel":
            self.resultado = None
        elif self.buttons_type in ("yesno", "okcancel", "retrycancel"):
            self.resultado = False
        else:
            self.resultado = True
        self.destroy()

# ============================================================================
# API Explícita y Directa para desarrollo moderno
# ============================================================================

def mostrar_error(titulo, mensaje, parent=None):
    dialog = CustomDialog(parent, title=titulo, message=mensaje, dialog_type="error", buttons_type="ok")
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window(dialog)
    return "ok"

def mostrar_exito(titulo, mensaje, parent=None):
    dialog = CustomDialog(parent, title=titulo, message=mensaje, dialog_type="success", buttons_type="ok")
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window(dialog)
    return "ok"

def mostrar_advertencia(titulo, mensaje, parent=None):
    dialog = CustomDialog(parent, title=titulo, message=mensaje, dialog_type="warning", buttons_type="ok")
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window(dialog)
    return "ok"

def mostrar_info(titulo, mensaje, parent=None):
    dialog = CustomDialog(parent, title=titulo, message=mensaje, dialog_type="info", buttons_type="ok")
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window(dialog)
    return "ok"

def mostrar_confirmacion(titulo, mensaje, parent=None) -> bool:
    dialog = CustomDialog(parent, title=titulo, message=mensaje, dialog_type="info", buttons_type="yesno")
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window(dialog)
    return dialog.resultado

def mostrar_confirmacion_exito(titulo, mensaje, parent=None) -> bool:
    """Diálogo de confirmación Sí/No con estilo de éxito (verde)."""
    dialog = CustomDialog(parent, title=titulo, message=mensaje, dialog_type="success", buttons_type="yesno")
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window(dialog)
    return dialog.resultado

# ============================================================================
# Wrappers de compatibilidad idéntica con tkinter.messagebox
# ============================================================================

def showinfo(title=None, message=None, **options):
    parent = options.get("parent", None)
    return mostrar_info(title or "Información", message or "", parent)

def showwarning(title=None, message=None, **options):
    parent = options.get("parent", None)
    return mostrar_advertencia(title or "Advertencia", message or "", parent)

def showerror(title=None, message=None, **options):
    parent = options.get("parent", None)
    return mostrar_error(title or "Error", message or "", parent)

def askyesno(title=None, message=None, **options):
    parent = options.get("parent", None)
    dialog = CustomDialog(parent, title=title or "Confirmación", message=message or "", dialog_type="info", buttons_type="yesno")
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window(dialog)
    return dialog.resultado

def askquestion(title=None, message=None, **options):
    res = askyesno(title, message, **options)
    return "yes" if res else "no"

def askokcancel(title=None, message=None, **options):
    parent = options.get("parent", None)
    dialog = CustomDialog(parent, title=title or "Confirmación", message=message or "", dialog_type="info", buttons_type="okcancel")
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window(dialog)
    return dialog.resultado

def askretrycancel(title=None, message=None, **options):
    parent = options.get("parent", None)
    dialog = CustomDialog(parent, title=title or "Reintentar", message=message or "", dialog_type="warning", buttons_type="retrycancel")
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window(dialog)
    return dialog.resultado

def askyesnocancel(title=None, message=None, **options):
    parent = options.get("parent", None)
    dialog = CustomDialog(parent, title=title or "Confirmación", message=message or "", dialog_type="warning", buttons_type="yesnocancel")
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window(dialog)
    return dialog.resultado

# ============================================================================
# Toast Flotante (Notificaciones No Bloqueantes)
# ============================================================================

_toast_activo = None

def mostrar_toast_centrado(parent, mensaje, duracion_ms=2500, bg_color="#10b981", fg_color="white"):
    """
    Muestra un Toast flotante centrado en relación a la ventana padre.
    Se autodestruye después de `duracion_ms`.
    Si aparece uno nuevo, reemplaza al anterior.
    """
    global _toast_activo
    
    if _toast_activo and _toast_activo.winfo_exists():
        _toast_activo.destroy()
        
    toast = tk.Toplevel(parent)
    _toast_activo = toast
    
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    
    paleta = obtener_paleta_activa()
    toast.configure(bg=paleta["border_color"]) 
    
    frame = ctk.CTkFrame(toast, fg_color=bg_color, corner_radius=8)
    frame.pack(fill="both", expand=True, padx=1, pady=1)
    
    lbl = ctk.CTkLabel(frame, text=mensaje, font=("Segoe UI", 16, "bold"), text_color=fg_color)
    lbl.pack(padx=25, pady=15)
    
    toast.update_idletasks()
    w = toast.winfo_reqwidth()
    h = toast.winfo_reqheight()
    
    if parent and parent.winfo_exists() and parent.winfo_viewable():
        p_width = parent.winfo_width()
        p_height = parent.winfo_height()
        p_x = parent.winfo_rootx()
        p_y = parent.winfo_rooty()
        
        x = p_x + (p_width - w) // 2
        y = p_y + (p_height - h) // 2
    else:
        x = (toast.winfo_screenwidth() - w) // 2
        y = (toast.winfo_screenheight() - h) // 2
        
    toast.geometry(f"{w}x{h}+{x}+{y}")
    
    # Desvanecer o simplemente destruir
    toast.after(duracion_ms, lambda: toast.destroy() if toast.winfo_exists() else None)
