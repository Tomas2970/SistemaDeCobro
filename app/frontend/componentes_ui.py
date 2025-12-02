# app/frontend/componentes_ui.py
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime

# Intentamos importar tkcalendar para el futuro (Fase 3 y 4)
# Si no está instalado, usa un Entry normal sin romper nada.
try:
    from tkcalendar import DateEntry
    HAY_CALENDARIO = True
except ImportError:
    HAY_CALENDARIO = False

class EntryNumerico(ttk.Entry):
    """
    Campo de texto que SOLO acepta números.
    - Se alinea a la derecha automáticamente.
    - Bloquea letras y símbolos.
    - max_chars: Cantidad máxima de números (ej: 8 para DNI, 11 para CUIT).
    """
    def __init__(self, parent, max_chars=None, *args, **kwargs):
        # --- CORRECCIÓN: Forzar alineación a la derecha ---
        if 'justify' not in kwargs:
            kwargs['justify'] = 'right'
        # --- FIN CORRECCIÓN ---
        
        super().__init__(parent, *args, **kwargs)
        self.max_chars = max_chars
        
        # Registrar la función de validación en Tkinter
        vcmd = (self.register(self._validar_numero), '%P')
        self.configure(validate='key', validatecommand=vcmd)

    def _validar_numero(self, texto_nuevo):
        # Si se borra todo, es válido
        if not texto_nuevo:
            return True
            
        # Verificar que sean solo dígitos
        if not texto_nuevo.isdigit():
            return False
            
        # Verificar longitud máxima (si se especificó)
        if self.max_chars is not None and len(texto_nuevo) > self.max_chars:
            return False
            
        return True

class EntryDecimal(ttk.Entry):
    """
    Campo para PRECIOS o CANTIDADES (con decimales).
    - Se alinea a la derecha.
    - Solo permite números y UN solo punto.
    """
    def __init__(self, parent, *args, **kwargs):
        # --- CORRECCIÓN: Forzar alineación a la derecha ---
        if 'justify' not in kwargs:
            kwargs['justify'] = 'right'
        # --- FIN CORRECCIÓN ---
        
        super().__init__(parent, *args, **kwargs)
        
        vcmd = (self.register(self._validar_decimal), '%P')
        self.configure(validate='key', validatecommand=vcmd)

    def _validar_decimal(self, texto_nuevo):
        if not texto_nuevo: return True
        # No permitir más de un punto
        if texto_nuevo.count('.') > 1: return False
        
        # Intentar ver si es un número válido (o está escribiendo el punto)
        try:
            # Permitir que el punto se escriba solo si no es el único caracter y hay algo antes.
            if texto_nuevo == '.' and self.get() != '': return False
            if texto_nuevo != '.': 
                float(texto_nuevo)
            return True
        except ValueError:
            return False

class SelectorFecha(ttk.Frame):
    """
    Componente para seleccionar fechas (Almanaque).
    Usa un calendario si está instalado, sino un campo de texto simple.
    
    NOTA DE CORRECCIÓN: Ahora el widget de entrada se accede como .widget_entrada
    para unificar el acceso a .delete() y .insert()
    """
    def __init__(self, parent, fecha_defecto=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.widget_entrada = None
        
        if HAY_CALENDARIO:
            self.entrada = DateEntry(self, width=12, background='darkblue',
                                     foreground='white', borderwidth=2,
                                     date_pattern='dd/mm/yyyy')
            self.widget_entrada = self.entrada # DateEntry actúa como su propio Entry
            if fecha_defecto:
                try:
                    self.entrada.set_date(fecha_defecto)
                except Exception:
                    pass
        else:
            # Fallback a Entry simple (sin almanaque)
            self.entrada = tk.Entry(self, width=12) 
            self.widget_entrada = self.entrada # Entry simple
            if fecha_defecto:
                try:
                    self.entrada.insert(0, fecha_defecto.strftime("%d/%m/%Y"))
                except AttributeError:
                    self.entrada.insert(0, str(fecha_defecto))
            
        self.entrada.pack(fill=tk.BOTH, expand=True)

    def get_date_str(self):
        """Retorna DD/MM/YYYY"""
        if HAY_CALENDARIO:
            try:
                return self.entrada.get_date().strftime("%d/%m/%Y")
            except Exception:
                return ""
        else:
            return self.entrada.get()
    
    def get_date_sql(self):
        """Retorna YYYY-MM-DD para la base de datos"""
        if HAY_CALENDARIO:
            try:
                return self.entrada.get_date().strftime("%Y-%m-%d")
            except Exception:
                return None
        else:
            # Intento manual de parseo si no hay calendario
            try:
                # Asumimos que el usuario lo escribió como DD/MM/YYYY
                parts = self.entrada.get().split('/')
                if len(parts) == 3:
                    return f"{parts[2]}-{parts[1]}-{parts[0]}"
                return None
            except:
                return None