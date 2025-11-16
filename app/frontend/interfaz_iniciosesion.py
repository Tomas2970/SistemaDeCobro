# app/frontend/interfaz_iniciosesion.py
import tkinter as tk
from tkinter import TclError # <--- Importamos TclError
from tkinter import messagebox
import logging

logger = logging.getLogger(__name__)

# --- FUNCIÓN DE NAVEGACIÓN POR TECLADO ---
def configurar_navegacion_teclado(ventana, widgets):
    """Configura navegación por TAB y ENTER automáticamente"""
    def on_tab(event, current_index):
        next_index = (current_index + 1) % len(widgets)
        widgets[next_index].focus_set()
        return "break"  # Prevenir comportamiento por defecto
    
    def on_shift_tab(event, current_index):
        prev_index = (current_index - 1) % len(widgets)
        widgets[prev_index].focus_set()
        return "break"
    
    for i, widget in enumerate(widgets):
        # Navegación con TAB
        widget.bind("<Tab>", lambda e, idx=i: on_tab(e, idx))
        widget.bind("<Shift-Tab>", lambda e, idx=i: on_shift_tab(e, idx))
        
        # ENTER en campos de texto va al siguiente (excepto el último)
        if isinstance(widget, (tk.Entry, tk.Entry)) and i < len(widgets) - 1:
            widget.bind("<Return>", lambda e, idx=i: on_tab(e, idx))
        
        # ENTER en botones los activa
        elif isinstance(widget, (tk.Button, tk.Button)):
            widget.bind("<Return>", lambda e, btn=widget: btn.invoke())

# --- FUNCIÓN PARA ESTILOS MODERNOS ---
def aplicar_estilos_login(ventana):
    """Aplica estilos modernos a la ventana de login"""
    # Configurar ventana
    ventana.configure(bg='#f8fafc')  # Fondo gris muy claro
    
    # Definir paleta de colores moderna
    colores = {
        'primary': '#2563eb',       # Azul vibrante
        'primary_hover': '#1d4ed8', # Azul oscuro (hover)
        'success': '#16a34a',       # Verde éxito
        'danger': '#dc2626',        # Rojo error
        'background': '#f8fafc',    # Fondo principal
        'surface': '#ffffff',       # Superficie (cards)
        'border': '#e2e8f0',        # Bordes
        'text_primary': '#1e293b',  # Texto principal
        'text_secondary': '#64748b' # Texto secundario
    }
    
    return colores

# --- CLASE CARD MODERNA ---
class Card(tk.Frame):
    """Componente card moderno con sombras visuales"""
    def __init__(self, parent, **kwargs):
        bg = kwargs.pop('bg', 'white')
        super().__init__(parent, bg=bg, **kwargs)
        self.configure(
            relief='solid',
            borderwidth=1,
            highlightthickness=0,
            padx=0,
            pady=0
        )

# --- BOTÓN MODERNO ---
class ModernButton(tk.Button):
    """Botón con efectos hover modernos"""
    def __init__(self, parent, **kwargs):
        # Colores por defecto
        self.normal_bg = kwargs.pop('bg', '#2563eb')
        self.hover_bg = kwargs.pop('hover_bg', '#1d4ed8')
        self.normal_fg = kwargs.pop('fg', 'white')
        
        super().__init__(parent, **kwargs)
        
        self.configure(
            bg=self.normal_bg,
            fg=self.normal_fg,
            borderwidth=0,
            cursor='hand2',
            font=('Segoe UI', 10, 'bold'),
            padx=20,
            pady=10,
            relief='flat'
        )
        
        # Bind eventos hover
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        self.configure(bg=self.hover_bg)
    
    def _on_leave(self, event):
        self.configure(bg=self.normal_bg)

def ui_login(parent: tk.Misc, backend):
    win = tk.Toplevel(parent)
    win.title("Inicio de Sesión - Supermercado Don Atilio")
    
    win.config(bg='#f8fafc')
    win.resizable(False, False)
    
    # --- CAMBIO 1: AÑADIR ANCHO MÍNIMO ---
    win.minsize(480, 0)
    
    # Aplicar estilos modernos
    colores = aplicar_estilos_login(win)
    
    usuario_logeado = None

    # --- HEADER CON LOGO ---
    header_frame = tk.Frame(win, bg=colores['primary'], height=100)
    header_frame.pack(fill=tk.X)
    header_frame.pack_propagate(False) 
    
    tk.Label(header_frame, 
             text="🛒 DON ATILIO", 
             bg=colores['primary'],
             fg='white',
             font=('Segoe UI', 20, 'bold')).pack(expand=True)
    
    tk.Label(header_frame,
             text="Sistema de Gestión Comercial",
             bg=colores['primary'],
             fg='#e0f2fe',
             font=('Segoe UI', 11)).pack(pady=(0, 20))

    # --- CARD DE LOGIN ---
    card = Card(win, bg=colores['surface'])
    card.pack(padx=40, pady=20, fill=tk.BOTH, expand=True)
    
    # Título del card
    tk.Label(card,
             text="Iniciar Sesión",
             bg=colores['surface'],
             fg=colores['text_primary'],
             font=('Segoe UI', 16, 'bold')).pack(pady=(25, 10))
    
    tk.Label(card,
             text="Ingrese sus credenciales para continuar",
             bg=colores['surface'],
             fg=colores['text_secondary'],
             font=('Segoe UI', 10)).pack(pady=(0, 25))

    # --- FORMULARIO ---
    form_frame = tk.Frame(card, bg=colores['surface'])
    form_frame.pack(padx=40, pady=10, fill=tk.X) # padx=40 hace el form más angosto

    # Campo Usuario
    usuario_frame = tk.Frame(form_frame, bg=colores['surface'])
    usuario_frame.pack(fill=tk.X, pady=(0, 20))
    
    tk.Label(usuario_frame,
             text="👤 Usuario:",
             bg=colores['surface'],
             fg=colores['text_primary'],
             font=('Segoe UI', 10, 'bold'),
             anchor='w').pack(fill=tk.X)
    
    entry_usuario_frame = tk.Frame(usuario_frame, bg=colores['surface'])
    entry_usuario_frame.pack(fill=tk.X, pady=(8, 0))
    
    entry_usuario = tk.Entry(entry_usuario_frame,
                             font=('Segoe UI', 11),
                             relief='solid',
                             borderwidth=1,
                             bg=colores['surface'],
                             highlightthickness=1,
                             highlightcolor=colores['primary'],
                             highlightbackground=colores['border'])
    entry_usuario.pack(fill=tk.X, ipady=8, padx=8)

    # Campo Contraseña
    contrasena_frame = tk.Frame(form_frame, bg=colores['surface'])
    contrasena_frame.pack(fill=tk.X, pady=(0, 20))
    
    tk.Label(contrasena_frame,
             text="🔒 Contraseña:",
             bg=colores['surface'],
             fg=colores['text_primary'],
             font=('Segoe UI', 10, 'bold'),
             anchor='w').pack(fill=tk.X)
    
    entry_contrasena_frame = tk.Frame(contrasena_frame, bg=colores['surface'])
    entry_contrasena_frame.pack(fill=tk.X, pady=(8, 0))
    
    entry_contrasena = tk.Entry(entry_contrasena_frame,
                                font=('Segoe UI', 11),
                                show="•",
                                relief='solid',
                                borderwidth=1,
                                bg=colores['surface'],
                                highlightthickness=1,
                                highlightcolor=colores['primary'],
                                highlightbackground=colores['border'])
    entry_contrasena.pack(fill=tk.X, ipady=8, padx=8)

    # --- BOTONES ---
    botones_frame = tk.Frame(card, bg=colores['surface'])
    botones_frame.pack(padx=40, pady=(10, 20), fill=tk.X)

    # (Función iniciar_sesion - CORREGIDA)
    def iniciar_sesion(event=None):
        nonlocal usuario_logeado
        usuario = entry_usuario.get().strip()
        contrasena = entry_contrasena.get().strip()
        
        if not usuario or not contrasena:
            messagebox.showwarning("Campos vacíos",
                                   "Complete todos los campos.",
                                   parent=win)
            entry_usuario.focus_set()
            return
            
        btn_login.config(text="Verificando...", state='disabled')
        btn_salir.config(state='disabled')
        win.update()
        
        try:
            usuario_db = backend.verificar_contraseña(usuario, contrasena)
            
            if usuario_db:
                usuario_logeado = usuario_db
                win.destroy() # <-- La ventana se destruye aquí
            else:
                messagebox.showerror("Error",
                                     "Usuario o contraseña incorrectos",
                                     parent=win)
                entry_contrasena.delete(0, tk.END)
                entry_usuario.focus_set()
                
        except Exception as e:
            logger.error(f"Error en login: {e}")
            messagebox.showerror("Error",
                               f"Error de conexión: {str(e)}",
                               parent=win)
        finally:
            # --- AQUÍ ESTÁ LA CORRECCIÓN ---
            try:
                # Intentamos reconfigurar solo si los botones aún existen.
                # Si 'win.destroy()' se llamó, esto dará un TclError.
                btn_login.config(text="Ingresar al Sistema", state='normal')
                btn_salir.config(state='normal')
            except TclError:
                # Capturamos el error esperado (porque la ventana
                # se destruyó) y simplemente no hacemos nada.
                pass 

    # (Función salir - sin cambios)
    def salir():
        if messagebox.askyesno("Confirmar salida", 
                              "¿Está seguro que desea salir del sistema?",
                              parent=win):
            win.destroy()

    # Botón Ingresar
    btn_login = ModernButton(botones_frame,
                             text="Ingresar al Sistema",
                             bg=colores['primary'],
                             hover_bg=colores['primary_hover'],
                             command=iniciar_sesion)
    btn_login.pack(fill=tk.X, pady=(0, 10), ipadx=10, ipady=8) 

    # Botón Salir
    btn_salir = ModernButton(botones_frame,
                             text="Salir del Sistema",
                             bg=colores['danger'],
                             hover_bg='#b91c1c',
                             command=salir)
    btn_salir.pack(fill=tk.X, ipadx=10, ipady=8)

    # --- FOOTER ---
    footer_frame = tk.Frame(win, bg=colores['background'], height=40)
    footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
    footer_frame.pack_propagate(False)
    
    tk.Label(footer_frame,
           text="Presione TAB para navegar • ENTER para confirmar",
           bg=colores['background'],
           fg=colores['text_secondary'],
           font=('Segoe UI', 9)).pack(expand=True)

    # --- CONFIGURAR NAVEGACIÓN POR TECLADO ---
    widgets_navegacion = [entry_usuario, entry_contrasena, btn_login, btn_salir]
    configurar_navegacion_teclado(win, widgets_navegacion)

    # --- EVENTOS DE TECLADO ADICIONALES ---
    def on_escape(event):
        salir()
    
    win.bind("<Escape>", on_escape)
    
    entry_contrasena.bind("<Return>", iniciar_sesion)
    
    entry_usuario.focus_set()

    # --- CENTRADO AUTOMÁTICO ---
    win.update_idletasks() 
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    window_width = win.winfo_width() 
    window_height = win.winfo_height()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    win.geometry(f"+{x}+{y}") # Posicionamos la ventana
    
    win.grab_set()
    win.wait_window()
    return usuario_logeado