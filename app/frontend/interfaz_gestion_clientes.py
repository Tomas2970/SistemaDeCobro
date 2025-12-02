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
    win.geometry("1000x550")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # --- BARRA DE BÚSQUEDA ---
    frame_busqueda = tk.Frame(win, bg="#f4f4f8")
    frame_busqueda.pack(pady=(15,0), padx=20, fill="x")
    
    tk.Label(frame_busqueda, text="🔍 Buscar (Nombre/DNI):", bg="#f4f4f8").pack(side=tk.LEFT)
    var_busqueda = tk.StringVar()
    entry_busqueda = tk.Entry(frame_busqueda, textvariable=var_busqueda, width=35)
    entry_busqueda.pack(side=tk.LEFT, padx=10)

    frame_lista = tk.Frame(win, bg="#f4f4f8")
    frame_lista.pack(pady=10, padx=20, fill="both", expand=True)

    cols = ["ID", "Nombre", "DNI/CUIT", "Teléfono", "Email", "Saldo (Deuda)", "Límite Crédito", "Activo"]
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", height=15)
    tree.pack(side="left", fill="both", expand=True)
    
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    ys.pack(side="right", fill="y")
    tree.configure(yscrollcommand=ys.set)
    
    for c in cols: tree.heading(c, text=c)
    
    tree.column("ID", width=40, anchor="center")
    tree.column("Nombre", width=180)
    tree.column("DNI/CUIT", width=100)
    tree.column("Teléfono", width=100)
    tree.column("Email", width=150)
    tree.column("Saldo (Deuda)", width=100, anchor="e")
    tree.column("Límite Crédito", width=100, anchor="e")
    tree.column("Activo", width=50, anchor="center")

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
            
            # 🔥 ORDENAMIENTO PERSONALIZADO
            # 1. Deudores (Saldo < 0)
            # 2. A Favor (Saldo > 0)
            # 3. Neutros (Saldo == 0)
            def custom_sort(c):
                saldo = float(c.get('saldo', 0.0))
                if saldo < -0.01: return 0  # Primero: Rojos
                if saldo > 0.01: return 1   # Segundo: Verdes
                return 2                    # Tercero: Negros (0)

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
                
                tree.insert("", tk.END, values=[
                    c.get('id_cliente'),
                    c.get('nombre'),
                    c.get('dni') or "-",
                    c.get('telefono') or "-",
                    c.get('email') or "-",
                    saldo_vis,
                    _fmt_mon(c.get('limite_credito')),
                    activo
                ], tags=(tag,))

    var_busqueda.trace_add("write", filtrar_lista)

    # --- Acciones ---
    def accion_nuevo():
        top = ui_crear_cliente(win, backend)
        if isinstance(top, tk.Toplevel):
            win.wait_window(top)
            cargar_datos()
        else:
            win.after(1000, cargar_datos)

    def abrir_editar():
        sel = tree.selection()
        if not sel: 
            messagebox.showwarning("Atención", "Seleccione un cliente para editar.", parent=win)
            return
        item = tree.item(sel[0], "values")
        
        # Abrimos editor y esperamos
        top = ui_crear_cliente(win, backend, id_cliente_a_editar=int(item[0]))
        if isinstance(top, tk.Toplevel):
            win.wait_window(top)
            cargar_datos()
    
    # 🔥 DOBLE CLICK RESTAURADO
    def on_doble_click(event):
        abrir_editar()

    tree.bind("<Double-1>", on_doble_click)

    def desactivar():
        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        if messagebox.askyesno("Confirmar", f"¿Desactivar a {item[1]}?"):
            backend.eliminar_cliente_logico(int(item[0]))
            cargar_datos()

    frame_botones = tk.Frame(win, bg="#f4f4f8")
    frame_botones.pack(pady=15, fill="x")

    tk.Button(frame_botones, text="+ Crear Cliente", command=accion_nuevo, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=20)
    tk.Button(frame_botones, text="✎ Editar", command=abrir_editar, bg="#FFC107").pack(side=tk.LEFT, padx=5)
    tk.Button(frame_botones, text="⛔ Desactivar", command=desactivar, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
    
    tk.Checkbutton(frame_botones, text="Ver Inactivos", variable=var_mostrar_inactivos, bg="#f4f4f8", command=cargar_datos).pack(side=tk.LEFT, padx=20)
    
    tk.Button(frame_botones, text="Cerrar", command=win.destroy, bg="#607D8B", fg="white").pack(side=tk.RIGHT, padx=20)

    cargar_datos()
    entry_busqueda.focus_set()
    configurar_navegacion_ventana(win)
    win.grab_set()