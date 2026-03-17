# app/frontend/interfaz_asignar_productos.py
# 🎨 ACTUALIZADO: Estilo de botones unificado
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

def ui_asignar_productos(parent: tk.Misc, backend, id_proveedor: int, nombre_proveedor: str):
    """Nueva interfaz de asignación rápida con Checkboxes simulados en Treeview"""
    win = Toplevel(parent)
    win.title(f"Asignar Productos a: {nombre_proveedor}")
    win.geometry("750x650")
    win.config(bg="#f4f4f8")
    win.resizable(False, True)

    # 🔥 ESTILOS MODERNOS
    style = ttk.Style()
    style.theme_use('clam')
    
    style.configure("Modern.Treeview",
                    background="#ffffff",
                    foreground="#1f2937",
                    rowheight=32,
                    fieldbackground="#ffffff",
                    borderwidth=0,
                    font=('Segoe UI', 10))
    
    style.configure("Modern.Treeview.Heading",
                    background="#f3f4f6",
                    foreground="#374151",
                    relief="flat",
                    borderwidth=1,
                    font=('Segoe UI', 10, 'bold'))

    memoria_productos = {}
    
    # --- 1. Header y Búsqueda ---
    frame_top = tk.Frame(win, bg="#ffffff", pady=12, padx=15)
    frame_top.pack(fill=tk.X, padx=10, pady=(10, 5))
    
    tk.Label(
        frame_top, 
        text="Buscar Producto:", 
        bg="#ffffff",
        font=("Segoe UI", 10, "bold"),
        fg="#1f2937"
    ).pack(side=tk.LEFT, padx=5)
    
    var_buscar = tk.StringVar()
    ent_buscar = tk.Entry(frame_top, textvariable=var_buscar, width=40, font=("Segoe UI", 10))
    ent_buscar.pack(side=tk.LEFT, padx=10)
    
    tk.Label(
        frame_top, 
        text="(Doble Clic o Espacio para marcar/desmarcar)", 
        bg="#ffffff", 
        fg="#6b7280",
        font=("Segoe UI", 9)
    ).pack(side=tk.LEFT)

    # --- 2. Lista Central (Treeview) ---
    frame_lista = tk.Frame(win, bg="#f4f4f8", padx=10)
    frame_lista.pack(fill=tk.BOTH, expand=True)

    cols = ("Estado", "ID", "Producto", "Categoría")
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", selectmode="browse", style="Modern.Treeview")
    
    tree.heading("Estado", text="Selección")
    tree.heading("ID", text="ID")
    tree.heading("Producto", text="Nombre del Producto")
    tree.heading("Categoría", text="Categoría")
    
    tree.column("Estado", width=80, anchor="center")
    tree.column("ID", width=60, anchor="center")
    tree.column("Producto", width=350)
    tree.column("Categoría", width=180)
    
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=ys.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    ys.pack(side=tk.RIGHT, fill=tk.Y)

    # --- Lógica de Datos ---
    def cargar_datos_iniciales():
        todos = backend.obtener_productos_full()
        asignados = backend.obtener_productos_por_proveedor(id_proveedor)
        ids_asignados = {p['id_producto'] for p in asignados}
        
        memoria_productos.clear()
        for p in todos:
            pid = p.get('id_producto') or p.get('id')
            if not pid: continue
            
            es_asignado = pid in ids_asignados
            memoria_productos[pid] = {
                'nombre': p.get('nombre', ''),
                'categoria': p.get('categoria') or p.get('nombre_categoria') or '',
                'asignado_original': es_asignado,
                'asignado_actual': es_asignado
            }
        
        renderizar_lista()

    def renderizar_lista(*args):
        tree.delete(*tree.get_children())
        filtro = var_buscar.get().lower().strip()
        
        ids_ordenados = sorted(memoria_productos.keys(), key=lambda k: memoria_productos[k]['nombre'].lower())
        
        for pid in ids_ordenados:
            data = memoria_productos[pid]
            nombre = data['nombre']
            
            if filtro and filtro not in nombre.lower() and filtro not in str(pid):
                continue
            
            icono = "☑ SI" if data['asignado_actual'] else "☐ NO"
            
            tree.insert("", tk.END, iid=str(pid), values=(
                icono,
                pid,
                nombre,
                data['categoria']
            ))

    var_buscar.trace_add("write", renderizar_lista)

    # --- Lógica de Interacción ---
    def toggle_seleccion(event=None):
        sel = tree.selection()
        if not sel: return
        
        pid_str = sel[0]
        pid = int(pid_str)
        
        estado_actual = memoria_productos[pid]['asignado_actual']
        memoria_productos[pid]['asignado_actual'] = not estado_actual
        
        data = memoria_productos[pid]
        icono = "☑ SI" if data['asignado_actual'] else "☐ NO"
        
        tree.item(pid_str, values=(icono, pid, data['nombre'], data['categoria']))

    tree.bind("<Double-1>", toggle_seleccion)
    tree.bind("<space>", toggle_seleccion)
    tree.bind("<Return>", toggle_seleccion)

    # --- Guardado ---
    def guardar_cambios():
        cambios = 0
        errores = 0

        # Calcular cambios pendientes antes de guardar
        pendientes = [(pid, data) for pid, data in memoria_productos.items()
                      if data['asignado_actual'] != data['asignado_original']]

        if not pendientes:
            messagebox.showinfo("Sin cambios", "No realizaste ningún cambio para guardar.", parent=win)
            return

        try:
            for pid, data in pendientes:
                if data['asignado_actual']:
                    ok = backend.asignar_producto_a_proveedor(id_proveedor, pid)
                else:
                    ok = backend.quitar_producto_a_proveedor(id_proveedor, pid)

                if ok:
                    cambios += 1
                else:
                    errores += 1

            if errores > 0:
                messagebox.showwarning("Resultado", f"Se aplicaron {cambios} cambios, pero hubo {errores} errores.", parent=win)
            else:
                messagebox.showinfo("Éxito", f"Se guardaron {cambios} cambio(s) correctamente.", parent=win)

            win.destroy()

        except Exception as e:
            messagebox.showerror("Error crítico", f"Falló el guardado: {e}", parent=win)

    # --- 3. Botones Inferiores ---
    frame_btns = tk.Frame(win, bg="#f4f4f8", pady=15)
    frame_btns.pack(fill=tk.X, side=tk.BOTTOM)
    
    # 🔥 BOTONES ESTILO NUEVO
    tk.Button(
        frame_btns, 
        text="Cancelar", 
        command=win.destroy, 
        bg="#6b7280", 
        fg="white",
        font=("Segoe UI", 10),
        relief="flat",
        padx=15,
        pady=10,
        cursor="hand2",
        activebackground="#4b5563"
    ).pack(side=tk.RIGHT, padx=10)
    
    tk.Button(
        frame_btns, 
        text="✓ Guardar Cambios", 
        command=guardar_cambios, 
        bg="#10b981", 
        fg="white", 
        font=("Segoe UI", 11, "bold"),
        relief="flat",
        padx=25,
        pady=10,
        cursor="hand2",
        activebackground="#059669"
    ).pack(side=tk.RIGHT, padx=10)

    cargar_datos_iniciales()
    configurar_navegacion_ventana(win)
    ent_buscar.focus_set()
    
    win.grab_set()