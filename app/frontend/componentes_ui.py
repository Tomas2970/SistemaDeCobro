# app/frontend/componentes_ui.py
import tkinter as tk
from tkinter import ttk

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
    - max_chars: Cantidad máxima de números (ej: 8 para DNI).
    """
    def __init__(self, parent, max_chars=None, *args, **kwargs):
        # Por defecto, alinear números a la derecha
        if 'justify' not in kwargs:
            kwargs['justify'] = 'right'
        
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
        if 'justify' not in kwargs:
            kwargs['justify'] = 'right'
        super().__init__(parent, *args, **kwargs)
        
        vcmd = (self.register(self._validar_decimal), '%P')
        self.configure(validate='key', validatecommand=vcmd)

    def _validar_decimal(self, texto_nuevo):
        if not texto_nuevo: return True
        # No permitir más de un punto
        if texto_nuevo.count('.') > 1: return False
        
        # Intentar ver si es un número válido (o está escribiendo el punto)
        try:
            if texto_nuevo != '.': 
                float(texto_nuevo)
            return True
        except ValueError:
            return False

class SelectorFecha(ttk.Frame):
    """
    Componente para seleccionar fechas.
    Usa un calendario si está instalado, sino un campo de texto.
    """
    def __init__(self, parent, fecha_defecto=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        if HAY_CALENDARIO:
            self.entrada = DateEntry(self, width=12, background='darkblue',
                                     foreground='white', borderwidth=2,
                                     date_pattern='dd/mm/yyyy')
            if fecha_defecto:
                self.entrada.set_date(fecha_defecto)
        else:
            self.entrada = ttk.Entry(self, width=12)
            if fecha_defecto:
                self.entrada.insert(0, fecha_defecto.strftime("%d/%m/%Y"))
            
        self.entrada.pack(fill=tk.BOTH, expand=True)

    def get_date_str(self):
        """Retorna DD/MM/YYYY"""
        if HAY_CALENDARIO:
            return self.entrada.get_date().strftime("%d/%m/%Y")
        else:
            return self.entrada.get()
    
    def get_date_sql(self):
        """Retorna YYYY-MM-DD para la base de datos"""
        if HAY_CALENDARIO:
            return self.entrada.get_date().strftime("%Y-%m-%d")
        else:
            # Intento manual de parseo si no hay calendario
            try:
                parts = self.entrada.get().split('/')
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
            except:
                return None