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

def obtener_paleta_activa():
    """Retorna la paleta de colores computada en tiempo real según el modo actual (Light/Dark)."""
    modo = ctk.get_appearance_mode()
    es_light = (modo == "Light")
    
    return {
        "bg_root": "#f3f4f6" if es_light else "#111827",
        "bg_surface": "#ffffff" if es_light else "#1f2937",
        "bg_pop": "#1f2937" if es_light else "#1f2937",  # Encabezados oscuros para contraste moderno
        "text_primary": "#1f2937" if es_light else "#ffffff",
        "text_secondary": "#6b7280" if es_light else "#94a3b8",
        "border_color": "#e5e7eb" if es_light else "#2d3748",
        
        "accent": "#3b82f6",
        "accent_hover": "#2563eb",
        
        "button_primary": "#3b82f6",
        "button_primary_hover": "#2563eb",
        "button_secondary": "#6b7280" if es_light else "#475569",
        "button_secondary_hover": "#4b5563" if es_light else "#334155",
        "button_danger": "#ef4444",
        "button_danger_hover": "#dc2626",
        "button_success": "#10b981",
        "button_success_hover": "#059669",
        "button_warning": "#f59e0b",
        "button_warning_hover": "#d97706",
        
        "input_bg": "#f9fafb" if es_light else "#374151",
        "input_fg": "#1f2937" if es_light else "#ffffff"
    }

def get_color(key):
    """Retorna un color seguro de la paleta."""
    return THEME_COLORS.get(key, "#ff00ff") # Magenta de error si no existe

def centrar_ventana(ventana):
    """Calcula el centro de la pantalla y posiciona la ventana ahí de forma robusta sin saltos visuales."""
    width = getattr(ventana, '_custom_width', None)
    height = getattr(ventana, '_custom_height', None)
    
    if not width or not height:
        geom = ventana.geometry()
        try:
            if 'x' in geom:
                partes = geom.split('+')[0].split('x')
                w = int(partes[0])
                h = int(partes[1])
                # Evitar usar tamaños por defecto como 200x200 de CTkToplevel no inicializados
                if w > 200 or h > 200:
                    width = w
                    height = h
        except:
            pass

    if not width or not height:
        ventana.update_idletasks()
        width = ventana.winfo_reqwidth()
        height = ventana.winfo_reqheight()

    if not width or width <= 100:
        width = 600
        height = 400

    x = (ventana.winfo_screenwidth() // 2) - (width // 2)
    y = (ventana.winfo_screenheight() // 2) - (height // 2)
    
    x = max(0, x)
    y = max(0, y)
    
    ventana.geometry(f"{width}x{height}+{x}+{y}")

def aplicar_tema_ventana(ventana):
    """Aplica la configuración base de CustomTkinter y centra la ventana (legacy)."""
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    # Computar paleta dinámica para el fondo principal
    paleta = obtener_paleta_activa()
    ventana.configure(fg_color=paleta["bg_root"])
    
    # Auto-centrado automático
    centrar_ventana(ventana)

def preparar_ventana(ventana):
    """Prepara una ventana ocultándola inicialmente para evitar flickering y saltos geométricos."""
    ventana.withdraw()
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    paleta = obtener_paleta_activa()
    ventana.configure(fg_color=paleta["bg_root"])
    
    # Interceptamos llamadas a geometry para recordar el tamaño deseado mientras está oculta
    orig_geom = ventana.geometry
    def custom_geometry(geometry_string=None):
        if geometry_string is not None:
            try:
                size_part = geometry_string.split('+')[0]
                if 'x' in size_part:
                    w, h = size_part.split('x')
                    ventana._custom_width = int(w)
                    ventana._custom_height = int(h)
            except Exception:
                pass
            return orig_geom(geometry_string)
        else:
            return orig_geom()
            
    ventana.geometry = custom_geometry

def centrar_y_mostrar_ventana(ventana):
    """Calcula la geometría real, centra la ventana y la revela en un solo paso visual."""
    centrar_ventana(ventana)
    ventana.deiconify()

def configurar_estilo_notebook():
    """Configura el estilo ttk para que los Notebooks no desentonen con el tema oscuro."""
    paleta = obtener_paleta_activa()
    style = ttk.Style()
    style.theme_use('clam')
    
    # Notebook (Contenedor de pestañas)
    style.configure("Custom.TNotebook", 
                    background=paleta["bg_root"],
                    borderwidth=0)
    
    style.configure("Custom.TNotebook.Tab",
                    background=paleta["bg_surface"],
                    foreground=paleta["text_secondary"],
                    padding=[15, 5],
                    font=("Segoe UI", 11, "bold"),
                    borderwidth=0)
    
    style.map("Custom.TNotebook.Tab",
              background=[("selected", paleta["accent"])],
              foreground=[("selected", "#ffffff")])

def configurar_estilo_treeview():
    """Configura el estilo de las tablas Treeview para el modo oscuro con máxima robustez."""
    style = ttk.Style()
    
    # 1. Asegurar tema clam (esencial para que fieldbackground funcione en Windows)
    try:
        style.theme_use('clam')
    except: pass
    
    # Computar paleta activa
    paleta = obtener_paleta_activa()
    col_bg = paleta["bg_root"] 
    col_fg = paleta["text_primary"]
    col_head = paleta["bg_pop"]
    col_accent = paleta["accent"]
    
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
                    
    # 3b. Configurar nuestro estilo específico "Compact.Treeview" para alta densidad de datos
    style.configure("Compact.Treeview",
                    background=col_bg,
                    foreground=col_fg,
                    fieldbackground=col_bg,
                    rowheight=35,          # Espaciado ultra compacto
                    font=("Segoe UI", 11),
                    borderwidth=0)
    
    style.configure("Compact.Treeview.Heading",
                    background=col_head,
                    foreground="#ffffff",
                    anchor="w",
                    relief="flat",
                    padding=[5, 5],
                    font=("Segoe UI", 11, "bold"))
    
    # 4. Mapas de colores para estados (Selección, etc.)
    style.map("Treeview",
              background=[("selected", col_accent)],
              foreground=[("selected", "#ffffff")])

    style.map("Modern.Treeview",
              background=[("selected", col_accent)],
              foreground=[("selected", "#ffffff")])
              
    style.map("Compact.Treeview",
              background=[("selected", col_accent)],
              foreground=[("selected", "#ffffff")])
    
    style.map("Modern.Treeview.Heading",
              background=[("active", col_accent), ("pressed", col_accent)])
              
    style.map("Compact.Treeview.Heading",
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
