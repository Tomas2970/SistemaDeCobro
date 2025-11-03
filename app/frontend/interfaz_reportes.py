# app/frontend/interfaz_reportes.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Optional
from datetime import date, datetime, timedelta # Importar datetime y timedelta
import logging

logger = logging.getLogger(__name__)

# --- Helper de formato de fecha ---
def _formatear_fecha_para_sql(fecha_str: str) -> str | None:
    """Convierte DD/MM/YYYY a YYYY-MM-DD. Devuelve None si es inválida."""
    if not fecha_str:
        return None
    try:
        fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
        return fecha_obj.strftime("%Y-%m-%d")
    except ValueError:
        return None 

# --- ¡NUEVO! Helper para mostrar fecha en la tabla ---
def _formatear_fecha_para_ui(fecha_sql: Any) -> str:
    """Convierte AAAA-MM-DD HH:MM:SS a DD/MM/AAAA HH:MM"""
    if not fecha_sql:
        return ""
    try:
        # (Convertimos a string primero por si viene como obj datetime)
        fecha_obj = datetime.fromisoformat(str(fecha_sql)) 
        return fecha_obj.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(fecha_sql) # Fallback

def ui_reportes(parent: tk.Misc, backend, usuario: dict) -> None: #Añadido 'usuario'
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
    cb_tipo.grid(row=0, column=1, columnspan=2, sticky="w")
    cb_tipo.current(0)

    # --- ¡NUEVO! Desplegable de Períodos ---
    tk.Label(frm, text="Período:", bg="#f4f4f8").grid(row=1, column=0, sticky="e", padx=6, pady=4)
    periodos = ["Personalizado", "Hoy", "Ayer", "Esta semana", "Este mes", "Mes pasado"]
    cb_periodo = ttk.Combobox(frm, state="readonly", width=20, values=periodos)
    cb_periodo.grid(row=1, column=1, sticky="w")
    cb_periodo.current(0) # Default "Personalizado"

    tk.Label(frm, text="Desde (DD/MM/YYYY):", bg="#f4f4f8").grid(row=2, column=0, sticky="e", padx=6, pady=4)
    ent_desde = tk.Entry(frm, width=14); ent_desde.grid(row=2, column=1, sticky="w")
    ent_desde.insert(0, f"01/01/{date.today().year}")

    tk.Label(frm, text="Hasta (DD/MM/YYYY):", bg="#f4f4f8").grid(row=3, column=0, sticky="e", padx=6, pady=4)
    ent_hasta = tk.Entry(frm, width=14); ent_hasta.grid(row=3, column=1, sticky="w")
    ent_hasta.insert(0, date.today().strftime("%d/%m/%Y"))

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
    
    # --- ¡NUEVO! Función para actualizar fechas ---
    def on_periodo_seleccionado(event=None):
        periodo = cb_periodo.get()
        hoy = date.today()
        
        # Habilitar/Deshabilitar entradas
        if periodo == "Personalizado":
            ent_desde.config(state="normal")
            ent_hasta.config(state="normal")
            return
        else:
            ent_desde.config(state="normal")
            ent_hasta.config(state="normal")
            
        desde, hasta = hoy, hoy # Default

        if periodo == "Hoy":
            desde, hasta = hoy, hoy
        elif periodo == "Ayer":
            ayer = hoy - timedelta(days=1)
            desde, hasta = ayer, ayer
        elif periodo == "Esta semana":
            # Lunes es weekday() 0, Domingo es 6
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fin_semana = inicio_semana + timedelta(days=6)
            desde, hasta = inicio_semana, fin_semana
        elif periodo == "Este mes":
            inicio_mes = hoy.replace(day=1)
            # Ir al primer día del siguiente mes y restar 1 día
            siguiente_mes = (inicio_mes + timedelta(days=32)).replace(day=1)
            fin_mes = siguiente_mes - timedelta(days=1)
            desde, hasta = inicio_mes, fin_mes
        elif periodo == "Mes pasado":
            fin_mes_pasado = hoy.replace(day=1) - timedelta(days=1)
            inicio_mes_pasado = fin_mes_pasado.replace(day=1)
            desde, hasta = inicio_mes_pasado, fin_mes_pasado
        
        # Actualizar campos
        ent_desde.delete(0, tk.END); ent_desde.insert(0, desde.strftime("%d/%m/%Y"))
        ent_hasta.delete(0, tk.END); ent_hasta.insert(0, hasta.strftime("%d/%m/%Y"))
        
        # Deshabilitar para que no se editen
        ent_desde.config(state="readonly")
        ent_hasta.config(state="readonly")

    cb_periodo.bind("<<ComboboxSelected>>", on_periodo_seleccionado)


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

    def _validar_fechas_sql() -> tuple[str, str] | None:
        desde_str = ent_desde.get().strip()
        hasta_str = ent_hasta.get().strip()
        
        desde_sql = _formatear_fecha_para_sql(desde_str)
        hasta_sql = _formatear_fecha_para_sql(hasta_str)
        
        if (desde_str and not desde_sql) or (hasta_str and not hasta_sql):
            messagebox.showerror("Formato Inválido", "Use el formato DD/MM/YYYY para las fechas.", parent=win)
            return None
        
        return (desde_sql or "1900-01-01", hasta_sql or "2999-12-31")

    def _fmt_mon(x: Any) -> str:
        try:
            return f"$ {float(x):,.2f}"
        except Exception:
            return str(x)

    def generar():
        try:
            rango = _validar_fechas_sql()
            if not rango: return
            desde_sql, hasta_sql = rango
            
            tipo = cb_tipo.get()
            
            if tipo == "Ventas por vendedor":
                setup_tree([("Fecha", 140), ("ID Venta", 90), ("Vendedor", 180), ("Total", 120)])
                vid = _vendedor_id_sel()
                datos = backend.reporte_ventas_por_vendedor(desde_sql, hasta_sql, vid)
                tree.delete(*tree.get_children())
                if not datos:
                    tree.insert("", "end", values=("Sin datos", "", "", "")); return
                for r in datos:
                    tree.insert("", "end", values=(
                        _formatear_fecha_para_ui(r.get("fecha")), # <-- ¡CORREGIDO!
                        r.get("id_venta") or "",
                        r.get("vendedor") or "",
                        _fmt_mon(r.get("total") or 0),
                    ))
            else: # Ventas diarias
                setup_tree([("Fecha (Día)", 140), ("Cant. Ventas", 110), ("Monto Total", 120)])
                datos = backend.obtener_ventas_diarias(desde_sql, hasta_sql)
                tree.delete(*tree.get_children())
                if not datos:
                    tree.insert("", "end", values=("Sin datos", "", "")); return
                for r in datos:
                    # Formatear solo la fecha, ya que viene como 'DATE'
                    fecha_dia = datetime.strptime(str(r.get("fecha")), "%Y-%m-%d").strftime("%d/%m/%Y")
                    tree.insert("", "end", values=(
                        fecha_dia, # <-- ¡CORREGIDO!
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
    on_periodo_seleccionado() # Para setear el default "Hoy"
    cb_periodo.current(0) # Lo volvemos a "Personalizado"
    on_periodo_seleccionado() # Para que active los campos
    
    win.grab_set()