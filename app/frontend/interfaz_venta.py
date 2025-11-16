# ============================================
# app/frontend/interfaz_venta.py
# ¡MEJORADO! Con navegación por teclado completa
# ============================================
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, Toplevel, Listbox, Scrollbar, SINGLE, EXTENDED
from tkinter import ttk
from typing import Any

try:
    from app.frontend.stock_alerts import check_low_stock_after_sale 
except ImportError:
    def check_low_stock_after_sale(*args, **kwargs):
        print("Advertencia: Módulo 'stock_alerts' no encontrado.")

try:
    from app.frontend.stock_event_manager import stock_events
except ImportError:
    print("ADVERTENCIA: No se pudo importar stock_event_manager")
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
    print(f"ADVERTENCIA: impresora.py no encontrado. Error: {e}")
    def imprimir_ticket(*args, **kwargs):
        messagebox.showerror("Error de Impresora", "No se encontró el archivo 'impresora.py'.")
        return False

try:
    from app.frontend.interfaz_forma_pago import mostrar_ventana_pago
except ImportError as e:
    print(f"ADVERTENCIA: No se pudo importar interfaz_forma_pago: {e}")
    def mostrar_ventana_pago(parent, total_venta, cliente_seleccionado):
        messagebox.showerror("Error Crítico", "No se encontró 'interfaz_forma_pago.py'.")
        return {'tipo_pago': 'efectivo', 'monto_pagado': total_venta, 'vuelto': 0}

# ¡NUEVO! Importar navegación por teclado
try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    print("ADVERTENCIA: navegacion_teclado_comun.py no encontrado")
    def configurar_navegacion_ventana(win):
        pass


def ui_venta(parent: tk.Misc, backend, usuario: dict) -> None:
    win = tk.Toplevel(parent)
    win.title("Interfaz de Venta")
    win.geometry("820x540") 
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    items: list[tuple[int | None, str, int, float, str]] = []
    cliente_sel: dict[str, Any] | None = None
    total_venta: float = 0.0 

    # ---------------- Cabecera: Cliente ----------------
    tk.Label(win, text="Cliente:", bg="#f4f4f8", font=("Helvetica", 10, "bold")).place(x=30, y=20)
    lbl_cliente = tk.Label(win, text="(ninguno)", bg="#f4f4f8", fg="blue"); lbl_cliente.place(x=100, y=20)

    def _upd_cliente():
        if cliente_sel:
            lbl_cliente.config(text=f"{cliente_sel.get('id_cliente','')} - {cliente_sel.get('nombre','')}")
        else:
            lbl_cliente.config(text="(ninguno)")

    def abrir_selector_cliente():
        nonlocal cliente_sel
        sel = Toplevel(win)
        sel.title("Elegir cliente")
        sel.geometry("460x420")
        sel.config(bg="#f4f4f8")
        sel.resizable(False, False)
        
        # ¡NUEVO! Aplicar navegación por teclado al popup
        configurar_navegacion_ventana(sel)
        
        tk.Label(sel, text="Buscar (nombre o DNI):", bg="#f4f4f8").pack(pady=6)
        var_pat = tk.StringVar()
        ent = tk.Entry(sel, textvariable=var_pat, width=40)
        ent.pack(pady=4)
        
        frame = tk.Frame(sel)
        frame.pack(expand=True, fill="both", padx=10, pady=10)
        sc = Scrollbar(frame)
        sc.pack(side="right", fill="y")
        lst = Listbox(frame, selectmode=SINGLE, yscrollcommand=sc.set, width=52, height=12)
        lst.pack(side="left", fill="both", expand=True)
        sc.config(command=lst.yview)
        
        data = backend.listar_clientes() 

        def render(filas):
            lst.delete(0, tk.END)
            for c in filas:
                dni_texto = c.get('dni') or ""
                lst.insert(tk.END, f"{c.get('id_cliente','')} | {c.get('nombre','')} | DNI:{dni_texto}")
        render(data)

        def filtrar(*_):
            q = var_pat.get().strip()
            if q.isdigit():
                c = backend.buscar_cliente_por_dni(q)
                render([c] if c else [])
            else:
                render(backend.buscar_cliente_por_nombre(q) if q else data)
        var_pat.trace_add("write", lambda *_: filtrar())

        def tomar():
            nonlocal cliente_sel
            sel_idx = lst.curselection()
            if not sel_idx:
                messagebox.showwarning("Atención", "Seleccione un cliente.")
                return
            rid = int(lst.get(sel_idx[0]).split("|")[0].strip())
            cliente_sel = next((c for c in data if int(c.get("id_cliente",-1))==rid), None)
            _upd_cliente()
            sel.destroy()

        btn_seleccionar = tk.Button(sel, text="Seleccionar", command=tomar)
        btn_seleccionar.pack(pady=8)
        btn_cancelar = tk.Button(sel, text="Cancelar", command=sel.destroy)
        btn_cancelar.pack()
        
        # ¡NUEVO! Foco inicial en el campo de búsqueda
        sel.after(100, lambda: ent.focus_set())
        
        sel.grab_set()
        sel.transient(win)

    def quitar_cliente():
        nonlocal cliente_sel
        cliente_sel = None
        _upd_cliente()

    btn_elegir_cliente = tk.Button(win, text="Elegir cliente", command=abrir_selector_cliente)
    btn_elegir_cliente.place(x=320, y=16)
    btn_quitar_cliente = tk.Button(win, text="Quitar", command=quitar_cliente)
    btn_quitar_cliente.place(x=420, y=16)

    # ---------------- Entrada de productos (por código/ID) ----------------
    tk.Label(win, text="Código de barras o ID:", bg="#f4f4f8").place(x=30, y=60)
    entry_producto = tk.Entry(win, width=34)
    entry_producto.place(x=190, y=60)
    
    tk.Label(win, text="Cantidad (o Kg):", bg="#f4f4f8").place(x=30, y=95)
    entry_cantidad = tk.Entry(win, width=10)
    entry_cantidad.insert(0, "1")
    entry_cantidad.place(x=130, y=95)
    
    btn_agregar = tk.Button(win, text="+ Agregar")
    btn_agregar.place(x=260, y=92)

    # ---------------- Lista de ítems ----------------
    lista = tk.Listbox(win, width=96, height=16, selectmode=EXTENDED, font=("Courier New", 10))
    lista.place(x=30, y=140) 

    btn_quitar = tk.Button(win, text="Quitar seleccionados")
    btn_quitar.place(x=30, y=470) 

    total_var = tk.StringVar(value="$ 0.00")
    tk.Label(win, text="Total:", bg="#f4f4f8").place(x=560, y=470) 
    tk.Entry(win, width=15, textvariable=total_var, state="readonly").place(x=600, y=470) 

    # ---------------- Utilidades ----------------
    def _resolver_producto(token: str) -> dict | None:
        token = token.strip()
        if not token: return None
        
        if token.isdigit():
            prod = backend.buscar_producto_por_id(int(token))
            if prod: return prod
        
        fn_cod = getattr(backend, "buscar_producto_por_codigo_barras", None)
        if callable(fn_cod):
            prod = fn_cod(token)
            if prod: return prod
        
        res = backend.buscar_producto_por_nombre(token) or []
        return res[0] if res else None

    def _stock_en_carrito(id_producto: int | None) -> float: 
        if id_producto is None:
            return 0.0
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

    NAME_W = 56
    QTY_W = 6 
    TOT_W = 12
    def _fmt_line(nombre: str, cant: float, parcial: float) -> str:
        n = (nombre[:NAME_W] + "…") if len(nombre) > NAME_W else nombre.ljust(NAME_W)
        
        if cant == int(cant): 
            qty_str = f"x{int(cant)}" 
        else:
            qty_str = f"x{cant:.3f}" 
            
        qty = qty_str.ljust(QTY_W)
        total = f"${parcial:,.2f}".rjust(TOT_W)
        return f"{n} {qty} = {total}"

    def _refrescar_lista() -> None:
        nonlocal total_venta
        lista.delete(0, tk.END)
        total_venta = 0.0 
        for _, nombre, cant, precio, _ in items:
            parcial = cant * precio
            total_venta += parcial
            lista.insert(tk.END, _fmt_line(nombre, cant, parcial))
        total_var.set(f"$ {total_venta:,.2f}")

    def quitar_seleccion():
        sel = list(lista.curselection())
        if not sel: return
        sel.reverse()
        for i in sel: items.pop(i)
        _refrescar_lista()

    btn_quitar.config(command=quitar_seleccion)
    
    def _reiniciar_venta_completa():
        """Limpia la pantalla para una nueva venta."""
        nonlocal items, cliente_sel, total_venta
        
        items.clear()
        cliente_sel = None
        total_venta = 0.0
        
        _refrescar_lista() 
        _upd_cliente()     
        
        entry_producto.delete(0, tk.END)
        entry_cantidad.delete(0, tk.END)
        entry_cantidad.insert(0, "1")
        
        entry_producto.focus_set()

    def manejar_escaneo_producto(event=None):
        """
        Maneja el escaneo/búsqueda de producto.
        Si es pesable, NO lo agrega automáticamente sino que pone foco en cantidad.
        """
        token = entry_producto.get().strip()
        if not token:
            messagebox.showwarning("Atención", "Ingrese un código, ID o nombre de producto.", parent=win)
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
            messagebox.showwarning("Atención", "Ingrese un código, ID o nombre de producto.", parent=win)
            return
        
        prod = _resolver_producto(token)
        if not prod:
            messagebox.showwarning("No encontrado", "No se encontró el producto.", parent=win)
            return

        es_pesable = bool(prod.get("es_pesable", False))
        cantidad_str = entry_cantidad.get().strip().replace(",", ".") or "1"
        
        try:
            if es_pesable:
                cant = float(cantidad_str)
            else:
                cant_float = float(cantidad_str)
                if cant_float != int(cant_float):
                    messagebox.showwarning("Error de Cantidad", 
                        f"El producto '{prod.get('nombre')}' no es pesable.\n"
                        "Solo se vende por unidades enteras (ej: 1, 2, 3).", parent=win)
                    return
                cant = int(cant_float)
                
            if cant <= 0: raise ValueError("Cantidad debe ser positiva")
                
        except ValueError:
            msg = "Cantidad inválida."
            if es_pesable:
                msg += " Use '1' o '1.250'."
            else:
                msg += " Use solo números enteros."
            messagebox.showwarning("Atención", msg, parent=win)
            return

        pid = int(prod.get("id_producto") or prod.get("id"))
        nombre = str(prod.get("nombre",""))
        codigo = str(prod.get("codigo_barras") or "")
        precio = float(prod.get("precio") or 0.0)
        stock_actual = float(prod.get("stock") or 0.0)

        ya_en_carrito = _stock_en_carrito(pid)
        disp_para_agregar = stock_actual - ya_en_carrito
        if cant > disp_para_agregar:
            message = (
                f"Stock insuficiente para '{nombre}'.\n\n"
                f"Disponible: {stock_actual:.3f}\n"
                f"En carrito: {ya_en_carrito:.3f}\n"
                f"Máximo agregable: {max(0, disp_para_agregar):.3f}"
            )
            messagebox.showwarning("Sin stock", message, parent=win)
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
            messagebox.showwarning("Atención", "Agregue al menos un producto.", parent=win)
            return
        
        info_pago = mostrar_ventana_pago(
            parent=win,
            total_venta=total_venta,
            cliente_seleccionado=(cliente_sel is not None)
        )
        
        if info_pago is None:
            return

        tipo_pago = info_pago['tipo_pago']

        if tipo_pago == "cuenta_corriente" and cliente_sel is None:
            messagebox.showerror("Error", "No se puede usar Cuenta Corriente sin un cliente seleccionado.", parent=win)
            return

        if tipo_pago == "cuenta_corriente":
            try:
                id_cli = cliente_sel.get("id_cliente")
                cuenta = backend.obtener_cuenta_por_cliente(id_cli) 
                saldo_actual = float(cuenta.get('saldo', 0.0))
                limite_credito = float(cuenta.get('limite_credito', 0.0))
                saldo_proyectado = saldo_actual - total_venta 
                
                if saldo_proyectado < -limite_credito:
                    disponible = limite_credito + saldo_actual 
                    msg = (
                        f"¡Límite de crédito excedido para {cliente_sel.get('nombre')}!\n\n"
                        f"Crédito Disponible: $ {disponible:,.2f}\n"
                        f"Esta venta de $ {total_venta:,.2f} NO puede ser procesada."
                    )
                    messagebox.showerror("Límite Excedido", msg, parent=win)
                    return 
            except Exception as e:
                messagebox.showerror("Error de Verificación", f"No se pudo verificar el límite de crédito:\n{e}", parent=win)
                return

        id_usuario = usuario.get("id_usuario") or usuario.get("id", 0)
        id_cliente = cliente_sel.get("id_cliente") if cliente_sel else None

        try:
            id_venta = backend.registrar_venta_completa(
                id_usuario=id_usuario,
                id_cliente=id_cliente,
                items=items,
                tipo_pago=tipo_pago
            )
            
            if not id_venta:
                messagebox.showerror("Error", "La venta no pudo ser registrada (ID nulo).", parent=win)
                return

        except Exception as e:
            messagebox.showerror("Error al Guardar Venta", f"La venta fue revertida.\n\nMotivo: {e}", parent=win)
            return

        try:
            msg_pregunta = f"Venta #{id_venta} registrada.\n¿Desea imprimir el ticket?"
            if messagebox.askyesno("Venta Registrada", msg_pregunta, parent=win):
                
                args_impresora = {
                    "id_venta": id_venta,
                    "items_de_la_venta": items,
                    "nombre_vendedor": usuario.get("nombre", "Vendedor"),
                    "metodo_pago": info_pago['tipo_pago'],
                    "monto_entregado": info_pago.get('monto_pagado', 0.0),
                    "vuelto": info_pago.get('vuelto', 0.0),
                    "cliente": cliente_sel.get('nombre', 'Consumidor Final') if cliente_sel else 'Consumidor Final'
                }
                
                imprimir_ticket(**args_impresora)
                
        except Exception as e:
            messagebox.showerror("Error de Impresión", f"La venta se guardó, pero no se pudo imprimir el ticket.\n\nError: {e}", parent=win)

        mensaje = f"✓ Venta #{id_venta} registrada exitosamente\n\n"
        mensaje += f"Total: ${total_venta:,.2f}\n"
        
        tipos_texto = {
            'efectivo': 'Efectivo',
            'tarjeta': 'Tarjeta Déb/Créd',
            'transferencia': 'Transferencia',
            'cuenta_corriente': 'Cuenta Corriente'
        }
        mensaje += f"Método: {tipos_texto.get(tipo_pago, tipo_pago)}\n"
        
        if tipo_pago == 'efectivo':
            mensaje += f"Paga con: ${info_pago['monto_pagado']:,.2f}\n"
            if info_pago['vuelto'] > 0:
                mensaje += f"\n💵 VUELTO: ${info_pago['vuelto']:,.2f}"
        
        messagebox.showinfo("Venta Exitosa", mensaje, parent=win)

        _reiniciar_venta_completa()
        
        win.after(100, lambda: stock_events.notificar_cambio_stock())

    btn_confirmar = tk.Button(win, text="Confirmar Venta", bg="#4CAF50", fg="white", command=confirmar_venta)
    btn_confirmar.place(x=640, y=16)
    
    btn_cancelar = tk.Button(win, text="Cancelar", bg="#f44336", fg="white", command=win.destroy)
    btn_cancelar.place(x=755, y=16)

    _upd_cliente()
    
    # ¡NUEVO! Atajos de teclado globales
    def atajo_confirmar(event):
        confirmar_venta()
        return "break"

    def atajo_cancelar(event):
        win.destroy()
        return "break"

    win.bind("<r>", atajo_confirmar)
    win.bind("<R>", atajo_confirmar)  # Mayúscula también
    win.bind("<c>", atajo_cancelar)
    win.bind("<C>", atajo_cancelar)
    
    # ¡NUEVO! Aplicar navegación por teclado a la ventana principal
    # Con confirmación para evitar cerrar accidentalmente durante una venta
    configurar_navegacion_ventana(win, confirmar_cierre=True)
    
    # ¡CRÍTICO! Foco inicial en el campo de búsqueda
    win.after(100, lambda: entry_producto.focus_set())
    
    win.grab_set()