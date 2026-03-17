# app/frontend/interfaz_gestion_clientes.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from app.frontend.interfaz_crear_cliente import ui_crear_cliente

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

def _fmt_mon(val):
    try: return f"$ {float(val):,.2f}"
    except: return "$ 0.00"

def ui_gestion_clientes(parent: tk.Misc, backend, usuario_actual: dict = None):
    win = tk.Toplevel(parent)
    win.title("Gestión de Clientes")
    win.geometry("1150x600") # 🔥 Ancho ajustado al quitar la columna
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except:
        pass

    style.configure(
        "Modern.Treeview",
        background="#ffffff",
        foreground="#1f2937",
        rowheight=28,
        fieldbackground="#ffffff",
        borderwidth=0,
        font=("Segoe UI", 10)
    )

    style.configure(
        "Modern.Treeview.Heading",
        background="#f3f4f6",
        foreground="#374151",
        font=("Segoe UI", 10, "bold"),
        relief="flat"
    )

    style.map("Modern.Treeview.Heading", background=[("active", "#e5e7eb")])

    # --- BARRA DE BÚSQUEDA ---
    frame_busqueda = tk.Frame(win, bg="#f4f4f8")
    frame_busqueda.pack(pady=(15,0), padx=20, fill="x")
    
    tk.Label(frame_busqueda, text="🔍", bg="#f4f4f8", font=("Segoe UI", 14)).pack(side=tk.LEFT)
    tk.Label(frame_busqueda, text="Buscar:", bg="#f4f4f8", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(5,10))
    var_busqueda = tk.StringVar()
    entry_busqueda = tk.Entry(frame_busqueda, textvariable=var_busqueda, width=35, font=("Segoe UI", 10))
    entry_busqueda.pack(side=tk.LEFT)

    frame_lista = tk.Frame(win, bg="#f4f4f8")
    frame_lista.pack(pady=10, padx=20, fill="both", expand=True)

    # 🔥 COLUMNAS ACTUALIZADAS: Se eliminó CUIT/CUIL
    cols = ["ID", "Nombre", "DNI", "Teléfono", "Email", "Dirección", "Saldo (Deuda)", "Límite Crédito", "Activo"]

    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", height=15, style="Modern.Treeview")
    tree.pack(side="left", fill="both", expand=True)
    
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    ys.pack(side="right", fill="y")
    tree.configure(yscrollcommand=ys.set)
    
    for c in cols: tree.heading(c, text=c)
    
    tree.column("ID", width=0, minwidth=0, stretch=False)
    tree.column("Nombre", width=180)
    tree.column("DNI", width=100, anchor="center")
    tree.column("Teléfono", width=110)
    tree.column("Email", width=170)
    tree.column("Dirección", width=200) 
    tree.column("Saldo (Deuda)", width=120, anchor="e")
    tree.column("Límite Crédito", width=120, anchor="e")
    tree.column("Activo", width=80, anchor="center")

    tree.tag_configure("deuda", foreground="#dc2626")
    tree.tag_configure("favor", foreground="#16a34a")
    tree.tag_configure("cero", foreground="black")

    var_mostrar_inactivos = tk.BooleanVar(value=False)
    todos_clientes = []

    def cargar_datos():
        nonlocal todos_clientes
        try:
            incluir = var_mostrar_inactivos.get()
            todos_clientes = backend.listar_clientes_con_saldos(incluir_inactivos=incluir)
            
            def custom_sort(c):
                saldo = float(c.get('saldo', 0.0))
                if saldo < -0.01: return 0  
                if saldo > 0.01: return 1   
                return 2                    

            todos_clientes.sort(key=custom_sort)
            filtrar_lista()
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando: {e}", parent=win)

    def filtrar_lista(*args):
        query = var_busqueda.get().lower().strip()
        for i in tree.get_children(): tree.delete(i)
        
        for c in todos_clientes:
            nom = str(c.get('nombre','')).lower()
            dni = str(c.get('dni','')).lower()
            
            if query in nom or query in dni:
                saldo = float(c.get('saldo', 0.0))
                tag = "cero"
                if saldo < -0.01: tag = "deuda"
                elif saldo > 0.01: tag = "favor"
                
                saldo_vis = f"- $ {abs(saldo):,.2f}" if saldo < 0 else f"+ $ {saldo:,.2f}"
                if abs(saldo) < 0.01: saldo_vis = "$ 0.00"

                activo = "SI" if c.get('activo') else "NO"
                
                # 🔥 Se eliminó el mapeo de CUIT para coincidir con las columnas
                tree.insert("", tk.END, values=[
                    c.get('id_cliente'),
                    c.get('nombre'),
                    c.get('dni') or "-",
                    c.get('telefono') or "-",
                    c.get('email') or "-",
                    c.get('direccion') or "-", 
                    saldo_vis,
                    _fmt_mon(c.get('limite_credito')),
                    activo
                ], tags=(tag,))

    var_busqueda.trace_add("write", filtrar_lista)

    def accion_nuevo():
        top = ui_crear_cliente(win, backend)
        if isinstance(top, tk.Toplevel):
            win.wait_window(top)
            cargar_datos()
        else:
            win.after(1000, cargar_datos)

    def abrir_editar():
        rol_id = usuario_actual.get('id_rol')
        if rol_id not in [1, 3]: 
            messagebox.showwarning("Acceso Denegado", "⚠️ Solo Administradores y Supervisores pueden modificar clientes.", parent=win)
            return

        sel = tree.selection()
        if not sel: 
            messagebox.showwarning("Atención", "Seleccione un cliente para editar.", parent=win)
            return
        item = tree.item(sel[0], "values")
        
        top = ui_crear_cliente(win, backend, id_cliente_a_editar=int(item[0]))
        if isinstance(top, tk.Toplevel):
            win.wait_window(top)
            cargar_datos()
    
    def on_doble_click(event):
        abrir_editar()

    tree.bind("<Double-1>", on_doble_click)

    def desactivar():
        rol_id = usuario_actual.get('id_rol')
        if rol_id != 1:
            messagebox.showwarning("Acceso Denegado", "No tienes permisos para desactivar clientes.", parent=win)
            return

        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        if messagebox.askyesno("Confirmar", f"¿Desactivar a {item[1]}?"):
            backend.eliminar_cliente_logico(int(item[0]))
            cargar_datos()

    def activar_cliente():
        rol_id = usuario_actual.get('id_rol')
        if rol_id not in [1, 3]:
            messagebox.showwarning("Acceso Denegado", "No tienes permisos para activar clientes.", parent=win)
            return

        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        
        # Índice ajustado: Activo ahora es la columna 8 (índice 8)
        if item[8] == 'SI': 
             messagebox.showwarning("Atención", "El cliente ya está activo.", parent=win)
             return

        if messagebox.askyesno("Confirmar", f"¿Activar cliente {item[1]}?"):
            if backend.activar_cliente_logico(int(item[0])):
                messagebox.showinfo("Éxito", "Cliente activado.", parent=win)
                cargar_datos()
            else:
                messagebox.showerror("Error", "No se pudo activar.", parent=win)

    frame_botones = tk.Frame(win, bg="#f4f4f8")
    frame_botones.pack(pady=15, fill="x", padx=20)

    frame_acciones = tk.Frame(frame_botones, bg="#f4f4f8")
    frame_acciones.pack(side=tk.LEFT)

    tk.Button(
        frame_acciones, text="➕ Crear Cliente", command=accion_nuevo, 
        bg="#16a34a", fg="white", font=("Segoe UI", 10, "bold"), 
        relief="flat", padx=15, pady=8, cursor="hand2", width=15
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        frame_acciones, text="🗑️ Desactivar", command=desactivar, 
        bg="#dc2626", fg="white", font=("Segoe UI", 9, "bold"), 
        relief="flat", padx=12, pady=7, cursor="hand2", width=12
    ).pack(side=tk.LEFT, padx=5)

    btn_activar = tk.Button(
        frame_acciones, text="✅ Activar", command=activar_cliente, 
        bg="#0ea5e9", fg="white", font=("Segoe UI", 9, "bold"), 
        relief="flat", padx=12, pady=7, cursor="hand2", width=10
    )

    def toggle_mostrar_inactivos():
        cargar_datos()
        if var_mostrar_inactivos.get():
            btn_activar.pack(side=tk.LEFT, padx=5)
        else:
            btn_activar.pack_forget()

    frame_filtros = tk.Frame(frame_botones, bg="#f4f4f8")
    frame_filtros.pack(side=tk.LEFT, padx=30)

    tk.Checkbutton(
        frame_filtros, text="Ver Inactivos", variable=var_mostrar_inactivos, 
        bg="#f4f4f8", font=("Segoe UI", 9), command=toggle_mostrar_inactivos
    ).pack(side=tk.LEFT)

    tk.Button(
        frame_botones, text="Cerrar", command=win.destroy, 
        bg="#64748b", fg="white", font=("Segoe UI", 9, "bold"), 
        relief="flat", padx=15, pady=7, cursor="hand2", width=10
    ).pack(side=tk.RIGHT)

    cargar_datos()
    entry_busqueda.focus_set()
    configurar_navegacion_ventana(win)
    win.grab_set()