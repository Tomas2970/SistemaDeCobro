# app/frontend/navegacion_teclado_comun.py
import tkinter as tk
from tkinter import ttk, messagebox

def configurar_navegacion_ventana(win: tk.Toplevel, confirmar_cierre: bool = False):
    """
    Configura navegación por teclado para una ventana Toplevel.
    
    Características:
    - Bloquea que las flechas/ENTER afecten la ventana de atrás.
    - Permite que ENTER dispare el botón que tenga el foco.
    - Se asegura de que los widgets importantes acepten TAB.
    - ESC cierra la ventana (con confirmación opcional).
    - Centra la ventana en pantalla automáticamente.
    
    Args:
        win: La ventana Toplevel a configurar
        confirmar_cierre: Si True, pide confirmación antes de cerrar con ESC
    """

    # --- ENTER: ejecutar el botón que tiene el foco ---
    def on_return(event):
        widget = win.focus_get()
        try:
            if isinstance(widget, (tk.Button, ttk.Button)):
                widget.invoke()
        except Exception:
            # No rompemos la app si algo falla
            pass
        # Consumimos el evento para que no llegue al menú de atrás
        return "break"

    win.bind("<Return>", on_return)
    win.bind("<KP_Enter>", on_return)  # ENTER del pad numérico

    # --- ESC: cerrar la ventana ---
    def on_escape(event):
        if confirmar_cierre:
            respuesta = messagebox.askyesno(
                "Confirmar",
                "¿Está seguro que desea cerrar esta ventana?",
                parent=win
            )
            if respuesta:
                win.destroy()
        else:
            win.destroy()
        return "break"
    
    win.bind("<Escape>", on_escape)

    # --- Bloquear flechas para que no lleguen al menú de atrás ---
    def bloquear_flechas(event):
        # El widget ya procesó la flecha, solo evitamos que siga
        return "break"

    for tecla in ("<Up>", "<Down>", "<Left>", "<Right>"):
        win.bind(tecla, bloquear_flechas)

    # --- Asegurar que los widgets importantes acepten TAB ---
    def habilitar_tab_en_hijos(widget):
        for child in widget.winfo_children():
            try:
                clase = child.winfo_class()
                # Labels, Frames y Canvas (usado por ctk para dibujar) no deben robar foco
                if clase not in ("TLabel", "Label", "Frame", "Canvas"):
                    child.configure(takefocus=True)
                elif clase == "Canvas":
                    child.configure(takefocus=False)
            except Exception:
                pass
            habilitar_tab_en_hijos(child)

    # Un poquito después de que se cree la ventana, así ya existen todos los widgets
    win.after(10, lambda: habilitar_tab_en_hijos(win))

    # --- Centrar la ventana en pantalla ---
    def _centrar():
        try:
            win.update_idletasks()
            w = win.winfo_width()
            h = win.winfo_height()
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
            # Solo centrar si la ventana no está maximizada
            if w < sw and h < sh:
                win.geometry(f"+{x}+{y}")
        except Exception:
            pass

    win.after(50, _centrar)

def configurar_navegacion_teclado(parent, widgets):
    '''Permite navegar entre los widgets dados con flechas arriba/abajo'''
    def focus_next(event, is_next):
        try:
            # Algunas veces event.widget devuelve un string (ej en ctk), o el widget root
            # Lo hacemos simple:
            if event.widget not in widgets: return
            idx = widgets.index(event.widget)
            next_idx = (idx + 1) if is_next else (idx - 1)
            widgets[next_idx % len(widgets)].focus_set()
            return "break"
        except Exception:
            pass

    for w in widgets:
        w.bind("<Down>", lambda e: focus_next(e, True))
        w.bind("<Up>", lambda e: focus_next(e, False))
