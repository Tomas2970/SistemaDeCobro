# app/frontend/interfaz_productos.py
# 🔥 ACTUALIZADO: Popup de asignación muestra datos de Empresa (sin vendedor)
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Listbox, MULTIPLE
import re

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

from app.frontend.componentes_ui import EntryDecimal, EntryNumerico
from app.frontend.stock_event_manager import stock_events

def ui_productos(parent: tk.Misc, backend, usuario: dict, id_producto_a_cargar: int | None = None, callback_on_save=None) -> None:
    
    win = tk.Toplevel(parent)
    win.title("Gestión de Productos")
    win.geometry("650x700") 
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # VALIDADORES
    def validar_len_30(t): return len(t) <= 30
    def validar_len_60(t): return len(t) <= 60
    
    def validar_stock(t):
        if t == "": return True
        if len(t) > 10: return False
        return re.match(r'^[0-9]*\.?[0-9]*$', t) is not None

    vc_30 = (win.register(validar_len_30), '%P')
    vc_60 = (win.register(validar_len_60), '%P')
    vc_stock = (win.register(validar_stock), '%P')

    # HEADER BÚSQUEDA
    frm_busqueda = tk.Frame(win, bg="#f4f4f8")
    frm_busqueda.pack(fill=tk.X, padx=20, pady=15) 
    tk.Label(frm_busqueda, text="Buscar (ID/Cód/Nom):", bg="#f4f4f8").pack(side=tk.LEFT)
    var_token = tk.StringVar()
    ent_busqueda = tk.Entry(frm_busqueda, textvariable=var_token, width=25, validate="key", validatecommand=vc_30)
    ent_busqueda.pack(side=tk.LEFT, padx=5)
    
    # FORMULARIO
    body = tk.Frame(win, bg="#f4f4f8")
    body.pack(fill=tk.X, padx=20, pady=5)
    body.columnconfigure(1, weight=1)

    row = 0
    def add_row(lbl: str, widget):
        nonlocal row
        tk.Label(body, text=lbl, bg="#f4f4f8").grid(row=row, column=0, sticky="e", padx=5, pady=8)
        widget.grid(row=row, column=1, sticky="w", padx=5, pady=8)
        row += 1

    var_id = tk.StringVar()
    
    var_nombre = tk.StringVar()
    ent_nombre = tk.Entry(body, textvariable=var_nombre, width=45, validate="key", validatecommand=vc_60)
    add_row("Nombre:", ent_nombre)
    
    combo_cat = ttk.Combobox(body, state="readonly", width=43)
    add_row("Categoría:", combo_cat)
    
    var_precio = tk.StringVar(value="0.00")
    ent_precio = EntryDecimal(body, textvariable=var_precio, width=15, justify="right")
    add_row("Precio Venta ($):", ent_precio)
    
    var_es_pesable = tk.BooleanVar(value=False)
    chk_pesable = tk.Checkbutton(body, text="Es pesable (kg) [Automático por Categoría]", variable=var_es_pesable, bg="#f4f4f8", fg="#555")
    add_row("", chk_pesable)
    
    categorias_data = []
    cat_map = {}
    
    def cargar_categorias_memoria():
        nonlocal categorias_data, cat_map
        categorias_data = backend.obtener_categorias()
        cat_map = {c['nombre']: c for c in categorias_data}
        combo_cat['values'] = [c['nombre'] for c in categorias_data]
        combo_cat.ids = [c['id_categoria'] for c in categorias_data]

    def al_cambiar_categoria(event=None):
        nombre_cat = combo_cat.get()
        datos_cat = cat_map.get(nombre_cat)
        if datos_cat:
            es_pesable_default = bool(datos_cat.get('es_pesable_default', False))
            var_es_pesable.set(es_pesable_default)
            if es_pesable_default:
                chk_pesable.config(state="normal", text="Es pesable (kg)")
            else:
                chk_pesable.config(state="disabled", text="Es pesable (kg) [Bloqueado por Categoría]")
        else:
            chk_pesable.config(state="normal", text="Es pesable (kg)")

    combo_cat.bind("<<ComboboxSelected>>", al_cambiar_categoria)

    var_cod = tk.StringVar()
    ent_cod = tk.Entry(body, textvariable=var_cod, width=45, validate="key", validatecommand=vc_30)
    add_row("Código Barras:", ent_cod)
    
    var_stock = tk.StringVar(value="0")
    ent_stock = tk.Entry(body, textvariable=var_stock, width=15, justify="right", validate="key", validatecommand=vc_stock) 
    add_row("Stock Actual:", ent_stock)
    
    var_stock_min = tk.StringVar(value="5")
    ent_stock_min = EntryNumerico(body, textvariable=var_stock_min, width=15, justify="right")
    add_row("Stock Mínimo:", ent_stock_min)

    var_asignar_prov = tk.BooleanVar(value=False)
    chk_asignar = tk.Checkbutton(body, text="Asignar a empresas proveedoras al guardar", 
                                 variable=var_asignar_prov, bg="#f4f4f8", font=("Segoe UI", 9, "bold"))
    chk_asignar.grid(row=row, column=1, sticky="w", padx=5, pady=10)
    row += 1

    def abrir_popup_asignacion(pid, nombre_prod):
        pop = Toplevel(win)
        pop.title(f"Asignar Empresas - {nombre_prod}")
        pop.geometry("700x550") 
        pop.config(bg="#f4f4f8")
        
        frm_bus = tk.Frame(pop, bg="#f4f4f8", pady=10)
        frm_bus.pack(fill=tk.X, padx=15)
        tk.Label(frm_bus, text="🔎 Buscar Empresa:", bg="#f4f4f8", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        var_filtro = tk.StringVar()
        ent_filtro = tk.Entry(frm_bus, textvariable=var_filtro, font=("Segoe UI", 10), width=40)
        ent_filtro.pack(side=tk.LEFT, padx=10)
        ent_filtro.focus_set()
        
        frm_tree = tk.Frame(pop, bg="#f4f4f8")
        frm_tree.pack(fill=tk.BOTH, expand=True, padx=15)
        
        # 🔥 TABLA MODERNA ACTUALIZADA: Empresa y CUIT
        cols = ("ID", "Empresa", "CUIT")
        tree_p = ttk.Treeview(frm_tree, columns=cols, show="headings", height=12, style="Modern.Treeview")
        tree_p.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sc_p = ttk.Scrollbar(frm_tree, orient="vertical", command=tree_p.yview)
        sc_p.pack(side=tk.RIGHT, fill=tk.Y)
        tree_p.configure(yscrollcommand=sc_p.set)
        
        tree_p.heading("ID", text="ID")
        tree_p.heading("Empresa", text="Empresa")
        tree_p.heading("CUIT", text="CUIT")
        tree_p.column("ID", width=60, anchor="center")
        tree_p.column("Empresa", width=350)
        tree_p.column("CUIT", width=150, anchor="center")
        
        tree_p.tag_configure('seleccionado', background='#dbeafe', foreground='#1e40af')
        
        all_provs = backend.obtener_proveedores()
        proveedores_seleccionados = set() 
        
        def filtrar_lista(*args):
            for i in tree_p.get_children(): 
                tree_p.delete(i)
            query = var_filtro.get().lower()
            for p in all_provs:
                if not p.get('activo', True): 
                    continue
                empresa = p.get('empresa', '')
                cuit = p.get('cuit') or "-"
                if query in empresa.lower() or query in str(cuit):
                    tag = 'seleccionado' if p['id_proveedor'] in proveedores_seleccionados else ''
                    prefijo = "✓ " if p['id_proveedor'] in proveedores_seleccionados else ""
                    tree_p.insert("", tk.END, 
                                values=(p['id_proveedor'], f"{prefijo}{empresa}", cuit),
                                tags=(tag,))
        
        var_filtro.trace_add("write", filtrar_lista)
        filtrar_lista()
        
        def toggle_seleccion(event=None):
            sel = tree_p.selection()
            if not sel: return
            p_id = int(tree_p.item(sel[0], "values")[0])
            if p_id in proveedores_seleccionados: proveedores_seleccionados.remove(p_id)
            else: proveedores_seleccionados.add(p_id)
            filtrar_lista()
        
        tree_p.bind("<Button-1>", lambda e: win.after(10, toggle_seleccion))
        
        fr_btns = tk.Frame(pop, bg="#f4f4f8", pady=15)
        fr_btns.pack(fill=tk.X)
        
        def guardar_asignaciones():
            if not proveedores_seleccionados:
                messagebox.showwarning("Atención", "Seleccione al menos una empresa.", parent=pop)
                return
            count = 0
            for p_id in proveedores_seleccionados:
                if backend.asignar_producto_a_proveedor(p_id, pid): count += 1
            messagebox.showinfo("Listo", f"Vinculado a {count} empresa(s).", parent=pop)
            pop.destroy()
        
        tk.Button(fr_btns, text="✓ Guardar Asignación", bg="#10b981", fg="white", 
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=25, pady=10, 
                  command=guardar_asignaciones, cursor="hand2").pack(side=tk.LEFT, padx=(220, 10))
        
        tk.Button(fr_btns, text="Cancelar", bg="#6b7280", fg="white", 
                  font=("Segoe UI", 10), relief="flat", padx=15, pady=10, 
                  command=pop.destroy, cursor="hand2").pack(side=tk.LEFT)
        
        configurar_navegacion_ventana(pop)
        pop.grab_set()
        win.wait_window(pop)

    actions = tk.Frame(win, bg="#f4f4f8", pady=10)
    actions.pack(fill=tk.X) 
    
    def limpiar():
        var_id.set(""); var_nombre.set(""); var_precio.set("0.00")
        var_stock.set("0"); var_stock_min.set("5"); var_cod.set("")
        var_es_pesable.set(False); chk_pesable.config(state="normal") 
        var_asignar_prov.set(False); combo_cat.set('')
        if combo_cat['values']: combo_cat.current(0); al_cambiar_categoria(None)
        ent_nombre.focus_set()

    def buscar():
        token = var_token.get().strip()
        if not token: return
        prod = backend.buscar_producto_por_codigo_barras(token) or \
               backend.buscar_producto_por_id(token) or \
               (backend.buscar_producto_por_nombre(token)[0] if backend.buscar_producto_por_nombre(token) else None)
        if prod:
            var_id.set(str(prod.get('id_producto')))
            var_nombre.set(prod.get('nombre'))
            var_precio.set(f"{float(prod.get('precio')): .2f}")
            stock_val = float(prod.get('stock'))
            es_pesable = bool(prod.get('es_pesable'))
            var_stock.set(f"{int(stock_val)}" if not es_pesable else f"{stock_val:.3f}")
            var_stock_min.set(str(prod.get('stock_minimo')))
            var_cod.set(prod.get('codigo_barras') or "")
            var_es_pesable.set(es_pesable)
            if prod.get('nombre_categoria') in combo_cat['values']:
                combo_cat.set(prod.get('nombre_categoria')); al_cambiar_categoria(None) 
        else: messagebox.showinfo("Info", "No encontrado.", parent=win)

    def guardar():
        try:
            nombre = var_nombre.get().strip()
            precio = float(var_precio.get() or 0)
            stock = float(var_stock.get() or 0)
            minimo = int(var_stock_min.get() or 0)
            codigo = var_cod.get().strip() or None

            # Validaciones antes de guardar
            if not nombre:
                messagebox.showwarning("Campo requerido", "El nombre del producto es obligatorio.", parent=win)
                return
            if precio <= 0:
                messagebox.showwarning("Campo requerido", "El precio de venta debe ser mayor a 0.", parent=win)
                return
            if combo_cat.current() < 0:
                messagebox.showwarning("Campo requerido", "Debe seleccionar una categoría.", parent=win)
                return

            idx = combo_cat.current()
            cat_id = combo_cat.ids[idx]
            pid = int(var_id.get()) if var_id.get().isdigit() else None
            es_creacion = (pid is None)

            if pid:
                backend.actualizar_producto(pid, nombre, precio, codigo, var_es_pesable.get(), cat_id, usuario.get('id_usuario'))
                backend.actualizar_inventario_absoluto(pid, stock, minimo, usuario.get('id_usuario'))
                res_id = pid
            else:
                res_id = backend.crear_producto_completo(nombre, cat_id, codigo, precio, stock, minimo, var_es_pesable.get(), usuario.get('id_usuario'))

            if not res_id:
                messagebox.showerror("Error", "No se pudo guardar el producto.", parent=win)
                return

            messagebox.showinfo("Éxito", "Producto guardado correctamente.", parent=win)
            stock_events.notificar_cambio_stock()
            if res_id and var_asignar_prov.get(): abrir_popup_asignacion(res_id, nombre)
            if es_creacion: limpiar()
            if callback_on_save: callback_on_save()
        except Exception as e: messagebox.showerror("Error", str(e), parent=win)
            
    tk.Button(frm_busqueda, text="🔍 Buscar", command=buscar, bg="#3b82f6", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8, cursor="hand2").pack(side=tk.LEFT, padx=2)
    tk.Button(frm_busqueda, text="Nuevo", command=limpiar, bg="#6b7280", fg="white", font=("Segoe UI", 10), relief="flat", padx=15, pady=8, cursor="hand2").pack(side=tk.LEFT, padx=2)
    tk.Button(actions, text="✓ Guardar", command=guardar, bg="#10b981", fg="white", font=("Segoe UI", 11, "bold"), relief="flat", padx=25, pady=10, cursor="hand2", width=20).pack(side=tk.LEFT, padx=40)
    tk.Button(actions, text="Cancelar", command=win.destroy, bg="#6b7280", fg="white", font=("Segoe UI", 10), relief="flat", padx=15, pady=10, cursor="hand2", width=15).pack(side=tk.RIGHT, padx=40)

    cargar_categorias_memoria()
    if id_producto_a_cargar: var_token.set(str(id_producto_a_cargar)); buscar()
    else: al_cambiar_categoria(None)
    configurar_navegacion_ventana(win, confirmar_cierre=True)
    win.grab_set()