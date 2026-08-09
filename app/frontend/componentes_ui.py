# app/frontend/componentes_ui.py
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime

try:
    from tkcalendar import DateEntry
    HAY_CALENDARIO = True
except ImportError:
    HAY_CALENDARIO = False


if HAY_CALENDARIO:
    class DateEntryMejorado(DateEntry):
        """
        Subclase de DateEntry que corrige el bug de tkcalendar donde hacer
        clic en los botones ◄ ► de navegación cierra el popup.

        CAUSA RAÍZ:
        Cuando el Entry tiene foco (situación normal al cargar una pantalla)
        y el usuario abre el popup, tkcalendar llama a _calendar.focus_set().
        Esto dispara el mecanismo validate='focusout' del Entry, que puede
        generar eventos de foco adicionales antes de que el popup esté
        completamente renderizado, o puede intentar reclamar el foco de vuelta.
        Resultado: el binding <FocusOut> del Calendar se instala en un momento
        inestable, o el handler original cierra el popup.

        SOLUCIÓN — cuatro capas de protección:
          1. drop_down() evalúa 'opening' ANTES de llamar a super(), para saber
             con certeza si estamos abriendo. Desactiva validate='focusout'
             durante la transición para eliminar la pelea de foco Entry↔Calendar.
          2. _on_focus_out_seguro usa winfo_toplevel() (más robusto que walk de
             .master) para detectar si el foco sigue dentro del popup.
          3. winfo_containing() (más robusto que coordenadas manuales, maneja
             DPI scaling de Windows) como fallback cuando focus_get()==None.
          4. _ampliar_botones_nav agrega <FocusIn> en los botones de navegación
             para devolver el foco al Calendar si el botón lo roba brevemente.
        """

        def drop_down(self):
            """
            Abre o cierra el popup del calendario.

            IMPORTANTE: evaluamos 'opening' ANTES de llamar a super() para
            saber con certeza si estamos abriendo el popup. Si verificáramos
            winfo_ismapped() DESPUÉS, podría devolver False por el delay de Tk.

            Desactivamos validate='focusout' durante la apertura para evitar
            que el mecanismo de validación del Entry pelee por el foco contra
            el Calendar durante la transición Entry→Calendar. La validación
            de la fecha se hace igual porque super().drop_down() llama a
            _validate_date() explícitamente al principio.
            """
            opening = not self._calendar.winfo_ismapped()
            if opening:
                # Suprimir validate='focusout' solo durante la apertura
                self.configure(validate='none')
            try:
                super().drop_down()
            finally:
                if opening:
                    # Restaurar en el siguiente ciclo del event loop,
                    # DESPUÉS de que se procesen los eventos de foco pendientes
                    self.after(0, lambda: (
                        self.configure(validate='focusout')
                        if self.winfo_exists() else None
                    ))
            if opening:
                # Instalar nuestro handler seguro de FocusOut
                self._calendar.unbind('<FocusOut>')
                self._calendar.bind('<FocusOut>', self._on_focus_out_seguro)
                self.after(1, self._ampliar_botones_nav)

        def _on_focus_out_seguro(self, event):
            """
            Handler <FocusOut> robusto que NO cierra el popup cuando el
            foco sigue dentro de él (botones ◄ ►, días, encabezados).

            Estrategia 1 — winfo_toplevel():
              Si el widget que recibió el foco pertenece al mismo Toplevel
              que el popup (_top_cal), el foco sigue dentro → re-enfocar.
              Más robusto que walk de .master porque maneja correctamente
              widgets definidos con distintas jerarquías de master.

            Estrategia 2 — winfo_containing():
              Si focus_get() es None (foco fue al SO o a widget sin
              representación Python), usamos winfo_containing() para
              identificar qué widget está bajo el cursor del mouse.
              winfo_containing() maneja DPI scaling de Windows correctamente,
              a diferencia del cálculo manual de coordenadas.

            Si ninguna estrategia detecta interacción interna → el usuario
            clickeó afuera → comportamiento original (cerrar el popup).
            """
            try:
                # Si el popup ya fue cerrado (p.ej. por _select al elegir día)
                if not self._top_cal.winfo_ismapped():
                    return

                # ── Estrategia 1: winfo_toplevel() ──────────────────────────
                focused = self.focus_get()
                if focused is not None:
                    try:
                        if focused.winfo_toplevel() is self._top_cal:
                            # El foco sigue dentro del popup → no cerrar
                            self.after(10, self._calendar.focus_set)
                            return
                    except Exception:
                        pass

                # ── Estrategia 2: winfo_containing() ────────────────────────
                # Útil cuando focus_get() devuelve None porque el SO recibió
                # el foco (ttk.Button en Windows a veces no toma Tk-focus).
                try:
                    ptr_x, ptr_y = self._top_cal.winfo_pointerxy()
                    widget_bajo_cursor = self._top_cal.winfo_containing(ptr_x, ptr_y)
                    if widget_bajo_cursor is not None:
                        if widget_bajo_cursor.winfo_toplevel() is self._top_cal:
                            self.after(10, self._calendar.focus_set)
                            return
                except Exception:
                    pass

            except Exception:
                pass

            # Ninguna estrategia detectó foco interno → cerrar (comportamiento original)
            self._on_focus_out_cal(event)

        def _ampliar_botones_nav(self):
            """
            Agranda el padding de los 4 botones de navegación y agrega un
            binding <FocusIn> que devuelve el foco al Calendar si el botón
            lo roba brevemente (capa de protección extra).
            """
            try:
                cal = self._calendar
                for btn in (cal._l_month, cal._r_month, cal._l_year, cal._r_year):
                    btn.configure(padding=(8, 4, 8, 4))
                    # Si el botón recibe el foco (raro en Windows pero posible),
                    # devolverlo inmediatamente al Calendar.
                    btn.bind('<FocusIn>',
                             lambda e: self.after(1, self._calendar.focus_set),
                             add='+')
            except Exception:
                pass

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
            self.entrada = DateEntryMejorado(
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
            # Prevenir auto-foco: cuando una pantalla con calendarios se carga,
            # el DateEntry (primer widget focusable) toma el foco automáticamente.
            # Esto causa que cualquier apertura del popup entre en el escenario
            # problemático "Entry tenía foco antes de abrir". Redirigimos el foco
            # al toplevel luego de 50ms (suficiente para que la pantalla cargue,
            # insignificante para el usuario).
            self.after(50, self._prevenir_autofoco)
        else:
            self.entrada = ctk.CTkEntry(self, width=120) 
            self.widget_entrada = self.entrada
            if fecha_defecto:
                try: self.entrada.insert(0, fecha_defecto.strftime("%d/%m/%Y"))
                except AttributeError: self.entrada.insert(0, str(fecha_defecto))
            
        self.entrada.pack(fill=tk.BOTH, expand=True)

    def _prevenir_autofoco(self):
        """Si el DateEntry tomó el foco automáticamente al cargar la pantalla,
        lo redirige al Toplevel padre para que ningún widget quede enfocado."""
        try:
            if self.winfo_exists() and self.focus_get() is self.entrada:
                self.winfo_toplevel().focus_set()
        except Exception:
            pass

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
