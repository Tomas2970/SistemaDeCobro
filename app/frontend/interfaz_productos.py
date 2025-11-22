# app/frontend/interfaz_productos.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Listbox, MULTIPLE
from typing import Optional

# Importar navegación y componentes
try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

from app.frontend.componentes_ui import EntryDecimal, EntryNumerico
from app.frontend.stock_event_manager import stock_events

def ui_productos(parent: tk.Misc, backend, usuario: dict, id_producto_a_cargar: int | None = None) -> None:
    
    win = tk.Toplevel(parent)
    win.title("Gestión de Productos")
    win.geometry("600x580") # Un poco más alto para el botón de proveedores
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
    
    # --- CATEGORÍA Y PESABLE INTELIGENTE ---
    combo_cat = ttk.Combobox(body, state="readonly", width=43)
    add_row("Categoría:", combo_cat)
    
    var_precio = tk.StringVar(value="0.00")
    ent_precio = EntryDecimal(body, textvariable=var_precio, width=15)
    add_row("Precio Venta ($):", ent_precio)
    
    var_es_pesable = tk.BooleanVar(value=False)
    chk_pesable = tk.Checkbutton(body, text="Es pesable (kg/lt)", variable=var_es_pesable, bg="#f4f4f8")
    add_row("", chk_pesable)
    
    # Lógica para bloquear "Pesable"
    def al_cambiar_categoria(event):
        cat_actual = combo_cat.get().lower()
        # Lista de palabras clave que NO suelen ser pesables
        no_pesables = ["bebida", "limpieza", "golosina", "almacen", "cigarro"]
        
        # Si la categoría contiene alguna de esas palabras, desmarcamos y deshabilitamos
        if any(x in cat_actual for x in no_pesables):
            var_es_pesable.set(False)
            chk_pesable.config(state="disabled")
        else:
            # Si es Carnes, Verduras, etc., habilitamos
            chk_pesable.config(state="normal")

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

    # --- GESTIONAR PROVEEDORES DEL PRODUCTO ---
    def gestionar_proveedores():
        pid_str = var_id.get()
        if not pid_str:
            messagebox.showwarning("Atención", "Primero debe guardar el producto para asignarle proveedores.", parent=win)
            return
        
        pid = int(pid_str)
        prod_nom = var_nombre.get()
        
        pop = Toplevel(win)
        pop.title(f"Proveedores de: {prod_nom}")
        pop.geometry("400x400")
        
        tk.Label(pop, text="Seleccione los proveedores que venden este producto:", bg="#f4f4f8", wraplength=380).pack(pady=10)
        
        # Lista con checkbox simulado (Listbox multiple)
        lb = Listbox(pop, selectmode=MULTIPLE, height=15)
        lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        all_provs = backend.obtener_proveedores()
        # Obtener quienes YA lo venden (necesitas implementar esto en backend o usar lógica inversa)
        # Truco: Usamos obtener_productos_por_proveedor para cada proveedor (lento) o agregamos funcion nueva.
        # Para simplificar AHORA sin tocar DB.py de nuevo, asumimos que marcamos de cero o usamos lógica simple.
        # MEJOR: Vamos a asumir que están todos desmarcados y el usuario elige.
        # (Para hacerlo perfecto necesitaríamos `backend.obtener_proveedores_de_producto(pid)`)
        
        for p in all_provs:
            lb.insert(tk.END, f"{p['id_proveedor']} - {p['nombre']}")
            
        def guardar_asignaciones():
            sels = lb.curselection()
            if not sels:
                messagebox.showinfo("Info", "Ningún proveedor seleccionado.")
                return
            
            count = 0
            for idx in sels:
                p_text = lb.get(idx)
                p_id = int(p_text.split(" - ")[0])
                # Asignar (backend ignora si ya existe gracias a IGNORE)
                if backend.asignar_producto_a_proveedor(p_id, pid):
                    count += 1
            
            messagebox.showinfo("Listo", f"Producto asignado a {count} proveedores.", parent=pop)
            pop.destroy()

        tk.Button(pop, text="Guardar Asignación", bg="#673AB7", fg="white", command=guardar_asignaciones).pack(pady=10)
        configurar_navegacion_ventana(pop)

    # Botón Proveedores (Solo habilitado si hay ID)
    btn_provs = tk.Button(body, text="📦 Asignar a Proveedores", command=gestionar_proveedores, bg="#E1BEE7")
    # Lo ponemos en la fila siguiente
    btn_provs.grid(row=row, column=1, sticky="w", padx=5, pady=10)

    # --- Botones Acciones ---
    actions = tk.Frame(win, bg="#f4f4f8", pady=10)
    actions.pack(fill=tk.X) 
    
    def guardar():
        try:
            nombre = var_nombre.get().strip()
            precio = float(var_precio.get() or 0)
            stock = float(var_stock.get() or 0)
            minimo = int(var_stock_min.get() or 0)
            codigo = var_cod.get().strip() or None
            
            if not nombre:
                messagebox.showwarning("Error", "El nombre es obligatorio", parent=win)
                return

            idx = combo_cat.current()
            cat_id = combo_cat.ids[idx] if hasattr(combo_cat, 'ids') and idx >= 0 else None

            pid = int(var_id.get()) if var_id.get().isdigit() else None
            
            if pid:
                backend.actualizar_producto(pid, nombre=nombre, precio=precio, codigo_barras=codigo, 
                                         es_pesable=var_es_pesable.get(), id_categoria=cat_id, id_usuario=usuario.get('id_usuario'))
                backend.actualizar_inventario_absoluto(pid, stock, minimo, id_usuario=usuario.get('id_usuario'))
                messagebox.showinfo("Éxito", "Producto actualizado.", parent=win)
            else:
                new_id = backend.crear_producto_completo(nombre, cat_id, codigo, precio, stock, minimo, var_es_pesable.get(), id_usuario=usuario.get('id_usuario'))
                if new_id:
                    var_id.set(str(new_id)) # Seteamos el ID para habilitar botón proveedores
                    messagebox.showinfo("Éxito", "Producto creado. Ahora puede asignar proveedores.", parent=win)
            
            stock_events.notificar_cambio_stock()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {e}", parent=win)

    def limpiar():
        var_id.set("")
        var_nombre.set("")
        var_precio.set("0.00")
        var_stock.set("0")
        var_stock_min.set("5")
        var_cod.set("")
        var_es_pesable.set(False)
        chk_pesable.config(state="normal")
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
            var_es_pesable.set(bool(prod.get('es_pesable')))
            
            c_name = prod.get('categoria') or prod.get('nombre_categoria')
            if c_name and c_name in combo_cat['values']:
                combo_cat.set(c_name)
                al_cambiar_categoria(None) # Ejecutar lógica de pesable
        else:
            messagebox.showinfo("Info", "No se encontró el producto.", parent=win)

    tk.Button(frm_busqueda, text="🔎 Buscar", command=buscar).pack(side=tk.LEFT, padx=2)
    tk.Button(frm_busqueda, text="Nuevo", command=limpiar).pack(side=tk.LEFT, padx=2)

    tk.Button(actions, text="💾 Guardar", bg="#4CAF50", fg="white", width=20, command=guardar).pack(side=tk.LEFT, padx=40)
    tk.Button(actions, text="Cancelar", bg="#f44336", fg="white", width=15, command=win.destroy).pack(side=tk.RIGHT, padx=40)

    # Carga inicial
    cats = backend.obtener_categorias()
    combo_cat['values'] = [c['nombre'] for c in cats]
    combo_cat.ids = [c['id_categoria'] for c in cats]
    if cats: combo_cat.current(0)
    al_cambiar_categoria(None) # Init state
    
    if id_producto_a_cargar:
        var_token.set(str(id_producto_a_cargar))
        buscar()

    configurar_navegacion_ventana(win, confirmar_cierre=True)
    win.after(50, lambda: ent_busqueda.focus_set())
    win.grab_set()