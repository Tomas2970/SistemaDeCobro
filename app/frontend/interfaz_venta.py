# ============================================
# app/frontend/interfaz_venta.py
# (¡MODIFICADO CON SELECCIÓN DE PAGO!)
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
    from app.impresora import imprimir_ticket
except ImportError:
    print("ADVERTENCIA: app/impresora.py no encontrado. La función de imprimir no estará disponible.")
    def imprimir_ticket(*args, **kwargs):
        messagebox.showerror("Error de Impresora", "No se encontró el archivo 'app/impresora.py'.")
        return False

# --- ¡NUEVO! Importamos el popup de forma de pago ---
try:
    from app.frontend.interfaz_forma_pago import pedir_forma_pago
except ImportError:
    def pedir_forma_pago(*args, **kwargs):
        messagebox.showerror("Error Crítico", "No se encontró 'interfaz_forma_pago.py'.")
        return None


def ui_venta(parent: tk.Misc, backend, usuario: dict) -> None:
    win = tk.Toplevel(parent)
    win.title("Interfaz de Venta")
    win.geometry("820x620")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # items: (id_producto | None, nombre, cant, precio_unit, codigo_barras | "")
    items: list[tuple[int | None, str, int, float, str]] = []
    cliente_sel: dict[str, Any] | None = None
    total_venta: float = 0.0 # Variable para guardar el total

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
        sel = Toplevel(win); sel.title("Elegir cliente"); sel.geometry("460x420"); sel.config(bg="#f4f4f8"); sel.resizable(False, False)
        tk.Label(sel, text="Buscar (nombre o DNI):", bg="#f4f4f8").pack(pady=6)
        var_pat = tk.StringVar(); ent = tk.Entry(sel, textvariable=var_pat, width=40); ent.pack(pady=4)
        frame = tk.Frame(sel); frame.pack(expand=True, fill="both", padx=10, pady=10)
        sc = Scrollbar(frame); sc.pack(side="right", fill="y")
        lst = Listbox(frame, selectmode=SINGLE, yscrollcommand=sc.set, width=52, height=12)
        lst.pack(side="left", fill="both", expand=True); sc.config(command=lst.yview)
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
                c = backend.buscar_cliente_por_dni(q); render([c] if c else [])
            else:
                render(backend.buscar_cliente_por_nombre(q) if q else data)

        var_pat.trace_add("write", lambda *_: filtrar())

        def tomar():
            nonlocal cliente_sel
            sel_idx = lst.curselection()
            if not sel_idx:
                messagebox.showwarning("Atención", "Seleccione un cliente."); return
            rid = int(lst.get(sel_idx[0]).split("|")[0].strip())
            cliente_sel = next((c for c in data if int(c.get("id_cliente",-1))==rid), None)
            _upd_cliente(); sel.destroy()

        tk.Button(sel, text="Seleccionar", command=tomar).pack(pady=8)
        tk.Button(sel, text="Cancelar", command=sel.destroy).pack()
        sel.grab_set(); sel.transient(win)

    def quitar_cliente():
        nonlocal cliente_sel
        cliente_sel = None; _upd_cliente()

    tk.Button(win, text="Elegir cliente", command=abrir_selector_cliente).place(x=320, y=16)
    tk.Button(win, text="Quitar", command=quitar_cliente).place(x=420, y=16)

    # ---------------- Entrada de productos (por código/ID) ----------------
    tk.Label(win, text="Código de barras o ID:", bg="#f4f4f8").place(x=30, y=60)
    entry_producto = tk.Entry(win, width=34); entry_producto.place(x=190, y=60)
    tk.Label(win, text="Cantidad:", bg="#f4f4f8").place(x=30, y=95)
    entry_cantidad = tk.Entry(win, width=10); entry_cantidad.insert(0, "1"); entry_cantidad.place(x=110, y=95)
    btn_agregar = tk.Button(win, text="+ Agregar"); btn_agregar.place(x=260, y=92)

    # ---------------- Venta rápida (sin código) ----------------
    box = tk.LabelFrame(win, text="Venta rápida (sin código)", bg="#f4f4f8")
    box.place(x=30, y=128, width=760, height=70)

    tk.Label(box, text="Categoría:", bg="#f4f4f8").place(x=10, y=8)
    combo_cat = ttk.Combobox(box, state="readonly", width=28); combo_cat.place(x=80, y=6)

    tk.Label(box, text="Precio:", bg="#f4f4f8").place(x=350, y=8)
    entry_precio_manual = tk.Entry(box, width=10); entry_precio_manual.place(x=400, y=6)

    tk.Label(box, text="Cant.:", bg="#f4f4f8").place(x=500, y=8)
    entry_cant_manual = tk.Entry(box, width=6); entry_cant_manual.insert(0, "1"); entry_cant_manual.place(x=540, y=6)

    btn_agregar_manual = tk.Button(box, text="+ Agregar manual"); btn_agregar_manual.place(x=620, y=4)

    try:
        cats = backend.obtener_categorias() or []
        nombres = ["(Seleccionar)"] + [str(c.get("nombre") or c.get("categoria") or "") for c in cats]
        combo_cat["values"] = nombres; combo_cat.current(0)
    except Exception:
        combo_cat["values"] = ["(Seleccionar)"]; combo_cat.current(0)

    # ---------------- Lista de ítems (monoespaciado para alinear) ----------------
    lista = tk.Listbox(win, width=96, height=16, selectmode=EXTENDED, font=("Courier New", 10))
    lista.place(x=30, y=210)

    btn_quitar = tk.Button(win, text="Quitar seleccionados"); btn_quitar.place(x=30, y=540)

    total_var = tk.StringVar(value="$ 0.00")
    tk.Label(win, text="Total:", bg="#f4f4f8").place(x=560, y=540)
    tk.Entry(win, width=15, textvariable=total_var, state="readonly").place(x=600, y=540)

    # ---------------- Utilidades ----------------
    def _resolver_producto(token: str) -> dict | None:
        token = token.strip()
        if not token: return None
        if token.isdigit():
            prod = backend.buscar_producto_por_id(int(token))
            if prod: return prod
        prod = backend.buscar_producto_por_codigo_barras(token) if hasattr(backend, "buscar_producto_por_codigo_barras") else backend.buscar_producto_por_codigo(token)
        if prod: return prod
        return backend.buscar_producto_por_nombre(token)

    def _stock_en_carrito(id_producto: int | None) -> int:
        if id_producto is None:
            return 0
        return sum(c for pid, _, c, _, _ in items if pid == id_producto)

    def _agregar_o_sumar(id_producto: int | None, nombre: str, cant: int, precio: float, codigo: str) -> None:
        if id_producto is None:
            items.append((None, nombre, cant, precio, ""))
            return
        for idx, (pid, _, c, p, cb) in enumerate(items):
            if pid == id_producto and abs(p - precio) < 1e-6:
                items[idx] = (pid, nombre, c + cant, precio, cb)
                return
        items.append((id_producto, nombre, cant, precio, codigo))

    NAME_W = 56
    QTY_W = 4
    TOT_W = 12
    def _fmt_line(nombre: str, cant: int, parcial: float) -> str:
        n = (nombre[:NAME_W] + "…") if len(nombre) > NAME_W else nombre.ljust(NAME_W)
        qty = f"x{cant}".ljust(QTY_W)
        total = f"${parcial:,.2f}".rjust(TOT_W)
        return f"{n} {qty} = {total}"

    def _refrescar_lista() -> None:
        nonlocal total_venta
        lista.delete(0, tk.END)
        total_venta = 0.0 # Resetea el total
        for _, nombre, cant, precio, _ in items:
            parcial = cant * precio; total_venta += parcial
            lista.insert(tk.END, _fmt_line(nombre, cant, parcial))
        total_var.set(f"$ {total_venta:,.2f}")

    def quitar_seleccion():
        sel = list(lista.curselection())
        if not sel: return
        sel.reverse()
        for i in sel: items.pop(i)
        _refrescar_lista()

    btn_quitar.config(command=quitar_seleccion)

    # ---------------- Agregar por código/ID ----------------
    def agregar_producto():
        token = entry_producto.get().strip()
        if not token:
            messagebox.showwarning("Atención", "Ingrese un código/ID o use Venta rápida."); return
        try:
            cant = int(entry_cantidad.get().strip() or "1")
            if cant <= 0: raise ValueError()
        except Exception:
            messagebox.showwarning("Atención", "Cantidad inválida."); return

        prod = _resolver_producto(token)
        if not prod:
            messagebox.showwarning("No encontrado", "No se encontró el producto."); return

        pid = int(prod.get("id_producto") or prod.get("id"))
        nombre = str(prod.get("nombre",""))
        codigo = str(prod.get("codigo_barras") or "")
        precio = float(prod.get("precio") or 0.0)
        stock_actual = int(prod.get("stock") or 0)

        ya_en_carrito = _stock_en_carrito(pid)
        disp_para_agregar = stock_actual - ya_en_carrito
        if cant > disp_para_agregar:
            message = (
                f"Stock insuficiente para '{nombre}'.\n"
                f"Disponible: {stock_actual} | En carrito: {ya_en_carrito} | "
                f"Máximo agregable: {max(0, disp_para_agregar)}."
            )
            messagebox.showwarning("Sin stock", message); return

        _agregar_o_sumar(pid, nombre, cant, precio, codigo)
        _refrescar_lista()
        entry_producto.delete(0, tk.END)
        entry_cantidad.delete(0, tk.END); entry_cantidad.insert(0, "1")

    btn_agregar.config(command=agregar_producto)
    entry_producto.bind("<Return>", lambda e: agregar_producto())

    # ---------------- Agregar manual (sin código) ----------------
    def agregar_manual():
        cat = combo_cat.get().strip()
        if not cat or cat.startswith("("):
            messagebox.showwarning("Atención", "Seleccione una categoría."); return
        try:
            precio = float(entry_precio_manual.get().replace(",", "."))
            if precio <= 0: raise ValueError()
        except Exception:
            messagebox.showwarning("Atención", "Precio inválido."); return
        try:
            cant = int(entry_cant_manual.get().strip() or "1")
            if cant <= 0: raise ValueError()
        except Exception:
            messagebox.showwarning("Atención", "Cantidad inválida."); return

        nombre_linea = f"{cat}"
        _agregar_o_sumar(None, nombre_linea, cant, precio, "")
        _refrescar_lista()

        combo_cat.current(0)
        entry_precio_manual.delete(0, tk.END)
        entry_cant_manual.delete(0, tk.END); entry_cant_manual.insert(0, "1")

    btn_agregar_manual.config(command=agregar_manual)

    # ---------------- Confirmar venta (¡REDISEÑADO!) ----------------
    def confirmar_venta():
        if not items:
            messagebox.showwarning("Atención", "Agregue al menos un producto."); return
        
        # 1. Llamar al popup para que el usuario elija
        tipo_pago = pedir_forma_pago(
            parent=win,
            total=total_venta,
            cliente_seleccionado=(cliente_sel is not None)
        )
        
        # 2. Si el usuario cerró el popup (canceló), no hacemos nada
        if tipo_pago is None:
            return # El usuario canceló la selección de pago

        # 3. Si el usuario eligió "Cuenta Corriente" pero no había cliente... (doble chequeo)
        if tipo_pago == "cuenta_corriente" and cliente_sel is None:
            messagebox.showerror("Error", "No se puede usar Cuenta Corriente sin un cliente seleccionado.")
            return

        # --- Si todo está OK, procedemos a guardar ---
        
        id_usuario = usuario.get("id_usuario") or usuario.get("id", 0)
        cid = cliente_sel.get("id_cliente") if cliente_sel else None

        # 4. Insertar la venta (aún con tipo_pago 'efectivo' por default)
        id_venta = backend.insertar_venta(id_usuario=id_usuario, id_cliente=cid)
        if not id_venta:
            messagebox.showerror("Error", "No se pudo crear la venta."); return

        # 5. Insertar todos los detalles
        try:
            for id_producto, nombre, cant, precio, _ in items:
                if id_producto is None:
                    ok = backend.insertar_detalle_venta_libre(id_venta=id_venta, nombre=nombre, cantidad=cant, precio_unitario=precio)
                else:
                    ok = backend.insertar_detalle_venta(id_venta, id_producto, cant, precio)
                if not ok:
                    raise RuntimeError(f"Fallo al insertar item '{nombre}'")
        except Exception as e:
            messagebox.showerror("Error Crítico", f"{e}.\nLa venta #{id_venta} se creó pero está INCOMPLETA. Contacte a soporte.")
            return

        # 6. ¡PASO CLAVE! Actualizar el tipo de pago.
        # Esto dispara el trigger que actualiza la cuenta corriente.
        try:
            if tipo_pago != "efectivo": # Solo actualizamos si no es el default
                backend.actualizar_pago_y_estado_venta(id_venta, tipo_pago)
        except Exception as e:
            messagebox.showerror("Error de Cuenta Corriente", f"La venta se guardó, pero hubo un error al aplicar el pago a la cuenta corriente:\n{e}")
            # La venta igual se guardó, así que continuamos

        # 7. Alerta de Stock Bajo
        try:
            _items_alert = [{"id_producto": pid, "cantidad": cant} for (pid, _, cant, _, _) in items if pid is not None]
            if _items_alert:
                check_low_stock_after_sale(parent=win, backend=backend, items_vendidos=_items_alert)
        except Exception as _e:
            print(f"[venta] alerta stock bajo post-venta: {_e}")

        # 8. Preguntar si quiere imprimir
        try:
            msg_pregunta = f"Venta #{id_venta} registrada.\n¿Desea imprimir el ticket?"
            if messagebox.askyesno("Venta Registrada", msg_pregunta, parent=win):
                imprimir_ticket(
                    id_venta=id_venta,
                    items_de_la_venta=items, 
                    nombre_vendedor=usuario.get("nombre", "Vendedor")
                )
        except Exception as e:
            messagebox.showerror("Error de Impresión", f"La venta se guardó, pero no se pudo imprimir el ticket.\n\nError: {e}", parent=win)

        # 9. Cerrar la ventana de venta
        win.destroy()

    tk.Button(win, text="Confirmar Venta", bg="#4CAF50", fg="white", command=confirmar_venta).place(x=640, y=16)
    tk.Button(win, text="Cancelar", bg="#f44336", fg="white", command=win.destroy).place(x=755, y=16)

    _upd_cliente()
    win.grab_set()