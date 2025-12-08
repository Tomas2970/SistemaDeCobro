# app/frontend/interfaz_compra.py
# 🎨 ACTUALIZADO: Estilo de botones unificado
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Listbox
from typing import Any

try:
    from app.frontend.componentes_ui import EntryDecimal
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass
    class EntryDecimal(tk.Entry): pass

try:
    from app.frontend.stock_event_manager import stock_events
except ImportError:
    class DummyStockEvents:
        def notificar_cambio_stock(self): pass
    stock_events = DummyStockEvents()

def ui_compra(parent: tk.Misc, backend, usuario: dict):
    
    win = tk.Toplevel(parent)
    win.title("Registrar Compra (Entrada de Mercadería)")
    win.geometry("1050x700") 
    win.config(bg="#f4f4f8")
    
    # 🔥 ESTILOS MODERNOS
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
    
    proveedor_sel: dict | None = None
    carrito: list[dict] = [] 
    
    try:
        categorias_cache = backend.obtener_categorias()
    except:
        categorias_cache = []

    def obtener_margen(id_cat):
        for c in categorias_cache:
            if c['id_categoria'] == id_cat:
                return float(c.get('margen_ganancia', 30.0))
        return 30.0

    # =================================================================
    # 1. SECCIÓN SUPERIOR: PROVEEDOR
    # =================================================================
    frame_top = tk.Frame(win, bg="#ffffff", pady=15, padx=15)
    frame_top.pack(fill=tk.X, padx=10, pady=(10, 5))

    tk.Label(frame_top, text="Proveedor:", bg="#ffffff", font=("Segoe UI", 11, "bold"), fg="#1f2937").pack(side=tk.LEFT)
    lbl_proveedor = tk.Label(frame_top, text="(Ninguno seleccionado)", fg="#6b7280", bg="#ffffff", font=("Segoe UI", 11), padx=10)
    lbl_proveedor.pack(side=tk.LEFT, padx=10)

    def seleccionar_proveedor():
        nonlocal proveedor_sel
        popup = tk.Toplevel(win)
        popup.title("Seleccionar Proveedor")
        popup.geometry("700x500")
        popup.config(bg="#f4f4f8")
        
        frm_busqueda = tk.Frame(popup, bg="#f4f4f8", pady=10)
        frm_busqueda.pack(fill=tk.X, padx=10)
        
        tk.Label(frm_busqueda, text="🔍 Buscar:", font=("Segoe UI", 10, "bold"), bg="#f4f4f8").pack(side=tk.LEFT, padx=5)
        var_buscar = tk.StringVar()
        entry_buscar = tk.Entry(frm_busqueda, textvariable=var_buscar, font=("Segoe UI", 10), width=40)
        entry_buscar.pack(side=tk.LEFT, padx=5)
        entry_buscar.focus_set()
        
        frm_lista = tk.Frame(popup, bg="#f4f4f8")
        frm_lista.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scroll = ttk.Scrollbar(frm_lista)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        lst = tk.Listbox(frm_lista, font=("Segoe UI", 10), yscrollcommand=scroll.set, width=90)
        lst.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=lst.yview)
        
        provs = backend.obtener_proveedores(incluir_inactivos=False)
        proveedores_texto = []
        
        for p in provs:
            estado = "" if p['activo'] else " (Inactivo)"
            empresa = f"{p.get('empresa', '-')}"
            dni_cuit = f"{p.get('dni_cuit', '-')}"
            texto = f"{p['id_proveedor']} | {p['nombre'].ljust(20)} | DNI/CUIT: {dni_cuit.ljust(15)} | Empresa: {empresa}{estado}"
            proveedores_texto.append(texto)
        
        def filtrar_proveedores(*args):
            lst.delete(0, tk.END)
            texto_busqueda = var_buscar.get().strip().lower()
            
            if not texto_busqueda:
                for texto in proveedores_texto: lst.insert(tk.END, texto)
            else:
                for texto in proveedores_texto:
                    if texto_busqueda in texto.lower(): lst.insert(tk.END, texto)
            
            if lst.size() > 0: lst.selection_set(0)
        
        var_buscar.trace_add("write", filtrar_proveedores)
        filtrar_proveedores()
        
        def confirmar():
            nonlocal proveedor_sel
            sel = lst.curselection()
            if not sel:
                messagebox.showwarning("Atención", "Seleccione un proveedor.", parent=popup)
                return
            
            texto_seleccionado = lst.get(sel[0])
            try:
                id_prov = int(texto_seleccionado.split(" | ")[0].strip()) 
            except:
                messagebox.showerror("Error", "No se pudo identificar el proveedor.", parent=popup)
                return
            
            prov_data = next((p for p in provs if p['id_proveedor'] == id_prov), None)
            
            if not prov_data: return
            if not prov_data['activo']:
                messagebox.showwarning("Atención", "No se puede registrar compras a un proveedor inactivo.", parent=popup)
                return

            proveedor_sel = prov_data
            texto_prov = proveedor_sel['nombre']
            if proveedor_sel.get('empresa'): texto_prov += f" - {proveedor_sel['empresa']}"
            
            lbl_proveedor.config(text=texto_prov, fg="#1f2937", font=("Segoe UI", 11, "bold"))
            btn_add_prod.config(state="normal") 
            popup.destroy()

        lst.bind("<Double-1>", lambda e: confirmar())
        lst.bind("<Return>", lambda e: confirmar())
        entry_buscar.bind("<Return>", lambda e: confirmar())
        
        frm_botones = tk.Frame(popup, bg="#f4f4f8", pady=10)
        frm_botones.pack(fill=tk.X)
        
        # 🔥 BOTONES ESTILO NUEVO
        tk.Button(
            frm_botones, 
            text="✓ Seleccionar", 
            command=confirmar, 
            bg="#10b981", 
            fg="white", 
            font=("Segoe UI", 10, "bold"), 
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            activebackground="#059669",
            width=20
        ).pack(pady=5)
        
        tk.Button(
            frm_botones, 
            text="Cancelar", 
            command=popup.destroy, 
            font=("Segoe UI", 10),
            bg="#6b7280",
            fg="white",
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2",
            activebackground="#4b5563",
            width=20
        ).pack()
        
        configurar_navegacion_ventana(popup)

    # 🔥 BOTÓN BUSCAR PROVEEDOR
    tk.Button(
        frame_top, 
        text="🔍 Buscar Proveedor", 
        command=seleccionar_proveedor, 
        bg="#3b82f6", 
        fg="white", 
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        padx=20,
        pady=8,
        cursor="hand2",
        activebackground="#2563eb"
    ).pack(side=tk.LEFT)

    # =================================================================
    # 2. GRILLA
    # =================================================================
    frame_grilla = tk.Frame(win, bg="#f4f4f8")
    frame_grilla.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    cols = ("ID", "Producto", "Cantidad", "Costo Unit.", "Subtotal", "Precio Venta Nuevo")
    tree = ttk.Treeview(frame_grilla, columns=cols, show="headings", style="Modern.Treeview")
    
    tree.column("ID", width=50, anchor="center")
    tree.column("Producto", width=300)
    tree.column("Cantidad", width=80, anchor="e")    
    tree.column("Costo Unit.", width=100, anchor="e") 
    tree.column("Subtotal", width=100, anchor="e")
    tree.column("Precio Venta Nuevo", width=120, anchor="e") 

    for c in cols: tree.heading(c, text=c)

    vsb = ttk.Scrollbar(frame_grilla, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)

    frame_totales = tk.Frame(win, bg="#f4f4f8")
    frame_totales.pack(fill=tk.X, padx=20, pady=5)
    lbl_total = tk.Label(frame_totales, text="TOTAL: $ 0.00", font=("Segoe UI", 16, "bold"), bg="#f4f4f8", fg="#dc2626")
    lbl_total.pack(side=tk.RIGHT)

    def repintar_tabla():
        for i in tree.get_children(): tree.delete(i)
        total_gral = 0.0
        for idx, item in enumerate(carrito):
            subtotal = item['cant'] * item['costo']
            total_gral += subtotal
            cant_str = f"{item['cant']:.3f}" if item['cant'] % 1 != 0 else f"{int(item['cant'])}"
            tree.insert("", tk.END, iid=str(idx), values=(
                item['id'], item['nombre'], cant_str,
                f"$ {item['costo']:.2f}", f"$ {subtotal:.2f}", f"$ {item['precio_venta']:.2f}"
            ))
        lbl_total.config(text=f"TOTAL: $ {total_gral:,.2f}")

    def editar_celda(row_id, col_id):
        try:
            idx = int(row_id)
            item = carrito[idx]
        except (ValueError, IndexError): return

        col_map = {'#3': 'cant', '#4': 'costo', '#6': 'precio_venta'}
        if col_id not in col_map: return

        campo = col_map[col_id]
        try:
            x, y, w, h = tree.bbox(row_id, col_id)
            if w == 0: return 
        except Exception: return

        valor_actual = item[campo]
        
        if campo == 'cant':
            try: from app.frontend.componentes_ui import EntryDecimal as CustomEntry
            except: CustomEntry = ttk.Entry
            entry = CustomEntry(tree)
        elif campo in ('costo', 'precio_venta'):
            try: from app.frontend.componentes_ui import EntryDecimal as CustomEntry
            except: CustomEntry = ttk.Entry
            entry = CustomEntry(tree)
        else:
            entry = ttk.Entry(tree)

        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, str(valor_actual))
        entry.select_range(0, tk.END)
        entry.focus_set()

        def confirmar_y_saltar(e=None):
            try:
                val = float(entry.get())
                if val < 0: raise ValueError
                item[campo] = val
                
                if campo == 'costo':
                    margen = item.get('margen', 30.0)
                    item['precio_venta'] = val * (1 + margen/100)

                entry.destroy()
                repintar_tabla()
                
                orden = ['#3', '#4', '#6']
                try:
                    curr_idx = orden.index(col_id)
                    if curr_idx < len(orden) - 1:
                        next_col = orden[curr_idx + 1]
                        win.after(10, lambda: editar_celda(row_id, next_col))
                    else:
                        next_row_idx = int(row_id) + 1
                        if next_row_idx < len(carrito):
                            win.after(10, lambda: editar_celda(str(next_row_idx), '#3'))
                except ValueError: pass

            except ValueError:
                messagebox.showwarning("Error", "Valor inválido", parent=win)
                entry.focus_set()

        entry.bind("<Return>", confirmar_y_saltar)
        entry.bind("<Tab>", confirmar_y_saltar)
        entry.bind("<Escape>", lambda e: entry.destroy())
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    def on_click(event):
        region = tree.identify("region", event.x, event.y)
        if region == "cell":
            col = tree.identify_column(event.x)
            row = tree.identify_row(event.y)
            if row: editar_celda(row, col)

    tree.bind("<Double-1>", on_click)

    def abrir_selector_producto():
        if not proveedor_sel: return
        popup = Toplevel(win)
        popup.title("Agregar Producto al Carrito")
        popup.geometry("500x450")
        popup.config(bg="#f4f4f8")
        
        tk.Label(popup, text="Buscar producto:", bg="#f4f4f8", font=("Segoe UI", 10)).pack(pady=5)
        var_bus = tk.StringVar()
        ent_bus = tk.Entry(popup, textvariable=var_bus, font=("Segoe UI", 10), width=40)
        ent_bus.pack(fill=tk.X, padx=10)
        ent_bus.focus_set()

        lst = Listbox(popup, height=15, font=("Segoe UI", 10))
        lst.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        todos_prods = backend.obtener_productos_por_proveedor(proveedor_sel['id_proveedor'])
        
        def filtrar(*_):
            lst.delete(0, tk.END)
            q = var_bus.get().lower()
            for p in todos_prods:
                txt = f"{p['id_producto']} | {p['nombre']}"
                if q in txt.lower(): lst.insert(tk.END, txt)
        var_bus.trace_add("write", filtrar)
        filtrar()

        def agregar_al_carrito():
            sel = lst.curselection()
            if not sel: return
            linea = lst.get(sel[0])
            pid = int(linea.split("|")[0].strip())
            
            prod_full = backend.buscar_producto_por_id(pid)
            if not prod_full: return

            id_cat = prod_full.get('id_categoria')
            margen = obtener_margen(id_cat)
            
            nuevo_item = {
                'id': pid, 'nombre': prod_full['nombre'],
                'cant': 1.0, 'costo': 1.0, 'margen': margen,
                'precio_venta': 1.0 * (1 + margen/100)
            }
            carrito.append(nuevo_item)
            repintar_tabla()
            popup.destroy()
            
            new_idx = str(len(carrito) - 1)
            win.after(100, lambda: editar_celda(new_idx, '#3'))

        lst.bind("<Double-1>", lambda e: agregar_al_carrito())
        lst.bind("<Return>", lambda e: agregar_al_carrito())

        fr_btns = tk.Frame(popup, bg="#f4f4f8", pady=10)
        fr_btns.pack(fill=tk.X)
        
        # 🔥 BOTÓN AGREGAR
        tk.Button(
            fr_btns, 
            text="+ Agregar al Carrito", 
            bg="#10b981", 
            fg="white", 
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            activebackground="#059669",
            command=agregar_al_carrito, 
            width=25
        ).pack()
        
        configurar_navegacion_ventana(popup)

    # =================================================================
    # FOOTER Y CONFIRMACIÓN
    # =================================================================
    frame_footer = tk.Frame(win, bg="#ffffff", height=70, pady=15)
    frame_footer.pack(fill=tk.X, side=tk.BOTTOM)
    
    inner_footer = tk.Frame(frame_footer, bg="#ffffff")
    inner_footer.pack(fill=tk.X, padx=20)

    # 🔥 BOTÓN AGREGAR PRODUCTO
    btn_add_prod = tk.Button(
        inner_footer, 
        text="+ Agregar Producto", 
        command=abrir_selector_producto, 
        bg="#3b82f6", 
        fg="white", 
        font=("Segoe UI", 10, "bold"), 
        state="disabled",
        relief="flat",
        padx=20,
        pady=8,
        cursor="hand2",
        activebackground="#2563eb"
    )
    btn_add_prod.pack(side=tk.LEFT)
    
    # 🔥 BOTÓN CANCELAR
    tk.Button(
        inner_footer, 
        text="Cancelar", 
        command=win.destroy, 
        bg="#6b7280", 
        fg="white", 
        font=("Segoe UI", 10),
        relief="flat",
        padx=15,
        pady=8,
        cursor="hand2",
        activebackground="#4b5563"
    ).pack(side=tk.LEFT, padx=15)

    def pedir_medio_pago():
        dialog = tk.Toplevel(win)
        dialog.title("Confirmar Compra")
        dialog.geometry("400x300")
        dialog.config(bg="#f4f4f8")
        dialog.resizable(False, False)
        dialog.transient(win)
        dialog.grab_set()
        
        win.update_idletasks()
        x = win.winfo_x() + (win.winfo_width() // 2) - 200
        y = win.winfo_y() + (win.winfo_height() // 2) - 150
        dialog.geometry(f"+{x}+{y}")

        seleccion = {"valor": None}
        total_pago = sum(item['cant'] * item['costo'] for item in carrito)

        tk.Label(dialog, text="Finalizar Compra", font=("Segoe UI", 14, "bold"), bg="#f4f4f8", fg="#1f2937").pack(pady=(15,5))
        tk.Label(dialog, text=f"Total a Pagar: $ {total_pago:,.2f}", 
                 font=("Segoe UI", 12), fg="#10b981", bg="#f4f4f8").pack(pady=5)
        
        tk.Label(dialog, text="Seleccione el medio de pago:", bg="#f4f4f8", font=("Segoe UI", 10)).pack(pady=10)

        frm_btns = tk.Frame(dialog, bg="#f4f4f8")
        frm_btns.pack(fill="x", padx=40)

        def set_pago(tipo):
            seleccion["valor"] = tipo
            dialog.destroy()

        estilo_btn = {"font": ("Segoe UI", 10), "width": 30, "relief": "flat", "cursor": "hand2", "pady": 8}
        
        tk.Button(frm_btns, text="💵 Efectivo (Descuenta de Caja)", bg="#dcfce7", fg="#065f46",
                  command=lambda: set_pago("efectivo"), **estilo_btn).pack(pady=5)
        
        tk.Button(frm_btns, text="🏦 Transferencia / Tarjeta", bg="#dbeafe", fg="#1e3a8a",
                  command=lambda: set_pago("transferencia"), **estilo_btn).pack(pady=5)
        
        tk.Button(frm_btns, text="📋 Cuenta Corriente (Deuda)", bg="#fee2e2", fg="#991b1b",
                  command=lambda: set_pago("cuenta_corriente"), **estilo_btn).pack(pady=5)

        tk.Button(dialog, text="Cancelar", command=dialog.destroy, bg="#6b7280", fg="white", 
                  relief="flat", padx=15, pady=8, cursor="hand2").pack(pady=15)
        
        win.wait_window(dialog)
        return seleccion["valor"]

    def guardar_compra():
        if not proveedor_sel:
            messagebox.showwarning("Atención", "Seleccione un proveedor antes de confirmar la compra.")
            return

        if not carrito:
            messagebox.showerror("Error", "Carrito vacío")
            return

        medio = pedir_medio_pago()
        if not medio: return

        try:
            id_compra = backend.insertar_compra(
                usuario['id_usuario'],
                proveedor_sel['id_proveedor'],
                carrito,
                medio_pago=medio
            )

            if not id_compra:
                raise Exception("Error al guardar compra (DB devolvió None)")

            for item in carrito:
                backend.actualizar_precio_producto(
                    item['id'],
                    item['precio_venta'],
                    id_usuario=usuario['id_usuario']
                )

            msj_extra = ""
            if medio == 'efectivo':
                msj_extra = "\n💰 Se descontó el dinero de la Caja."
            elif medio == 'cuenta_corriente':
                msj_extra = "\n📋 Se registró la deuda con el proveedor."
            else:
                msj_extra = f"\n📄 Registrado como {medio.upper()}."

            messagebox.showinfo("Éxito", f"Compra registrada correctamente.{msj_extra}")
            stock_events.notificar_cambio_stock()
            win.destroy()

        except ValueError as ve:
            messagebox.showwarning("No se pudo registrar", str(ve))
        except Exception as e:
            messagebox.showerror("Error Crítico", str(e))

    # 🔥 BOTÓN CONFIRMAR COMPRA
    tk.Button(
        inner_footer, 
        text="✓ CONFIRMAR COMPRA", 
        command=guardar_compra,
        bg="#10b981", 
        fg="white", 
        font=("Segoe UI", 11, "bold"),
        relief="flat",
        padx=25,
        pady=10,
        cursor="hand2",
        activebackground="#059669"
    ).pack(side=tk.RIGHT)

    win.bind("<F2>", lambda e: btn_add_prod.invoke())
    configurar_navegacion_ventana(win, confirmar_cierre=True)
    win.grab_set()