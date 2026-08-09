# app/frontend/interfaz_asignar_productos.py
# 🎨 ACTUALIZADO: Estilo de botones unificado
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, Toplevel
from app.frontend import custom_dialogs as messagebox

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

def ui_asignar_productos(parent: tk.Misc, backend, id_proveedor: int, nombre_proveedor: str):
    import customtkinter as ctk
    from app.frontend.theme_config import get_color, configurar_estilo_treeview, preparar_ventana, centrar_y_mostrar_ventana
    
    # 🔥 CARGA DE ESTILOS Y COLORES
    configurar_estilo_treeview()
    col_bg = get_color("bg_root")
    col_card = get_color("bg_surface")
    col_text = get_color("text_primary")
    col_input_bg = "#374151"
    col_input_fg = "#ffffff"
    col_border = "#2d3748"

    win = ctk.CTkToplevel(parent)
    preparar_ventana(win)
    win.title(f"Asignar Productos a: {nombre_proveedor}")
    win.geometry("800x700")
    win.resizable(True, True)
    win.minsize(680, 500)

    memoria_productos = {}
    
    # --- 1. Header y Búsqueda ---
    frame_top = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
    frame_top.pack(fill=tk.X, padx=20, pady=(20, 5))
    
    ctk.CTkLabel(frame_top, text="🔍 Buscar Producto:", font=("Segoe UI", 13, "bold"), text_color=col_text).pack(side="left", padx=15, pady=15)
    var_buscar = tk.StringVar()
    
    ent_buscar = ctk.CTkEntry(frame_top, textvariable=var_buscar, font=("Segoe UI", 12), width=300, height=38, placeholder_text="Buscar producto...")
    ent_buscar.pack(side="left", padx=15)
    
    def limpiar_filtros_asignar():
        var_buscar.set("")
        ent_buscar.focus_set()
        
    ctk.CTkButton(frame_top, text="🧹 Limpiar", command=limpiar_filtros_asignar, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 12, "bold"), width=100, height=35).pack(side="left", padx=(0, 10))
    
    ctk.CTkLabel(frame_top, text="(Espacio p/ marcar)", font=("Segoe UI", 11), text_color="#9ca3af").pack(side="left", padx=10)

    # --- 3. Botones Inferiores (empacados PRIMERO para que no queden aplastados) ---
    frame_btns = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
    frame_btns.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=(5, 20))

    # --- 2. Lista Central (Treeview) ---
    frame_lista = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
    frame_lista.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

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

    # Tags de color: verde suave para asignados, gris para no asignados
    tree.tag_configure("asignado", background="#14532d", foreground="#bbf7d0")
    tree.tag_configure("no_asignado", background="", foreground="#94a3b8")
    
    ys = ctk.CTkScrollbar(frame_lista, command=tree.yview)
    ys.pack(side="right", fill="y", padx=(0, 5), pady=5)
    tree.configure(yscrollcommand=ys.set)
    tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)

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
        
        # Ordenar: primero asignados (SI), luego no asignados (NO), alfabético dentro de cada grupo
        ids_ordenados = sorted(
            memoria_productos.keys(),
            key=lambda k: (0 if memoria_productos[k]['asignado_actual'] else 1,
                           memoria_productos[k]['nombre'].lower())
        )
        
        for pid in ids_ordenados:
            data = memoria_productos[pid]
            nombre = data['nombre']
            
            if filtro and filtro not in nombre.lower() and filtro not in str(pid):
                continue
            
            icono = "☑ SI" if data['asignado_actual'] else "☐ NO"
            tag = "asignado" if data['asignado_actual'] else "no_asignado"
            
            tree.insert("", tk.END, iid=str(pid), tags=(tag,), values=(
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
        tag = "asignado" if data['asignado_actual'] else "no_asignado"
        
        tree.item(pid_str, values=(icono, pid, data['nombre'], data['categoria']), tags=(tag,))

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

    # --- Botones (el frame ya fue empacado arriba, solo agregamos los botones) ---
    ctk.CTkButton(frame_btns, text="✓ Guardar Cambios", command=guardar_cambios, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 15, "bold"), width=200, height=45).pack(side="left", padx=20, pady=15)
    ctk.CTkButton(frame_btns, text="Cerrar", command=win.destroy, fg_color="#4b5563", hover_color="#374151", font=("Segoe UI", 14, "bold"), width=140, height=45).pack(side="right", padx=20, pady=15)

    cargar_datos_iniciales()
    configurar_navegacion_ventana(win)
    ent_buscar.focus_set()
    
    centrar_y_mostrar_ventana(win)
    win.grab_set()