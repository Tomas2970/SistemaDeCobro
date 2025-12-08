# ============================================
# app/frontend/interfaz_venta.py
# 🎨 ACTUALIZADO: Estilo de botones unificado
# ============================================
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, Toplevel, ttk, Listbox, SINGLE
from typing import Any


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


def ui_venta(parent: tk.Misc, backend, usuario: dict) -> None:
    win = tk.Toplevel(parent)
    win.title("Punto de Venta - Supermercado Don Atilio")
    win.geometry("1000x700") 
    win.config(bg="#f4f4f8")
    win.resizable(True, True) 

    # 🔥 Estilos modernos para Treeview
    style = ttk.Style()
    style.theme_use('clam')
    
    # Estilo para el Treeview
    style.configure("Modern.Treeview",
                    background="#ffffff",
                    foreground="#1f2937",
                    rowheight=32,
                    fieldbackground="#ffffff",
                    borderwidth=0,
                    font=('Segoe UI', 10))
    
    # Estilo para los encabezados (más sutil y moderno)
    style.configure("Modern.Treeview.Heading",
                    background="#f3f4f6",
                    foreground="#374151",
                    relief="flat",
                    borderwidth=1,
                    font=('Segoe UI', 10, 'bold'))
    
    style.map("Modern.Treeview.Heading",
              background=[('active', '#e5e7eb')])
    
    # Colores alternados para filas
    style.map('Modern.Treeview',
              background=[('selected', '#3b82f6')],
              foreground=[('selected', 'white')])

    # --- Validadores ---
    def validar_len_30(t): return len(t) <= 30
    def validar_len_10(t): return len(t) <= 10
    
    vc_30 = (win.register(validar_len_30), '%P')
    vc_10 = (win.register(validar_len_10), '%P')

    items: list[tuple[int | None, str, int, float, str]] = []
    cliente_sel: dict[str, Any] | None = None
    total_venta: float = 0.0 

    # ================================================================
    # ESTRUCTURA DE LAYOUT (FRAMES)
    # ================================================================
    
    # 1. HEADER (Cliente)
    frm_header = tk.Frame(win, bg="#ffffff", pady=12, padx=15, relief="flat", bd=0)
    frm_header.pack(fill="x", padx=10, pady=(10, 5))

    # 2. INPUTS (Producto y Cantidad)
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
        sel = Toplevel(win)
        sel.title("Seleccionar Cliente")
        sel.geometry("500x450")
        sel.config(bg="#f4f4f8")
        
        configurar_navegacion_ventana(sel)
        
        tk.Label(sel, text="Buscar (nombre o DNI):", bg="#f4f4f8", font=("Segoe UI", 10)).pack(pady=(10,5))
        var_pat = tk.StringVar()
        ent = tk.Entry(sel, textvariable=var_pat, width=40, font=("Segoe UI", 10))
        ent.pack(pady=5)
        
        frame_list = tk.Frame(sel)
        frame_list.pack(expand=True, fill="both", padx=15, pady=5)
        sc = tk.Scrollbar(frame_list)
        sc.pack(side="right", fill="y")
        lst = Listbox(frame_list, selectmode=SINGLE, yscrollcommand=sc.set, width=50, height=12, font=("Segoe UI", 10))
        lst.pack(side="left", fill="both", expand=True)
        sc.config(command=lst.yview)
        
        data = backend.listar_clientes() 

        def render(filas):
            lst.delete(0, tk.END)
            for c in filas:
                dni_texto = c.get('dni') or "-"
                lst.insert(tk.END, f"{c.get('id_cliente','')} | {c.get('nombre','')} | DNI: {dni_texto}")
        render(data)

        def filtrar(*_):
            q = var_pat.get().strip()
            if q.isdigit():
                c = backend.buscar_cliente_por_dni(q)
                render([c] if c else [])
            else:
                render(backend.buscar_cliente_por_nombre(q) if q else data)
        var_pat.trace_add("write", lambda *_: filtrar())

        def tomar(event=None): 
            nonlocal cliente_sel
            sel_idx = lst.curselection()
            if not sel_idx: return 
            rid = int(lst.get(sel_idx[0]).split("|")[0].strip())
            cliente_sel = next((c for c in data if int(c.get("id_cliente",-1))==rid), None)
            _upd_cliente()
            sel.destroy()

        lst.bind("<Double-1>", tomar)
        lst.bind("<Return>", tomar)

        btn_frm = tk.Frame(sel, bg="#f4f4f8")
        btn_frm.pack(pady=10)
        
        # 🔥 BOTONES ESTILO NUEVO
        btn_sel = tk.Button(btn_frm, text="✓ Seleccionar", command=tomar, 
                           bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"),
                           relief="flat", padx=20, pady=8, cursor="hand2",
                           activebackground="#059669", activeforeground="white")
        btn_sel.pack(side="left", padx=5)
        
        btn_canc = tk.Button(btn_frm, text="Cancelar", command=sel.destroy,
                            bg="#6b7280", fg="white", font=("Segoe UI", 10),
                            relief="flat", padx=15, pady=8, cursor="hand2",
                            activebackground="#4b5563", activeforeground="white")
        btn_canc.pack(side="left", padx=5)
        
        sel.after(100, lambda: ent.focus_set())
        sel.grab_set()
        sel.transient(win)

    def quitar_cliente():
        nonlocal cliente_sel; cliente_sel = None; _upd_cliente()

    def _upd_cliente():
        if cliente_sel:
            lbl_cliente.config(text=f"{cliente_sel.get('nombre','')} (ID: {cliente_sel.get('id_cliente','')})", 
                             fg="#1f2937", font=("Segoe UI", 11, "bold"))
        else:
            lbl_cliente.config(text="(Consumidor Final)", fg="#6b7280", font=("Segoe UI", 11, "normal"))

    # 🔥 BOTONES ESTILO NUEVO (Cliente)
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
    # 2. SECCIÓN INPUTS
    # ================================================================
    tk.Label(frm_inputs, text="Código / Nombre:", bg="#f4f4f8", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
    
    entry_producto = tk.Entry(frm_inputs, width=30, font=("Segoe UI", 11), validate="key", validatecommand=vc_30)
    entry_producto.pack(side="left", padx=5)
    
    tk.Label(frm_inputs, text="Cant:", bg="#f4f4f8", font=("Segoe UI", 10)).pack(side="left", padx=(15, 5))
    
    entry_cantidad = tk.Entry(frm_inputs, width=8, font=("Segoe UI", 11), justify="center", validate="key", validatecommand=vc_10)
    entry_cantidad.insert(0, "1")
    entry_cantidad.pack(side="left", padx=5)
    
    # 🔥 BOTÓN AGREGAR ESTILO NUEVO
    btn_agregar = tk.Button(frm_inputs, text="+ Agregar", 
                           bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"),
                           relief="flat", padx=20, pady=8, cursor="hand2",
                           activebackground="#059669", activeforeground="white")
    btn_agregar.pack(side="left", padx=10)

    # ================================================================
    # 3. LISTA (TREEVIEW) - 🔥 ESTILO MODERNO
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
    
    # Lado Izquierdo: Botones secundarios
    # 🔥 BOTÓN QUITAR ESTILO NUEVO
    btn_quitar = tk.Button(frm_footer, text="🗑️ Quitar Seleccionado", 
                          bg="#f3f4f6", fg="#ef4444", font=("Segoe UI", 9, "bold"),
                          relief="flat", padx=15, pady=8, cursor="hand2",
                          activebackground="#e5e7eb", activeforeground="#dc2626")
    btn_quitar.pack(side="left")

    # Lado Derecho: Total y Confirmar
    frame_totales = tk.Frame(frm_footer, bg="#f4f4f8")
    frame_totales.pack(side="right")

    lbl_total_titulo = tk.Label(frame_totales, text="TOTAL A PAGAR:", font=("Segoe UI", 12), bg="#f4f4f8", fg="#6b7280")
    lbl_total_titulo.pack(side="left", padx=5)
    
    lbl_total_monto = tk.Label(frame_totales, text="$ 0.00", font=("Segoe UI", 24, "bold"), bg="#f4f4f8", fg="#059669")
    lbl_total_monto.pack(side="left", padx=10)

    # 🔥 BOTONES PRINCIPALES ESTILO NUEVO
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
    # LÓGICA
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
        entry_cantidad.insert(0, "1"); entry_producto.focus_set()

    def manejar_escaneo_producto(event=None):
        token = entry_producto.get().strip()
        if not token:
            messagebox.showwarning("Atención", "Ingrese un código, ID o nombre.", parent=win)
            return
        prod = _resolver_producto(token)
        if not prod:
            messagebox.showwarning("No encontrado", "No se encontró el producto.", parent=win)
            return
        
        es_pesable = bool(prod.get("es_pesable", False))
        if es_pesable:
            entry_cantidad.delete(0, tk.END)
            entry_cantidad.focus_set()
            entry_producto.config(bg="#fff3cd")
            win.after(500, lambda: entry_producto.config(bg="white"))
            return
        
        agregar_producto()
    
    entry_producto.bind("<Return>", manejar_escaneo_producto)
    
    def agregar_producto():
        token = entry_producto.get().strip()
        if not token:
            messagebox.showwarning("Atención", "Ingrese un código.", parent=win); return
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
        entry_producto.focus_set()

    btn_agregar.config(command=agregar_producto)
    entry_cantidad.bind("<Return>", lambda e: agregar_producto())
    
    def confirmar_venta():
        if not items:
            messagebox.showwarning("Atención", "Carrito vacío.", parent=win); return
        
        info_pago = mostrar_ventana_pago(parent=win, total_venta=total_venta, cliente_seleccionado=(cliente_sel is not None))
        if info_pago is None: return

        tipo_pago = info_pago['tipo_pago']

        if tipo_pago == 'efectivo':
            try:
                id_usuario = usuario.get("id_usuario") or usuario.get("id", 0) 
                caja_abierta = backend.obtener_session_abierta(id_usuario=id_usuario)
                
                if not caja_abierta:
                    messagebox.showwarning(
                        "⚠️ Caja Cerrada", 
                        "No se puede registrar una venta en EFECTIVO sin abrir la caja primero.", 
                        parent=win
                    )
                    return 
            except Exception as e:
                messagebox.showerror("Error", f"Error verificación caja: {e}", parent=win); return

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

        try:
            id_venta = backend.registrar_venta_completa(id_usuario=id_usuario, id_cliente=id_cliente, items=items, tipo_pago=tipo_pago)
            if not id_venta:
                messagebox.showerror("Error", "ID de venta nulo.", parent=win); return
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
    win.after(50, lambda: entry_producto.focus_set())
    win.grab_set()