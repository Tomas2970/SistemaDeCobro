# ================================
# app/frontend/interfaz_reportes.py
# (REEMPLAZAR COMPLETO ESTE ARCHIVO)
# ================================
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

TIPOS = [
    "Ventas por vendedor",
    "Ventas por período",
    "Ventas totales",
]

def ui_reportes(parent: tk.Misc, backend, usuario: dict) -> None:
    win = tk.Toplevel(parent)
    win.title("📊 Reportes - Supermercado Don Atilio")
    win.geometry("900x600")
    win.config(bg="#f4f4f8")

    tk.Label(win, text="Generador de Reportes", bg="#4CAF50", fg="white",
             font=("Arial", 16, "bold"), pady=10).pack(fill=tk.X)

    frm = tk.Frame(win, bg="#f4f4f8"); frm.pack(pady=12)

    # Tipo
    tk.Label(frm, text="Tipo de reporte:", bg="#f4f4f8").grid(row=0, column=0, padx=8, sticky="e")
    tipo = ttk.Combobox(frm, values=TIPOS, state="readonly", width=28)
    tipo.grid(row=0, column=1, sticky="w"); tipo.current(0)

    # Fechas
    tk.Label(frm, text="Desde (YYYY-MM-DD):", bg="#f4f4f8").grid(row=1, column=0, padx=8, pady=4, sticky="e")
    entry_desde = tk.Entry(frm, width=15); entry_desde.insert(0, f"{date.today().year}-01-01"); entry_desde.grid(row=1, column=1, sticky="w")

    tk.Label(frm, text="Hasta (YYYY-MM-DD):", bg="#f4f4f8").grid(row=2, column=0, padx=8, pady=4, sticky="e")
    entry_hasta = tk.Entry(frm, width=15); entry_hasta.insert(0, str(date.today())); entry_hasta.grid(row=2, column=1, sticky="w")

    # Filtro vendedor (solo para "Ventas por vendedor")
    lbl_v = tk.Label(frm, text="Vendedor:", bg="#f4f4f8")
    combo_v = ttk.Combobox(frm, state="readonly", width=28)
    btn_reload = tk.Button(frm, text="↻", relief="groove", width=2)

    vendedores_cache: list[dict] = []

    def cargar_vendedores():
        nonlocal vendedores_cache
        vendedores_cache = backend.obtener_vendedores() or []
        nombres = ["(Todos)"] + [f"{v.get('id_usuario','')} - {v.get('nombre','')}" for v in vendedores_cache]
        combo_v["values"] = nombres
        if nombres:
            combo_v.current(0)

    def toggle_vendedor(*_):
        if tipo.get() == "Ventas por vendedor":
            lbl_v.grid(row=0, column=2, padx=(24,8), sticky="e")
            combo_v.grid(row=0, column=3, sticky="w")
            btn_reload.grid(row=0, column=4, padx=6, sticky="w")
            cargar_vendedores()
        else:
            lbl_v.grid_forget(); combo_v.grid_forget(); btn_reload.grid_forget()

    btn_reload.configure(command=cargar_vendedores)
    tipo.bind("<<ComboboxSelected>>", toggle_vendedor)
    toggle_vendedor()

    # Tabla
    tree = ttk.Treeview(win, show="headings"); tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)
    yscroll = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
    tree.configure(yscroll=yscroll.set); yscroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _set_headers(headers: list[str]) -> None:
        cols = [f"c{i}" for i in range(1, len(headers)+1)]
        tree["columns"] = cols
        for i, h in enumerate(headers, 1):
            tree.heading(f"c{i}", text=h)
            tree.column(f"c{i}", width=max(120, int(820/len(headers))))

    def _fill_rows(rows: list[dict], headers: list[str]) -> None:
        for r in tree.get_children(): tree.delete(r)
        for fila in rows:
            vals = []
            for h in headers:
                vals.append(
                    fila.get(h, fila.get(h.title(), fila.get(h.replace(" ", "_"), "")))
                )
            tree.insert("", tk.END, values=vals)

    def _id_vendedor_sel() -> int | None:
        val = combo_v.get().strip() if combo_v.winfo_ismapped() else ""
        if not val or val.startswith("("):
            return None
        try:
            return int(val.split("-")[0].strip())
        except Exception:
            return None

    def generar():
        tp, desde, hasta = tipo.get(), entry_desde.get().strip(), entry_hasta.get().strip()
        try:
            if tp == "Ventas por vendedor":
                id_v = _id_vendedor_sel()
                datos = backend.reporte_ventas_por_vendedor(desde, hasta, id_v)
                # filas separadas por vendedor (y por fecha si así lo retorna tu DB)
                headers = ["Fecha", "Vendedor", "Cant. Ventas", "Monto Total"]
            elif tp == "Ventas por período":
                datos = backend.obtener_ventas_diarias(desde, hasta)
                headers = ["Fecha", "Cant. Ventas", "Monto Total"]
            else:  # Ventas totales
                datos = backend.obtener_ventas_diarias(None, None)
                headers = ["Fecha", "Cant. Ventas", "Monto Total"]

            _set_headers(headers)
            _fill_rows(datos, headers)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte:\n{e}")

    tk.Button(win, text="📈 Generar Reporte", bg="#2196F3", fg="white",
              font=("Arial", 11, "bold"), width=20, command=generar).pack(pady=6)
    tk.Button(win, text="Cerrar", bg="#f44336", fg="white", width=12, command=win.destroy).pack(pady=6)
    win.grab_set()