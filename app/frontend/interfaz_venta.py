# app/frontend/interfaz_venta.py
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, Toplevel, Listbox, Scrollbar, SINGLE, EXTENDED
from typing import Any

def ui_venta(parent: tk.Misc, backend, usuario: dict) -> None:
    win = tk.Toplevel(parent)
    win.title("Interfaz de Venta")
    win.geometry("760x560")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # items: (id_producto, nombre, cant, precio_unit, codigo_barras)
    items: list[tuple[int, str, int, float, str]] = []
    cliente_sel: dict[str, Any] | None = None

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
        sel = Toplevel(win); sel.title("Elegir cliente"); sel.geometry("440x400"); sel.config(bg="#f4f4f8"); sel.resizable(False, False)
        tk.Label(sel, text="Buscar (nombre o DNI):", bg="#f4f4f8").pack(pady=6)
        var_pat = tk.StringVar(); ent = tk.Entry(sel, textvariable=var_pat, width=40); ent.pack(pady=4); ent.focus_set()
        frame = tk.Frame(sel); frame.pack(expand=True, fill="both", padx=10, pady=10)
        sc = Scrollbar(frame); sc.pack(side="right", fill="y")
        lst = Listbox(frame, selectmode=SINGLE, yscrollcommand=sc.set, width=50, height=12)
        lst.pack(side="left", fill="both", expand=True); sc.config(command=lst.yview)
        data = backend.listar_clientes()
        def render(filas): lst.delete(0, tk.END); [lst.insert(tk.END, f"{c.get('id_cliente','')} | {c.get('nombre','')} | DNI:{c.get('dni','')}") for c in filas]
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
            pool = backend.listar_clientes()
            cliente_sel = next((c for c in pool if int(c.get("id_cliente",-1))==rid), {"id_cliente":rid})
            _upd_cliente(); sel.destroy()
        lst.bind("<Double-1>", lambda e: tomar())
        tk.Button(sel, text="Seleccionar", bg="#4CAF50", fg="white", command=tomar).pack(pady=8)
        tk.Button(sel, text="Cancelar", bg="#f44336", fg="white", command=sel.destroy).pack()
        sel.grab_set(); sel.transient(win)

    def quitar_cliente():
        nonlocal cliente_sel; cliente_sel=None; _upd_cliente()

    tk.Button(win, text="Elegir cliente", command=abrir_selector_cliente).place(x=300, y=16)
    tk.Button(win, text="Quitar", command=quitar_cliente).place(x=400, y=16)

    # ---------------- Entrada de productos ----------------
    tk.Label(win, text="Código de barras o ID:", bg="#f4f4f8").place(x=30, y=60)
    entry_producto = tk.Entry(win, width=34); entry_producto.place(x=190, y=60)
    tk.Label(win, text="Cantidad:", bg="#f4f4f8").place(x=30, y=95)
    entry_cantidad = tk.Entry(win, width=10); entry_cantidad.insert(0, "1"); entry_cantidad.place(x=110, y=95)
    btn_agregar = tk.Button(win, text="+ Agregar")
    btn_agregar.place(x=260, y=92)

    # Lista de ítems (multiselección)
    lista = tk.Listbox(win, width=92, height=16, selectmode=EXTENDED)
    lista.place(x=30, y=140)
    tk.Label(win, text="Tips: Ctrl/Cmd para selección múltiple. Supr también quita.", bg="#f4f4f8", fg="gray").place(x=30, y=420)

    # Acciones sobre la lista
    btn_quitar = tk.Button(win, text="Quitar seleccionados")
    btn_quitar.place(x=30, y=450)

    total_var = tk.StringVar(value="$ 0.00")
    tk.Label(win, text="Total:", bg="#f4f4f8").place(x=30, y=500)
    tk.Entry(win, width=15, textvariable=total_var, state="readonly").place(x=80, y=500)

    # ---------------- Utilidades ----------------
    def _resolver_producto(token: str) -> dict | None:
        token = token.strip()
        if not token: return None
        if token.isdigit():
            prod = backend.buscar_producto_por_id(int(token))
            if prod: return prod
        prod = backend.buscar_producto_por_codigo_barras(token)
        if prod: return prod
        res = backend.buscar_producto_por_nombre(token) or []
        return res[0] if res else None

    def _stock_en_carrito(pid: int) -> int:
        """Cantidad de ese producto ya agregada en el carrito."""
        s = 0
        for idp, _, cant, _, _ in items:
            if int(idp) == int(pid):
                s += int(cant)
        return s

    def _agregar_o_sumar(pid: int, nombre: str, cant: int, precio: float, codigo: str) -> None:
        """Si ya estaba en carrito, suma cantidad; si no, lo agrega."""
        for idx, (idp, nom, c, p, cb) in enumerate(items):
            if idp == pid and abs(p - precio) < 1e-9:
                items[idx] = (idp, nom, c + cant, p, cb)
                return
        items.append((pid, nombre, cant, precio, codigo))

    def _refrescar_lista():
        lista.delete(0, tk.END)
        total = 0.0
        for idp, nombre, cant, precio, _ in items:
            subtotal = cant * precio
            total += subtotal
            lista.insert(tk.END, f"[{idp}] {nombre}  x{cant}  @ ${precio:,.2f}  = ${subtotal:,.2f}")
        total_var.set(f"$ {total:,.2f}")

    def _quitar_seleccionados(*_):
        sel = list(lista.curselection())
        if not sel:
            messagebox.showinfo("Quitar", "Seleccioná uno o más ítems para quitar.")
            return
        # borrar de atrás hacia adelante para no mover índices
        for idx in reversed(sel):
            if 0 <= idx < len(items):
                items.pop(idx)
        _refrescar_lista()

    lista.bind("<Delete>", _quitar_seleccionados)
    btn_quitar.config(command=_quitar_seleccionados)

    # ---------------- Agregar producto (con validación de stock) ----------------
    def agregar_producto():
        patron = entry_producto.get().strip()
        if not patron:
            messagebox.showwarning("Atención", "Ingrese código, ID o parte del nombre.")
            return
        try:
            cant = int(entry_cantidad.get())
            assert cant > 0
        except Exception:
            messagebox.showerror("Cantidad inválida", "Ingrese una cantidad entera > 0.")
            return

        prod = _resolver_producto(patron)
        if not prod:
            messagebox.showinfo("Sin resultados", "No se encontró el producto.")
            return

        pid = int(prod.get("id_producto") or prod.get("id") or 0)
        nombre = str(prod.get("nombre") or "")
        precio = float(prod.get("precio") or 0.0)
        codigo = str(prod.get("codigo_barras") or "")

        # Validar stock: disponible - ya en carrito
        stock_actual = int(backend.obtener_stock(pid))
        ya_en_carrito = _stock_en_carrito(pid)
        disp_para_agregar = stock_actual - ya_en_carrito

        if cant > disp_para_agregar:
            message = (
                f"Stock insuficiente para '{nombre}'.\n"
                f"Disponible: {stock_actual} | En carrito: {ya_en_carrito} | "
                f"Podés agregar como máximo: {max(0, disp_para_agregar)}."
            )
            messagebox.showwarning("Sin stock", message)
            return

        _agregar_o_sumar(pid, nombre, cant, precio, codigo)
        _refrescar_lista()
        entry_producto.delete(0, tk.END)
        entry_cantidad.delete(0, tk.END); entry_cantidad.insert(0, "1")

    btn_agregar.config(command=agregar_producto)
    entry_producto.bind("<Return>", lambda e: agregar_producto())

    # ---------------- Confirmar venta ----------------
    def confirmar_venta():
        if not items:
            messagebox.showwarning("Atención", "Agregue al menos un producto.")
            return

        id_usuario = usuario.get("id_usuario") or usuario.get("id", 0)
        cid = cliente_sel.get("id_cliente") if cliente_sel else None
        id_venta = backend.insertar_venta(id_usuario=id_usuario, id_cliente=cid)
        if not id_venta:
            messagebox.showerror("Error", "No se pudo crear la venta.")
            return

        for id_producto, _, cant, precio, _ in items:
            ok = backend.insertar_detalle_venta(id_venta, id_producto, cant, precio)
            if not ok:
                messagebox.showerror("Error", f"Fallo al insertar item {id_producto}. La venta puede haber quedado parcial.")
                return

        messagebox.showinfo("OK", f"Venta #{id_venta} registrada.")
        win.destroy()

    tk.Button(win, text="Confirmar Venta", bg="#4CAF50", fg="white", command=confirmar_venta).place(x=560, y=500)
    tk.Button(win, text="Cancelar", bg="#f44336", fg="white", command=win.destroy).place(x=680, y=500)

    _upd_cliente()
    win.grab_set()
