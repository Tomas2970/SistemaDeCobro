# ============================================
# app/frontend/interfaz_venta.py
# 🔥 ACTUALIZADO: Cantidad PRIMERO + Foco automático
# ============================================
from __future__ import annotations
import tkinter as tk
from tkinter import Toplevel, ttk, Listbox, SINGLE
from app.frontend import custom_dialogs as messagebox
from typing import Any
import re

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
    from app.frontend.theme_config import THEME_COLORS, get_color, aplicar_tema_ventana, configurar_estilo_treeview, preparar_ventana, centrar_y_mostrar_ventana
except ImportError:
    def get_color(k): return "#000000"
    def aplicar_tema_ventana(w): pass
    def configurar_estilo_treeview(): pass
    def preparar_ventana(w): pass
    def centrar_y_mostrar_ventana(w): pass


from app.frontend.autorizacion import solicitar_autorizacion_supervisor

from app.frontend.broadcast_manager import ToastBroadcast

def ui_venta(parent: tk.Misc, backend, usuario: dict) -> None:
    import customtkinter as ctk

    for w in parent.winfo_children():
        if isinstance(w, ctk.CTkToplevel) and w.title() == "Punto de Venta - Supermercado Don Atilio":
            w.lift()
            w.focus_force()
            return

    # 🔥 VALIDACIÓN DE CAJA ABIERTA
    try:
        session_actual = backend.obtener_session_activa()
    except Exception:
        session_actual = None
        
    if not session_actual:
        messagebox.showerror(
            "⚠️ Caja Cerrada",
            "No se puede abrir el punto de venta porque la caja está cerrada.\n\n"
            "Por favor, abra la caja antes de iniciar una venta.",
            parent=parent.winfo_toplevel()
        )
        return

    win = ctk.CTkToplevel(parent)
    from app.frontend.theme_config import preparar_ventana, centrar_y_mostrar_ventana
    preparar_ventana(win)
    win.title("Punto de Venta - Supermercado Don Atilio")
    try: win.state('zoomed')
    except: win.geometry("1100x750")
    
    col_bg = "#f3f4f6" if ctk.get_appearance_mode() == "Light" else "#111827"
    col_card = "#ffffff" if ctk.get_appearance_mode() == "Light" else "#1f2937"
    col_border = "#e5e7eb" if ctk.get_appearance_mode() == "Light" else "#374151"
    font_title = ("Segoe UI", 15, "bold")
    font_normal = ("Segoe UI", 14)
    font_big = ("Segoe UI", 24, "bold")
    
    win.configure(fg_color=col_bg)
    # 🔥 POLLING DE CAJA CERRADA REMOTAMENTE (cada 10s)
    caja_cerrada_remotamente = False
    
    def polling_estado_caja():
        nonlocal caja_cerrada_remotamente
        if not win.winfo_exists() or caja_cerrada_remotamente: return
        
        try:
            session = backend.obtener_session_activa()
            if not session:
                caja_cerrada_remotamente = True
                verificar_expulsion()
        except Exception:
            pass
        
        if not caja_cerrada_remotamente:
            win.after(10000, polling_estado_caja)
            
    def verificar_expulsion():
        """Expulsa al usuario si la caja se cerró, SALVO que esté en medio de una venta."""
        if caja_cerrada_remotamente:
            if not items:
                # No hay venta activa, expulsar inmediatamente
                messagebox.showerror(
                    "⛔ Caja Cerrada Remotamente", 
                    "Su sesión de caja ha sido cerrada de forma forzada por el Encargado de Turno.\n\n"
                    "El sistema lo redirigirá al menú principal.", 
                    parent=win
                )
                win.destroy()
            else:
                # Mostrar un Toast discreto para avisar que es su última venta
                ToastBroadcast(win, "⚠️ SU CAJA FUE CERRADA. Por favor, finalice este ticket actual. No podrá realizar nuevas ventas.")

    # Iniciar ciclo de polling de caja
    win.after(10000, polling_estado_caja)

    # VALIDADORES
    def validar_len_30(t): return len(t) <= 30
    def validar_cantidad(t):
        if t == "": return True
        if len(t) > 5: return False
        return bool(re.match(r'^[0-9]{0,4}[.,]?[0-9]{0,3}$', t))
    
    vc_30 = (win.register(validar_len_30), '%P')
    vc_cantidad = (win.register(validar_cantidad), '%P')

    items = []
    cliente_sel = None
    total_venta = 0.0 

    # ==================================
    # ESTRUCTURA LAYOUT CTK
    # ==================================
    frm_header = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_width=1, border_color=col_border)
    frm_header.pack(fill="x", padx=25, pady=(25, 10))

    frm_inputs = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_width=1, border_color=col_border)
    frm_inputs.pack(fill="x", padx=25, pady=10)
    
    frm_footer = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_width=1, border_color=col_border)
    frm_footer.pack(side="bottom", fill="x", padx=25, pady=(10, 25))
    
    frm_lista = ctk.CTkFrame(win, fg_color=col_card, corner_radius=10, border_width=1, border_color=col_border)
    frm_lista.pack(fill="both", expand=True, padx=25, pady=10)

    # 1. HEADER CLIENTE
    ctk.CTkLabel(frm_header, text="👤 Cliente Actual:", font=font_title, text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white").pack(side="left", padx=20, pady=20)
    
    lbl_cliente = ctk.CTkLabel(frm_header, text="(Consumidor Final)", font=("Segoe UI", 12), text_color="#6b7280")
    lbl_cliente.pack(side="left")
    
    def abrir_selector_cliente():
        nonlocal cliente_sel
        popup = ctk.CTkToplevel(win)
        popup.title("Seleccionar Cliente")
        popup.geometry("750x650")
        preparar_ventana(popup)
        popup.resizable(False, False)
        
        frm_bus = ctk.CTkFrame(popup, fg_color="transparent")
        frm_bus.pack(fill="x", padx=25, pady=(25, 10))
        
        ctk.CTkLabel(frm_bus, text="🔎 Buscar cliente:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).pack(side="left")
        var_bus = tk.StringVar()
        ent_bus = ctk.CTkEntry(frm_bus, textvariable=var_bus, font=("Segoe UI", 13), width=450, height=40, placeholder_text="Nombre o DNI...")
        ent_bus.pack(side="left", padx=20)
        ent_bus.focus_set()
        
        frm_tree_cont = ctk.CTkFrame(popup, fg_color=get_color("bg_surface"), corner_radius=10, border_width=1, border_color=get_color("border_color"))
        frm_tree_cont.pack(fill="both", expand=True, padx=25, pady=10)
        
        cols = ("ID", "Nombre", "DNI")
        configurar_estilo_treeview()
        tree_c = ttk.Treeview(frm_tree_cont, columns=cols, show="headings", height=8, style="Modern.Treeview")
        tree_c.column("ID", width=0, stretch=False)
        tree_c.configure(displaycolumns=("Nombre", "DNI"))
        
        sc_c = ctk.CTkScrollbar(frm_tree_cont, command=tree_c.yview)
        sc_c.pack(side="right", fill="y", padx=(0, 5), pady=5)
        tree_c.configure(yscrollcommand=sc_c.set)
        tree_c.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        for c in cols: tree_c.heading(c, text=c)
        tree_c.column("ID", width=80, anchor="center"); tree_c.column("Nombre", width=400); tree_c.column("DNI", width=150, anchor="center")
        
        todos_clis = backend.listar_clientes()
        
        def filtrar(*_):
            for i in tree_c.get_children(): tree_c.delete(i)
            q = var_bus.get().lower()
            for c in todos_clis:
                dni = c.get('dni') or "-"
                if q in c['nombre'].lower() or q in str(dni):
                    tree_c.insert("", tk.END, values=(c['id_cliente'], c['nombre'], dni))
            hijos = tree_c.get_children()
            if hijos: tree_c.selection_set(hijos[0])
        
        var_bus.trace_add("write", filtrar)
        filtrar()
        
        def seleccionar(event=None):
            nonlocal cliente_sel
            sel = tree_c.selection()
            if not sel: return
            cid = int(tree_c.item(sel[0], "values")[0])
            cliente_sel = next((c for c in todos_clis if c['id_cliente'] == cid), None)
            _upd_cliente()
            popup.destroy()
        
        tree_c.bind("<Double-1>", seleccionar)
        tree_c.bind("<Return>", seleccionar)
        
        fr_btns = ctk.CTkFrame(popup, fg_color="transparent")
        fr_btns.pack(fill="x", padx=25, pady=20)
        
        def limpiar_cliente():
            nonlocal cliente_sel
            cliente_sel = None
            _upd_cliente()
            popup.destroy()
        
        ctk.CTkButton(fr_btns, text="✓ Seleccionar", fg_color=get_color("button_primary"), hover_color=get_color("button_primary_hover"),
                      font=("Segoe UI", 13, "bold"), height=45, command=seleccionar).pack(side="left", padx=5)
        
        def abrir_nuevo_cliente_popup():
            if ui_crear_cliente:
                def al_guardar_cliente(nuevo_id=None):
                    nonlocal todos_clis, cliente_sel
                    todos_clis = backend.listar_clientes()
                    filtrar()
                    if nuevo_id and isinstance(nuevo_id, int):
                        new_cli = next((c for c in todos_clis if c['id_cliente'] == nuevo_id), None)
                        if new_cli:
                            cliente_sel = new_cli
                            _upd_cliente()
                            popup.destroy()
                ui_crear_cliente(popup, backend, callback_on_save=al_guardar_cliente)

        def abrir_creacion_cliente_autorizado():
            if usuario.get('id_rol') in (1, 3):  # Admin o Supervisor → acceso directo
                abrir_nuevo_cliente_popup()
            else:  # Vendedor → pedir credenciales de administrador
                def on_autorizado(usr_autorizado):
                    abrir_nuevo_cliente_popup()
                solicitar_autorizacion_supervisor(popup, backend, usuario, on_autorizado)

        ctk.CTkButton(fr_btns, text="➕ Nuevo", fg_color=get_color("secondary") if hasattr(get_color, 'secondary') else "#10b981", 
                      font=("Segoe UI", 13, "bold"), height=45, command=abrir_creacion_cliente_autorizado).pack(side="left", padx=5)
        
        ctk.CTkButton(fr_btns, text="Consumidor Final", fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"),
                      font=("Segoe UI", 13), height=45, command=limpiar_cliente).pack(side="left", padx=5)
        
        configurar_navegacion_ventana(popup)
        popup.after(100, lambda: ent_bus.focus_set())
        centrar_y_mostrar_ventana(popup)
        popup.grab_set()

    def quitar_cliente():
        nonlocal cliente_sel
        cliente_sel = None
        _upd_cliente()

    def _upd_cliente():
        if cliente_sel:
            lbl_cliente.configure(text=f"{cliente_sel.get('nombre','')} (ID: {cliente_sel.get('id_cliente','')})", text_color="#1f2937" if ctk.get_appearance_mode()=="Light" else "white", font=("Segoe UI", 12, "bold"))
        else:
            lbl_cliente.configure(text="(Consumidor Final)", text_color="#6b7280", font=("Segoe UI", 12, "normal"))

    # Botones cliente
    ctk.CTkButton(frm_header, text="🔍 Cambiar", font=font_title, fg_color="#3b82f6", width=120, height=45, command=abrir_selector_cliente).pack(side="right", padx=(10, 20))
    btn_no_cli = ctk.CTkButton(frm_header, text="❌ Quitar", font=font_normal, fg_color="#ef4444", width=80, height=45, command=quitar_cliente)
    btn_no_cli.pack(side="right")

    # 2. INPUTS
    ctk.CTkLabel(frm_inputs, text="Cant.", font=font_title, text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white").pack(side="left", padx=(20, 10), pady=20)
    
    entry_cantidad = ctk.CTkEntry(frm_inputs, font=font_big, width=100, height=45, justify="center")
    entry_cantidad.configure(validate="key", validatecommand=vc_cantidad)
    entry_cantidad.insert(0, "1")
    entry_cantidad.pack(side="left", padx=10)
    
    # Forzar el foco directo al producto (evita que la etiqueta u otros elementos tomen foco intermedio)
    entry_cantidad.bind("<Tab>", lambda e: "break" if entry_producto.focus_set() or True else "break")
    
    ctk.CTkLabel(frm_inputs, text="Código o Producto:", font=font_title, text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white").pack(side="left", padx=(30, 10))
    
    entry_producto = ctk.CTkEntry(frm_inputs, font=font_normal, height=45, placeholder_text="Escanee código o busque producto...")
    entry_producto.configure(validate="key", validatecommand=vc_30)
    entry_producto.pack(side="left", fill="x", expand=True, padx=10)
    
    popup_sugerencias = None
    listbox_sugerencias = None
    sugerencias_activas = []
    _debounce_id = None
    
    btn_agregar = ctk.CTkButton(frm_inputs, text="+ Agregar", font=font_title, fg_color="#10b981", hover_color="#059669", width=120, height=45)
    btn_agregar.pack(side="left", padx=20)

    def abrir_creacion_producto_autorizado():
        def abrir_con_usuario(usr):
            if ui_productos:
                ui_productos(
                    parent=win,
                    backend=backend,
                    usuario=usr,
                    id_producto_a_cargar=None,
                    callback_on_save=lambda: messagebox.showinfo("Éxito", "Producto cargado. Ya puede escanearlo.", parent=win)
                )
            else:
                messagebox.showerror("Error", "Módulo de productos no disponible", parent=win)

        if usuario.get('id_rol') == 1:
            abrir_con_usuario(usuario)
        else:
            solicitar_autorizacion_supervisor(win, backend, usuario, abrir_con_usuario)

    btn_nuevo_producto = ctk.CTkButton(frm_inputs, text="🔓 Nuevo Prod.", font=font_normal, fg_color="#f59e0b", hover_color="#d97706", width=130, height=45, command=abrir_creacion_producto_autorizado)
    btn_nuevo_producto.pack(side="left", padx=5)

    # 3. LISTA
    # (Ya configurado al inicio de la función)
    
    cols = ("ID", "Producto", "Precio", "Cant", "Subtotal")
    tree = ttk.Treeview(frm_lista, columns=cols, show="headings", style="Modern.Treeview")
    tree.column("ID", width=0, stretch=False)
    tree.configure(displaycolumns=("Producto", "Precio", "Cant", "Subtotal"))
    tree.column("Producto", width=500, anchor="w")
    tree.column("Precio", width=150, anchor="e")
    tree.column("Cant", width=100, anchor="center")
    tree.column("Subtotal", width=150, anchor="e")
    
    tree.heading("ID", text="ID")
    tree.heading("Producto", text="DESCRIPCIÓN")
    tree.heading("Precio", text="PRECIO UNIT.")
    tree.heading("Cant", text="CANT.")
    tree.heading("Subtotal", text="SUBTOTAL")
    
    vsb = ctk.CTkScrollbar(frm_lista, command=tree.yview)
    vsb.pack(side="right", fill="y", padx=(0, 5), pady=5)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)

    # 4. FOOTER
    btn_cancelar = ctk.CTkButton(frm_footer, text="🗑️ Cancelar", fg_color="#ef4444", hover_color="#dc2626", font=font_title, width=150, height=55)
    btn_cancelar.pack(side="left", padx=20, pady=20)

    btn_quitar = ctk.CTkButton(frm_footer, text="➖ Quitar Ítem", fg_color="#f59e0b", hover_color="#d97706", font=font_title, width=150, height=55)
    btn_quitar.pack(side="left", padx=(0, 20), pady=20)

    btn_confirmar = ctk.CTkButton(frm_footer, text="💳 COBRAR (F12)", fg_color="#10b981", hover_color="#059669", font=font_big, width=250, height=65)
    btn_confirmar.pack(side="right", padx=20, pady=20)

    lbl_total_monto = ctk.CTkLabel(frm_footer, text="$ 0.00", font=("Segoe UI", 48, "bold"), text_color="#111827" if ctk.get_appearance_mode()=="Light" else "white")
    lbl_total_monto.pack(side="right", padx=30)
    
    ctk.CTkLabel(frm_footer, text="TOTAL:", font=("Segoe UI", 18, "bold"), text_color="#6b7280").pack(side="right", padx=0)

    
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
            if win.winfo_exists():
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
                popup_sugerencias = ctk.CTkToplevel(win)
                popup_sugerencias.withdraw()  # Ocultar inicialmente
                popup_sugerencias.overrideredirect(True)  # Sin bordes de ventana
                popup_sugerencias.config(bg="#1e293b", relief="solid", bd=1)
                
                listbox_sugerencias = tk.Listbox(
                    popup_sugerencias,
                    height=min(8, len(sugerencias_activas)),
                    width=55,
                    font=("Segoe UI", 10),
                    selectmode=tk.SINGLE,
                    relief="flat",
                    bg="#1e293b",
                    fg="#e2e8f0",
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
            
            # Mostrar el nombre del producto en el Entry (no el ID interno)
            entry_producto.delete(0, tk.END)
            entry_producto.insert(0, prod.get('nombre', ''))
            
            # Ocultar sugerencias
            ocultar_sugerencias()
            
            # Agregar directamente pasando el producto ya resuelto
            agregar_producto(prod_preseleccionado=prod)
    
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
        if not win.winfo_exists():
            return
        try:
            for i in tree.get_children(): tree.delete(i)
        except tk.TclError:
            return
        
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
            
        lbl_total_monto.configure(text=f"$ {total_venta:,.2f}")

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

    btn_quitar.configure(command=quitar_seleccion)
    tree.bind("<Delete>", quitar_seleccion)
    
    def _reiniciar_venta_completa():
        nonlocal items, cliente_sel, total_venta
        items.clear(); cliente_sel = None; total_venta = 0.0
        _refrescar_lista(); _upd_cliente()     
        entry_producto.delete(0, tk.END); entry_cantidad.delete(0, tk.END)
        entry_cantidad.insert(0, "1")
        # 🔥 FOCO EN PRODUCTO (lectura continua optimizada)
        entry_producto.focus_set()

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
    
    def agregar_producto(prod_preseleccionado=None):
        if caja_cerrada_remotamente and not items:
            verificar_expulsion()
            return
            
        token = entry_producto.get().strip()
        if not token and not prod_preseleccionado:
            messagebox.showwarning("Atención", "Ingrese un código.", parent=win); return
        
        # 🔥 Ocultar sugerencias antes de agregar
        ocultar_sugerencias()
        
        prod = prod_preseleccionado or _resolver_producto(token)
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
        # 🔥 VOLVER A PRODUCTO (lectura continua optimizada)
        entry_producto.focus_set()

    btn_agregar.configure(command=agregar_producto)
    
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
            elif "Stock insuficiente" in str(ve):
                messagebox.showwarning(
                    "⚠️ Stock Insuficiente", 
                    f"No se pudo completar la venta debido a un cambio en el inventario:\n\n{ve}",
                    parent=win
                )
            else:
                messagebox.showerror("Error", f"Venta revertida.\n{ve}", parent=win)
            return
        except Exception as e:
            messagebox.showerror("Error", f"Venta revertida.\n{e}", parent=win); return

        try:
            from app.frontend.custom_dialogs import mostrar_confirmacion_exito
            imprimir = mostrar_confirmacion_exito(
                "✅ Venta Registrada", 
                f"Venta #{id_venta} registrada con éxito.\nTotal: ${total_venta:,.2f}\n\n¿Desea imprimir el ticket?",
                parent=win
            )
        except Exception as e:
            print(f"Error en diálogo de confirmación: {e}")
            imprimir = False

        if imprimir in (True, 'yes', 'True', '1'):
            try:
                imprimir_ticket(id_venta=id_venta, items_de_la_venta=items, nombre_vendedor=usuario.get("nombre", "Vendedor"), 
                                metodo_pago=info_pago['tipo_pago'], monto_entregado=info_pago.get('monto_pagado', 0.0), 
                                vuelto=info_pago.get('vuelto', 0.0), cliente=cliente_sel.get('nombre', 'Consumidor Final') if cliente_sel else 'Consumidor Final')
            except Exception as e:
                messagebox.showerror("Error", f"Error Impresión: {e}", parent=win)

        _reiniciar_venta_completa()
        if win.winfo_exists():
            win.after(100, lambda: stock_events.notificar_cambio_stock())
            win.after(200, verificar_expulsion)

    def cancelar_venta():
        if items:
            if not messagebox.askyesno("Confirmar", "Hay productos en el carrito.\n¿Seguro que desea cancelar la venta?", parent=win):
                return
        win.destroy()

    btn_confirmar.configure(command=confirmar_venta)
    btn_cancelar.configure(command=cancelar_venta)

    _upd_cliente()
    
    def enfocar_cantidad(event=None):
        entry_cantidad.focus_set()
        entry_cantidad.select_range(0, tk.END)
        return "break"

    win.bind("<F2>", lambda e: abrir_selector_cliente())
    win.bind("<F12>", lambda e: confirmar_venta())
    win.bind("<Escape>", lambda e: cancelar_venta())
    win.bind("<F5>", enfocar_cantidad)
    
    configurar_navegacion_ventana(win)
    # 🔥 FOCO INICIAL EN PRODUCTO (lectura continua optimizada)
    win.after(50, lambda: entry_producto.focus_set())
    if win.state() == 'zoomed':
        win.deiconify()
    else:
        centrar_y_mostrar_ventana(win)
    win.grab_set()