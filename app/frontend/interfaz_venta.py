# app/frontend/interfaz_venta.py
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, Toplevel, Listbox, Scrollbar, SINGLE
from typing import Any

def ui_venta(parent: tk.Misc, backend, usuario: dict) -> None:
    win = tk.Toplevel(parent)
    win.title("Interfaz de Venta")
    win.geometry("640x500")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # Estado de la venta
    items: list[tuple[int, str, int, float]] = []   # (id_producto, nombre, cantidad, precio)
    cliente_sel: dict[str, Any] | None = None       # {'id_cliente':..., 'nombre':..., 'dni':...}

    # ---------------- Cliente ----------------
    tk.Label(win, text="Cliente:", bg="#f4f4f8", font=("Helvetica", 10, "bold")).place(x=30, y=20)
    lbl_cliente = tk.Label(win, text="(ninguno)", bg="#f4f4f8", fg="blue")
    lbl_cliente.place(x=100, y=20)

    def actualizar_cliente_label() -> None:
        # Por qué: feedback claro para el cajero
        lbl_cliente.config(
            text=f"{cliente_sel['id_cliente']} - {cliente_sel.get('nombre','')}"
            if cliente_sel else "(ninguno)"
        )

    def abrir_selector_cliente() -> None:
        nonlocal cliente_sel
        sel = Toplevel(win)
        sel.title("Elegir cliente")
        sel.geometry("420x380")
        sel.config(bg="#f4f4f8")
        sel.resizable(False, False)

        tk.Label(sel, text="Buscar (nombre o DNI):", bg="#f4f4f8").pack(pady=6)
        var_pat = tk.StringVar()
        ent = tk.Entry(sel, textvariable=var_pat, width=40)
        ent.pack(pady=4)
        ent.focus_set()

        frame = tk.Frame(sel)
        frame.pack(expand=True, fill="both", padx=10, pady=10)
        sc = Scrollbar(frame); sc.pack(side="right", fill="y")
        lst = Listbox(frame, selectmode=SINGLE, yscrollcommand=sc.set, width=50, height=12)
        lst.pack(side="left", fill="both", expand=True); sc.config(command=lst.yview)

        data = backend.listar_clientes()  # requiere DB.obtener_clientes(); si no, lista vacía

        def poblar(filas: list[dict]) -> None:
            lst.delete(0, tk.END)
            for c in filas:
                rid = c.get("id_cliente", "")
                nom = c.get("nombre", "")
                dni = c.get("dni", "")
                lst.insert(tk.END, f"{rid} | {nom} | DNI:{dni}")

        poblar(data)

        def filtrar(*_args) -> None:
            q = var_pat.get().strip()
            if q.isdigit():
                cand = backend.buscar_cliente_por_dni(q)
                poblar([cand] if cand else [])
            else:
                poblar(backend.buscar_cliente_por_nombre(q) if q else data)

        var_pat.trace_add("write", lambda *_: filtrar())

        def tomar_seleccion(_evt=None) -> None:
            nonlocal cliente_sel
            sel_idx = lst.curselection()
            if not sel_idx:
                messagebox.showwarning("Atención", "Seleccione un cliente.")
                return
            texto = lst.get(sel_idx[0])
            try:
                rid = int(texto.split("|")[0].strip())
            except Exception:
                messagebox.showerror("Error", "No se pudo leer el id del cliente seleccionado.")
                return
            pool = backend.listar_clientes()
            cliente_sel = next((c for c in pool if int(c.get("id_cliente", -1)) == rid),
                               {"id_cliente": rid, "nombre": texto})
            actualizar_cliente_label()
            sel.destroy()

        lst.bind("<Double-1>", tomar_seleccion)
        tk.Button(sel, text="Seleccionar", bg="#4CAF50", fg="white",
                  command=tomar_seleccion).pack(pady=8)
        tk.Button(sel, text="Cancelar", bg="#f44336", fg="white",
                  command=sel.destroy).pack()

        sel.grab_set()
        sel.transient(win)

    def quitar_cliente() -> None:
        nonlocal cliente_sel
        cliente_sel = None
        actualizar_cliente_label()

    tk.Button(win, text="Elegir cliente", command=abrir_selector_cliente).place(x=300, y=16)
    tk.Button(win, text="Quitar", command=quitar_cliente).place(x=400, y=16)

    # ---------------- Productos ----------------
    tk.Label(win, text="Producto:", bg="#f4f4f8").place(x=30, y=60)
    entry_producto = tk.Entry(win, width=34); entry_producto.place(x=110, y=60)

    tk.Label(win, text="Cantidad:", bg="#f4f4f8").place(x=30, y=95)
    entry_cantidad = tk.Entry(win, width=10); entry_cantidad.insert(0, "1"); entry_cantidad.place(x=110, y=95)

    def agregar_por_nombre() -> None:
        patron = entry_producto.get().strip()
        if not patron:
            messagebox.showwarning("Atención", "Ingrese parte del nombre del producto.")
            return
        resultados = backend.buscar_producto_por_nombre(patron) or []
        if not resultados:
            messagebox.showinfo("Sin resultados", "No se encontraron productos.")
            return
        prod = resultados[0]  # simple: tomar el primero; se puede mejorar con un selector
        try:
            cant = int(entry_cantidad.get())
            if cant <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Cantidad inválida", "Ingrese una cantidad entera > 0.")
            return
        items.append((int(prod["id_producto"]), str(prod["nombre"]), cant, float(prod["precio"])))
        refrescar()

    tk.Button(win, text="+ Agregar", command=agregar_por_nombre).place(x=260, y=92)

    lista = tk.Listbox(win, width=74, height=12); lista.place(x=30, y=130)
    total_var = tk.StringVar(value="$ 0.00")
    tk.Label(win, text="Total:", bg="#f4f4f8").place(x=30, y=360)
    tk.Entry(win, width=15, textvariable=total_var, state="readonly").place(x=80, y=360)

    def refrescar() -> None:
        lista.delete(0, tk.END)
        total = 0.0
        for _, nombre, cant, precio in items:
            subtotal = cant * precio
            total += subtotal
            lista.insert(tk.END, f"{nombre}  x{cant}  = ${subtotal:,.2f}")
        total_var.set(f"$ {total:,.2f}")

    # ---------------- Confirmación ----------------
    def confirmar_venta() -> None:
        if not items:
            messagebox.showwarning("Atención", "Agregue al menos un producto.")
            return
        id_usuario = usuario.get("id_usuario") or usuario.get("id", 0)
        cid = cliente_sel.get("id_cliente") if cliente_sel else None  # None => NULL en DB
        id_venta = backend.insertar_venta(id_usuario=id_usuario, id_cliente=cid)
        if not id_venta:
            messagebox.showerror("Error", "No se pudo crear la venta.")
            return
        for id_producto, _, cant, precio in items:
            ok = backend.insertar_detalle_venta(id_venta, id_producto, cant, precio)
            if not ok:
                messagebox.showerror("Error", f"Fallo al insertar producto {id_producto}.")
                return
        messagebox.showinfo("OK", f"Venta #{id_venta} registrada.")
        win.destroy()

    tk.Button(win, text="Confirmar Venta", bg="#4CAF50", fg="white",
              command=confirmar_venta).place(x=420, y=440)
    tk.Button(win, text="Cancelar", bg="#f44336", fg="white",
              command=win.destroy).place(x=540, y=440)

    actualizar_cliente_label()
    win.grab_set()
