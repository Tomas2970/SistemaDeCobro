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
                # Labels y Frames no suelen necesitar foco
                if clase not in ("TLabel", "Label", "Frame"):
                    child.configure(takefocus=True)
            except Exception:
                pass
            habilitar_tab_en_hijos(child)

    # Un poquito después de que se cree la ventana, así ya existen todos los widgets
    win.after(10, lambda: habilitar_tab_en_hijos(win))