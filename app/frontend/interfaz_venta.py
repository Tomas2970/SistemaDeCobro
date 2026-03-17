# ============================================
# app/frontend/interfaz_venta.py
# 🔥 ACTUALIZADO: Cantidad PRIMERO + Foco automático
# ============================================
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, Toplevel, ttk, Listbox, SINGLE
from typing import Any

from app.frontend.interfaz_productos import ui_productos
try:
    from app.frontend.interfaz_crear_cliente import ui_crear_cliente
except ImportError:
    ui_crear_cliente = None


try:
    from app.frontend.stock_event_manager import stock_events
except ImportError:
    class DummyStockEvents:
        def notificar_cambio_stock(self): pass
    stock_events = DummyStockEvents()

try:
    import sys
    import os
    app_dir = os.path.join(os.path.dirname(__file__), '..')
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    
    import impresora
    imprimir_ticket = impresora.imprimir_ticket
except ImportError as e:
    def imprimir_ticket(*args, **kwargs): return False

try:
    from app.frontend.interfaz_forma_pago import mostrar_ventana_pago
except ImportError as e:
    def mostrar_ventana_pago(parent, total_venta, cliente_seleccionado):
        return {'tipo_pago': 'efectivo', 'monto_pagado': total_venta, 'vuelto': 0}

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win): pass

try:
    from app.frontend.interfaz_productos import ui_crear_producto
except ImportError:
    def ui_crear_producto(parent, backend, callback=None): 
        messagebox.showerror("Error", "Módulo de creación de productos no disponible")
        return None


try:
    from app.frontend.interfaz_productos import ui_crear_producto
except ImportError:
    def ui_crear_producto(parent, backend, callback=None): 
        messagebox.showerror("Error", "Módulo de creación de productos no disponible")
        return None


def solicitar_autorizacion_supervisor(parent, backend, usuario_actual, callback_exito=None):
    popup = Toplevel(parent)
    popup.title("🔓 Autorización")
    popup.geometry("380x300") # Ventana más angosta
    popup.config(bg="#f4f4f8")
    popup.resizable(False, False)
    popup.transient(parent)
    popup.grab_set()
    
    frm_main = tk.Frame(popup, bg="#ffffff", padx=20, pady=20)
    frm_main.pack(fill="both", expand=True, padx=15, pady=15)
    
    tk.Label(frm_main, text="Autorización de Administrador", 
             bg="#ffffff", font=("Segoe UI", 11, "bold"), fg="#1f2937").pack(pady=(0, 15))
    
    tk.Label(frm_main, text="Usuario:", bg="#ffffff", font=("Segoe UI", 9)).pack(anchor="w", padx=45)
    entry_user = tk.Entry(frm_main, font=("Segoe UI", 10), relief="solid", bd=1, width=25, justify="center") # Campo más corto
    entry_user.pack(pady=(2, 10))
    entry_user.focus_set()
    
    tk.Label(frm_main, text="Contraseña:", bg="#ffffff", font=("Segoe UI", 9)).pack(anchor="w", padx=45)
    entry_pass = tk.Entry(frm_main, show="●", font=("Segoe UI", 10), relief="solid", bd=1, width=25, justify="center") # Campo más corto
    entry_pass.pack(pady=(2, 20))
    
    def validar():
        u_nom = entry_user.get().strip()
        u_pass = entry_pass.get().strip()
        
        if not u_nom or not u_pass:
            messagebox.showwarning("Atención", "Ingrese credenciales", parent=popup)
            return
        
        try:
            supervisor = backend.verificar_contraseña(u_nom, u_pass) #
            
            if supervisor and supervisor.get('id_rol') == 1:
                popup.grab_release()
                popup.destroy()
                if callback_exito:
                    parent.after(100, lambda: callback_exito(supervisor))
            else:
                messagebox.showerror("Error", "No autorizado.", parent=popup)
                entry_pass.delete(0, tk.END)
                
        except Exception as e:
            messagebox.showerror("Error", f"Fallo: {e}", parent=popup)
    
    # 🔥 UN SOLO FRAME Y UN SOLO BOTÓN DE CADA TIPO
    frm_btns = tk.Frame(popup, bg="#f4f4f8")
    frm_btns.pack(pady=5)
    
    tk.Button(frm_btns, text="✓ Autorizar", bg="#10b981", fg="white", font=("Segoe UI", 9, "bold"), 
              relief="flat", padx=20, pady=8, command=validar, cursor="hand2").pack(side="left", padx=5)
    
    tk.Button(frm_btns, text="Cancelar", bg="#6b7280", fg="white", font=("Segoe UI", 9), 
              relief="flat", padx=15, pady=8, command=popup.destroy, cursor="hand2").pack(side="left", padx=5)

    entry_pass.bind("<Return>", lambda e: validar())


def ui_venta(parent: tk.Misc, backend, usuario: dict) -> None:
    # Evitar múltiples ventanas de venta abiertas al mismo tiempo
    for w in parent.winfo_children():
        if isinstance(w, tk.Toplevel) and w.title() == "Punto de Venta - Supermercado Don Atilio":
            w.lift()
            w.focus_force()
            return

    win = tk.Toplevel(parent)
    win.title("Punto de Venta - Supermercado Don Atilio")
    win.geometry("1000x700")
    win.config(bg="#f4f4f8")
    win.resizable(True, True) 

    # ESTILOS MODERNOS
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
    
    style.map("Modern.Treeview.Heading",
              background=[('active', '#e5e7eb')])
    
    style.map('Modern.Treeview',
              background=[('selected', '#3b82f6')],
              foreground=[('selected', 'white')])

    # VALIDADORES
    def validar_len_30(t): return len(t) <= 30
    def validar_cantidad(t):
        if t == "": return True
        if len(t) > 5: return False  # max 5 chars: "1.750"
        # Permite: solo digitos, o digitos con punto/coma decimal
        import re
        return bool(re.match(r'^[0-9]{0,4}[.,]?[0-9]{0,3}$', t))
    
    vc_30 = (win.register(validar_len_30), '%P')
    vc_cantidad = (win.register(validar_cantidad), '%P')

    items: list[tuple[int | None, str, int, float, str]] = []
    cliente_sel: dict[str, Any] | None = None
    total_venta: float = 0.0 

    # ================================================================
    # ESTRUCTURA DE LAYOUT (FRAMES)
    # ================================================================
    
    # 1. HEADER (Cliente)
    frm_header = tk.Frame(win, bg="#ffffff", pady=12, padx=15, relief="flat", bd=0)
    frm_header.pack(fill="x", padx=10, pady=(10, 5))

    # 2. INPUTS (Cantidad y Producto - ORDEN INVERTIDO)
    frm_inputs = tk.Frame(win, bg="#f4f4f8", pady=8)
    frm_inputs.pack(fill="x", padx=10, pady=5)

    # 3. LISTA (Treeview)
    frm_lista = tk.Frame(win, bg="#f4f4f8", relief="flat", bd=0)
    frm_lista.pack(fill="both", expand=True, padx=10, pady=5)

    # 4. FOOTER (Total y Botones)
    frm_footer = tk.Frame(win, bg="#f4f4f8", pady=15, padx=10)
    frm_footer.pack(fill="x", side="bottom")

    # ================================================================
    # 1. SECCIÓN CLIENTE
    # ================================================================
    tk.Label(frm_header, text="👤 Cliente:", bg="#ffffff", font=("Segoe UI", 11, "bold"), fg="#1f2937").pack(side="left")
    
    lbl_cliente = tk.Label(frm_header, text="(Consumidor Final)", bg="#ffffff", font=("Segoe UI", 11), fg="#6b7280")
    lbl_cliente.pack(side="left", padx=(5, 20))

    def abrir_selector_cliente():
        nonlocal cliente_sel
        popup = Toplevel(win)
        popup.title("Seleccionar Cliente")
        popup.geometry("700x550")  # Altura aumentada para visibilidad
        popup.config(bg="#f4f4f8")
        
        # Marco de búsqueda
        frm_bus = tk.Frame(popup, bg="#f4f4f8", pady=10)
        frm_bus.pack(fill=tk.X, padx=15)
        tk.Label(frm_bus, text="🔎 Buscar cliente:", bg="#f4f4f8", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        var_bus = tk.StringVar()
        ent_bus = tk.Entry(frm_bus, textvariable=var_bus, font=("Segoe UI", 10), width=40)
        ent_bus.pack(side=tk.LEFT, padx=10)
        ent_bus.focus_set()
        
        # Marco para Treeview
        frm_tree = tk.Frame(popup, bg="#f4f4f8")
        frm_tree.pack(fill=tk.BOTH, expand=True, padx=15)
        
        # 🔥 TABLA MODERNA: Solo ID, Nombre y DNI
        cols = ("ID", "Nombre", "DNI")
        tree_c = ttk.Treeview(frm_tree, columns=cols, show="headings", height=12, style="Modern.Treeview")
        tree_c.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sc_c = ttk.Scrollbar(frm_tree, orient="vertical", command=tree_c.yview)
        sc_c.pack(side=tk.RIGHT, fill=tk.Y)
        tree_c.configure(yscrollcommand=sc_c.set)
        
        tree_c.heading("ID", text="ID")
        tree_c.heading("Nombre", text="Nombre")
        tree_c.heading("DNI", text="DNI")
        tree_c.column("ID", width=60, anchor="center")
        tree_c.column("Nombre", width=350)
        tree_c.column("DNI", width=150, anchor="center")
        
        todos_clis = backend.listar_clientes()
        
        def filtrar(*_):
            for i in tree_c.get_children(): 
                tree_c.delete(i)
            q = var_bus.get().lower()
            for c in todos_clis:
                dni = c.get('dni') or "-"
                if q in c['nombre'].lower() or q in str(dni):
                    tree_c.insert("", tk.END, values=(c['id_cliente'], c['nombre'], dni))
            hijos = tree_c.get_children()
            if hijos: 
                tree_c.selection_set(hijos[0])
        
        var_bus.trace_add("write", filtrar)
        filtrar()
        
        def seleccionar(event=None):
            nonlocal cliente_sel
            sel = tree_c.selection()
            if not sel: 
                return
            cid = int(tree_c.item(sel[0], "values")[0])
            cliente_sel = next((c for c in todos_clis if c['id_cliente'] == cid), None)
            _upd_cliente()
            popup.destroy()
        
        tree_c.bind("<Double-1>", seleccionar)
        tree_c.bind("<Return>", seleccionar)
        
        # Marco de botones
        fr_btns = tk.Frame(popup, bg="#f4f4f8", pady=15)
        fr_btns.pack(fill=tk.X)
        
        def limpiar_cliente():
            nonlocal cliente_sel
            cliente_sel = None
            _upd_cliente()
            popup.destroy()
        
        tk.Button(fr_btns, text="✓ Seleccionar", bg="#10b981", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=10,
                  command=seleccionar, cursor="hand2",
                  activebackground="#059669", activeforeground="white").pack(side=tk.LEFT, padx=(20, 5))

        def abrir_nuevo_cliente():
            if ui_crear_cliente:
                ui_crear_cliente(popup, backend)
                # Recargar lista tras crear
                nonlocal todos_clis
                todos_clis = backend.listar_clientes()
                filtrar()

        tk.Button(fr_btns, text="➕ Nuevo Cliente", bg="#3b82f6", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=10,
                  command=abrir_nuevo_cliente, cursor="hand2").pack(side=tk.LEFT, padx=5)

        tk.Button(fr_btns, text="Consumidor Final", bg="#6b7280", fg="white",
                  font=("Segoe UI", 10), relief="flat", padx=15, pady=10,
                  command=limpiar_cliente, cursor="hand2",
                  activebackground="#4b5563", activeforeground="white").pack(side=tk.LEFT, padx=5)
        
        configurar_navegacion_ventana(popup)
        popup.after(100, lambda: ent_bus.focus_set())
        popup.grab_set()
        popup.transient(win)

    def quitar_cliente():
        nonlocal cliente_sel; cliente_sel = None; _upd_cliente()

    def _upd_cliente():
        if cliente_sel:
            lbl_cliente.config(text=f"{cliente_sel.get('nombre','')} (ID: {cliente_sel.get('id_cliente','')})", 
                             fg="#1f2937", font=("Segoe UI", 11, "bold"))
        else:
            lbl_cliente.config(text="(Consumidor Final)", fg="#6b7280", font=("Segoe UI", 11, "normal"))

    btn_cli = tk.Button(frm_header, text="🔍 Buscar Cliente", command=abrir_selector_cliente, 
                       bg="#3b82f6", fg="white", font=("Segoe UI", 10, "bold"),
                       relief="flat", padx=15, pady=8, cursor="hand2",
                       activebackground="#2563eb", activeforeground="white")
    btn_cli.pack(side="left", padx=5)
    
    btn_no_cli = tk.Button(frm_header, text="× Quitar", command=quitar_cliente, 
                          bg="#ef4444", fg="white", font=("Segoe UI", 9),
                          relief="flat", padx=12, pady=8, cursor="hand2",
                          activebackground="#dc2626", activeforeground="white")
    btn_no_cli.pack(side="left", padx=5)

    # ================================================================
    # 2. SECCIÓN INPUTS - 🔥 ORDEN INVERTIDO: CANTIDAD PRIMERO
    # ================================================================
    
    # 🔥 CANTIDAD PRIMERO
    tk.Label(frm_inputs, text="Cant:", bg="#f4f4f8", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 5))
    
    entry_cantidad = tk.Entry(frm_inputs, width=8, font=("Segoe UI", 11), justify="center", validate="key", validatecommand=vc_cantidad)
    entry_cantidad.insert(0, "1")
    entry_cantidad.pack(side="left", padx=5)
    
    # 🔥 PRODUCTO DESPUÉS
    tk.Label(frm_inputs, text="Código / Nombre:", bg="#f4f4f8", font=("Segoe UI", 10)).pack(side="left", padx=(15, 5))
    
    entry_producto = tk.Entry(frm_inputs, width=30, font=("Segoe UI", 11), validate="key", validatecommand=vc_30)
    entry_producto.pack(side="left", padx=5)
    
    # 🔥 Variables para popup de sugerencias y debounce del escáner
    popup_sugerencias = None
    listbox_sugerencias = None
    sugerencias_activas = []
    _debounce_id = None  # para cancelar búsquedas previas
    
    # BOTÓN AGREGAR
    btn_agregar = tk.Button(frm_inputs, text="+ Agregar", 
                           bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"),
                           relief="flat", padx=20, pady=8, cursor="hand2",
                           activebackground="#059669", activeforeground="white")
    btn_agregar.pack(side="left", padx=10)
    
    def abrir_creacion_producto_autorizado():
        """Si el usuario es admin (rol 1), abre directamente. Si no, pide autorización."""
        def abrir_con_usuario(usr):
            if ui_productos:
                ui_productos(
                    parent=win,
                    backend=backend,
                    usuario=usr,
                    id_producto_a_cargar=None,
                    callback_on_save=lambda: messagebox.showinfo("Éxito", "Producto cargado. Ya puede escanearlo.")
                )
            else:
                messagebox.showerror("Error", "Módulo de productos no disponible", parent=win)

        if usuario.get('id_rol') == 1:
            # Admin: abre directo sin pedir autorización
            abrir_con_usuario(usuario)
        else:
            solicitar_autorizacion_supervisor(win, backend, usuario, abrir_con_usuario)
    
    btn_nuevo_producto = tk.Button(frm_inputs, text="🔓 Agregar Producto Nuevo", 
                                   bg="#f59e0b", fg="white", font=("Segoe UI", 9, "bold"),
                                   relief="flat", padx=15, pady=8, cursor="hand2",
                                   command=abrir_creacion_producto_autorizado,
                                   activebackground="#d97706", activeforeground="white")
    btn_nuevo_producto.pack(side="left", padx=5)

    # ================================================================
    # 3. LISTA (TREEVIEW)
    # ================================================================
    cols = ("ID", "Producto", "Precio", "Cant", "Subtotal")
    tree = ttk.Treeview(frm_lista, columns=cols, show="headings", style="Modern.Treeview")
    
    tree.column("ID", width=50, anchor="center")
    tree.column("Producto", width=400, anchor="w")
    tree.column("Precio", width=100, anchor="e")
    tree.column("Cant", width=80, anchor="center")
    tree.column("Subtotal", width=120, anchor="e")
    
    tree.heading("ID", text="ID")
    tree.heading("Producto", text="Producto")
    tree.heading("Precio", text="Precio Unit.")
    tree.heading("Cant", text="Cant.")
    tree.heading("Subtotal", text="Subtotal")
    
    vsb = ttk.Scrollbar(frm_lista, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    # ================================================================
    # 4. FOOTER (TOTALES Y ACCIONES)
    # ================================================================
    
    btn_quitar = tk.Button(frm_footer, text="🗑️ Quitar Seleccionado", 
                          bg="#f3f4f6", fg="#ef4444", font=("Segoe UI", 9, "bold"),
                          relief="flat", padx=15, pady=8, cursor="hand2",
                          activebackground="#e5e7eb", activeforeground="#dc2626")
    btn_quitar.pack(side="left")

    frame_totales = tk.Frame(frm_footer, bg="#f4f4f8")
    frame_totales.pack(side="right")

    lbl_total_titulo = tk.Label(frame_totales, text="TOTAL A PAGAR:", font=("Segoe UI", 12), bg="#f4f4f8", fg="#6b7280")
    lbl_total_titulo.pack(side="left", padx=5)
    
    lbl_total_monto = tk.Label(frame_totales, text="$ 0.00", font=("Segoe UI", 24, "bold"), bg="#f4f4f8", fg="#059669")
    lbl_total_monto.pack(side="left", padx=10)

    btn_confirmar = tk.Button(frame_totales, text="✓ COBRAR", 
                             bg="#10b981", fg="white", font=("Segoe UI", 12, "bold"),
                             relief="flat", padx=30, pady=10, cursor="hand2",
                             activebackground="#059669", activeforeground="white")
    btn_confirmar.pack(side="left", padx=(20, 5))
    
    btn_cancelar = tk.Button(frame_totales, text="Cancelar", 
                            bg="#6b7280", fg="white", font=("Segoe UI", 10),
                            relief="flat", padx=15, pady=10, cursor="hand2",
                            activebackground="#4b5563", activeforeground="white")
    btn_cancelar.pack(side="left", padx=5)

    # ================================================================
    # LÓGICA - 🔥 BÚSQUEDA DINÁMICA CON POPUP FLOTANTE
    # ================================================================
    
    def mostrar_sugerencias(event=None):
        """Muestra popup flotante con sugerencias mientras escribe."""
        nonlocal popup_sugerencias, listbox_sugerencias, sugerencias_activas, _debounce_id
        
        # 🔥 Si el evento es de flechas arriba/abajo, ignorar (navegación activa)
        if event and event.keysym in ['Up', 'Down']:
            return
        
        token = entry_producto.get().strip()
        
        # Si escribe menos de 2 caracteres, ocultar sugerencias
        if len(token) < 2:
            ocultar_sugerencias()
            return
        
        # 🔥 DEBOUNCE: cancelar búsqueda anterior y esperar 180ms antes de buscar
        # Esto evita que el escáner dispare N búsquedas mientras escribe el código
        if _debounce_id is not None:
            win.after_cancel(_debounce_id)
        
        def _ejecutar_busqueda():
            nonlocal _debounce_id
            _debounce_id = None
            _buscar_y_mostrar_sugerencias(token)
        
        _debounce_id = win.after(180, _ejecutar_busqueda)
    
    def _buscar_y_mostrar_sugerencias(token):
        """Ejecuta la búsqueda real y muestra el popup."""
        nonlocal popup_sugerencias, listbox_sugerencias, sugerencias_activas
        
        # Buscar productos que coincidan
        try:
            resultados = backend.buscar_producto_por_nombre(token)
            if not resultados:
                ocultar_sugerencias()
                return
            
            # Limitar a 8 resultados máximo
            sugerencias_activas = resultados[:8]
            
            # Crear popup si no existe
            if popup_sugerencias is None or not popup_sugerencias.winfo_exists():
                popup_sugerencias = tk.Toplevel(win)
                popup_sugerencias.withdraw()  # Ocultar inicialmente
                popup_sugerencias.overrideredirect(True)  # Sin bordes de ventana
                popup_sugerencias.config(bg="#ffffff", relief="solid", bd=1)
                
                listbox_sugerencias = tk.Listbox(
                    popup_sugerencias,
                    height=min(8, len(sugerencias_activas)),
                    width=55,
                    font=("Segoe UI", 10),
                    selectmode=tk.SINGLE,
                    relief="flat",
                    bg="#ffffff",
                    selectbackground="#3b82f6",
                    selectforeground="white",
                    highlightthickness=0
                )
                listbox_sugerencias.pack(fill="both", expand=True, padx=1, pady=1)
                
                # Bindings para el listbox
                listbox_sugerencias.bind('<Double-Button-1>', lambda e: seleccionar_de_sugerencias())
                listbox_sugerencias.bind('<Return>', lambda e: seleccionar_de_sugerencias())
            
            # Actualizar altura según cantidad de resultados
            listbox_sugerencias.config(height=min(8, len(sugerencias_activas)))
            
            # Limpiar y llenar con sugerencias
            listbox_sugerencias.delete(0, tk.END)
            for prod in sugerencias_activas:
                nombre = prod.get('nombre', '')
                precio = float(prod.get('precio', 0))
                stock = float(prod.get('stock', 0))
                texto = f"{nombre} - ${precio:,.2f} (Stock: {stock:.0f})"
                listbox_sugerencias.insert(tk.END, texto)
            
            # Seleccionar primer elemento siempre (ya no hay navegación activa aquí)
            if sugerencias_activas:
                listbox_sugerencias.select_set(0)
                listbox_sugerencias.see(0)
            
            # Posicionar el popup debajo del Entry
            x = entry_producto.winfo_rootx()
            y = entry_producto.winfo_rooty() + entry_producto.winfo_height() + 2
            popup_sugerencias.geometry(f"+{x}+{y}")
            popup_sugerencias.deiconify()  # Mostrar
            
        except Exception as e:
            print(f"Error en búsqueda dinámica: {e}")
            import traceback
            traceback.print_exc()
    
    def ocultar_sugerencias():
        """Oculta el popup de sugerencias."""
        nonlocal popup_sugerencias
        if popup_sugerencias and popup_sugerencias.winfo_exists():
            popup_sugerencias.withdraw()
    
    def seleccionar_de_sugerencias(event=None):
        """Selecciona un producto del popup con Enter o doble clic."""
        nonlocal sugerencias_activas
        
        if not listbox_sugerencias or not listbox_sugerencias.winfo_exists():
            return
        
        sel = listbox_sugerencias.curselection()
        if not sel or not sugerencias_activas:
            return
        
        # Obtener producto seleccionado
        idx = sel[0]
        if idx < len(sugerencias_activas):
            prod = sugerencias_activas[idx]
            
            # Llenar el Entry con el código o ID del producto
            entry_producto.delete(0, tk.END)
            codigo = prod.get('codigo_barras') or str(prod.get('id_producto'))
            entry_producto.insert(0, codigo)
            
            # Ocultar sugerencias
            ocultar_sugerencias()
            
            # Agregar directamente
            agregar_producto()
    
    def navegar_sugerencias(event):
        """Permite navegar con flechas arriba/abajo en el popup."""
        if not listbox_sugerencias or not listbox_sugerencias.winfo_exists():
            return
        
        sel = listbox_sugerencias.curselection()
        if not sel:
            listbox_sugerencias.select_set(0)
            return
        
        idx = sel[0]
        
        if event.keysym == 'Down':
            nuevo_idx = min(idx + 1, listbox_sugerencias.size() - 1)
        elif event.keysym == 'Up':
            nuevo_idx = max(idx - 1, 0)
        else:
            return
        
        listbox_sugerencias.select_clear(0, tk.END)
        listbox_sugerencias.select_set(nuevo_idx)
        listbox_sugerencias.see(nuevo_idx)
        
        # Prevenir que el Entry procese la flecha
        return "break"
    
    # 🔥 BINDINGS PARA BÚSQUEDA DINÁMICA
    entry_producto.bind('<KeyRelease>', mostrar_sugerencias)
    entry_producto.bind('<Down>', navegar_sugerencias)
    entry_producto.bind('<Up>', navegar_sugerencias)
    entry_producto.bind('<Escape>', lambda e: ocultar_sugerencias())
    
    # ================================================================
    # LÓGICA - RESTO DE FUNCIONES
    # ================================================================
    
    def _resolver_producto(token: str) -> dict | None:
        return backend.buscar_producto_inteligente(token)

    def _stock_en_carrito(id_producto: int | None) -> float: 
        if id_producto is None: return 0.0
        return sum(c for pid, _, c, _, _ in items if pid == id_producto)

    def _agregar_o_sumar(id_producto: int | None, nombre: str, cant: float, precio: float, codigo: str) -> None: 
        if id_producto is None:
            items.append((None, nombre, cant, precio, ""))
            return
        for idx, (pid, _, c, p, cb) in enumerate(items):
            if pid == id_producto and abs(p - precio) < 1e-6:
                items[idx] = (pid, nombre, c + cant, precio, cb)
                return
        items.append((id_producto, nombre, cant, precio, codigo))

    def _refrescar_lista() -> None:
        nonlocal total_venta
        for i in tree.get_children(): tree.delete(i)
        
        total_venta = 0.0 
        for pid, nombre, cant, precio, _ in items:
            parcial = cant * precio
            total_venta += parcial
            
            cant_str = f"{int(cant)}" if cant == int(cant) else f"{cant:.3f}"
            
            tree.insert("", "end", values=(
                pid if pid else "-",
                nombre,
                f"$ {precio:,.2f}",
                cant_str,
                f"$ {parcial:,.2f}"
            ))
            
        lbl_total_monto.config(text=f"$ {total_venta:,.2f}")

    def quitar_seleccion(event=None):
        sel = tree.selection()
        if not sel: return
        indices = []
        for s in sel:
            idx = tree.index(s)
            indices.append(idx)
        
        indices.sort(reverse=True)
        for i in indices:
            items.pop(i)
        
        _refrescar_lista()

    btn_quitar.config(command=quitar_seleccion)
    tree.bind("<Delete>", quitar_seleccion)
    
    def _reiniciar_venta_completa():
        nonlocal items, cliente_sel, total_venta
        items.clear(); cliente_sel = None; total_venta = 0.0
        _refrescar_lista(); _upd_cliente()     
        entry_producto.delete(0, tk.END); entry_cantidad.delete(0, tk.END)
        entry_cantidad.insert(0, "1")
        # 🔥 FOCO EN CANTIDAD (no en producto)
        entry_cantidad.focus_set()

    def manejar_escaneo_producto(event=None):
        """Cuando presiona Enter en Producto."""
        # 🔥 Si hay sugerencias visibles, seleccionar de ahí
        if listbox_sugerencias and listbox_sugerencias.winfo_exists():
            seleccionar_de_sugerencias()
            return
        
        # Si no hay sugerencias, buscar normalmente
        token = entry_producto.get().strip()
        if not token:
            messagebox.showwarning("Atención", "Ingrese un código, ID o nombre.", parent=win)
            return
        
        # Agregar directamente
        agregar_producto()
    
    entry_producto.bind("<Return>", manejar_escaneo_producto)
    
    # 🔥 ENTER EN CANTIDAD → AVANZA A PRODUCTO
    def avanzar_a_producto(event=None):
        """Cuando presiona Enter en Cantidad, avanza al campo Producto."""
        entry_producto.focus_set()
        entry_producto.select_range(0, tk.END)  # Selecciona todo el texto si hay algo
    
    entry_cantidad.bind("<Return>", avanzar_a_producto)

    def _redirigir_escaneo_desde_cantidad(event=None):
        """
        Si en el campo cantidad se escriben más de 2 chars (ej: escáner manda código directo),
        redirige el contenido a entry_producto y ejecuta agregar con cantidad 1.
        """
        texto = entry_cantidad.get()
        # Si tiene más de 2 chars es un código de barras ingresado en el campo equivocado
        # Solo redirige si parece un código de barras (más de 5 chars)
        # así no interfiere con cantidades decimales como 1.750
        if len(texto) > 5:
            codigo = texto
            entry_cantidad.delete(0, tk.END)
            entry_cantidad.insert(0, "1")
            entry_producto.delete(0, tk.END)
            entry_producto.insert(0, codigo)
            # Pequeño delay para que termine de escribir el escáner
            win.after(80, agregar_producto)
    
    entry_cantidad.bind("<KeyRelease>", _redirigir_escaneo_desde_cantidad)
    
    def agregar_producto():
        token = entry_producto.get().strip()
        if not token:
            messagebox.showwarning("Atención", "Ingrese un código.", parent=win); return
        
        # 🔥 Ocultar sugerencias antes de agregar
        ocultar_sugerencias()
        
        prod = _resolver_producto(token)
        if not prod:
            messagebox.showwarning("No encontrado", "No se encontró el producto.", parent=win); return

        es_pesable = bool(prod.get("es_pesable", False))
        cantidad_str = entry_cantidad.get().strip().replace(",", ".") or "1"
        try:
            if es_pesable: cant = float(cantidad_str)
            else:
                cant_float = float(cantidad_str)
                if cant_float != int(cant_float):
                    messagebox.showwarning("Error", "Producto no pesable. Use enteros.", parent=win); return
                cant = int(cant_float)
            if cant <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Atención", "Cantidad inválida.", parent=win); return

        pid = int(prod.get("id_producto") or prod.get("id"))
        nombre = str(prod.get("nombre",""))
        codigo = str(prod.get("codigo_barras") or "")
        precio = float(prod.get("precio") or 0.0)
        stock_actual = float(prod.get("stock") or 0.0)

        ya_en_carrito = _stock_en_carrito(pid)
        disp_para_agregar = stock_actual - ya_en_carrito
        
        if cant > disp_para_agregar:
             messagebox.showerror(
                 "Stock Insuficiente", 
                 f"No hay stock suficiente para agregar {cant} unidades.\n\n"
                 f"• Disponible real: {stock_actual:.3f}\n"
                 f"• Ya en carrito: {ya_en_carrito:.3f}\n"
                 f"• Máximo agregable: {max(0, disp_para_agregar):.3f}",
                 parent=win
             )
             return

        _agregar_o_sumar(pid, nombre, cant, precio, codigo)
        _refrescar_lista()
        
        entry_producto.delete(0, tk.END)
        entry_cantidad.delete(0, tk.END)
        entry_cantidad.insert(0, "1")
        # 🔥 VOLVER A CANTIDAD (flujo continuo)
        entry_cantidad.focus_set()

    btn_agregar.config(command=agregar_producto)
    
    def confirmar_venta():
        if not items:
            messagebox.showwarning("Atención", "Carrito vacío.", parent=win); return
        
        info_pago = mostrar_ventana_pago(parent=win, total_venta=total_venta, cliente_seleccionado=(cliente_sel is not None))
        if info_pago is None: return

        tipo_pago = info_pago['tipo_pago']

        if tipo_pago == "cuenta_corriente" and cliente_sel is None:
            messagebox.showerror("Error", "Se requiere cliente para Cta. Cte.", parent=win); return

        if tipo_pago == "cuenta_corriente":
            try:
                id_cli = cliente_sel.get("id_cliente")
                cuenta = backend.obtener_cuenta_por_cliente(id_cli) 
                saldo_actual = float(cuenta.get('saldo', 0.0))
                limite_credito = float(cuenta.get('limite_credito', 0.0))
                
                saldo_proyectado = saldo_actual - total_venta 
                
                if saldo_proyectado < -limite_credito:
                    es_deuda = saldo_actual < 0
                    limite_credito_abs = abs(limite_credito)
                    credito_disponible_bruto = limite_credito_abs + saldo_actual 
                    monto_faltante = total_venta - credito_disponible_bruto
                    
                    msg = (
                        "Crédito Insuficiente (Límite Excedido)\n\n"
                        f"• Límite Total de Crédito: $ {limite_credito_abs:,.2f}\n"
                        f"• Saldo Actual: {'-' if es_deuda else '+'} $ {abs(saldo_actual):,.2f} ({'Deuda Pendiente' if es_deuda else 'A Favor'})\n"
                        f"• **Crédito Disponible: $ {max(0, credito_disponible_bruto):,.2f}**\n\n"
                        f"La venta de $ {total_venta:,.2f} excede el límite por $ {monto_faltante:,.2f}."
                    )
                    
                    messagebox.showerror("⚠️ Límite de Crédito Excedido", msg, parent=win)
                    return 
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error verificación crédito: {e}", parent=win); return

        id_usuario = usuario.get("id_usuario") or usuario.get("id", 0)
        id_cliente = cliente_sel.get("id_cliente") if cliente_sel else None

        # 🔥 OBTENER ID DE LA SESIÓN DE CAJA ACTUAL
        try:
            session_actual = backend.obtener_session_activa()
            id_session = session_actual.get('id_session') if session_actual else None
        except Exception:
            id_session = None

        try:
            # 🔥 PASAR id_session AL BACKEND
            id_venta = backend.registrar_venta_completa(
                id_usuario=id_usuario, 
                id_cliente=id_cliente, 
                items=items, 
                tipo_pago=tipo_pago,
                id_session=id_session  # 🔥 NUEVO PARÁMETRO
            )
            if not id_venta:
                messagebox.showerror("Error", "ID de venta nulo.", parent=win); return
        except ValueError as ve:
            if "CAJA_CERRADA" in str(ve):
                messagebox.showerror(
                    "⚠️ Caja Cerrada", 
                    "No se puede procesar la venta porque la caja está cerrada.\n\n"
                    "Por favor, abra la caja antes de continuar.", 
                    parent=win
                )
            else:
                messagebox.showerror("Error", f"Venta revertida.\n{ve}", parent=win)
            return
        except Exception as e:
            messagebox.showerror("Error", f"Venta revertida.\n{e}", parent=win); return

        try:
            if messagebox.askyesno("Venta Registrada", "Imprimir ticket?", parent=win):
                imprimir_ticket(id_venta=id_venta, items_de_la_venta=items, nombre_vendedor=usuario.get("nombre", "Vendedor"), 
                                metodo_pago=info_pago['tipo_pago'], monto_entregado=info_pago.get('monto_pagado', 0.0), 
                                vuelto=info_pago.get('vuelto', 0.0), cliente=cliente_sel.get('nombre', 'Consumidor Final') if cliente_sel else 'Consumidor Final')
        except Exception as e:
            messagebox.showerror("Error", f"Error Impresión: {e}", parent=win)

        messagebox.showinfo("Venta Exitosa", f"Venta #{id_venta} OK.\nTotal: ${total_venta:,.2f}", parent=win)
        _reiniciar_venta_completa()
        win.after(100, lambda: stock_events.notificar_cambio_stock())

    btn_confirmar.config(command=confirmar_venta)
    btn_cancelar.config(command=win.destroy)

    _upd_cliente()
    
    win.bind("<F2>", lambda e: abrir_selector_cliente())
    win.bind("<F5>", lambda e: confirmar_venta())
    win.bind("<Escape>", lambda e: win.destroy())
    
    configurar_navegacion_ventana(win)
    # 🔥 FOCO INICIAL EN CANTIDAD (no en producto)
    win.after(50, lambda: entry_cantidad.focus_set())
    win.grab_set()