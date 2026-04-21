import codecs

codigo = """
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
"""

with codecs.open('app/frontend/navegacion_teclado_comun.py', 'a', 'utf-8') as f:
    f.write(codigo)

print("Funcion de atajos por teclado restaurada exitosamente.")
