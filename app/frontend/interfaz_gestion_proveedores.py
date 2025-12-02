# app/frontend/interfaz_gestion_proveedores.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from app.frontend.interfaz_crear_proveedor import ui_crear_proveedor

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
    from app.frontend.componentes_ui import EntryDecimal
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass
    class EntryDecimal(tk.Entry): pass

try:
    from app.frontend.interfaz_asignar_productos import ui_asignar_productos
except ImportError:
    ui_asignar_productos = None

def _fmt_mon(val):
    try: return f"$ {float(val):,.2f}"
    except: return "$ 0.00"

def ui_gestion_proveedores(parent: tk.Misc, backend, usuario_actual: dict = None): 
    
    win = tk.Toplevel(parent)
    win.title("Gestión de Proveedores")
    win.geometry("1050x650") 
    win.config(bg="#f4f4f8")
    win.resizable(False, False)
    
    # --- BARRA DE BÚSQUEDA ---
    frame_busqueda = tk.Frame(win, bg="#f4f4f8")
    frame_busqueda.pack(pady=(15,0), padx=20, fill="x")
    
    tk.Label(frame_busqueda, text="🔍 Buscar (Nombre/Empresa):", bg="#f4f4f8", font=("Segoe UI", 10)).pack(side=tk.LEFT)
    var_busqueda = tk.StringVar()
    entry_busqueda = tk.Entry(frame_busqueda, textvariable=var_busqueda, width=35)
    entry_busqueda.pack(side=tk.LEFT, padx=10)
    
    # -------------------------

    frame_lista = tk.Frame(win, bg="#f4f4f8")
    frame_lista.pack(pady=10, padx=20, fill="both", expand=True)

    cols = ["ID", "Nombre", "Empresa", "Teléfono", "Email", "Saldo (Deuda)", "Activo"]
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", height=15)
    tree.pack(side="left", fill="both", expand=True)
    
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    ys.pack(side="right", fill="y")
    tree.configure(yscrollcommand=ys.set)
    
    for c in cols: tree.heading(c, text=c)
    
    tree.column("ID", width=50, anchor="center")
    tree.column("Nombre", width=180)
    tree.column("Empresa", width=150)
    tree.column("Teléfono", width=100)
    tree.column("Email", width=150)
    tree.column("Saldo (Deuda)", width=120, anchor="e") 
    tree.column("Activo", width=60, anchor="center")
    
    tree.tag_configure("deuda", foreground="#dc2626")
    tree.tag_configure("favor", foreground="#16a34a")
    tree.tag_configure("cero", foreground="black")

    var_mostrar_inactivos = tk.BooleanVar(value=False)

    # Cache de proveedores para filtrar sin ir a BD cada vez
    todos_proveedores = []

    def cargar_datos():
        nonlocal todos_proveedores
        try:
            incluir_inactivos = var_mostrar_inactivos.get()
            todos_proveedores = backend.obtener_proveedores(incluir_inactivos=incluir_inactivos)
            todos_proveedores.sort(key=lambda x: float(x.get('saldo', 0.0)))
            filtrar_lista() # Aplicar filtro actual
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando: {e}", parent=win)

    def filtrar_lista(*args):
        query = var_busqueda.get().lower().strip()
        for i in tree.get_children(): tree.delete(i)
        
        for p in todos_proveedores:
            nombre = str(p.get('nombre', '')).lower()
            empresa = str(p.get('empresa', '')).lower()
            
            # Filtro simple
            if query in nombre or query in empresa:
                
                estado = "SI" if p.get('activo') else "NO"
                saldo = float(p.get('saldo', 0.0))
                
                tag = "cero"
                if saldo < -0.01: tag = "deuda"
                elif saldo > 0.01: tag = "favor"
                
                saldo_vis = f"- $ {abs(saldo):,.2f}" if saldo < 0 else f"+ $ {saldo:,.2f}"
                if abs(saldo) < 0.01: saldo_vis = "$ 0.00"

                tree.insert("", tk.END, values=[
                    p.get('id_proveedor', ''), 
                    p.get('nombre', ''), 
                    p.get('empresa', ''),
                    p.get('telefono', ''), 
                    p.get('email', ''), 
                    saldo_vis, 
                    estado
                ], tags=(tag,))

    var_busqueda.trace_add("write", filtrar_lista)

    frame_botones = tk.Frame(win, bg="#f4f4f8")
    frame_botones.pack(pady=15, fill="x")

    def accion_nuevo():
        ui_crear_proveedor(win, backend)
        win.after(100, cargar_datos)

    def abrir_editar_proveedor():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un proveedor.", parent=win)
            return
        item = tree.item(sel[0], "values")
        ui_crear_proveedor(win, backend, id_proveedor_a_editar=int(item[0]))
        cargar_datos()
    
    def on_doble_click(event):
        abrir_editar_proveedor()

    tree.bind("<Double-1>", on_doble_click)
    
    def abrir_pagar_deuda():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un proveedor.", parent=win)
            return
        item_vals = tree.item(sel[0], "values")
        id_prov = int(item_vals[0])
        nombre_prov = item_vals[1]
        
        pop = Toplevel(win)
        pop.title(f"Registrar Pago a {nombre_prov}")
        pop.geometry("400x350")
        pop.config(bg="#f4f4f8")
        pop.transient(win)
        pop.grab_set()
        
        tk.Label(pop, text=f"Pagar a: {nombre_prov}", font=("bold", 12), bg="#f4f4f8").pack(pady=10)
        
        tk.Label(pop, text="Monto ($):", bg="#f4f4f8").pack(pady=5)
        ent_monto = EntryDecimal(pop, font=("Segoe UI", 12), width=15, justify="center")
        ent_monto.pack()
        ent_monto.focus_set()
        
        tk.Label(pop, text="Medio de Pago:", bg="#f4f4f8").pack(pady=5)
        cb_medio = ttk.Combobox(pop, values=["efectivo", "transferencia", "cheque"], state="readonly", width=18)
        cb_medio.current(0)
        cb_medio.pack()
        
        tk.Label(pop, text="Observación:", bg="#f4f4f8").pack(pady=5)
        ent_obs = tk.Entry(pop, width=30)
        ent_obs.pack()
        
        def confirmar_pago():
            try:
                monto = float(ent_monto.get())
                if monto <= 0: raise ValueError("Monto debe ser positivo")
                uid = usuario_actual['id_usuario'] if usuario_actual else 1
                
                backend.registrar_pago_proveedor(id_prov, monto, cb_medio.get(), uid, ent_obs.get())
                
                messagebox.showinfo("Éxito", "Pago registrado.", parent=pop)
                pop.destroy()
                cargar_datos()
            except ValueError as ve: messagebox.showwarning("Error", str(ve), parent=pop)
            except Exception as e: messagebox.showerror("Error Crítico", str(e), parent=pop)

        tk.Button(pop, text="CONFIRMAR PAGO", command=confirmar_pago, bg="#16a34a", fg="white").pack(pady=20)
        configurar_navegacion_ventana(pop)

    def abrir_asignar_productos():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un proveedor.", parent=win)
            return
        if not ui_asignar_productos:
            messagebox.showerror("Error", "Módulo no encontrado.", parent=win)
            return
        item = tree.item(sel[0], "values")
        ui_asignar_productos(win, backend, int(item[0]), str(item[1]))

    def desactivar_proveedor():
        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        if messagebox.askyesno("Confirmar", f"¿Desactivar a '{item[1]}'?", parent=win):
            try:
                if backend.eliminar_proveedor_logico(int(item[0])):
                    messagebox.showinfo("Éxito", "Desactivado.", parent=win)
                    cargar_datos()
            except Exception as e:
                messagebox.showerror("Error", f"{e}", parent=win)

    tk.Button(frame_botones, text="+ Nuevo", command=accion_nuevo, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=10)
    tk.Button(frame_botones, text="✎ Editar", command=abrir_editar_proveedor, bg="#FFC107").pack(side=tk.LEFT, padx=5)
    tk.Button(frame_botones, text="💲 PAGAR DEUDA", command=abrir_pagar_deuda, bg="#0ea5e9", fg="white", font=("bold", 9)).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_botones, text="📦 Productos", command=abrir_asignar_productos, bg="#7c3aed", fg="white").pack(side=tk.LEFT, padx=5)
    
    tk.Checkbutton(frame_botones, text="Inactivos", variable=var_mostrar_inactivos, bg="#f4f4f8", command=cargar_datos).pack(side=tk.LEFT, padx=20)
    
    tk.Button(frame_botones, text="Cerrar", command=win.destroy, bg="#607D8B", fg="white").pack(side=tk.RIGHT, padx=10)
    tk.Button(frame_botones, text="Borrar", command=desactivar_proveedor, bg="#f44336", fg="white").pack(side=tk.RIGHT, padx=5)

    cargar_datos()
    entry_busqueda.focus_set()
    configurar_navegacion_ventana(win)
    win.grab_set()
    win.transient(parent)