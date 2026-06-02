# app/frontend/componentes_ui.py
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime

try:
    from tkcalendar import DateEntry
    HAY_CALENDARIO = True
except ImportError:
    HAY_CALENDARIO = False

import customtkinter as ctk

class EntryNumerico(ctk.CTkEntry):
    def __init__(self, parent, max_chars=None, *args, **kwargs):
        if 'justify' not in kwargs:
            kwargs['justify'] = 'right'
        super().__init__(parent, *args, **kwargs)
        self.max_chars = max_chars
        vcmd = (self.register(self._validar_numero), '%P')
        self.configure(validate='key', validatecommand=vcmd)

    def _validar_numero(self, texto_nuevo):
        if not texto_nuevo: return True
        if not texto_nuevo.isdigit(): return False
        if self.max_chars is not None and len(texto_nuevo) > self.max_chars: return False
        return True

class EntryDecimal(ctk.CTkEntry):
    def __init__(self, parent, *args, **kwargs):
        if 'justify' not in kwargs:
            kwargs['justify'] = 'right'
        super().__init__(parent, *args, **kwargs)
        vcmd = (self.register(self._validar_decimal), '%P')
        self.configure(validate='key', validatecommand=vcmd)

    def _validar_decimal(self, texto_nuevo):
        if not texto_nuevo: return True
        if texto_nuevo.count('.') > 1: return False
        try:
            if texto_nuevo == '.' and self.get() != '': return False
            if texto_nuevo != '.': float(texto_nuevo)
            return True
        except ValueError: return False
        except: return False

class SelectorFecha(ctk.CTkFrame):
    def __init__(self, parent, fecha_defecto=None, *args, **kwargs):
        super().__init__(parent, fg_color="transparent", *args, **kwargs)
        self.widget_entrada = None
        
        if HAY_CALENDARIO:
            self.entrada = DateEntry(
                self, width=12,
                background='#1f2937', 
                foreground='#f9fafb',
                borderwidth=0,
                headersbackground='#111827',
                headersforeground='#9ca3af',
                selectbackground='#3b82f6',
                selectforeground='white',
                normalbackground='#1f2937',
                normalforeground='#f9fafb',
                weekendbackground='#1f2937',
                weekendforeground='#ef4444',
                othermonthforeground='#4b5563',
                othermonthbackground='#1f2937',
                othermonthweforeground='#7f1d1d',
                othermonthwebackground='#1f2937',
                font=('Segoe UI', 11),
                date_pattern='dd/mm/yyyy'
            )
            self.widget_entrada = self.entrada
            if fecha_defecto:
                try: self.entrada.set_date(fecha_defecto)
                except: pass
        else:
            self.entrada = ctk.CTkEntry(self, width=120) 
            self.widget_entrada = self.entrada
            if fecha_defecto:
                try: self.entrada.insert(0, fecha_defecto.strftime("%d/%m/%Y"))
                except AttributeError: self.entrada.insert(0, str(fecha_defecto))
            
        self.entrada.pack(fill=tk.BOTH, expand=True)

    def get_date_str(self):
        if HAY_CALENDARIO:
            try: return self.entrada.get_date().strftime("%d/%m/%Y")
            except: return ""
        else:
            return self.entrada.get()
    
    def get_date_sql(self):
        if HAY_CALENDARIO:
            try: return self.entrada.get_date().strftime("%Y-%m-%d")
            except: return None
        else:
            try:
                parts = self.entrada.get().split('/')
                if len(parts) == 3: return f"{parts[2]}-{parts[1]}-{parts[0]}"
                return None
            except: return None

class Card(ctk.CTkFrame):
    def __init__(self, parent, bg_color=None, corner_radius=10, **kwargs):
        if bg_color is None:
            from app.frontend.theme_config import obtener_paleta_activa
            bg_color = obtener_paleta_activa()["bg_surface"]
        super().__init__(parent, fg_color=bg_color, corner_radius=corner_radius, **kwargs)

class ModernButton(ctk.CTkButton):
    def __init__(self, parent, text, command, bg=None, hover_bg=None, fg="white", font=None, style_type=None, **kwargs):
        from app.frontend.theme_config import obtener_paleta_activa
        paleta = obtener_paleta_activa()
        
        # Si se especifica style_type o no se pasan colores específicos, usar el diseño estandarizado
        if style_type is not None or (bg is None and hover_bg is None):
            tipo = style_type or "primary"
            estilos = {
                "primary": (paleta["accent"], paleta["accent_hover"], "#ffffff"),
                "secondary": (paleta["button_secondary"], paleta["button_secondary_hover"], paleta["text_primary"]),
                "success": (paleta["button_success"], paleta["button_success_hover"], "#ffffff"),
                "danger": (paleta["button_danger"], paleta["button_danger_hover"], "#ffffff"),
                "warning": (paleta["button_warning"], paleta["button_warning_hover"], "#ffffff")
            }
            bg_col, hov_col, txt_col = estilos.get(tipo, estilos["primary"])
        else:
            # Mantener compatibilidad con firmas antiguas
            bg_col = bg
            hov_col = hover_bg
            txt_col = fg
            
        diseno_font = font or ("Segoe UI", 12, "bold")
        super().__init__(parent, text=text, command=command, fg_color=bg_col, hover_color=hov_col, text_color=txt_col, font=diseno_font, **kwargs)

def configurar_scrollbar_coherente(scrollbar):
    """Estiliza la barra de desplazamiento según el modo activo para dar una apariencia premium."""
    from app.frontend.theme_config import obtener_paleta_activa
    paleta = obtener_paleta_activa()
    scrollbar.configure(
        fg_color="transparent",
        button_color=paleta["border_color"],
        button_hover_color=paleta["accent"]
    )
