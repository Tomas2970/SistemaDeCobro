# app/frontend/interfaz_asignar_productos.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

def ui_asignar_productos(parent: tk.Misc, backend, id_proveedor: int, nombre_proveedor: str):
    """
    Nueva interfaz de asignación rápida con Checkboxes simulados en Treeview.
    """
    win = Toplevel(parent)
    win.title(f"Asignar Productos a: {nombre_proveedor}")
    win.geometry("700x600")
    win.config(bg="#f4f4f8")
    win.resizable(False, True)

    # Datos en memoria
    # diccionario: {id_producto: {'nombre': str, 'asignado_original': bool, 'asignado_actual': bool}}
    memoria_productos = {}
    
    # --- 1. Header y Búsqueda ---
    frame_top = tk.Frame(win, bg="#f4f4f8", pady=10, padx=10)
    frame_top.pack(fill=tk.X)
    
    tk.Label(frame_top, text="Buscar Producto:", bg="#f4f4f8").pack(side=tk.LEFT)
    var_buscar = tk.StringVar()
    ent_buscar = tk.Entry(frame_top, textvariable=var_buscar, width=40)
    ent_buscar.pack(side=tk.LEFT, padx=10)
    
    tk.Label(frame_top, text="(Doble Clic o Espacio para marcar/desmarcar)", bg="#f4f4f8", fg="gray").pack(side=tk.LEFT)

    # --- 2. Lista Central (Treeview) ---
    frame_lista = tk.Frame(win, bg="#f4f4f8", padx=10)
    frame_lista.pack(fill=tk.BOTH, expand=True)

    # Columnas: Estado (Check), ID, Nombre, Categoría
    cols = ("Estado", "ID", "Producto", "Categoría")
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", selectmode="browse")
    
    tree.heading("Estado", text="Selección")
    tree.heading("ID", text="ID")
    tree.heading("Producto", text="Nombre del Producto")
    tree.heading("Categoría", text="Categoría")
    
    tree.column("Estado", width=80, anchor="center")
    tree.column("ID", width=60, anchor="center")
    tree.column("Producto", width=300)
    tree.column("Categoría", width=150)
    
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=ys.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    ys.pack(side=tk.RIGHT, fill=tk.Y)

    # --- Lógica de Datos ---
    def cargar_datos_iniciales():
        # 1. Traer TODOS los productos activos
        todos = backend.obtener_productos_full()
        
        # 2. Traer los que YA tiene asignados este proveedor
        asignados = backend.obtener_productos_por_proveedor(id_proveedor)
        ids_asignados = {p['id_producto'] for p in asignados}
        
        # 3. Llenar memoria
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
        # Guardar selección actual si la hay
        # (Omitido para simplificar, vuelve al inicio al filtrar)
        
        tree.delete(*tree.get_children())
        filtro = var_buscar.get().lower().strip()
        
        # Ordenar por nombre para facilitar búsqueda
        ids_ordenados = sorted(memoria_productos.keys(), key=lambda k: memoria_productos[k]['nombre'].lower())
        
        for pid in ids_ordenados:
            data = memoria_productos[pid]
            nombre = data['nombre']
            
            # Filtrado
            if filtro and filtro not in nombre.lower() and filtro not in str(pid):
                continue
            
            # Estado visual
            icono = "☑ SÍ" if data['asignado_actual'] else "☐ NO"
            # Opcional: cambiar color de fondo si está seleccionado (requiere tags)
            
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
        
        pid_str = sel[0] # El iid es el ID del producto
        pid = int(pid_str)
        
        # Invertir estado
        estado_actual = memoria_productos[pid]['asignado_actual']
        memoria_productos[pid]['asignado_actual'] = not estado_actual
        
        # Actualizar visualmente solo esa fila (para no recargar todo y perder scroll)
        data = memoria_productos[pid]
        icono = "☑ SÍ" if data['asignado_actual'] else "☐ NO"
        
        tree.item(pid_str, values=(icono, pid, data['nombre'], data['categoria']))

    # Bindings
    tree.bind("<Double-1>", toggle_seleccion)
    tree.bind("<space>", toggle_seleccion)
    tree.bind("<Return>", toggle_seleccion)

    # --- Guardado ---
    def guardar_cambios():
        cambios = 0
        errores = 0
        
        try:
            for pid, data in memoria_productos.items():
                # Solo actuar si hubo cambios
                if data['asignado_actual'] != data['asignado_original']:
                    if data['asignado_actual']:
                        # Asignar
                        ok = backend.asignar_producto_a_proveedor(id_proveedor, pid)
                    else:
                        # Quitar
                        ok = backend.quitar_producto_a_proveedor(id_proveedor, pid)
                    
                    if ok: 
                        cambios += 1
                    else:
                        errores += 1
            
            if errores > 0:
                messagebox.showwarning("Resultado", f"Se aplicaron {cambios} cambios, pero hubo {errores} errores.")
            else:
                messagebox.showinfo("Éxito", f"Se actualizaron correctamente los productos del proveedor.")
            
            win.destroy()
            
        except Exception as e:
            messagebox.showerror("Error crítico", f"Falló el guardado: {e}")

    # --- 3. Botones Inferiores ---
    frame_btns = tk.Frame(win, bg="#f4f4f8", pady=15)
    frame_btns.pack(fill=tk.X, side=tk.BOTTOM)
    
    tk.Button(frame_btns, text="Guardar Cambios", command=guardar_cambios, 
              bg="#4CAF50", fg="white", font=("Segoe UI", 11, "bold"), padx=20).pack(side=tk.RIGHT, padx=20)
    
    tk.Button(frame_btns, text="Cancelar", command=win.destroy, 
              bg="#f44336", fg="white", padx=10).pack(side=tk.RIGHT, padx=10)

    # Init
    cargar_datos_iniciales()
    configurar_navegacion_ventana(win)
    ent_buscar.focus_set()
    
    win.grab_set()