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
        
        altura = 720 
        self.win.geometry(f"1300x{altura}") 
        self.win.config(bg="#f4f4f8")
        
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        style.configure("Modern.Treeview",
                        background="#ffffff",
                        foreground="#1f2937",
                        rowheight=30,
                        fieldbackground="#ffffff",
                        borderwidth=0,
                        font=('Segoe UI', 9))
        
        style.configure("Modern.Treeview.Heading",
                        background="#f3f4f6",
                        foreground="#374151",
                        relief="flat",
                        borderwidth=1,
                        font=('Segoe UI', 10, 'bold'))
        
        style.map("Modern.Treeview.Heading",
                  background=[('active', '#e5e7eb')])

        frm_header = tk.Frame(self.win, bg="#3b82f6", pady=15)
        frm_header.pack(fill="x")
        tk.Label(frm_header, text="HISTORIALES DEL SISTEMA", 
                 font=("Segoe UI", 16, "bold"), fg="white", bg="#3b82f6").pack()

        self.vendedor_ids = [None]
        self.vendedor_nombres = ["(Todos)"]
        self.cliente_ids = [None, 0]
        self.cliente_nombres = ["(Todos)", "(Consumidor Final)"]
        self.cliente_ids_pagos = [None]
        self.cliente_nombres_pagos = ["(Todos)"]
        self.proveedor_ids = [None]
        self.proveedor_nombres = ["(Todos)"]
        self.proveedores_map_id = {}
        self.proveedores_map_nombre = {}
        
        # cargar_datos_combos se difiere para que la ventana abra sin demora
        self.win.after(50, self.cargar_datos_combos)

        # Footer con boton cerrar - se packea ANTES del notebook para reservar espacio
        frm_footer = tk.Frame(self.win, bg="#f4f4f8", pady=8)
        frm_footer.pack(fill="x", padx=10, side=tk.BOTTOM)
        tk.Button(frm_footer, text="Cerrar", command=self.win.destroy,
                  bg="#64748b", fg="white", font=("Segoe UI", 10),
                  relief="flat", padx=20, pady=6, cursor="hand2").pack(side=tk.RIGHT)

        self.notebook = ttk.Notebook(self.win)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(10,0))

        self.tab_ventas = ttk.Frame(self.notebook)
        self.tab_compras = ttk.Frame(self.notebook)
        self.tab_pagos = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_ventas, text="🛒 Ventas")
        self.notebook.add(self.tab_compras, text="📦 Compras")
        self.notebook.add(self.tab_pagos, text="💰 Pagos Cta. Cte.")

        if tiene_permiso(usuario, 'ver_historial_movimientos'):
            self.tab_caja = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_caja, text="💵 Movimientos de Caja")
            self._crear_tab_caja()
        
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
        
    def crear_boton_accion(self, parent, text, command, color, width=12):
        btn = tk.Button(parent,
                        text=text,
                        command=command,
                        bg=color,
                        fg="white",
                        font=("Segoe UI", 10, "bold"),
                        relief="flat",
                        padx=12,
                        pady=6,
                        cursor="hand2",
                        width=width,
                        activebackground=self._darken_color(color))
        return btn

    def _darken_color(self, hex_color):
        colors = {
            "#3b82f6": "#2563eb",
            "#10b981": "#059669",
            "#16a34a": "#059669",
            "#03A9F4": "#0288d1",
            "#ef4444": "#dc2626",
            "#f59e0b": "#d97706"
        }
        return colors.get(hex_color, hex_color)

    def cargar_datos_combos(self):
        try:
            vends = self.backend.obtener_vendedores() or []
            self.vendedor_nombres = ["(Todos)"] + [v.get("nombre", "") for v in vends]
            self.vendedor_ids = [None] + [v.get("id_usuario") for v in vends]
            
            clis = self.backend.listar_clientes() or []
            self.cliente_nombres = ["(Todos)", "(Consumidor Final)"] + [c.get("nombre", "") for c in clis]
            self.cliente_ids = [None, 0] + [c.get("id_cliente") for c in clis]
            
            self.cliente_nombres_pagos = ["(Todos)"] + [c.get("nombre", "") for c in clis]
            self.cliente_ids_pagos = [None] + [c.get("id_cliente") for c in clis]
            
            provs = self.backend.obtener_proveedores(incluir_inactivos=True) or []
            self.proveedor_nombres = ["(Todos)"] + [p.get("nombre", "") for p in provs]
            self.proveedor_ids = [None] + [p.get("id_proveedor") for p in provs]
            self.proveedores_map_id = {p['id_proveedor']: p for p in provs} 
            self.proveedores_map_nombre = {p['nombre']: p for p in provs} 
        except Exception as e:
            logger.error(f"Error carga combos: {e}")
        finally:
            # Actualizar los combos ya renderizados con los datos recién cargados
            try:
                if hasattr(self, 'cb_vendedor_v'):
                    self.cb_vendedor_v['values'] = self.vendedor_nombres
                    self.cb_vendedor_v.current(0)
                if hasattr(self, 'cb_cliente_v'):
                    self.cb_cliente_v['values'] = self.cliente_nombres
                    self.cb_cliente_v.current(0)
                if hasattr(self, 'cb_proveedor_c'):
                    self.cb_proveedor_c['values'] = self.proveedor_nombres
                    self.cb_proveedor_c.current(0)
                if hasattr(self, 'cb_cliente_p'):
                    self.cb_cliente_p['values'] = self.cliente_nombres_pagos
                    self.cb_cliente_p.current(0)
            except Exception:
                pass

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
        tab_text = self.notebook.tab(idx, "text")
        
        if "Ventas" in tab_text: self.buscar_ventas()
        elif "Compras" in tab_text: self.buscar_compras()
        elif "Pagos" in tab_text: self.buscar_pagos()
        elif "Caja" in tab_text: self.buscar_caja()

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

        self.crear_boton_accion(frm, "🔍 Buscar", self.buscar_ventas, "#3b82f6", width=10).grid(row=1, column=4, padx=5)
        self.crear_boton_accion(frm, "📊 Exportar", lambda: self.exportar_a_csv(0), "#10b981", width=10).grid(row=1, column=5, padx=5)
        
        cols = ("ID", "Fecha", "Cliente", "Vendedor", "Total", "Estado", "Pago")
        self.tree_maestro_v = ttk.Treeview(self.tab_ventas, columns=cols, show="headings", height=8, style="Modern.Treeview") 
        self.tree_maestro_v.pack(fill="both", expand=True, padx=10, pady=5)
        for c in cols: self.tree_maestro_v.heading(c, text=c)
        self.tree_maestro_v.column("ID", width=0, minwidth=0, stretch=False)  # oculta, usada internamente
        self.tree_maestro_v.column("Total", anchor="e") 
        self.tree_maestro_v.bind("<<TreeviewSelect>>", self.mostrar_detalle_venta)

        cols_d = ("Prod", "Código", "Cant", "P. Unit", "Subtotal")
        self.tree_detalle_v = ttk.Treeview(self.tab_ventas, columns=cols_d, show="headings", height=8, style="Modern.Treeview") 
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

        self.crear_boton_accion(frm, "🔍 Buscar", self.buscar_compras, "#3b82f6", width=10).grid(row=1, column=5)
        self.crear_boton_accion(frm, "📊 Exportar", lambda: self.exportar_a_csv(1), "#10b981", width=10).grid(row=1, column=6, padx=5)

        cols = ("ID", "Fecha", "Empresa", "CUIT", "Total", "Estado", "Pago", "Usuario")
        self.tree_maestro_c = ttk.Treeview(self.tab_compras, columns=cols, show="headings", height=8, style="Modern.Treeview")
        self.tree_maestro_c.pack(fill="both", expand=True, padx=10, pady=5)
        for c in cols: self.tree_maestro_c.heading(c, text=c)
        self.tree_maestro_c.column("ID", width=0, minwidth=0, stretch=False)  # oculta, usada internamente
        self.tree_maestro_c.column("Total", anchor="e")
        self.tree_maestro_c.column("Estado", width=100, anchor="center")
        self.tree_maestro_c.column("Pago", width=100, anchor="center")
        self.tree_maestro_c.column("Empresa", width=160)
        self.tree_maestro_c.column("CUIT", width=110, anchor="center")
        self.tree_maestro_c.bind("<<TreeviewSelect>>", self.mostrar_detalle_compra)

        cols_d = ("Prod", "Código", "Cant", "Costo", "Precio Venta Asignado", "Subtotal")
        self.tree_detalle_c = ttk.Treeview(self.tab_compras, columns=cols_d, show="headings", height=6, style="Modern.Treeview")
        self.tree_detalle_c.pack(fill="both", expand=True, padx=10, pady=(0,10))
        for c in cols_d: self.tree_detalle_c.heading(c, text=c)
        self.tree_detalle_c.column("Costo", anchor="e", width=100)
        self.tree_detalle_c.column("Precio Venta Asignado", anchor="e", width=100)
        self.tree_detalle_c.column("Subtotal", anchor="e", width=100)

    def buscar_compras(self):
        for i in self.tree_maestro_c.get_children(): self.tree_maestro_c.delete(i)
        for i in self.tree_detalle_c.get_children(): self.tree_detalle_c.delete(i)
        try:
            d_sql = self.fecha_desde_c.get_date_sql()
            h_sql = self.fecha_hasta_c.get_date_sql()
            id_prov_filtro = self.proveedor_ids[self.cb_proveedor_c.current()]
            
            if hasattr(self, 'filtro_compra_id') and self.filtro_compra_id:
                compras = [c for c in self.backend.obtener_compras_maestro(None, None, None) 
                            if c['id_compra'] == self.filtro_compra_id]
                self.filtro_compra_id = None
            else:
                compras = self.backend.obtener_compras_maestro(d_sql, h_sql, id_prov_filtro)
            
            prov_map = self.proveedores_map_nombre

            nombre_usuario_sel = self.vendedor_nombres[self.cb_usuario_c.current()]
            if nombre_usuario_sel != "(Todos)":
                compras = [c for c in compras if c.get('usuario') == nombre_usuario_sel]

            for c in compras:
                medio = c.get('medio_pago') or '-'
                prov_data = prov_map.get(c.get('proveedor'), {})
                
                cuit_val = prov_data.get('cuit', '-')
                empresa_val = prov_data.get('empresa') or c.get('proveedor') or '-'

                self.tree_maestro_c.insert("", tk.END, values=[
                    c.get('id_compra'), 
                    _formatear_fecha_para_ui(c.get('fecha')),
                    empresa_val, 
                    cuit_val, 
                    _fmt_mon(c.get('total')),
                    c.get('estado'), 
                    medio, 
                    c.get('usuario')
                ])
        except Exception as e: logger.error(f"Error buscar compras: {e}")

    def mostrar_detalle_compra(self, event=None):
        for i in self.tree_detalle_c.get_children(): self.tree_detalle_c.delete(i)
        sel = self.tree_maestro_c.selection()
        if not sel: return
        
        id_c = self.tree_maestro_c.item(sel[0], "values")[0]
        

        if self.tree_maestro_c.item(sel[0], "values")[5] == "PAGO DEUDA":
            return
            
        try:
            dets = self.backend.obtener_compra_detalle(int(id_c))
            for d in dets:
                precio_venta = d.get('precio_venta_historico')
                precio_venta_txt = _fmt_mon(precio_venta) if precio_venta else "-"
                
                self.tree_detalle_c.insert("", tk.END, values=[
                    d.get('nombre_producto'),
                    d.get('codigo_barras'),
                    d.get('cantidad'),
                    _fmt_mon(d.get('precio_unitario')),
                    precio_venta_txt,
                    _fmt_mon(d.get('subtotal'))
                ])
        except Exception as e:
            logger.error(f"Error al mostrar detalle compra: {e}")
            pass

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
        self.cb_cliente_p = ttk.Combobox(frm, state="readonly", values=self.cliente_nombres_pagos, width=20)
        self.cb_cliente_p.current(0)
        self.cb_cliente_p.grid(row=1, column=1, padx=5)

        tk.Label(frm, text="Registró:", bg="#f4f4f8").grid(row=1, column=2, sticky="e")
        self.cb_usuario_p = ttk.Combobox(frm, state="readonly", values=self.vendedor_nombres, width=15)
        self.cb_usuario_p.current(0)
        self.cb_usuario_p.grid(row=1, column=3, padx=5)

        self.crear_boton_accion(frm, "🔍 Buscar", self.buscar_pagos, "#3b82f6", width=10).grid(row=1, column=4, padx=5)
        self.crear_boton_accion(frm, "📊 Exportar", lambda: self.exportar_a_csv(2), "#10b981", width=10).grid(row=1, column=5, padx=5)

        cols = ("Fecha", "Cliente", "Monto", "Método", "Registró")
        self.tree_pagos = ttk.Treeview(self.tab_pagos, columns=cols, show="headings", height=12, style="Modern.Treeview")
        self.tree_pagos.pack(fill="both", expand=True, padx=10, pady=10)
        for c in cols: self.tree_pagos.heading(c, text=c)
        self.tree_pagos.column("Monto", anchor="e")

    def buscar_pagos(self):
        for i in self.tree_pagos.get_children(): self.tree_pagos.delete(i)
        try:
            d_sql = self.fecha_desde_p.get_date_sql()
            h_sql = self.fecha_hasta_p.get_date_sql()
            
            id_cli_idx = self.cb_cliente_p.current()
            id_cli = self.cliente_ids_pagos[id_cli_idx] 
            
            id_usuario = self.vendedor_ids[self.cb_usuario_p.current()]
            
            if hasattr(self, 'filtro_cliente_id') and self.filtro_cliente_id:
                id_cli = self.filtro_cliente_id
                self.filtro_cliente_id = None
                try: self.cb_cliente_p.current(self.cliente_ids_pagos.index(id_cli))
                except: pass

            pagos = self.backend.obtener_pagos_maestro(d_sql, h_sql, id_cli, id_usuario)
            for p in pagos:
                self.tree_pagos.insert("", tk.END, values=[
                    _formatear_fecha_para_ui(p.get('fecha')),
                    p.get('cliente_nombre'), _fmt_mon(p.get('monto')),
                    p.get('metodo'), p.get('usuario_nombre')
                ])
        except Exception as e: logger.error(f"Error pagos: {e}")

    def _crear_tab_caja(self):
        frm = tk.Frame(self.tab_caja, bg="#f4f4f8", padx=10, pady=10)
        frm.pack(fill=tk.X)
        
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
        
        tk.Label(frm, text="Mostrar:", bg="#f4f4f8").grid(row=1, column=0, sticky="e", pady=5)
        
        self.opciones_filtro_caja = {
            "(Todo)": (None, None),
            "🛒 Ventas (todas)": ('ingreso', "venta"),
            "💰 Cobros Cta. Cte.": ('ingreso', "cobro_cta_cte"),
            "📦 Pagos a Proveedores": ('egreso', "pago_proveedor"),
            "🔻 Retiros/Ajustes (-)": ('egreso', "retiro_caja"), 
            "💸 Gastos Varios": ('egreso', "gasto_vario"),
            "↩️ Reembolsos/Devoluciones": ('egreso', "devolucion_efectivo") 
        }
        
        self.cb_filtro_rapido_cj = ttk.Combobox(frm, values=list(self.opciones_filtro_caja.keys()), state="readonly", width=30)
        self.cb_filtro_rapido_cj.current(0)
        self.cb_filtro_rapido_cj.grid(row=1, column=1, padx=5, sticky="w")

        tk.Label(frm, text="Usuario:", bg="#f4f4f8").grid(row=1, column=2, sticky="e")
        self.cb_usuario_caja = ttk.Combobox(frm, state="readonly", values=self.vendedor_nombres, width=15)
        self.cb_usuario_caja.current(0)
        self.cb_usuario_caja.grid(row=1, column=3, padx=5)
        
        self.crear_boton_accion(frm, "🔍 Buscar", self.buscar_caja, "#3b82f6", width=10).grid(row=1, column=4, padx=5)
        self.crear_boton_accion(frm, "📊 Exportar", lambda: self.exportar_a_csv(3), "#10b981", width=10).grid(row=1, column=5, padx=5)
        
        cols = ("Fecha", "Usuario", "Tipo", "Motivo", "Monto", "Descripción")
        self.tree_caja = ttk.Treeview(self.tab_caja, columns=cols, show="headings", height=15, style="Modern.Treeview")
        self.tree_caja.pack(fill="both", expand=True, padx=10, pady=10)
        
        for c in cols: self.tree_caja.heading(c, text=c, anchor="center")
        self.tree_caja.column("Fecha",       width=130, anchor="center")
        self.tree_caja.column("Usuario",     width=110, anchor="center")
        self.tree_caja.column("Tipo",        width=90,  anchor="center")
        self.tree_caja.column("Motivo",      width=160, anchor="center")
        self.tree_caja.column("Monto",       width=130, anchor="e", minwidth=130)
        self.tree_caja.column("Descripción", width=380, anchor="w", stretch=tk.YES) 
        
        self.tree_caja.tag_configure('ingreso', background='#d1fae5')
        self.tree_caja.tag_configure('egreso', background='#fee2e2')
        self.tree_caja.tag_configure('cierre', background='#e0f2fe', font=("Segoe UI", 9, "bold")) 

    def buscar_caja(self):
        for i in self.tree_caja.get_children(): self.tree_caja.delete(i)
        try:
            d_sql = self.fecha_desde_cj.get_date_sql()
            h_sql = self.fecha_hasta_cj.get_date_sql()
            
            seleccion = self.cb_filtro_rapido_cj.get()
            tipo_filtro, motivo_filtro = self.opciones_filtro_caja.get(seleccion, (None, None))
            
            db_tipo = tipo_filtro
            db_motivo = motivo_filtro
            
            # Para filtros agrupados ("venta" y "cobro_cta_cte") pedimos solo por tipo al backend
            # y filtramos por motivo acá para capturar todas las variantes
            MOTIVOS_VENTA = {'venta_efectivo', 'venta_transferencia', 'venta_tarjeta', 'venta_cuenta_corriente', 'venta_debito', 'venta_qr'}
            MOTIVOS_COBRO_CTA = {'pago_cuenta_corriente_efectivo', 'pago_cuenta_corriente_transferencia', 
                                  'pago_cuenta_corriente_tarjeta', 'cobro_cuenta_corriente', 'cobro_cta_cte'}
            
            if motivo_filtro in ("venta", "cobro_cta_cte"):
                db_motivo = None  # No filtrar por motivo en el backend
            elif seleccion == "(Todo)":
                db_tipo = None
                db_motivo = None

            id_usuario = None
            try:
                if self.cb_usuario_caja.current() > 0:
                    id_usuario = self.vendedor_ids[self.cb_usuario_caja.current()] 
            except: pass

            movimientos = self.backend.obtener_historial_movimientos_caja(
                fecha_desde=d_sql,
                fecha_hasta=h_sql,
                tipo=db_tipo,
                motivo=db_motivo,
                id_usuario=id_usuario
            )
            

            def _formatear_fecha(f):
                if not f: return ""
                try: return f.strftime("%d/%m/%Y %H:%M")
                except: return str(f)

            for mov in movimientos:
                
                motivo_raw = mov.get('motivo') or ''
                
                # Filtro local para opciones agrupadas
                if motivo_filtro == "venta":
                    # Incluir todo motivo que empiece con "venta" o sea una venta
                    if not (motivo_raw.startswith('venta') or motivo_raw in MOTIVOS_VENTA):
                        continue
                elif motivo_filtro == "cobro_cta_cte":
                    if not (motivo_raw in MOTIVOS_COBRO_CTA or 
                            'cuenta_corriente' in motivo_raw or 
                            'cta_cte' in motivo_raw):
                        continue
                elif seleccion != "(Todo)":
                    if motivo_raw in ['apertura_caja', 'cierre_caja']:
                        continue
                
                es_cierre = (motivo_raw == 'cierre_caja')
                es_apertura = (motivo_raw == 'apertura_caja')
                es_ingreso = (mov.get('tipo') == 'ingreso')
                
                tag = 'ingreso' if es_ingreso else 'egreso'
                if es_cierre or es_apertura: tag = 'cierre' 
                
                if es_apertura:
                    tipo_visual = "🟢 APERTURA"
                elif es_cierre:
                    tipo_visual = "🔒 CIERRE"
                else:
                    tipo_visual = "➕ INGRESO" if es_ingreso else "➖ EGRESO"
                
                mapeo_motivos = {
                    'venta_efectivo': '🛒 Venta',
                    'venta_transferencia': '🛒 Venta',
                    'venta_tarjeta': '🛒 Venta',
                    'venta_debito': '🛒 Venta',
                    'venta_qr': '🛒 Venta',
                    'venta_cuenta_corriente': '🛒 Venta',
                    'apertura_caja': '🟢 Apertura de Caja',
                    'cierre_caja': '🔒 Cierre de Caja',
                    'pago_cuenta_corriente_efectivo': '💰 Cobro Cta. Cte.',
                    'pago_cuenta_corriente_transferencia': '💰 Cobro Cta. Cte.',
                    'pago_cuenta_corriente_tarjeta': '💰 Cobro Cta. Cte.',
                    'cobro_cuenta_corriente': '💰 Cobro Cta. Cte.',
                    'cobro_cta_cte': '💰 Cobro Cta. Cte.',
                    'pago_proveedor': '📦 Pago a Proveedor',
                    'gasto_vario': '💸 Gasto Vario',
                    'retiro_caja': '🔻 Retiro/Ajuste',  
                    'devolucion_efectivo': '↩️ Reembolso',
                    'ajuste_positivo': '🔺 Ajuste (+)',
                    'ajuste_negativo': '🔻 Ajuste (-)',
                    'otro': '❓ Otro'
                }
                # Si el motivo empieza con "venta" pero no está en el mapa, mostrar "Venta" igual
                if motivo_raw and motivo_raw not in mapeo_motivos and motivo_raw.startswith('venta'):
                    motivo_txt = '🛒 Venta'
                else:
                    motivo_txt = mapeo_motivos.get(motivo_raw, motivo_raw.replace('_', ' ').title() if motivo_raw else '-')
                
                # 🔥 CORRECCIÓN DESCRIPCIÓN: Priorizar observaciones del usuario para Cierres
                descripcion = mov.get('descripcion', '').strip() or '-'
                if es_cierre:
                    obs_manual = mov.get('observaciones_cierre', '').strip()
                    if obs_manual:
                        # Se concatena el resumen del sistema con la observación del usuario
                        descripcion = f"{descripcion} | Obs: {obs_manual}"
                
                self.tree_caja.insert("", tk.END, values=(
                    _formatear_fecha(mov['fecha_hora']),
                    mov['usuario_nombre'],
                    tipo_visual,
                    motivo_txt,
                    _fmt_mon(mov['monto']),
                    descripcion
                ), tags=(tag,))
                
        except Exception as e:
            logger.error(f"Error cargando caja: {e}")
            messagebox.showerror("Error", str(e))
        
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
                else: cols_d = ["Producto", "Código", "Cantidad", "Costo", "Precio Venta", "Subtotal"] 
                
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
                        if tab_id == 0: 
                            detalles_bd = self.backend.obtener_venta_detalle(int(id_operacion))
                        else: 
                            if vals_m[5] == "PAGO DEUDA":
                                continue
                            detalles_bd = self.backend.obtener_compra_detalle(int(id_operacion))

                        for d in detalles_bd:
                            row_prod = [
                                d.get('nombre_producto', ''), 
                                d.get('codigo_barras', ''),
                                d.get('cantidad', 0),
                                _fmt_mon(d.get('precio_unitario' if tab_id==0 else 'precio_unitario', 0)),
                            ]
                            if tab_id == 1:
                                precio_venta = d.get('precio_venta_historico')
                                row_prod.append(_fmt_mon(precio_venta) if precio_venta else "-")
                                
                            row_prod.append(_fmt_mon(d.get('subtotal', 0)))
                            filas_productos.append(row_prod)

                    clean_m = [str(x).strip() for x in vals_m]
                    if filas_productos:
                        for row_prod in filas_productos:
                            clean_prod = [str(x).strip() for x in row_prod]
                            len_prod = len(cols_d)
                            if len(clean_prod) < len_prod:
                                clean_prod.extend([""] * (len_prod - len(clean_prod)))
                            w.writerow(clean_m + clean_prod)
                    else:
                        w.writerow(clean_m + [""]*len(cols_d))

            messagebox.showinfo("Éxito", "Reporte generado con contexto.")
        except Exception as e:
            logger.error(f"Error csv combinado: {e}")
            messagebox.showerror("Error", f"Error: {e}")

    def exportar_a_csv(self, tab_id):
        hoy = datetime.now().strftime("%d-%m-%Y")
        nombres = {0: "ventas", 1: "compras", 2: "pagos", 3: "caja"}
        nombre_base = f"{nombres.get(tab_id, 'datos')}_{hoy}.csv"

        if tab_id in [2, 3]:
            if tab_id == 2: tree = self.tree_pagos
            else: tree = self.tree_caja
            self._guardar_csv_simple(tree, nombre_base)
            return

        opcion = self._preguntar_tipo_exportacion()
        if not opcion: return

        tree_m = self.tree_maestro_v if tab_id == 0 else self.tree_maestro_c

        if opcion == "maestro":
            self._guardar_csv_simple(tree_m, f"listado_general_{nombre_base}")

        elif opcion == "detalle":
            if not tree_m.selection():
                messagebox.showwarning("Atención", "Seleccione una fila primero para ver su detalle.", parent=self.win)
                return
            sel = tree_m.selection()
            datos_cabecera = tree_m.item(sel[0], 'values')
            self._guardar_csv_combinado([datos_cabecera], tree_m, tab_id, f"detalle_venta_{datos_cabecera[0]}_{nombre_base}", False) 

        elif opcion == "ambos":
            items_maestro = [tree_m.item(i, 'values') for i in tree_m.get_children()]
            self._guardar_csv_combinado(items_maestro, tree_m, tab_id, f"reporte_completo_{nombre_base}", False)
            

ui_historiales = Historiales