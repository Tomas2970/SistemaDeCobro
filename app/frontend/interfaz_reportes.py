# app/frontend/interfaz_reportes.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)

def ui_reportes(parent: tk.Misc, backend) -> None:
    win = tk.Toplevel(parent)
    win.title("🧾 Reportes - Supermercado Don Atilio")
    win.geometry("980x620")
    win.configure(bg="#f4f4f8")
    win.resizable(True, True)

    header = tk.Frame(win, bg="#2e9e44", height=60)
    header.pack(fill=tk.X)
    tk.Label(header, text="Generador de Reportes", bg="#2e9e44", fg="white",
             font=("Helvetica", 16, "bold")).pack(pady=12)

    body = tk.Frame(win, bg="#f4f4f8")
    body.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

    # -------- Filtros
    frm = tk.Frame(body, bg="#f4f4f8")
    frm.pack(fill=tk.X, pady=8)

    tk.Label(frm, text="Tipo de reporte:", bg="#f4f4f8").grid(row=0, column=0, sticky="e", padx=6)
    cb_tipo = ttk.Combobox(frm, state="readonly", width=28,
                           values=["Ventas por vendedor", "Ventas diarias"])
    cb_tipo.grid(row=0, column=1, sticky="w")
    cb_tipo.current(0)

    hoy = date.today().isoformat()
    tk.Label(frm, text="Desde (YYYY-MM-DD):", bg="#f4f4f8").grid(row=1, column=0, sticky="e", padx=6, pady=4)
    ent_desde = tk.Entry(frm, width=14); ent_desde.grid(row=1, column=1, sticky="w")
    ent_desde.insert(0, f"{date.today().year}-01-01")

    tk.Label(frm, text="Hasta (YYYY-MM-DD):", bg="#f4f4f8").grid(row=2, column=0, sticky="e", padx=6, pady=4)
    ent_hasta = tk.Entry(frm, width=14); ent_hasta.grid(row=2, column=1, sticky="w")
    ent_hasta.insert(0, hoy)

    tk.Label(frm, text="Vendedor:", bg="#f4f4f8").grid(row=0, column=2, sticky="e", padx=(24,6))
    cb_vendedor = ttk.Combobox(frm, state="readonly", width=28)
    cb_vendedor.grid(row=0, column=3, sticky="w")

    def load_vendedores():
        try:
            vendedores = backend.obtener_vendedores() or []
        except Exception as e:
            logger.exception("obtener_vendedores()")
            vendedores = []
        nombres = ["(Todos)"]; ids = [None]
        for v in vendedores:
            nombres.append(str(v.get("nombre") or ""))
            ids.append(int(v.get("id_usuario") or v.get("id") or 0) or None)
        cb_vendedor["values"] = nombres
        cb_vendedor.ids = ids  # type: ignore
        cb_vendedor.current(0)

    ttk.Button(frm, text="↻", width=3, command=load_vendedores).grid(row=0, column=4, padx=4)

    # -------- Tabla
    table_frame = tk.Frame(body, bg="#f4f4f8")
    table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    tree: ttk.Treeview

    def setup_tree(cols: list[tuple[str, int]]):
        nonlocal tree
        for w in list(table_frame.children.values()):
            w.destroy()
        columns = [c for c, _ in cols]
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        for name, width in cols:
            tree.heading(name, text=name)
            tree.column(name, width=width, anchor="w")

    setup_tree([("Fecha", 140), ("ID Venta", 90), ("Vendedor", 180), ("Total", 120)])

    # -------- Acciones
    btns = tk.Frame(body, bg="#f4f4f8"); btns.pack(fill=tk.X)

    def _vendedor_id_sel() -> Optional[int]:
        try:
            idx = cb_vendedor.current()
            return getattr(cb_vendedor, "ids", [None])[idx]  # type: ignore
        except Exception:
            return None

    def _validar_fechas() -> tuple[str, str] | None:
        d = ent_desde.get().strip(); h = ent_hasta.get().strip()
        if len(d) != 10 or len(h) != 10 or d[4] != "-" or h[4] != "-":
            messagebox.showwarning("Fechas", "Formato esperado: YYYY-MM-DD.")
            return None
        return d, h

    def _fmt_mon(x: Any) -> str:
        try:
            return f"$ {float(x):,.2f}"
        except Exception:
            return str(x)

    def generar():
        try:
            rango = _validar_fechas()
            if not rango: return
            desde, hasta = rango
            tipo = cb_tipo.get()
            if tipo == "Ventas por vendedor":
                setup_tree([("Fecha", 140), ("ID Venta", 90), ("Vendedor", 180), ("Total", 120)])
                vid = _vendedor_id_sel()
                datos = backend.reporte_ventas_por_vendedor(desde, hasta, vid)
                tree.delete(*tree.get_children())
                if not datos:
                    tree.insert("", "end", values=("Sin datos", "", "", "")); return
                for r in datos:
                    tree.insert("", "end", values=(
                        str(r.get("fecha") or "")[:19],
                        r.get("id_venta") or "",
                        r.get("vendedor") or "",
                        _fmt_mon(r.get("total") or 0),
                    ))
            else:
                setup_tree([("Fecha", 140), ("Cant. Ventas", 110), ("Monto Total", 120)])
                datos = backend.obtener_ventas_diarias(desde, hasta)
                tree.delete(*tree.get_children())
                if not datos:
                    tree.insert("", "end", values=("Sin datos", "", "")); return
                for r in datos:
                    tree.insert("", "end", values=(
                        str(r.get("fecha") or ""),
                        r.get("total_ventas") or r.get("Cant. Ventas") or 0,
                        _fmt_mon(r.get("monto_total") or 0),
                    ))
        except Exception as e:
            logger.exception("generar()")
            messagebox.showerror("Error", f"No se pudo generar el reporte:\n{e}")

    ttk.Button(btns, text="Generar", width=14, command=generar).pack(side=tk.LEFT, padx=4, pady=6)

    def on_tipo_changed(_evt=None):
        is_vend = cb_tipo.get() == "Ventas por vendedor"
        cb_vendedor.configure(state=("readonly" if is_vend else "disabled"))

    cb_tipo.bind("<<ComboboxSelected>>", on_tipo_changed)

    # Init
    load_vendedores()
    on_tipo_changed()
    win.grab_set()
