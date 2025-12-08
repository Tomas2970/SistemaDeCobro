# app/frontend/interfaz_productos.py
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

# 🔥 AHORA ACEPTA callback_on_save
def ui_productos(parent: tk.Misc, backend, usuario: dict, id_producto_a_cargar: int | None = None, callback_on_save=None) -> None:
    
    win = tk.Toplevel(parent)
    win.title("Gestión de Productos")
    win.geometry("650x700") 
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # --- Validadores ---
    def validar_len_30(t): return len(t) <= 30
    def validar_len_60(t): return len(t) <= 60
    
    # Validar que stock sea numero decimal positivo (permite borrar todo)
    def validar_stock(t):
        if t == "": return True
        if len(t) > 10: return False
        return re.match(r'^[0-9]*\.?[0-9]*$', t) is not None

    vc_30 = (win.register(validar_len_30), '%P')
    vc_60 = (win.register(validar_len_60), '%P')
    vc_stock = (win.register(validar_stock), '%P')

    # --- Header Búsqueda ---
    frm_busqueda = tk.Frame(win, bg="#f4f4f8")
    frm_busqueda.pack(fill=tk.X, padx=20, pady=15) 
    tk.Label(frm_busqueda, text="Buscar (ID/Cód/Nom):", bg="#f4f4f8").pack(side=tk.LEFT)
    var_token = tk.StringVar()
    ent_busqueda = tk.Entry(frm_busqueda, textvariable=var_token, width=25, validate="key", validatecommand=vc_30)
    ent_busqueda.pack(side=tk.LEFT, padx=5)
    
    # 🔥 BOTÓN BUSCAR
    tk.Button(
        frm_busqueda, 
        text="🔍 Buscar", 
        command=buscar,
        bg="#3b82f6", # AZUL_BUSCAR
        fg="white",
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        padx=15,
        pady=8,
        cursor="hand2",
        activebackground="#2563eb"
    ).pack(side=tk.LEFT, padx=2)

    # 🔥 BOTÓN NUEVO
    tk.Button(
        frm_busqueda, 
        text="Nuevo", 
        command=limpiar,
        bg="#6b7280", # GRIS_SECUNDARIO
        fg="white",
        font=("Segoe UI", 10),
        relief="flat",
        padx=15,
        pady=8,
        cursor="hand2",
        activebackground="#4b5563"
    ).pack(side=tk.LEFT, padx=2)

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
    
    # Lógica Categoría
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
    
    # Alineación derecha
    var_stock = tk.StringVar(value="0")
    ent_stock = tk.Entry(body, textvariable=var_stock, width=15, justify="right", validate="key", validatecommand=vc_stock) 
    add_row("Stock Actual:", ent_stock)
    
    var_stock_min = tk.StringVar(value="5")
    ent_stock_min = EntryNumerico(body, textvariable=var_stock_min, width=15, justify="right")
    add_row("Stock Mínimo:", ent_stock_min)

    var_asignar_prov = tk.BooleanVar(value=False)
    chk_asignar = tk.Checkbutton(body, text="Asignar a proveedores al guardar", 
                                 variable=var_asignar_prov, bg="#f4f4f8", font=("Segoe UI", 9, "bold"))
    chk_asignar.grid(row=row, column=1, sticky="w", padx=5, pady=10)
    row += 1

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
                # Muestra DNI/CUIT para distinguir proveedores con el mismo nombre
                dni_cuit = p.get('dni_cuit') or "-"
                texto = f"{p['id_proveedor']} - {p['nombre']} (DNI: {dni_cuit})"
                if query in texto.lower(): lb.insert(tk.END, texto)
        var_filtro.trace_add("write", filtrar_lista)
        filtrar_lista() 
            
        def guardar_asignaciones():
            sels = lb.curselection()
            count = 0
            for idx in sels:
                p_text = lb.get(idx)
                p_id = int(p_text.split(" - ")[0])
                if backend.asignar_producto_a_proveedor(p_id, pid): count += 1
            messagebox.showinfo("Listo", f"Asignado a {count} proveedores.", parent=pop)
            pop.destroy()

        tk.Button(pop, text="Guardar Asignación", bg="#4CAF50", fg="white", command=guardar_asignaciones).pack(pady=10)
        ent_filtro.focus_set()
        pop.transient(win); pop.grab_set(); win.wait_window(pop)

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
            
            # --- Popup Asignación o Mensaje Éxito ---
            if producto_guardado_id and var_asignar_prov.get():
                abrir_popup_asignacion(producto_guardado_id, nombre)
            else:
                messagebox.showinfo("Éxito", msg, parent=win)
            
            # --- EJECUTAR CALLBACK DE ACTUALIZACIÓN ---
            if callback_on_save:
                try: callback_on_save()
                except: pass

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {e}", parent=win)

    def limpiar():
        var_id.set(""); var_nombre.set(""); var_precio.set("0.00")
        var_stock.set("0"); var_stock_min.set("5"); var_cod.set("")
        var_es_pesable.set(False) 
        chk_pesable.config(state="normal", text="Es pesable (kg)") 
        var_asignar_prov.set(False); combo_cat.set(''); ent_nombre.focus_set()

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
            
            # 🔥 Lógica Formato Stock Inteligente
            stock_val = float(prod.get('stock'))
            es_pesable = bool(prod.get('es_pesable'))
            
            if not es_pesable and stock_val.is_integer():
                var_stock.set(f"{int(stock_val)}") # Muestra "10"
            else:
                var_stock.set(f"{stock_val:.3f}") # Muestra "10.000"
            
            var_stock_min.set(str(prod.get('stock_minimo')))
            var_cod.set(prod.get('codigo_barras') or "")
            var_es_pesable.set(es_pesable)
            c_name = prod.get('categoria') or prod.get('nombre_categoria')
            if c_name and c_name in combo_cat['values']:
                combo_cat.set(c_name)
                al_cambiar_categoria(None) 
        else:
            messagebox.showinfo("Info", "No se encontró el producto.", parent=win)

    def eliminar_producto():
        """Borrado lógico de producto (Desactivar)"""
        if not usuario.get('id_rol') in [1, 3]: # Solo Admin/Supervisor
             return messagebox.showwarning("Acceso", "Solo Admin/Supervisor puede eliminar productos.", parent=win)
        
        pid_str = var_id.get()
        if not pid_str: return
        
        if messagebox.askyesno("Confirmar Eliminación", "¿Desactivar este producto?."):
            try:
                if backend.eliminar_producto(int(pid_str), id_usuario=usuario.get('id_usuario')):
                    messagebox.showinfo("Éxito", "Producto desactivado.")
                    limpiar()
                    if callback_on_save: callback_on_save()
                else:
                    messagebox.showerror("Error", "No se pudo desactivar.", parent=win)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)


    # tk.Button(frm_busqueda, text="🔎 Buscar", command=buscar).pack(side=tk.LEFT, padx=2) # Movido arriba
    # tk.Button(frm_busqueda, text="Nuevo", command=limpiar).pack(side=tk.LEFT, padx=2) # Movido arriba
    
    # 🔥 BOTÓN GUARDAR
    tk.Button(
        actions, 
        text="✓ Guardar", 
        command=guardar,
        bg="#10b981", # VERDE_CONFIRMAR
        fg="white", 
        font=("Segoe UI", 11, "bold"),
        relief="flat",
        padx=25,
        pady=10,
        cursor="hand2",
        activebackground="#059669",
        width=20
    ).pack(side=tk.LEFT, padx=40)
    
    # 🔥 BOTÓN DESACTIVAR
    tk.Button(
        actions, 
        text="× Desactivar", 
        command=eliminar_producto,
        bg="#ef4444", # ROJO_CANCELAR
        fg="white", 
        font=("Segoe UI", 10),
        relief="flat",
        padx=20,
        pady=10,
        cursor="hand2",
        activebackground="#dc2626",
        width=15
    ).pack(side=tk.LEFT, padx=5)
    
    # 🔥 BOTÓN CANCELAR
    tk.Button(
        actions, 
        text="Cancelar", 
        command=win.destroy,
        bg="#6b7280", # GRIS_SECUNDARIO
        fg="white", 
        font=("Segoe UI", 10),
        relief="flat",
        padx=15,
        pady=10,
        cursor="hand2",
        activebackground="#4b5563",
        width=15
    ).pack(side=tk.RIGHT, padx=40)

    cargar_categorias_memoria()
    if combo_cat['values']: combo_cat.current(0)
    if id_producto_a_cargar:
        var_token.set(str(id_producto_a_cargar)); buscar()
    else:
        al_cambiar_categoria(None)

    configurar_navegacion_ventana(win, confirmar_cierre=True)
    win.after(50, lambda: ent_busqueda.focus_set())
    win.grab_set()