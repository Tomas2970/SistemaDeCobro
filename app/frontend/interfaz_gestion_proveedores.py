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
    win.title("Gestión de Empresas Proveedoras")
    win.geometry("1150x650") 
    win.config(bg="#f4f4f8")
    win.resizable(False, False)
    
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
    style.map("Modern.Treeview.Heading", background=[('active', '#e5e7eb')])

    # --- BARRA DE BÚSQUEDA ---
    frame_busqueda = tk.Frame(win, bg="#f4f4f8")
    frame_busqueda.pack(pady=(15,0), padx=20, fill="x")
    
    tk.Label(frame_busqueda, text="🔍", bg="#f4f4f8", font=("Segoe UI", 14)).pack(side=tk.LEFT)
    tk.Label(frame_busqueda, text="Buscar Empresa/CUIT:", bg="#f4f4f8", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(5,10))
    var_busqueda = tk.StringVar()
    entry_busqueda = tk.Entry(frame_busqueda, textvariable=var_busqueda, width=35, font=("Segoe UI", 10))
    entry_busqueda.pack(side=tk.LEFT)

    frame_lista = tk.Frame(win, bg="#f4f4f8")
    frame_lista.pack(pady=10, padx=20, fill="both", expand=True)

    # 🔥 COLUMNAS FILTRADAS: Solo datos de Empresa
    cols = ["ID", "Empresa", "CUIT", "Teléfono", "Email", "Dirección", "Saldo (Deuda)", "Activo"]
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", height=15, style="Modern.Treeview")
    tree.pack(side="left", fill="both", expand=True)
    
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    ys.pack(side="right", fill="y")
    tree.configure(yscrollcommand=ys.set)
    
    for c in cols: tree.heading(c, text=c)
    
    tree.column("ID", width=0, minwidth=0, stretch=False)
    tree.column("Empresa", width=220) 
    tree.column("CUIT", width=130, anchor="center")
    tree.column("Teléfono", width=110)
    tree.column("Email", width=190)
    tree.column("Dirección", width=220)
    tree.column("Saldo (Deuda)", width=120, anchor="e")
    tree.column("Activo", width=80, anchor="center")
    
    tree.tag_configure("deuda", foreground="#dc2626")
    tree.tag_configure("favor", foreground="#16a34a")
    tree.tag_configure("cero", foreground="black")

    var_mostrar_inactivos = tk.BooleanVar(value=False)
    todos_proveedores = []

    def cargar_datos():
        nonlocal todos_proveedores
        try:
            incluir_inactivos = var_mostrar_inactivos.get()
            todos_proveedores = backend.obtener_proveedores(incluir_inactivos=incluir_inactivos)
            todos_proveedores.sort(key=lambda x: float(x.get('saldo', 0.0)))
            filtrar_lista()
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando: {e}", parent=win)
            
    def filtrar_lista(*args):
        query = var_busqueda.get().lower().strip()
        for i in tree.get_children(): tree.delete(i)
        
        for p in todos_proveedores:
            empresa = str(p.get('empresa', '')).lower()
            cuit = str(p.get('cuit', '')).lower()
            
            if query in empresa or query in cuit:
                estado = "SI" if p.get('activo') else "NO"
                saldo = float(p.get('saldo', 0.0))
                
                tag = "cero"
                if saldo < -0.01: tag = "deuda"
                elif saldo > 0.01: tag = "favor"
                
                saldo_vis = f"- $ {abs(saldo):,.2f}" if saldo < 0 else f"+ $ {saldo:,.2f}"
                if abs(saldo) < 0.01: saldo_vis = "$ 0.00"

                tree.insert("", tk.END, values=[
                    p.get('id_proveedor', ''), 
                    p.get('empresa', ''),
                    p.get('cuit', '-'),
                    p.get('telefono', ''), 
                    p.get('email', ''), 
                    p.get('direccion', '-'),
                    saldo_vis, 
                    estado
                ], tags=(tag,))

    var_busqueda.trace_add("write", filtrar_lista)

    def recargar_lista_callback():
        win.after(100, cargar_datos)

    def accion_nuevo():
        ui_crear_proveedor(win, backend, callback_on_save=recargar_lista_callback)

    def abrir_editar_proveedor():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una empresa.", parent=win)
            return
        item = tree.item(sel[0], "values")
        ui_crear_proveedor(win, backend, id_proveedor_a_editar=int(item[0]), callback_on_save=recargar_lista_callback)
    
    tree.bind("<Double-1>", lambda e: abrir_editar_proveedor())
    
    def abrir_pagar_deuda():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una empresa.", parent=win)
            return
        item_vals = tree.item(sel[0], "values")
        id_prov = int(item_vals[0])
        nombre_empresa = item_vals[1]
        
        pop = Toplevel(win)
        pop.title(f"Registrar Pago a {nombre_empresa}")
        pop.geometry("400x350")
        pop.config(bg="#f4f4f8") 
        pop.transient(win)
        pop.grab_set()
        
        tk.Label(pop, text=f"Empresa: {nombre_empresa}", font=("Segoe UI", 12, "bold"), bg="#f4f4f8").pack(pady=10)
        tk.Label(pop, text="Monto a abonar ($):", bg="#f4f4f8").pack(pady=5)
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
            except ValueError as ve:
                if "CAJA_CERRADA" in str(ve):
                    messagebox.showerror(
                        "⚠️ Caja Cerrada", 
                        "No se puede procesar el pago porque la caja está cerrada.\n\n"
                        "Por favor, abra la caja antes de continuar.", 
                        parent=pop
                    )
                else:
                    messagebox.showerror("Error", str(ve), parent=pop)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=pop)
                
        tk.Button(pop, text="CONFIRMAR PAGO", command=confirmar_pago, bg="#16a34a", fg="white", 
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8, cursor="hand2").pack(pady=20)
        configurar_navegacion_ventana(pop)

    def abrir_asignar_productos():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una empresa.", parent=win)
            return
        item = tree.item(sel[0], "values")
        if ui_asignar_productos:
            ui_asignar_productos(win, backend, int(item[0]), str(item[1]))

    def desactivar_proveedor():
        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        if messagebox.askyesno("Confirmar", f"¿Desactivar la empresa '{item[1]}'?", parent=win):
            try:
                if backend.eliminar_proveedor_logico(int(item[0])):
                    cargar_datos()
            except Exception as e:
                messagebox.showerror("Error", f"{e}", parent=win)

    def activar_proveedor():
        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        if messagebox.askyesno("Confirmar", f"¿Activar la empresa '{item[1]}'?", parent=win):
            try:
                if backend.activar_proveedor_logico(int(item[0])):
                    cargar_datos()
            except Exception as e:
                messagebox.showerror("Error", f"{e}", parent=win)

    # --- FRAME DE BOTONES ---
    frame_botones = tk.Frame(win, bg="#f4f4f8")
    frame_botones.pack(pady=15, fill="x", padx=20)

    frame_acciones = tk.Frame(frame_botones, bg="#f4f4f8")
    frame_acciones.pack(side=tk.LEFT)

    tk.Button(frame_acciones, text="➕ Nueva Empresa", command=accion_nuevo, 
              bg="#16a34a", fg="white", font=("Segoe UI", 10, "bold"), 
              relief="flat", padx=15, pady=8, cursor="hand2").pack(side=tk.LEFT, padx=5)
    
    tk.Button(frame_acciones, text="💳 PAGAR", command=abrir_pagar_deuda, 
              bg="#0ea5e9", fg="white", font=("Segoe UI", 9, "bold"), 
              relief="flat", padx=12, pady=7, cursor="hand2").pack(side=tk.LEFT, padx=5)
    
    tk.Button(frame_acciones, text="📦 Productos", command=abrir_asignar_productos, 
              bg="#7c3aed", fg="white", font=("Segoe UI", 9), 
              relief="flat", padx=12, pady=7, cursor="hand2").pack(side=tk.LEFT, padx=5)
    
    tk.Button(frame_acciones, text="🗑️ Desactivar", command=desactivar_proveedor, 
              bg="#dc2626", fg="white", font=("Segoe UI", 9), 
              relief="flat", padx=12, pady=7, cursor="hand2").pack(side=tk.LEFT, padx=5)

    btn_activar = tk.Button(frame_acciones, text="✅ Activar", command=activar_proveedor, 
                            bg="#059669", fg="white", font=("Segoe UI", 9), 
                            relief="flat", padx=12, pady=7, cursor="hand2")

    def toggle_mostrar_inactivos():
        cargar_datos()
        if var_mostrar_inactivos.get(): btn_activar.pack(side=tk.LEFT, padx=5)
        else: btn_activar.pack_forget()

    tk.Checkbutton(frame_botones, text="Ver Inactivas", variable=var_mostrar_inactivos, 
                   bg="#f4f4f8", font=("Segoe UI", 9), command=toggle_mostrar_inactivos).pack(side=tk.LEFT, padx=30)

    tk.Button(frame_botones, text="Cerrar", command=win.destroy, bg="#64748b", fg="white", 
              font=("Segoe UI", 9), relief="flat", padx=15, pady=7, cursor="hand2").pack(side=tk.RIGHT)

    cargar_datos()
    entry_busqueda.focus_set()
    configurar_navegacion_ventana(win)
    win.grab_set()
    win.transient(parent)