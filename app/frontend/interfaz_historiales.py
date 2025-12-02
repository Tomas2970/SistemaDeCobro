# app/frontend/interfaz_historiales.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Any
from datetime import date, datetime, timedelta
import logging
import csv

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
    from app.database.permisos import tiene_permiso
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass
    def tiene_permiso(u, a): return True

try:
    from app.frontend.componentes_ui import SelectorFecha
except ImportError:
    class SelectorFecha(tk.Frame):
        def __init__(self, master, **kwargs):
            super().__init__(master, **kwargs)
            self.widget_entrada = tk.Entry(self, width=12)
            self.widget_entrada.pack(fill=tk.BOTH, expand=True)
            self.entrada = self.widget_entrada
        def get_date_sql(self):
            try:
                val = self.entrada.get()
                return datetime.strptime(val, "%d/%m/%Y").strftime("%Y-%m-%d")
            except: return None

logger = logging.getLogger(__name__)

def _formatear_fecha_para_ui(fecha_sql: Any) -> str:
    if not fecha_sql: return ""
    try:
        if isinstance(fecha_sql, (date, datetime)):
            return fecha_sql.strftime("%d/%m/%Y %H:%M")
        fecha_obj = datetime.fromisoformat(str(fecha_sql))
        return fecha_obj.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(fecha_sql)

def _fmt_mon(val: Any) -> str:
    try: return f"$ {float(val):,.2f}"
    except: return "$ 0.00"

# --- LÓGICA DE FILTROS RÁPIDOS ---
def aplicar_filtro_rapido(event, combo, entry_desde, entry_hasta):
    seleccion = combo.get()
    hoy = date.today()
    f_ini, f_fin = None, None

    if seleccion == "Hoy":
        f_ini, f_fin = hoy, hoy
    elif seleccion == "Ayer":
        f_ini = f_fin = hoy - timedelta(days=1)
    elif seleccion == "Esta Semana":
        f_ini = hoy - timedelta(days=hoy.weekday())
        f_fin = hoy
    elif seleccion == "Semana Pasada":
        fin_semana_pasada = hoy - timedelta(days=hoy.weekday() + 1)
        f_ini = fin_semana_pasada - timedelta(days=6)
        f_fin = fin_semana_pasada
    elif seleccion == "Este Mes":
        f_ini = hoy.replace(day=1)
        f_fin = hoy
    elif seleccion == "Mes Pasado":
        primero_este_mes = hoy.replace(day=1)
        ultimo_mes_pasado = primero_este_mes - timedelta(days=1)
        f_ini = ultimo_mes_pasado.replace(day=1)
        f_fin = ultimo_mes_pasado

    if f_ini and f_fin:
        entry_desde.delete(0, tk.END); entry_desde.insert(0, f_ini.strftime("%d/%m/%Y"))
        entry_hasta.delete(0, tk.END); entry_hasta.insert(0, f_fin.strftime("%d/%m/%Y"))


class Historiales:
    def __init__(self, parent: tk.Misc, backend, usuario: dict,
                 tab_inicial: int = 0,
                 filtro_fecha: str | None = None,
                 filtro_vendedor_id: int | None = None,
                 filtro_fecha_desde_default: str | None = None,
                 filtro_fecha_hasta_default: str | None = None,
                 filtro_venta_id: int | None = None,
                 filtro_compra_id: int | None = None,
                 filtro_cliente_id: int | None = None):
        
        self.backend = backend
        self.usuario = usuario
        
        self.win = tk.Toplevel(parent)
        self.win.title("📋 Historiales del Sistema")
        
        screen_height = self.win.winfo_screenwidth()
        altura = min(750, screen_height - 100)
        self.win.geometry(f"1250x{altura}")
        self.win.config(bg="#f4f4f8")
        
        frm_header = tk.Frame(self.win, bg="#2563eb", pady=15)
        frm_header.pack(fill="x")
        tk.Label(frm_header, text="HISTORIALES DEL SISTEMA", 
                 font=("Segoe UI", 16, "bold"), fg="white", bg="#2563eb").pack()

        # Datos para combos
        self.vendedor_ids = [None]
        self.vendedor_nombres = ["(Todos)"]
        self.cliente_ids = [None]
        self.cliente_nombres = ["(Todos)", "(Consumidor Final)"]
        self.proveedor_ids = [None]
        self.proveedor_nombres = ["(Todos)"]
        
        self.cargar_datos_combos()

        self.notebook = ttk.Notebook(self.win)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_ventas = ttk.Frame(self.notebook)
        self.tab_compras = ttk.Frame(self.notebook)
        self.tab_pagos = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_ventas, text="🛒 Ventas")
        self.notebook.add(self.tab_compras, text="📦 Compras")
        self.notebook.add(self.tab_pagos, text="💰 Pagos Cta. Cte.")

        # Verificar si tiene permiso para ver caja, y si es así, CREAR la pestaña
        if tiene_permiso(usuario, 'ver_historial_movimientos'):
            self.tab_caja = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_caja, text="💵 Movimientos de Caja")
            self._crear_tab_caja() # <--- ESTA ES LA LINEA QUE DABA ERROR

        self._crear_tab_ventas()
        self._crear_tab_compras()
        self._crear_tab_pagos()

        self.loaded_flags = {0: False, 1: False, 2: False, 3: False} 

        self._aplicar_filtros_iniciales(filtro_fecha, filtro_fecha_desde_default, 
                                      filtro_fecha_hasta_default, filtro_vendedor_id,
                                      filtro_venta_id, filtro_compra_id, filtro_cliente_id)

        if 0 <= tab_inicial < self.notebook.index("end"):
            self.notebook.select(tab_inicial)

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        configurar_navegacion_ventana(self.win)
        self.win.grab_set()

    def cargar_datos_combos(self):
        try:
            vends = self.backend.obtener_vendedores() or []
            self.vendedor_nombres = ["(Todos)"] + [v.get("nombre", "") for v in vends]
            self.vendedor_ids = [None] + [v.get("id_usuario") for v in vends]
            
            clis = self.backend.listar_clientes() or []
            self.cliente_nombres = ["(Todos)", "(Consumidor Final)"] + [c.get("nombre", "") for c in clis]
            self.cliente_ids = [None, 0] + [c.get("id_cliente") for c in clis]
            
            provs = self.backend.obtener_proveedores(incluir_inactivos=True) or []
            self.proveedor_nombres = ["(Todos)"] + [p.get("nombre", "") for p in provs]
            self.proveedor_ids = [None] + [p.get("id_proveedor") for p in provs]
        except Exception as e:
            logger.error(f"Error carga combos: {e}")

    def _aplicar_filtros_iniciales(self, f_fecha, f_desde, f_hasta, f_vend, f_vta, f_comp, f_cli):
        if f_fecha:
            self.fecha_desde_v.widget_entrada.delete(0, tk.END); self.fecha_desde_v.widget_entrada.insert(0, f_fecha)
            self.fecha_hasta_v.widget_entrada.delete(0, tk.END); self.fecha_hasta_v.widget_entrada.insert(0, f_fecha)
        elif f_desde and f_hasta:
            self.fecha_desde_v.widget_entrada.delete(0, tk.END); self.fecha_desde_v.widget_entrada.insert(0, f_desde)
            self.fecha_hasta_v.widget_entrada.delete(0, tk.END); self.fecha_hasta_v.widget_entrada.insert(0, f_hasta)
        
        if f_vend:
            try:
                idx = self.vendedor_ids.index(f_vend)
                self.cb_vendedor_v.current(idx)
            except: pass
            
        self.filtro_venta_id = f_vta
        self.filtro_compra_id = f_comp
        self.filtro_cliente_id = f_cli

        self.win.after(100, self.buscar_ventas)
        self.loaded_flags[0] = True

    def on_tab_change(self, event):
        idx = self.notebook.index(self.notebook.select())
        if not self.loaded_flags.get(idx, False):
            if idx == 1: self.buscar_compras()
            elif idx == 2: self.buscar_pagos()
            elif idx == 3 and hasattr(self, 'buscar_caja'): self.buscar_caja()
            self.loaded_flags[idx] = True

    # ----------------------------------------------------------------
    # PESTAÑA VENTAS
    # ----------------------------------------------------------------
    def _crear_tab_ventas(self):
        frm = tk.Frame(self.tab_ventas, bg="#f4f4f8", padx=10, pady=10)
        frm.pack(fill=tk.X)

        tk.Label(frm, text="Rango:", bg="#f4f4f8", font=("bold", 9)).grid(row=0, column=0, sticky="e")
        cb_rango = ttk.Combobox(frm, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Este Mes", "Mes Pasado"], state="readonly", width=12)
        cb_rango.current(0)
        cb_rango.grid(row=0, column=1, padx=5)

        tk.Label(frm, text="Desde:", bg="#f4f4f8").grid(row=0, column=2)
        self.fecha_desde_v = SelectorFecha(frm)
        self.fecha_desde_v.grid(row=0, column=3)
        self.fecha_desde_v.widget_entrada.delete(0, tk.END)
        self.fecha_desde_v.widget_entrada.insert(0, f"01/{date.today().month:02d}/{date.today().year}")

        tk.Label(frm, text="Hasta:", bg="#f4f4f8").grid(row=0, column=4)
        self.fecha_hasta_v = SelectorFecha(frm)
        self.fecha_hasta_v.grid(row=0, column=5)
        self.fecha_hasta_v.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_v.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        
        cb_rango.bind("<<ComboboxSelected>>", lambda e: aplicar_filtro_rapido(e, cb_rango, self.fecha_desde_v.widget_entrada, self.fecha_hasta_v.widget_entrada))

        tk.Label(frm, text="Vendedor:", bg="#f4f4f8").grid(row=1, column=0, sticky="e", pady=5)
        self.cb_vendedor_v = ttk.Combobox(frm, state="readonly", values=self.vendedor_nombres, width=15)
        self.cb_vendedor_v.current(0)
        self.cb_vendedor_v.grid(row=1, column=1, padx=5)

        tk.Label(frm, text="Cliente:", bg="#f4f4f8").grid(row=1, column=2, sticky="e")
        self.cb_cliente_v = ttk.Combobox(frm, state="readonly", values=self.cliente_nombres, width=15)
        self.cb_cliente_v.current(0)
        self.cb_cliente_v.grid(row=1, column=3, padx=5)

        tk.Button(frm, text="🔍 Buscar", command=self.buscar_ventas, bg="#03A9F4", fg="white").grid(row=1, column=4, padx=5)
        tk.Button(frm, text="📊 Exportar", command=lambda: self.exportar_a_csv(0), bg="#16a34a", fg="white").grid(row=1, column=5, padx=5)
        
        cols = ("ID", "Fecha", "Cliente", "Vendedor", "Total", "Estado", "Pago")
        self.tree_maestro_v = ttk.Treeview(self.tab_ventas, columns=cols, show="headings", height=10)
        self.tree_maestro_v.pack(fill="both", expand=True, padx=10, pady=5)
        for c in cols: self.tree_maestro_v.heading(c, text=c)
        self.tree_maestro_v.column("ID", width=50, anchor="center")
        self.tree_maestro_v.column("Total", anchor="e") 
        self.tree_maestro_v.bind("<<TreeviewSelect>>", self.mostrar_detalle_venta)

        tk.Label(self.tab_ventas, text="Detalle de la venta seleccionada:", bg="#f4f4f8", font=("bold")).pack(anchor="w", padx=10)
        cols_d = ("Prod", "Código", "Cant", "P. Unit", "Subtotal")
        self.tree_detalle_v = ttk.Treeview(self.tab_ventas, columns=cols_d, show="headings", height=6)
        self.tree_detalle_v.pack(fill="both", expand=True, padx=10, pady=(0,10))
        for c in cols_d: self.tree_detalle_v.heading(c, text=c)
        self.tree_detalle_v.column("P. Unit", anchor="e")
        self.tree_detalle_v.column("Subtotal", anchor="e")

    def buscar_ventas(self):
        for i in self.tree_maestro_v.get_children(): self.tree_maestro_v.delete(i)
        for i in self.tree_detalle_v.get_children(): self.tree_detalle_v.delete(i)
        try:
            d_sql = self.fecha_desde_v.get_date_sql()
            h_sql = self.fecha_hasta_v.get_date_sql()
            id_vend = self.vendedor_ids[self.cb_vendedor_v.current()]
            id_cli = self.cliente_ids[self.cb_cliente_v.current()]
            
            if hasattr(self, 'filtro_venta_id') and self.filtro_venta_id:
                ventas = [v for v in self.backend.obtener_ventas_maestro(None, None, None, None) 
                          if v['id_venta'] == self.filtro_venta_id]
                self.filtro_venta_id = None 
            else:
                ventas = self.backend.obtener_ventas_maestro(d_sql, h_sql, id_cli, id_vend)
                
            for v in ventas:
                self.tree_maestro_v.insert("", tk.END, values=[
                    v.get('id_venta'), _formatear_fecha_para_ui(v.get('fecha')),
                    v.get('cliente') or "Consumidor Final", v.get('vendedor'),
                    _fmt_mon(v.get('total')), v.get('estado'), v.get('tipo_pago')
                ])
        except Exception as e: messagebox.showerror("Error", str(e))

    def mostrar_detalle_venta(self, event=None):
        for i in self.tree_detalle_v.get_children(): self.tree_detalle_v.delete(i)
        sel = self.tree_maestro_v.selection()
        if not sel: return
        id_v = self.tree_maestro_v.item(sel[0], "values")[0]
        try:
            dets = self.backend.obtener_venta_detalle(int(id_v))
            for d in dets:
                self.tree_detalle_v.insert("", tk.END, values=[
                    d.get('nombre_producto'), d.get('codigo_barras'),
                    d.get('cantidad'), _fmt_mon(d.get('precio_unitario')),
                    _fmt_mon(d.get('subtotal'))
                ])
        except Exception: pass

    # ----------------------------------------------------------------
    # PESTAÑA COMPRAS
    # ----------------------------------------------------------------
    def _crear_tab_compras(self):
        frm = tk.Frame(self.tab_compras, bg="#f4f4f8", padx=10, pady=10)
        frm.pack(fill=tk.X)

        tk.Label(frm, text="Rango:", bg="#f4f4f8", font=("bold", 9)).grid(row=0, column=0, sticky="e")
        cb_rango = ttk.Combobox(frm, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Este Mes", "Mes Pasado"], state="readonly", width=12)
        cb_rango.current(0)
        cb_rango.grid(row=0, column=1, padx=5)

        tk.Label(frm, text="Desde:", bg="#f4f4f8").grid(row=0, column=2)
        self.fecha_desde_c = SelectorFecha(frm)
        self.fecha_desde_c.grid(row=0, column=3)
        self.fecha_desde_c.widget_entrada.delete(0, tk.END)
        self.fecha_desde_c.widget_entrada.insert(0, f"01/{date.today().month:02d}/{date.today().year}")

        tk.Label(frm, text="Hasta:", bg="#f4f4f8").grid(row=0, column=4)
        self.fecha_hasta_c = SelectorFecha(frm)
        self.fecha_hasta_c.grid(row=0, column=5)
        self.fecha_hasta_c.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_c.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        
        cb_rango.bind("<<ComboboxSelected>>", lambda e: aplicar_filtro_rapido(e, cb_rango, self.fecha_desde_c.widget_entrada, self.fecha_hasta_c.widget_entrada))

        tk.Label(frm, text="Proveedor:", bg="#f4f4f8").grid(row=1, column=0, sticky="e", pady=5)
        self.cb_proveedor_c = ttk.Combobox(frm, state="readonly", values=self.proveedor_nombres, width=20)
        self.cb_proveedor_c.current(0)
        self.cb_proveedor_c.grid(row=1, column=1, columnspan=2, sticky="w", padx=5)

        tk.Label(frm, text="Usuario:", bg="#f4f4f8").grid(row=1, column=3, sticky="e")
        self.cb_usuario_c = ttk.Combobox(frm, state="readonly", values=self.vendedor_nombres, width=15)
        self.cb_usuario_c.current(0)
        self.cb_usuario_c.grid(row=1, column=4, padx=5)

        tk.Button(frm, text="🔍 Buscar", command=self.buscar_compras, bg="#03A9F4", fg="white").grid(row=1, column=5)
        tk.Button(frm, text="📊 Exportar", command=lambda: self.exportar_a_csv(1), bg="#16a34a", fg="white").grid(row=1, column=6, padx=5)

        cols = ("ID", "Fecha", "Proveedor", "Total", "Estado", "Pago", "Usuario")
        self.tree_maestro_c = ttk.Treeview(self.tab_compras, columns=cols, show="headings", height=8)
        self.tree_maestro_c.pack(fill="both", expand=True, padx=10, pady=5)
        for c in cols: self.tree_maestro_c.heading(c, text=c)
        self.tree_maestro_c.column("ID", width=50, anchor="center")
        self.tree_maestro_c.column("Total", anchor="e")
        self.tree_maestro_c.column("Estado", width=80, anchor="center")
        self.tree_maestro_c.column("Pago", width=100, anchor="center")
        self.tree_maestro_c.bind("<<TreeviewSelect>>", self.mostrar_detalle_compra)

        cols_d = ("Prod", "Código", "Cant", "Costo", "Subtotal")
        self.tree_detalle_c = ttk.Treeview(self.tab_compras, columns=cols_d, show="headings", height=6)
        self.tree_detalle_c.pack(fill="both", expand=True, padx=10, pady=(0,10))
        for c in cols_d: self.tree_detalle_c.heading(c, text=c)
        self.tree_detalle_c.column("Costo", anchor="e"); self.tree_detalle_c.column("Subtotal", anchor="e")

    def buscar_compras(self):
        for i in self.tree_maestro_c.get_children(): self.tree_maestro_c.delete(i)
        for i in self.tree_detalle_c.get_children(): self.tree_detalle_c.delete(i)
        try:
            d_sql = self.fecha_desde_c.get_date_sql()
            h_sql = self.fecha_hasta_c.get_date_sql()
            id_prov = self.proveedor_ids[self.cb_proveedor_c.current()]
            
            if hasattr(self, 'filtro_compra_id') and self.filtro_compra_id:
                compras = [c for c in self.backend.obtener_compras_maestro(None, None, None) 
                           if c['id_compra'] == self.filtro_compra_id]
                self.filtro_compra_id = None
            else:
                compras = self.backend.obtener_compras_maestro(d_sql, h_sql, id_prov)
            
            nombre_usuario_sel = self.vendedor_nombres[self.cb_usuario_c.current()]
            if nombre_usuario_sel != "(Todos)":
                compras = [c for c in compras if c.get('usuario') == nombre_usuario_sel]

            for c in compras:
                medio = c.get('medio_pago') or '-'
                self.tree_maestro_c.insert("", tk.END, values=[
                    c.get('id_compra'), _formatear_fecha_para_ui(c.get('fecha')),
                    c.get('proveedor'), _fmt_mon(c.get('total')),
                    c.get('estado'), medio, c.get('usuario')
                ])
        except Exception as e: logger.error(f"Error buscar compras: {e}")

    def mostrar_detalle_compra(self, event=None):
        for i in self.tree_detalle_c.get_children(): self.tree_detalle_c.delete(i)
        sel = self.tree_maestro_c.selection()
        if not sel: return
        id_c = self.tree_maestro_c.item(sel[0], "values")[0]
        try:
            dets = self.backend.obtener_compra_detalle(int(id_c))
            for d in dets:
                self.tree_detalle_c.insert("", tk.END, values=[
                    d.get('nombre_producto'), d.get('codigo_barras'),
                    d.get('cantidad'), _fmt_mon(d.get('precio_unitario')),
                    _fmt_mon(d.get('subtotal'))
                ])
        except Exception: pass

    # ----------------------------------------------------------------
    # PESTAÑA PAGOS
    # ----------------------------------------------------------------
    def _crear_tab_pagos(self):
        frm = tk.Frame(self.tab_pagos, bg="#f4f4f8", padx=10, pady=10)
        frm.pack(fill=tk.X)

        tk.Label(frm, text="Rango:", bg="#f4f4f8", font=("bold", 9)).grid(row=0, column=0, sticky="e")
        cb_rango = ttk.Combobox(frm, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Este Mes", "Mes Pasado"], state="readonly", width=12)
        cb_rango.current(0)
        cb_rango.grid(row=0, column=1, padx=5)

        tk.Label(frm, text="Desde:", bg="#f4f4f8").grid(row=0, column=2)
        self.fecha_desde_p = SelectorFecha(frm)
        self.fecha_desde_p.grid(row=0, column=3)
        self.fecha_desde_p.widget_entrada.delete(0, tk.END)
        self.fecha_desde_p.widget_entrada.insert(0, f"01/{date.today().month:02d}/{date.today().year}")

        tk.Label(frm, text="Hasta:", bg="#f4f4f8").grid(row=0, column=4)
        self.fecha_hasta_p = SelectorFecha(frm)
        self.fecha_hasta_p.grid(row=0, column=5)
        self.fecha_hasta_p.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_p.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        
        cb_rango.bind("<<ComboboxSelected>>", lambda e: aplicar_filtro_rapido(e, cb_rango, self.fecha_desde_p.widget_entrada, self.fecha_hasta_p.widget_entrada))

        tk.Label(frm, text="Cliente:", bg="#f4f4f8").grid(row=1, column=0, sticky="e", pady=5)
        self.cb_cliente_p = ttk.Combobox(frm, state="readonly", values=self.cliente_nombres, width=20)
        self.cb_cliente_p.current(0)
        self.cb_cliente_p.grid(row=1, column=1, padx=5)

        tk.Label(frm, text="Registró:", bg="#f4f4f8").grid(row=1, column=2, sticky="e")
        self.cb_usuario_p = ttk.Combobox(frm, state="readonly", values=self.vendedor_nombres, width=15)
        self.cb_usuario_p.current(0)
        self.cb_usuario_p.grid(row=1, column=3, padx=5)

        tk.Button(frm, text="🔍 Buscar", command=self.buscar_pagos, bg="#03A9F4", fg="white").grid(row=1, column=4, padx=5)
        tk.Button(frm, text="📊 Exportar", command=lambda: self.exportar_a_csv(2), bg="#16a34a", fg="white").grid(row=1, column=5, padx=5)

        cols = ("ID", "Fecha", "Cliente", "Monto", "Método", "Registró")
        self.tree_pagos = ttk.Treeview(self.tab_pagos, columns=cols, show="headings", height=12)
        self.tree_pagos.pack(fill="both", expand=True, padx=10, pady=10)
        for c in cols: self.tree_pagos.heading(c, text=c)
        self.tree_pagos.column("ID", width=50, anchor="center")
        self.tree_pagos.column("Monto", anchor="e")

    def buscar_pagos(self):
        for i in self.tree_pagos.get_children(): self.tree_pagos.delete(i)
        try:
            d_sql = self.fecha_desde_p.get_date_sql()
            h_sql = self.fecha_hasta_p.get_date_sql()
            id_cli = self.cliente_ids[self.cb_cliente_p.current()]
            id_usuario = self.vendedor_ids[self.cb_usuario_p.current()]
            
            if hasattr(self, 'filtro_cliente_id') and self.filtro_cliente_id:
                id_cli = self.filtro_cliente_id
                self.filtro_cliente_id = None
                try: self.cb_cliente_p.current(self.cliente_ids.index(id_cli))
                except: pass

            pagos = self.backend.obtener_pagos_maestro(d_sql, h_sql, id_cli, id_usuario)
            for p in pagos:
                self.tree_pagos.insert("", tk.END, values=[
                    p.get('id_pago'), _formatear_fecha_para_ui(p.get('fecha')),
                    p.get('cliente_nombre'), _fmt_mon(p.get('monto')),
                    p.get('metodo'), p.get('usuario_nombre')
                ])
        except Exception as e: logger.error(f"Error pagos: {e}")

    # ----------------------------------------------------------------
    # PESTAÑA CAJA (RESTAURADA)
    # ----------------------------------------------------------------
    def _crear_tab_caja(self):
        frm = tk.Frame(self.tab_caja, bg="#f4f4f8", padx=10, pady=10)
        frm.pack(fill=tk.X)
        
        # FILA 0: Fechas
        tk.Label(frm, text="Rango:", bg="#f4f4f8", font=("bold", 9)).grid(row=0, column=0, sticky="e")
        cb_rango = ttk.Combobox(frm, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Este Mes", "Mes Pasado"], state="readonly", width=12)
        cb_rango.current(0)
        cb_rango.grid(row=0, column=1, padx=5)

        tk.Label(frm, text="Desde:", bg="#f4f4f8").grid(row=0, column=2)
        self.fecha_desde_cj = SelectorFecha(frm)
        self.fecha_desde_cj.grid(row=0, column=3)
        self.fecha_desde_cj.widget_entrada.delete(0, tk.END)
        self.fecha_desde_cj.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))

        tk.Label(frm, text="Hasta:", bg="#f4f4f8").grid(row=0, column=4)
        self.fecha_hasta_cj = SelectorFecha(frm)
        self.fecha_hasta_cj.grid(row=0, column=5)
        self.fecha_hasta_cj.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_cj.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        
        cb_rango.bind("<<ComboboxSelected>>", lambda e: aplicar_filtro_rapido(e, cb_rango, self.fecha_desde_cj.widget_entrada, self.fecha_hasta_cj.widget_entrada))
        
        # FILA 1: Filtro de Usuario y Botón Buscar
        tk.Label(frm, text="Usuario:", bg="#f4f4f8").grid(row=1, column=0, sticky="e", pady=5)
        self.cb_usuario_caja = ttk.Combobox(frm, state="readonly", values=self.vendedor_nombres, width=15)
        self.cb_usuario_caja.current(0)
        self.cb_usuario_caja.grid(row=1, column=1, padx=5, sticky="w")
        
        tk.Button(frm, text="🔍 Buscar", command=self.buscar_caja, bg="#03A9F4", fg="white").grid(row=1, column=2, padx=10, sticky="w")
        tk.Button(frm, text="📊 Exportar", command=lambda: self.exportar_a_csv(3), bg="#16a34a", fg="white").grid(row=1, column=3, padx=10, sticky="w")
        
        cols = ("ID", "Fecha", "Usuario", "Tipo", "Motivo", "Monto", "Desc")
        self.tree_caja = ttk.Treeview(self.tab_caja, columns=cols, show="headings", height=15)
        self.tree_caja.pack(fill="both", expand=True, padx=10, pady=10)
        
        for c in cols: self.tree_caja.heading(c, text=c)
        self.tree_caja.column("ID", width=50); self.tree_caja.column("Monto", width=100, anchor="e")
        self.tree_caja.column("Desc", width=250)
        
        self.tree_caja.tag_configure('ingreso', background='#d1fae5')
        self.tree_caja.tag_configure('egreso', background='#fee2e2')

    def buscar_caja(self):
        for i in self.tree_caja.get_children(): self.tree_caja.delete(i)
        try:
            d_sql = self.fecha_desde_cj.get_date_sql()
            h_sql = self.fecha_hasta_cj.get_date_sql()
            data = self.backend.obtener_historial_movimientos_caja(d_sql, h_sql)
            
            # Filtro por usuario en el cliente
            nombre_usuario_sel = self.vendedor_nombres[self.cb_usuario_caja.current()]
            if nombre_usuario_sel != "(Todos)":
                data = [r for r in data if r.get('usuario_nombre') == nombre_usuario_sel]
            
            for r in data:
                tag = r['tipo']
                tipo_txt = "➕" if r['tipo'] == 'ingreso' else "➖"
                self.tree_caja.insert("", "end", values=(
                    r['id_movimiento'], _formatear_fecha_para_ui(r['fecha_hora']), 
                    r['usuario_nombre'], tipo_txt, r['motivo'], 
                    _fmt_mon(r['monto']), r['descripcion']
                ), tags=(tag,))
        except Exception as e: logger.error(f"Error caja: {e}")

    # ----------------------------------------------------------------
    # EXPORTACIÓN SEGURA E INTELIGENTE
    # ----------------------------------------------------------------
    def exportar_a_csv(self, tab_id):
        hoy = datetime.now().strftime("%d-%m-%Y")
        nombres = {0: "ventas", 1: "compras", 2: "pagos", 3: "caja"}
        nombre_base = f"{nombres.get(tab_id, 'datos')}_{hoy}.csv"

        # 1. Si son Pagos o Caja, exportamos directo (son tablas simples)
        if tab_id in [2, 3]:
            if tab_id == 2: tree = self.tree_pagos
            else: tree = self.tree_caja
            self._guardar_csv_simple(tree, nombre_base)
            return

        # 2. Si son Ventas o Compras, preguntamos qué quiere el usuario
        opcion = self._preguntar_tipo_exportacion()
        if not opcion: return

        # Definir árboles según pestaña
        tree_m = self.tree_maestro_v if tab_id == 0 else self.tree_maestro_c
        tree_d = self.tree_detalle_v if tab_id == 0 else self.tree_detalle_c

        # 3. Ejecutar lógica
        if opcion == "maestro":
            self._guardar_csv_simple(tree_m, f"listado_general_{nombre_base}")

        elif opcion == "detalle":
            if not tree_d.get_children():
                messagebox.showwarning("Atención", "No hay detalles visibles. Selecciona una venta primero.")
                return
            sel = tree_m.selection()
            if not sel: return
            datos_cabecera = tree_m.item(sel[0], 'values')
            self._guardar_csv_combinado([datos_cabecera], tree_m, tab_id, f"detalle_venta_{datos_cabecera[0]}_{nombre_base}", True)

        elif opcion == "ambos":
            items_maestro = [tree_m.item(i, 'values') for i in tree_m.get_children()]
            self._guardar_csv_combinado(items_maestro, tree_m, tab_id, f"reporte_completo_{nombre_base}", False)

    def _preguntar_tipo_exportacion(self) -> str | None:
        dialog = tk.Toplevel(self.win)
        dialog.title("Exportar a Excel")
        dialog.geometry("400x280")
        dialog.config(bg="white")
        dialog.resizable(False, False)
        try: configurar_navegacion_ventana(dialog)
        except: pass

        seleccion = {"valor": None}
        tk.Label(dialog, text="Seleccione el tipo de reporte:", font=("Segoe UI", 11, "bold"), bg="white").pack(pady=15)

        def set_sel(val):
            seleccion["valor"] = val
            dialog.destroy()

        b1 = ttk.Button(dialog, text="📄 Listado General (Resumen)", command=lambda: set_sel("maestro"))
        b1.pack(fill="x", padx=30, pady=5)
        tk.Label(dialog, text="1 renglón por operación. Ideal para ver totales.", bg="white", fg="gray", font=("Arial", 8)).pack()

        b2 = ttk.Button(dialog, text="🔍 Detalle de la Selección", command=lambda: set_sel("detalle"))
        b2.pack(fill="x", padx=30, pady=5)
        tk.Label(dialog, text="Lista de productos de la fila seleccionada.", bg="white", fg="gray", font=("Arial", 8)).pack()

        b3 = ttk.Button(dialog, text="📑 Reporte Completo (Todo)", command=lambda: set_sel("ambos"))
        b3.pack(fill="x", padx=30, pady=5)
        tk.Label(dialog, text="Sábana de datos completa con todos los productos.", bg="white", fg="gray", font=("Arial", 8)).pack()

        dialog.transient(self.win)
        dialog.grab_set()
        self.win.wait_window(dialog)
        return seleccion["valor"]

    def _guardar_csv_simple(self, tree: ttk.Treeview, nombre_archivo: str):
        if not tree.get_children(): return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Excel CSV", "*.csv")], initialfile=nombre_archivo)
        if not path: return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f, delimiter=';')
                w.writerow([tree.heading(c)['text'] for c in tree['columns']])
                for item in tree.get_children(): w.writerow(tree.item(item, 'values'))
            messagebox.showinfo("Éxito", "Archivo exportado.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def _guardar_csv_combinado(self, lista_datos_maestro, tree_maestro, tab_id, nombre_archivo, usar_detalle_visual=False):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Excel CSV", "*.csv")], initialfile=nombre_archivo)
        if not path: return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f, delimiter=';')
                cols_m = [tree_maestro.heading(c)['text'] for c in tree_maestro['columns']]
                if tab_id == 0: cols_d = ["Producto", "Código", "Cantidad", "P. Unit", "Subtotal"]
                else: cols_d = ["Producto", "Código", "Cantidad", "Costo", "Subtotal"]
                w.writerow(cols_m + cols_d)

                items_detalle_visual = []
                if usar_detalle_visual:
                    tree_d = self.tree_detalle_v if tab_id == 0 else self.tree_detalle_c
                    for item in tree_d.get_children():
                        items_detalle_visual.append(tree_d.item(item, 'values'))

                for vals_m in lista_datos_maestro:
                    id_operacion = vals_m[0]
                    filas_productos = []
                    if usar_detalle_visual:
                        filas_productos = items_detalle_visual
                    else:
                        detalles_bd = []
                        if tab_id == 0: detalles_bd = self.backend.obtener_venta_detalle(int(id_operacion))
                        else: detalles_bd = self.backend.obtener_compra_detalle(int(id_operacion))
                        for d in detalles_bd:
                            filas_productos.append([
                                d.get('nombre_producto', ''), d.get('codigo_barras', ''),
                                d.get('cantidad', 0),
                                _fmt_mon(d.get('precio_unitario' if tab_id==0 else 'costo_unitario', 0)),
                                _fmt_mon(d.get('subtotal', 0))
                            ])

                    clean_m = [str(x).strip() for x in vals_m]
                    if filas_productos:
                        for row_prod in filas_productos:
                            clean_prod = [str(x).strip() for x in row_prod]
                            w.writerow(clean_m + clean_prod)
                    else:
                        w.writerow(clean_m + [""]*len(cols_d))

            messagebox.showinfo("Éxito", "Reporte generado con contexto.")
        except Exception as e:
            logger.error(f"Error csv combinado: {e}")
            messagebox.showerror("Error", f"Error: {e}")

ui_historiales = Historiales