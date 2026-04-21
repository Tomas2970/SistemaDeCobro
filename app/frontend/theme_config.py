# app/frontend/theme_config.py
import customtkinter as ctk
from tkinter import ttk

# Paleta centralizada para toda la aplicación
THEME_COLORS = {
    "bg_root": "#111827",          # Fondo ultra oscuro (Gris/Azul profundidad)
    "bg_surface": "#1f2937",       # Fondo de tarjetas y paneles
    "bg_pop": "#1f2937",           # Fondo para popups/selectores (ahora igual que bg_surface para encabezados más oscuros)
    
    "text_primary": "#ffffff",     # Blanco puro para máxima nitidez
    "text_secondary": "#94a3b8",   # Gris azulado suave
    
    "accent_primary": "#3b82f6",   # Azul brillante (Acción)
    "accent_hover": "#2563eb",     # Azul hover
    
    "button_primary": "#3b82f6",
    "button_primary_hover": "#2563eb",
    "button_secondary": "#475569",
    "button_secondary_hover": "#334155",
    "button_danger": "#ef4444",
    "button_danger_hover": "#dc2626",
    
    "border_color": "#2d3748"      # Gris azulado oscuro para bordes suaves
}

# Variable global para evitar re-inicializar
_ESTILOS_INICIALIZADOS = False

def get_color(key):
    """Retorna un color seguro de la paleta."""
    return THEME_COLORS.get(key, "#ff00ff") # Magenta de error si no existe

def centrar_ventana(ventana):
    """Calcula el centro de la pantalla y posiciona la ventana ahí."""
    ventana.update_idletasks()
    width = ventana.winfo_width()
    height = ventana.winfo_height()
    x = (ventana.winfo_screenwidth() // 2) - (width // 2)
    y = (ventana.winfo_screenheight() // 2) - (height // 2)
    ventana.geometry(f'+{x}+{y}')

def aplicar_tema_ventana(ventana):
    """Aplica la configuración base de CustomTkinter y centra la ventana."""
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    ventana.configure(fg_color=get_color("bg_root"))
    
    # Auto-centrado automático
    centrar_ventana(ventana)

def configurar_estilo_notebook():
    """Configura el estilo ttk para que los Notebooks no desentonen con el tema oscuro."""
    style = ttk.Style()
    style.theme_use('clam')
    
    # Notebook (Contenedor de pestañas)
    style.configure("Custom.TNotebook", 
                    background=get_color("bg_root"),
                    borderwidth=0)
    
    style.configure("Custom.TNotebook.Tab",
                    background=get_color("bg_surface"),
                    foreground=get_color("text_secondary"),
                    padding=[15, 5],
                    font=("Segoe UI", 11, "bold"),
                    borderwidth=0)
    
    style.map("Custom.TNotebook.Tab",
              background=[("selected", get_color("accent_primary"))],
              foreground=[("selected", "#ffffff")])

def configurar_estilo_treeview():
    """Configura el estilo de las tablas Treeview para el modo oscuro con máxima robustez."""
    style = ttk.Style()
    
    # 1. Asegurar tema clam (esencial para que fieldbackground funcione en Windows)
    try:
        style.theme_use('clam')
    except: pass
    
    # Usar bg_root para que el fondo de la tabla sea igual al fondo de la app (Negro azulado profundo)
    col_bg = get_color("bg_root") 
    col_fg = get_color("text_primary")
    col_head = get_color("bg_pop")
    col_accent = get_color("accent_primary")
    
    # 2. Configurar el estilo base de Treeview para que afecte a TODOS
    style.configure("Treeview",
                    background=col_bg,
                    foreground=col_fg,
                    fieldbackground=col_bg,
                    rowheight=42,          # Aumentado para mejor legibilidad
                    font=("Segoe UI", 12), # Aumentado como pidió el usuario
                    borderwidth=0)
    
    style.configure("Treeview.Heading",
                    background=col_head,
                    foreground="#ffffff",
                    anchor="w",
                    relief="flat",
                    font=("Segoe UI", 12, "bold"))
    
    # 3. Configurar nuestro estilo específico "Modern.Treeview"
    style.configure("Modern.Treeview",
                    background=col_bg,
                    foreground=col_fg,
                    fieldbackground=col_bg,
                    rowheight=45,          # Espaciado premium
                    font=("Segoe UI", 12),
                    borderwidth=0)
    
    style.configure("Modern.Treeview.Heading",
                    background=col_head,
                    foreground="#ffffff",
                    anchor="w",
                    relief="flat",
                    padding=[10, 10],
                    font=("Segoe UI", 12, "bold"))
    
    # 4. Mapas de colores para estados (Selección, etc.)
    style.map("Treeview",
              background=[("selected", col_accent)],
              foreground=[("selected", "#ffffff")])

    style.map("Modern.Treeview",
              background=[("selected", col_accent)],
              foreground=[("selected", "#ffffff")])
    
    style.map("Modern.Treeview.Heading",
              background=[("active", col_accent), ("pressed", col_accent)])

def inicializar_estilos_globales():
    """Llamar una sola vez al inicio de la aplicación en main.py."""
    global _ESTILOS_INICIALIZADOS
    if _ESTILOS_INICIALIZADOS: return
    
    configurar_estilo_notebook()
    configurar_estilo_treeview()
    _ESTILOS_INICIALIZADOS = True

class Theme:
    """Clase legacy para compatibilidad si algún módulo la invoca."""
    PRIMARY = THEME_COLORS["accent_primary"]
    TEXT_PRIMARY = THEME_COLORS["text_primary"]
    BG_ROOT = THEME_COLORS["bg_root"]
    
    @classmethod
    def font_standard(cls, size=11, **kwargs):
        weight = kwargs.get('weight', '')
        return ('Segoe UI', size, weight) if weight else ('Segoe UI', size)
