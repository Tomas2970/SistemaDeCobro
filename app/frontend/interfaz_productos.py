# app/frontend/interfaz_productos.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Listbox, MULTIPLE
from typing import Optional

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

from app.frontend.componentes_ui import EntryDecimal, EntryNumerico
from app.frontend.stock_event_manager import stock_events

def ui_productos(parent: tk.Misc, backend, usuario: dict, id_producto_a_cargar: int | None = None) -> None:
    
    win = tk.Toplevel(parent)
    win.title("Gestión de Productos")
    win.geometry("650x700") # Un poco más alto por si acaso
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # --- Header Búsqueda ---
    frm_busqueda = tk.Frame(win, bg="#f4f4f8")
    frm_busqueda.pack(fill=tk.X, padx=20, pady=15) 
    tk.Label(frm_busqueda, text="Buscar (ID/Cód/Nom):", bg="#f4f4f8").pack(side=tk.LEFT)
    var_token = tk.StringVar()
    ent_busqueda = tk.Entry(frm_busqueda, textvariable=var_token, width=25)
    ent_busqueda.pack(side=tk.LEFT, padx=5)
    
    # --- Formulario ---
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
    ent_id = tk.Entry(body, textvariable=var_id, width=10, state="readonly", justify="center")
    add_row("ID:", ent_id)
    
    var_nombre = tk.StringVar()
    ent_nombre = tk.Entry(body, textvariable=var_nombre, width=45)
    add_row("Nombre:", ent_nombre)
    
    combo_cat = ttk.Combobox(body, state="readonly", width=43)
    add_row("Categoría:", combo_cat)
    
    var_precio = tk.StringVar(value="0.00")
    ent_precio = EntryDecimal(body, textvariable=var_precio, width=15)
    
    try:
        from app.database.permisos import tiene_permiso
        if not tiene_permiso(usuario, 'modificar_precios'):
            ent_precio.config(state='disabled')
    except ImportError: pass
    
    add_row("Precio Venta ($):", ent_precio)
    
    var_es_pesable = tk.BooleanVar(value=False)
    # Definimos el widget explícitamente para poder acceder a él luego
    chk_pesable = tk.Checkbutton(body, text="Es pesable (kg) [Automático por Categoría]", variable=var_es_pesable, bg="#f4f4f8", fg="#555")
    add_row("", chk_pesable)
    
    # --- LOGICA INTELIGENTE DE CATEGORÍA ---
    categorias_data = []
    cat_map = {}
    
    def cargar_categorias_memoria():
        nonlocal categorias_data, cat_map
        categorias_data = backend.obtener_categorias()
        cat_map = {c['nombre']: c for c in categorias_data}
        
        combo_cat['values'] = [c['nombre'] for c in categorias_data]
        combo_cat.ids = [c['id_categoria'] for c in categorias_data]

    # 🔥 CORRECCIÓN FUNDAMENTAL AQUÍ:
    def al_cambiar_categoria(event=None):
        # Esta función se ejecuta al elegir del combo O manualmente al cargar
        nombre_cat = combo_cat.get()
        datos_cat = cat_map.get(nombre_cat)
        
        if datos_cat:
            # 1. Obtenemos qué dice la categoría (si es pesable o no)
            es_pesable_default = bool(datos_cat.get('es_pesable_default', False))
            
            # 2. Seteamos el valor del checkbox
            var_es_pesable.set(es_pesable_default)

            # 3. 🔥 HABILITAMOS O DESHABILITAMOS EL WIDGET
            if es_pesable_default:
                # Si la categoría dice que SI es pesable, lo dejamos habilitado (normal)
                # por si el usuario quiere desmarcarlo en una excepción.
                chk_pesable.config(state="normal", text="Es pesable (kg)")
            else:
                # Si la categoría dice que NO es pesable (ej: Bebidas),
                # lo DESHABILITAMOS para que no pueda marcarlo.
                chk_pesable.config(state="disabled", text="Es pesable (kg) [Bloqueado por Categoría]")
        else:
            # Si no hay categoría seleccionada, reseteamos
            chk_pesable.config(state="normal", text="Es pesable (kg)")


    combo_cat.bind("<<ComboboxSelected>>", al_cambiar_categoria)

    var_cod = tk.StringVar()
    ent_cod = tk.Entry(body, textvariable=var_cod, width=45)
    add_row("Código Barras:", ent_cod)
    
    var_stock = tk.StringVar(value="0")
    ent_stock = EntryDecimal(body, textvariable=var_stock, width=15)
    add_row("Stock Actual:", ent_stock)
    
    var_stock_min = tk.StringVar(value="10")
    ent_stock_min = EntryNumerico(body, textvariable=var_stock_min, width=15)
    add_row("Stock Mínimo:", ent_stock_min)

    var_asignar_prov = tk.BooleanVar(value=False)
    chk_asignar = tk.Checkbutton(body, text="Asignar a proveedores al guardar", 
                                 variable=var_asignar_prov, bg="#f4f4f8", font=("Segoe UI", 9, "bold"))
    chk_asignar.grid(row=row, column=1, sticky="w", padx=5, pady=10)
    row += 1

    # (La función abrir_popup_asignacion sigue igual...)
    def abrir_popup_asignacion(pid, nombre_prod):
        pop = Toplevel(win)
        pop.title(f"Proveedores para: {nombre_prod}")
        pop.geometry("450x450")
        
        tk.Label(pop, text="Buscar Proveedor:", bg="#f4f4f8").pack(pady=(10,0))
        var_filtro = tk.StringVar()
        ent_filtro = tk.Entry(pop, textvariable=var_filtro)
        ent_filtro.pack(fill=tk.X, padx=10, pady=5)
        
        lb = Listbox(pop, selectmode=MULTIPLE, height=15)
        lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        all_provs = backend.obtener_proveedores()
        
        def filtrar_lista(*args):
            query = var_filtro.get().lower()
            lb.delete(0, tk.END)
            for p in all_provs:
                if not p['activo']: continue
                texto = f"{p['id_proveedor']} - {p['nombre']}"
                if query in texto.lower():
                    lb.insert(tk.END, texto)
        
        var_filtro.trace_add("write", filtrar_lista)
        filtrar_lista() 
            
        def guardar_asignaciones():
            sels = lb.curselection()
            count = 0
            for idx in sels:
                p_text = lb.get(idx)
                p_id = int(p_text.split(" - ")[0])
                if backend.asignar_producto_a_proveedor(p_id, pid):
                    count += 1
            
            messagebox.showinfo("Listo", f"Asignado a {count} proveedores.", parent=pop)
            pop.destroy()

        tk.Button(pop, text="Guardar Asignación", bg="#4CAF50", fg="white", command=guardar_asignaciones).pack(pady=10)
        ent_filtro.focus_set()
        pop.transient(win)
        pop.grab_set()
        win.wait_window(pop)

    actions = tk.Frame(win, bg="#f4f4f8", pady=10)
    actions.pack(fill=tk.X) 
    
    def guardar():
        try:
            nombre = var_nombre.get().strip()
            try: precio = float(var_precio.get() or 0)
            except: precio = 0.0
            try: stock = float(var_stock.get() or 0)
            except: stock = 0.0
            try: minimo = int(var_stock_min.get() or 0)
            except: minimo = 0
            
            codigo = var_cod.get().strip() or None
            
            if not nombre:
                messagebox.showwarning("Error", "El nombre es obligatorio", parent=win)
                return

            idx = combo_cat.current()
            cat_id = combo_cat.ids[idx] if hasattr(combo_cat, 'ids') and idx >= 0 else None

            pid_str = var_id.get()
            pid = int(pid_str) if pid_str.isdigit() else None
            
            producto_guardado_id = None

            # IMPORTANTE: Usamos var_es_pesable.get(). 
            # Si el checkbox estaba deshabilitado en FALSE, esto enviará FALSE.
            
            if pid:
                backend.actualizar_producto(pid, nombre=nombre, precio=precio, codigo_barras=codigo, 
                                         es_pesable=var_es_pesable.get(), id_categoria=cat_id, id_usuario=usuario.get('id_usuario'))
                backend.actualizar_inventario_absoluto(pid, stock, minimo, id_usuario=usuario.get('id_usuario'))
                producto_guardado_id = pid
                msg = "Producto actualizado."
            else:
                new_id = backend.crear_producto_completo(nombre, cat_id, codigo, precio, stock, minimo, var_es_pesable.get(), id_usuario=usuario.get('id_usuario'))
                if new_id:
                    producto_guardado_id = new_id
                    var_id.set(str(new_id))
                    msg = "Producto creado."
            
            stock_events.notificar_cambio_stock()
            
            if producto_guardado_id and var_asignar_prov.get():
                abrir_popup_asignacion(producto_guardado_id, nombre)
            else:
                messagebox.showinfo("Éxito", msg, parent=win)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {e}", parent=win)

    def limpiar():
        var_id.set("")
        var_nombre.set("")
        var_precio.set("0.00")
        var_stock.set("0")
        var_stock_min.set("5")
        var_cod.set("")
        
        # 🔥 CORRECCIÓN EN LIMPIAR:
        var_es_pesable.set(False) 
        chk_pesable.config(state="normal", text="Es pesable (kg)") # Reseteamos estado
        
        var_asignar_prov.set(False)
        combo_cat.set('')
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
            var_stock.set(f"{float(prod.get('stock')): .3f}")
            var_stock_min.set(str(prod.get('stock_minimo')))
            var_cod.set(prod.get('codigo_barras') or "")
            
            # Setear el valor actual de la base de datos
            var_es_pesable.set(bool(prod.get('es_pesable')))
            
            c_name = prod.get('categoria') or prod.get('nombre_categoria')
            if c_name and c_name in combo_cat['values']:
                combo_cat.set(c_name)
                # 🔥 CORRECCIÓN EN BUSCAR:
                # Forzamos la ejecución de la lógica para bloquear/desbloquear
                # el checkbox según la categoría que acabamos de cargar.
                al_cambiar_categoria(None) 
        else:
            messagebox.showinfo("Info", "No se encontró el producto.", parent=win)

    tk.Button(frm_busqueda, text="🔎 Buscar", command=buscar).pack(side=tk.LEFT, padx=2)
    tk.Button(frm_busqueda, text="Nuevo", command=limpiar).pack(side=tk.LEFT, padx=2)

    tk.Button(actions, text="💾 Guardar", bg="#4CAF50", fg="white", width=20, command=guardar).pack(side=tk.LEFT, padx=40)
    tk.Button(actions, text="Cancelar", bg="#f44336", fg="white", width=15, command=win.destroy).pack(side=tk.RIGHT, padx=40)

    cargar_categorias_memoria()
    if combo_cat['values']: combo_cat.current(0)
    
    # Si cargamos un producto al iniciar, aplicar la lógica también
    if id_producto_a_cargar:
        var_token.set(str(id_producto_a_cargar))
        buscar()
    else:
        # Si es nuevo, aplicar lógica de la primera categoría por defecto
        al_cambiar_categoria(None)


    configurar_navegacion_ventana(win, confirmar_cierre=True)
    win.after(50, lambda: ent_busqueda.focus_set())
    win.grab_set()