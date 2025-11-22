# app/frontend/interfaz_categorias.py
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from app.frontend.componentes_ui import EntryDecimal
from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana

def ui_categorias(parent: tk.Misc, backend):
    win = Toplevel(parent)
    win.title("Gestión de Categorías")
    win.geometry("500x400")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # --- Lista ---
    frame_lista = tk.Frame(win, bg="#f4f4f8")
    frame_lista.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    cols = ("ID", "Nombre", "Margen (%)")
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings")
    
    tree.heading("ID", text="ID")
    tree.heading("Nombre", text="Nombre")
    tree.heading("Margen (%)", text="Margen Sugerido (%)")
    
    tree.column("ID", width=50, anchor="center")
    tree.column("Nombre", width=200)
    tree.column("Margen (%)", width=100, anchor="e")
    
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=ys.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    ys.pack(side=tk.RIGHT, fill=tk.Y)

    def cargar():
        for i in tree.get_children(): tree.delete(i)
        cats = backend.obtener_categorias()
        for c in cats:
            tree.insert("", tk.END, values=(
                c['id_categoria'],
                c['nombre'],
                f"{float(c.get('margen_ganancia', 0)):.2f}"
            ))

    # --- Variable para controlar si ya hay una ventana de edición abierta ---
    ventana_edicion_abierta = False

    def abrir_editor(categoria=None):
        nonlocal ventana_edicion_abierta
        if ventana_edicion_abierta: 
            return # Evitar abrir más de una

        pop = Toplevel(win)
        ventana_edicion_abierta = True # Marcar como abierta
        
        titulo = "Editar Categoría" if categoria else "Nueva Categoría"
        pop.title(titulo)
        pop.geometry("300x240")
        pop.config(bg="#f4f4f8")
        
        # Al cerrar la ventana, liberar la bandera
        def on_close():
            nonlocal ventana_edicion_abierta
            ventana_edicion_abierta = False
            pop.destroy()
        
        pop.protocol("WM_DELETE_WINDOW", on_close)
        
        tk.Label(pop, text="Nombre:", bg="#f4f4f8").pack(pady=(20,5))
        ent_nom = tk.Entry(pop, width=30)
        ent_nom.pack()
        if categoria: ent_nom.insert(0, categoria[1])
        
        tk.Label(pop, text="Margen de Ganancia (%):", bg="#f4f4f8").pack(pady=(10,5))
        ent_mar = EntryDecimal(pop, width=10)
        ent_mar.pack()
        val_margen = categoria[2] if categoria else "30.00"
        ent_mar.insert(0, val_margen)

        def guardar():
            nom = ent_nom.get().strip()
            try: mar = float(ent_mar.get())
            except: 
                messagebox.showerror("Error", "Margen inválido", parent=pop)
                return
            if not nom:
                messagebox.showerror("Error", "Nombre obligatorio", parent=pop)
                return
            if categoria:
                backend.actualizar_categoria(categoria[0], nom, mar)
            else:
                backend.crear_categoria(nom, mar)
            cargar()
            on_close()

        tk.Button(pop, text="Guardar", bg="#4CAF50", fg="white", command=guardar).pack(pady=20)
        
        configurar_navegacion_ventana(pop)
        
        # --- CLAVE PARA QUE NO SE PUEDA CLICKEAR ATRÁS ---
        pop.transient(win) # La mantiene siempre encima de la ventana padre
        pop.grab_set()     # Secuestra todos los eventos, nada más funciona hasta cerrar esta
        ent_nom.focus_set()
        win.wait_window(pop) # Espera a que se cierre para continuar código si fuera necesario

    def editar_seleccionado():
        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], 'values')
        abrir_editor(item)

    # Botones
    frame_btns = tk.Frame(win, bg="#f4f4f8")
    frame_btns.pack(pady=10)
    tk.Button(frame_btns, text="+ Nueva Categoría", bg="#03A9F4", fg="white", command=lambda: abrir_editor(None)).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_btns, text="✎ Editar Margen/Nombre", bg="#FFC107", command=editar_seleccionado).pack(side=tk.LEFT, padx=10)

    tree.bind("<Double-1>", lambda e: editar_seleccionado())

    cargar()
    configurar_navegacion_ventana(win, confirmar_cierre=True)
    win.grab_set()