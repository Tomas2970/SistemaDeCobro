from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from app.frontend.theme_config import THEME_COLORS, get_color, aplicar_tema_ventana, configurar_estilo_notebook, configurar_estilo_treeview
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
    class SelectorFecha(ctk.CTkFrame):
        def __init__(self, master, **kwargs):
            super().__init__(master, fg_color="transparent", **kwargs)
            self.widget_entrada = ctk.CTkEntry(self, width=120)
            self.widget_entrada.pack(fill=tk.BOTH, expand=True)
            self.entrada = self.widget_entrada
        def get_date_sql(self):
            try:
                val = self.entrada.get()
                from datetime import datetime
                return datetime.strptime(val, "%d/%m/%Y").strftime("%Y-%m-%d")
            except: return None

def _aplicar_filtro_rapido_logic(seleccion, entry_desde, entry_hasta):
    hoy = date.today()
    f_ini, f_fin = None, None
    if seleccion == "Hoy": f_ini = f_fin = hoy
    elif seleccion == "Ayer": f_ini = f_fin = hoy - timedelta(days=1)
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
        
        self.win = ctk.CTkToplevel(parent)
        self.win.title("📋 Historiales del Sistema")
        
        altura = 720 
        self.win.geometry(f"1300x{altura}") 
        aplicar_tema_ventana(self.win)
        
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        configurar_estilo_treeview()

        frm_header = ctk.CTkFrame(self.win, fg_color=get_color("accent_primary"), corner_radius=0)
        frm_header.pack(fill="x")
        ctk.CTkLabel(frm_header, text="HISTORIALES DEL SISTEMA", font=("Segoe UI", 18, "bold"), text_color="white").pack(pady=15)

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

        # Variables para selección de filtros (Buscadores)
        self.vendedor_sel = {"id": None, "nombre": "(Todos)"}
        self.cliente_sel = {"id": None, "nombre": "(Todos)"}
        self.proveedor_sel = {"id": None, "nombre": "(Todos)"}
        self.usuario_c_sel = {"id": None, "nombre": "(Todos)"}
        self.cliente_p_sel = {"id": None, "nombre": "(Todos)"}
        self.usuario_p_sel = {"id": None, "nombre": "(Todos)"}
        
        # cargar_datos_combos se difiere drásticamente para que la ventana CTk se renderice fluidamente antes de bloquear mysql
        self.win.after(300, self.cargar_datos_combos)

        # Footer con boton cerrar - se packea ANTES del notebook para reservar espacio
        frm_footer = ctk.CTkFrame(self.win, fg_color="transparent")
        frm_footer.pack(fill="x", padx=10, side=tk.BOTTOM)
        ctk.CTkButton(frm_footer, text="Cerrar", command=self.win.destroy, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), font=("Segoe UI", 13, "bold"), width=120).pack(side=tk.RIGHT, pady=10)

        configurar_estilo_notebook()
        self.notebook = ttk.Notebook(self.win, style="Custom.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(10,0))

        self.tab_ventas = ttk.Frame(self.notebook)
        self.tab_compras = ttk.Frame(self.notebook)
        self.tab_pagos = ttk.Frame(self.notebook)

        # Base oscura para CADA pestaña
        for t, attr in [(self.tab_ventas, 'bg_ventas'), (self.tab_compras, 'bg_compras'), (self.tab_pagos, 'bg_pagos')]:
            setattr(self, attr, ctk.CTkFrame(t, fg_color=get_color("bg_root"), corner_radius=0))
            getattr(self, attr).pack(fill="both", expand=True)
        
        self.notebook.add(self.tab_ventas, text="🛒 Ventas")
        self.notebook.add(self.tab_compras, text="📦 Compras")
        self.notebook.add(self.tab_pagos, text="💰 Pagos Cta. Cte.")

        if tiene_permiso(usuario, 'ver_historial_movimientos'):
            self.tab_caja = ttk.Frame(self.notebook)
            self.bg_caja = ctk.CTkFrame(self.tab_caja, fg_color=get_color("bg_root"), corner_radius=0)
            self.bg_caja.pack(fill="both", expand=True)
            self.notebook.add(self.tab_caja, text="📊 Movimientos de Caja")
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
        return ctk.CTkButton(parent, text=text, command=command, fg_color=color, hover_color=self._darken_color(color), width=width*8, font=("Segoe UI", 13, "bold"), cursor="hand2")

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

    def _abrir_selector_entidad(self, tipo: str, var_seleccion: dict, lista_datos: list, label_update: ctk.CTkLabel):
        popup = ctk.CTkToplevel(self.win)
        popup.title(f"Seleccionar {tipo}")
        popup.geometry("500x550")
        aplicar_tema_ventana(popup)
        
        configurar_navegacion_ventana(popup)

        var_pat = tk.StringVar()
        ctk.CTkLabel(popup, text=f"Buscar {tipo} (ID/Nombre):", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).pack(pady=(15,5), padx=15, anchor="w")
        ent = ctk.CTkEntry(popup, textvariable=var_pat, font=("Segoe UI", 13), height=40, placeholder_text="Nombre o ID...")
        ent.pack(fill="x", padx=15, pady=5)
        
        frame_list = ctk.CTkFrame(popup, fg_color=get_color("bg_surface"), corner_radius=10, border_color=get_color("border_color"), border_width=1)
        frame_list.pack(expand=True, fill="both", padx=15, pady=10)
        
        cols = ("ID", "Nombre")
        tree_sel = ttk.Treeview(frame_list, columns=cols, show="headings", style="Modern.Treeview", height=12)
        tree_sel.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        sc = ttk.Scrollbar(frame_list, command=tree_sel.yview)
        sc.pack(side="right", fill="y", pady=5)
        tree_sel.configure(yscrollcommand=sc.set)
        
        tree_sel.column("ID", width=70, anchor="center")
        tree_sel.column("Nombre", width=350, anchor="w")
        tree_sel.heading("ID", text="ID")
        tree_sel.heading("Nombre", text="Nombre")
        
        tree_sel.insert("", "end", iid="opt_all", values=["-", "(Todos)"])

        def render(filas):
            for i in tree_sel.get_children(): 
                if i != "opt_all": tree_sel.delete(i)
            for c in filas:
                # Manejar diferentes estructuras de datos
                id_val = c.get('id_usuario') or c.get('id_cliente') or c.get('id_proveedor') or c.get('id')
                nombre_val = c.get('nombre') or c.get('razon_social') or "-"
                tree_sel.insert("", "end", values=[id_val, nombre_val])

        render(lista_datos)
        
        def filtrar(*_):
            q = var_pat.get().strip().lower()
            if not q:
                render(lista_datos)
                return
            filas_filtradas = []
            for d in lista_datos:
                id_v = str(d.get('id_usuario') or d.get('id_cliente') or d.get('id_proveedor') or d.get('id') or '').lower()
                nom_v = str(d.get('nombre') or d.get('razon_social') or '').lower()
                if q in id_v or q in nom_v:
                    filas_filtradas.append(d)
            render(filas_filtradas)

        var_pat.trace_add("write", filtrar)

        def tomar(event=None): 
            sel_id = tree_sel.focus()
            if not sel_id: return 
            if sel_id == "opt_all":
                var_seleccion["id"] = None
                var_seleccion["nombre"] = "(Todos)"
            else:
                vals = tree_sel.item(sel_id, "values")
                if not vals: return
                var_seleccion["id"] = vals[0]
                var_seleccion["nombre"] = vals[1]
            label_update.configure(text=var_seleccion["nombre"], text_color=get_color("text_primary"), font=("Segoe UI", 12, "bold"))
            popup.destroy()

        tree_sel.bind("<Double-1>", tomar)
        tree_sel.bind("<Return>", tomar)

        btn_frm = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frm.pack(fill="x", side="bottom", padx=15, pady=(5, 15))
        
        ctk.CTkButton(btn_frm, text="Cancelar", command=popup.destroy, fg_color="#ef4444", hover_color="#dc2626", font=("Segoe UI", 13, "bold"), width=150, height=45).pack(side="left", padx=10)
        ctk.CTkButton(btn_frm, text="✓ Seleccionar", command=tomar, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 14, "bold"), width=180, height=45).pack(side="right", padx=10)
        
        popup.after(100, lambda: ent.focus_set())
        popup.grab_set()
        popup.transient(self.win)
        self.win.wait_window(popup)

    def _on_rango_change(self, seleccion, selector_desde, selector_hasta):
        _aplicar_filtro_rapido_logic(seleccion, selector_desde.widget_entrada, selector_hasta.widget_entrada)

    def cargar_datos_combos(self):
        try:
            vends = self.backend.obtener_vendedores() or []
            self.vendedores_raw = vends
            self.vendedor_nombres = ["(Todos)"] + [v.get("nombre", "") for v in vends]
            self.vendedor_ids = [None] + [v.get("id_usuario") for v in vends]
            
            clis = self.backend.listar_clientes() or []
            self.clientes_raw = clis
            self.cliente_nombres = ["(Todos)", "(Consumidor Final)"] + [c.get("nombre", "") for c in clis]
            self.cliente_ids = [None, 0] + [c.get("id_cliente") for c in clis]
            
            self.cliente_nombres_pagos = ["(Todos)"] + [c.get("nombre", "") for c in clis]
            self.cliente_ids_pagos = [None] + [c.get("id_cliente") for c in clis]
            
            provs = self.backend.obtener_proveedores(incluir_inactivos=True) or []
            self.proveedores_raw = provs
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
                    self.cb_vendedor_v.configure(values=self.vendedor_nombres)
                if hasattr(self, 'cb_cliente_v'):
                    self.cb_cliente_v.configure(values=self.cliente_nombres)
                if hasattr(self, 'cb_proveedor_c'):
                    self.cb_proveedor_c.configure(values=self.proveedor_nombres)
                if hasattr(self, 'cb_cliente_p'):
                    self.cb_cliente_p.configure(values=self.cliente_nombres_pagos)
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

        self.win.after(400, self.buscar_ventas)
        self.loaded_flags[0] = True

    def on_tab_change(self, event):
        idx = self.notebook.index(self.notebook.select())
        tab_text = self.notebook.tab(idx, "text")
        
        if "Ventas" in tab_text: self.buscar_ventas()
        elif "Compras" in tab_text: self.buscar_compras()
        elif "Pagos" in tab_text: self.buscar_pagos()
        elif "Caja" in tab_text: self.buscar_caja()

    def _crear_tab_ventas(self):
        # Usar self.bg_ventas como padre en lugar de self.tab_ventas
        frm = ctk.CTkFrame(self.bg_ventas, fg_color="transparent")
        frm.pack(fill="x", padx=10, pady=(2, 5))

        ctk.CTkLabel(frm, text="Rango:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=0, column=0, sticky="e")
        cb_rango = ctk.CTkOptionMenu(frm, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Este Mes", "Mes Pasado"], 
                                     command=lambda v: self._on_rango_change(v, self.fecha_desde_v, self.fecha_hasta_v),
                                     width=140, fg_color=get_color("bg_pop"), button_color=get_color("bg_pop"))
        cb_rango.set("Personalizado")
        cb_rango.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(frm, text="Desde:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=0, column=2)
        self.fecha_desde_v = SelectorFecha(frm)
        self.fecha_desde_v.grid(row=0, column=3)
        self.fecha_desde_v.widget_entrada.delete(0, tk.END)
        self.fecha_desde_v.widget_entrada.insert(0, f"01/{date.today().month:02d}/{date.today().year}")

        ctk.CTkLabel(frm, text="Hasta:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=0, column=4)
        self.fecha_hasta_v = SelectorFecha(frm)
        self.fecha_hasta_v.grid(row=0, column=5)
        self.fecha_hasta_v.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_v.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        
        cb_rango.bind("<<ComboboxSelected>>", lambda e: _aplicar_filtro_rapido_logic(cb_rango.get(), self.fecha_desde_v.widget_entrada, self.fecha_hasta_v.widget_entrada))

        ctk.CTkLabel(frm, text="Vendedor:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=1, column=0, sticky="e", pady=5)
        self.lbl_vendedor_v = ctk.CTkLabel(frm, text="(Todos)", font=("Segoe UI", 12), text_color=get_color("text_secondary"))
        self.lbl_vendedor_v.grid(row=1, column=1, padx=5, sticky="w")
        ctk.CTkButton(frm, text="🔍", width=35, height=30, fg_color="#3b82f6", command=lambda: self._abrir_selector_entidad("Vendedor", self.vendedor_sel, self.vendedores_raw, self.lbl_vendedor_v)).grid(row=1, column=1, padx=(70, 0), sticky="w")

        ctk.CTkLabel(frm, text="Cliente:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=1, column=2, sticky="e")
        self.lbl_cliente_v = ctk.CTkLabel(frm, text="(Todos)", font=("Segoe UI", 12), text_color=get_color("text_secondary"))
        self.lbl_cliente_v.grid(row=1, column=3, padx=5, sticky="w")
        ctk.CTkButton(frm, text="🔍", width=35, height=30, fg_color="#3b82f6", command=lambda: self._abrir_selector_entidad("Cliente", self.cliente_sel, self.clientes_raw, self.lbl_cliente_v)).grid(row=1, column=3, padx=(70, 0), sticky="w")

        self.crear_boton_accion(frm, "🔍 Buscar", self.buscar_ventas, "#3b82f6", width=10).grid(row=1, column=4, padx=5)
        self.crear_boton_accion(frm, "📊 Exportar", lambda: self.exportar_a_csv(0), "#10b981", width=10).grid(row=1, column=5, padx=5)
        
        cols = ("ID", "Fecha", "Cliente", "Vendedor", "Total", "Estado", "Pago")
        self.tree_maestro_v = ttk.Treeview(self.bg_ventas, columns=cols, show="headings", height=5, style="Modern.Treeview") 
        self.tree_maestro_v.pack(fill="both", expand=True, padx=10, pady=5)
        for c in cols: self.tree_maestro_v.heading(c, text=c)
        self.tree_maestro_v.column("ID", width=0, stretch=False)
        self.tree_maestro_v.configure(displaycolumns=("Fecha", "Cliente", "Vendedor", "Total", "Estado", "Pago"))
        self.tree_maestro_v.column("Total", anchor="e") 
        self.tree_maestro_v.bind("<<TreeviewSelect>>", self.mostrar_detalle_venta)

        cols_d = ("Prod", "Código", "Cant", "P. Unit", "Subtotal")
        self.tree_detalle_v = ttk.Treeview(self.bg_ventas, columns=cols_d, show="headings", height=8, style="Modern.Treeview") 
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
            id_vend = self.vendedor_sel['id']
            id_cli = self.cliente_sel['id']
            
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
        except Exception as e: messagebox.showerror("Error", str(e), parent=self.win)

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
        frm = ctk.CTkFrame(self.bg_compras, fg_color="transparent")
        frm.pack(fill="x", padx=10, pady=(2, 2))

        ctk.CTkLabel(frm, text="Rango:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=0, column=0, sticky="e")
        cb_rango = ctk.CTkOptionMenu(frm, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Este Mes", "Mes Pasado"], 
                                     command=lambda v: self._on_rango_change(v, self.fecha_desde_c, self.fecha_hasta_c),
                                     width=140, fg_color=get_color("bg_pop"), button_color=get_color("bg_pop"))
        cb_rango.set("Personalizado")
        cb_rango.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(frm, text="Desde:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=0, column=2)
        self.fecha_desde_c = SelectorFecha(frm)
        self.fecha_desde_c.grid(row=0, column=3)
        self.fecha_desde_c.widget_entrada.delete(0, tk.END)
        self.fecha_desde_c.widget_entrada.insert(0, f"01/{date.today().month:02d}/{date.today().year}")

        ctk.CTkLabel(frm, text="Hasta:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=0, column=4)
        self.fecha_hasta_c = SelectorFecha(frm)
        self.fecha_hasta_c.grid(row=0, column=5)
        self.fecha_hasta_c.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_c.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        
        # Eliminación de bind legacy de combobox

        ctk.CTkLabel(frm, text="Proveedor:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=1, column=0, sticky="e", pady=5)
        self.lbl_proveedor_c = ctk.CTkLabel(frm, text="(Todos)", font=("Segoe UI", 12), text_color=get_color("text_secondary"))
        self.lbl_proveedor_c.grid(row=1, column=1, padx=5, sticky="w")
        ctk.CTkButton(frm, text="🔍", width=35, height=30, fg_color="#3b82f6", command=lambda: self._abrir_selector_entidad("Proveedor", self.proveedor_sel, self.proveedores_raw, self.lbl_proveedor_c)).grid(row=1, column=1, padx=(70, 0), sticky="w")

        ctk.CTkLabel(frm, text="Vendedor:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=1, column=2, sticky="e")
        self.lbl_usuario_c = ctk.CTkLabel(frm, text="(Todos)", font=("Segoe UI", 12), text_color=get_color("text_secondary"))
        self.lbl_usuario_c.grid(row=1, column=3, padx=5, sticky="w")
        ctk.CTkButton(frm, text="🔍", width=35, height=30, fg_color="#3b82f6", command=lambda: self._abrir_selector_entidad("Vendedor", self.usuario_c_sel, self.vendedores_raw, self.lbl_usuario_c)).grid(row=1, column=3, padx=(70, 0), sticky="w")

        self.crear_boton_accion(frm, "🔍 Buscar", self.buscar_compras, "#3b82f6", width=10).grid(row=1, column=5)
        self.crear_boton_accion(frm, "📊 Exportar", lambda: self.exportar_a_csv(1), "#10b981", width=10).grid(row=1, column=6, padx=5)

        cols = ("ID", "Fecha", "Empresa", "CUIT", "Total", "Estado", "Pago", "Vendedor")
        self.tree_maestro_c = ttk.Treeview(self.bg_compras, columns=cols, show="headings", height=5, style="Modern.Treeview")
        self.tree_maestro_c.pack(fill="both", expand=True, padx=10, pady=5)
        for c in cols: self.tree_maestro_c.heading(c, text=c)
        self.tree_maestro_c.column("ID", width=0, stretch=False)
        self.tree_maestro_c.configure(displaycolumns=("Fecha", "Empresa", "CUIT", "Total", "Estado", "Pago", "Vendedor"))
        self.tree_maestro_c.column("Total", anchor="e")
        self.tree_maestro_c.column("Estado", width=100, anchor="center")
        self.tree_maestro_c.column("Pago", width=100, anchor="center")
        self.tree_maestro_c.column("Empresa", width=160)
        self.tree_maestro_c.column("CUIT", width=110, anchor="center")
        self.tree_maestro_c.bind("<<TreeviewSelect>>", self.mostrar_detalle_compra)

        cols_d = ("Prod", "Código", "Cant", "Costo", "Precio Venta Asignado", "Subtotal")
        self.tree_detalle_c = ttk.Treeview(self.bg_compras, columns=cols_d, show="headings", height=8, style="Modern.Treeview")
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
            if hasattr(self, 'filtro_compra_id') and self.filtro_compra_id:
                compras = [c for c in self.backend.obtener_compras_maestro(None, None, None) 
                             if c['id_compra'] == self.filtro_compra_id]
                self.filtro_compra_id = None
            else:
                id_prov_filtro = self.proveedor_sel['id']
                compras = self.backend.obtener_compras_maestro(d_sql, h_sql, id_prov_filtro)
            
            prov_map = self.proveedores_map_nombre

            nombre_usuario_sel = self.usuario_c_sel['nombre']
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
        frm = ctk.CTkFrame(self.bg_pagos, fg_color="transparent")
        frm.pack(fill="x", padx=10, pady=(2, 2))

        ctk.CTkLabel(frm, text="Rango:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=0, column=0, sticky="e")
        cb_rango = ctk.CTkOptionMenu(frm, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Este Mes", "Mes Pasado"], 
                                     command=lambda v: self._on_rango_change(v, self.fecha_desde_p, self.fecha_hasta_p),
                                     width=140, fg_color=get_color("bg_pop"), button_color=get_color("bg_pop"))
        cb_rango.set("Personalizado")
        cb_rango.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(frm, text="Desde:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=0, column=2)
        self.fecha_desde_p = SelectorFecha(frm)
        self.fecha_desde_p.grid(row=0, column=3)
        self.fecha_desde_p.widget_entrada.delete(0, tk.END)
        self.fecha_desde_p.widget_entrada.insert(0, f"01/{date.today().month:02d}/{date.today().year}")

        ctk.CTkLabel(frm, text="Hasta:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=0, column=4)
        self.fecha_hasta_p = SelectorFecha(frm)
        self.fecha_hasta_p.grid(row=0, column=5)
        self.fecha_hasta_p.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_p.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        
        # Eliminación de bind legacy de combobox

        ctk.CTkLabel(frm, text="Cliente:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=1, column=0, sticky="e", pady=5)
        self.lbl_cliente_p = ctk.CTkLabel(frm, text="(Todos)", font=("Segoe UI", 12), text_color=get_color("text_secondary"))
        self.lbl_cliente_p.grid(row=1, column=1, padx=5, sticky="w")
        ctk.CTkButton(frm, text="🔍", width=35, height=30, fg_color="#3b82f6", command=lambda: self._abrir_selector_entidad("Cliente", self.cliente_p_sel, self.clientes_raw, self.lbl_cliente_p)).grid(row=1, column=1, padx=(70, 0), sticky="w")

        ctk.CTkLabel(frm, text="Vendedor:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=1, column=2, sticky="e")
        self.lbl_usuario_p = ctk.CTkLabel(frm, text="(Todos)", font=("Segoe UI", 12), text_color=get_color("text_secondary"))
        self.lbl_usuario_p.grid(row=1, column=3, padx=5, sticky="w")
        ctk.CTkButton(frm, text="🔍", width=35, height=30, fg_color="#3b82f6", command=lambda: self._abrir_selector_entidad("Vendedor", self.usuario_p_sel, self.vendedores_raw, self.lbl_usuario_p)).grid(row=1, column=3, padx=(70, 0), sticky="w")

        self.crear_boton_accion(frm, "🔍 Buscar", self.buscar_pagos, "#3b82f6", width=10).grid(row=1, column=4, padx=5)
        self.crear_boton_accion(frm, "📊 Exportar", lambda: self.exportar_a_csv(2), "#10b981", width=10).grid(row=1, column=5, padx=5)

        cols = ("Fecha", "Cliente", "Monto", "Método", "Vendedor")
        self.tree_pagos = ttk.Treeview(self.bg_pagos, columns=cols, show="headings", height=8, style="Modern.Treeview")
        self.tree_pagos.pack(fill="both", expand=True, padx=10, pady=10)
        for c in cols: self.tree_pagos.heading(c, text=c)
        # Aquí no hay ID en cols, así que no hace falta displaycolumns manual si no se incluyó.
        self.tree_pagos.column("Monto", anchor="e")

    def buscar_pagos(self):
        for i in self.tree_pagos.get_children(): self.tree_pagos.delete(i)
        try:
            d_sql = self.fecha_desde_p.get_date_sql()
            h_sql = self.fecha_hasta_p.get_date_sql()
            
            id_cli = self.cliente_p_sel['id']
            id_usuario = self.usuario_p_sel['id']
            
            if hasattr(self, 'filtro_cliente_id') and self.filtro_cliente_id:
                id_cli = self.filtro_cliente_id
                self.filtro_cliente_id = None
                try:
                    cliente_data = next((c for c in self.clientes_raw if c['id_cliente'] == id_cli), None)
                    if cliente_data:
                        self.cliente_p_sel['id'] = id_cli
                        self.cliente_p_sel['nombre'] = cliente_data['nombre']
                        self.lbl_cliente_p.configure(text=cliente_data['nombre'], text_color=get_color("text_primary"), font=("Segoe UI", 12, "bold"))
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
        frm = ctk.CTkFrame(self.bg_caja, fg_color="transparent")
        frm.pack(fill="x", padx=10, pady=(2, 2))
        
        ctk.CTkLabel(frm, text="Rango:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=0, column=0, sticky="e")
        cb_rango = ctk.CTkOptionMenu(frm, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Este Mes", "Mes Pasado"], 
                                     command=lambda v: self._on_rango_change(v, self.fecha_desde_cj, self.fecha_hasta_cj),
                                     width=140, fg_color=get_color("bg_pop"), button_color=get_color("bg_pop"))
        cb_rango.set("Personalizado")
        cb_rango.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(frm, text="Desde:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=0, column=2)
        self.fecha_desde_cj = SelectorFecha(frm)
        self.fecha_desde_cj.grid(row=0, column=3)
        self.fecha_desde_cj.widget_entrada.delete(0, tk.END)
        self.fecha_desde_cj.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))

        ctk.CTkLabel(frm, text="Hasta:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=0, column=4)
        self.fecha_hasta_cj = SelectorFecha(frm)
        self.fecha_hasta_cj.grid(row=0, column=5)
        self.fecha_hasta_cj.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_cj.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        
        cb_rango.bind("<<ComboboxSelected>>", lambda e: _aplicar_filtro_rapido_logic(cb_rango.get(), self.fecha_desde_cj.widget_entrada, self.fecha_hasta_cj.widget_entrada))
        
        ctk.CTkLabel(frm, text="Mostrar:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=1, column=0, sticky="e", pady=5)
        
        self.opciones_filtro_caja = {
            "(Todo)": (None, None),
            "🛒 Ventas": ('ingreso', "venta"),
            "💰 Cobros Cta. Cte.": ('ingreso', "cobro_cta_cte"),
            "📦 Pagos a Prov.": ('egreso', "pago_proveedor"),
            "🟢 Aperturas": (None, "apertura_caja"),
            "🔒 Cierres": (None, "cierre_caja"),
            "🔻 Retiros/Ajustes": ('egreso', "retiro_caja"), 
            "💸 Gastos Varios": ('egreso', "gasto_vario")        }
        
        self.cb_filtro_rapido_cj = ctk.CTkOptionMenu(frm, values=list(self.opciones_filtro_caja.keys()), width=240,
                                                    fg_color=get_color("bg_pop"), button_color=get_color("bg_pop"))
        self.cb_filtro_rapido_cj.set("(Todo)")
        self.cb_filtro_rapido_cj.grid(row=1, column=1, padx=5, sticky="w")

        ctk.CTkLabel(frm, text="Usuario:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).grid(row=1, column=2, sticky="e")
        self.cb_usuario_caja = ctk.CTkOptionMenu(frm, values=self.vendedor_nombres, width=150,
                                                 fg_color=get_color("bg_pop"), button_color=get_color("bg_pop"))
        self.cb_usuario_caja.set(self.vendedor_nombres[0])
        self.cb_usuario_caja.grid(row=1, column=3, padx=5)
        
        self.crear_boton_accion(frm, "🔍 Buscar", self.buscar_caja, "#3b82f6", width=10).grid(row=1, column=4, padx=5)
        self.crear_boton_accion(frm, "📊 Exportar", lambda: self.exportar_a_csv(3), "#10b981", width=10).grid(row=1, column=5, padx=5)
        
        cols = ("Fecha", "Usuario", "Tipo", "Motivo", "Monto", "Descripción")
        self.tree_caja = ttk.Treeview(self.bg_caja, columns=cols, show="headings", height=10, style="Modern.Treeview")
        self.tree_caja.pack(fill="both", expand=True, padx=10, pady=10)
        
        for c in cols: self.tree_caja.heading(c, text=c)
        self.tree_caja.column("Fecha",       width=130, anchor="center")
        self.tree_caja.column("Usuario",     width=110, anchor="center")
        self.tree_caja.column("Tipo",        width=90,  anchor="center")
        self.tree_caja.column("Motivo",      width=160, anchor="center")
        self.tree_caja.column("Monto",       width=130, anchor="e", minwidth=130)
        self.tree_caja.column("Descripción", width=380, anchor="w", stretch=tk.YES) 
        
        # Colores para tipos de movimientos (Oscurecidos para contraste con texto blanco/claro)
        self.tree_caja.tag_configure('ingreso', foreground='#4ade80') # Verde claro
        self.tree_caja.tag_configure('egreso', foreground='#f87171')  # Rojo claro
        self.tree_caja.tag_configure('cierre', background='#334155', foreground='#ffffff') # Gris oscuro con blanco

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
                nombre_u = self.cb_usuario_caja.get()
                if nombre_u != "(Todos)":
                    id_usuario = self.vendedor_ids[self.vendedor_nombres.index(nombre_u)] 
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
                elif seleccion not in ("(Todo)", "🟢 Aperturas", "🔒 Cierres"):
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
                desc_val = mov.get('descripcion')
                descripcion = (desc_val if desc_val else '').strip() or '-'
                if es_cierre:
                    obs_val = mov.get('observaciones_cierre')
                    obs_manual = (obs_val if obs_val else '').strip()
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
        dialog = ctk.CTkToplevel(self.win)
        dialog.title("Exportar a Excel")
        dialog.geometry("400x280")
        dialog.configure(fg_color=get_color("bg_root"))
        dialog.resizable(False, False)
        try: configurar_navegacion_ventana(dialog)
        except: pass

        seleccion = {"valor": None}
        def set_sel(val):
            seleccion["valor"] = val
            dialog.destroy()
        ctk.CTkLabel(dialog, text="Seleccione el tipo de reporte:", font=("Segoe UI", 14, "bold"), text_color=get_color("text_primary")).pack(pady=20)

        b1 = ctk.CTkButton(dialog, text="📄 Listado General (Resumen)", command=lambda: set_sel("maestro"), height=40)
        b1.pack(fill="x", padx=30, pady=(5, 0))
        ctk.CTkLabel(dialog, text="1 renglón por operación. Ideal para ver totales.", text_color="gray", font=("Arial", 11)).pack(pady=(0, 10))

        b2 = ctk.CTkButton(dialog, text="🔍 Detalle de la Selección", command=lambda: set_sel("detalle"), height=40)
        b2.pack(fill="x", padx=30, pady=(5, 0))
        ctk.CTkLabel(dialog, text="Lista de productos de la fila seleccionada.", text_color="gray", font=("Arial", 11)).pack(pady=(0, 10))

        b3 = ctk.CTkButton(dialog, text="📑 Reporte Completo (Todo)", command=lambda: set_sel("ambos"), height=40)
        b3.pack(fill="x", padx=30, pady=(10, 5))
        ctk.CTkLabel(dialog, text="Sábana de datos completa con todos los productos.", text_color="gray", font=("Arial", 11)).pack(pady=(0, 20))

        dialog.transient(self.win)
        dialog.grab_set()
        self.win.wait_window(dialog)
        return seleccion["valor"]

    def _guardar_csv_simple(self, tree: ttk.Treeview, nombre_archivo: str):
        if not tree.get_children(): return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Excel CSV", "*.csv")], initialfile=nombre_archivo, parent=self.win)
        if not path: return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f, delimiter=';')
                w.writerow([tree.heading(c)['text'] for c in tree['columns']])
                for item in tree.get_children(): w.writerow(tree.item(item, 'values'))
            messagebox.showinfo("Éxito", "Archivo exportado.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def _guardar_csv_combinado(self, lista_datos_maestro, tree_maestro, tab_id, nombre_archivo, usar_detalle_visual=False):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Excel CSV", "*.csv")], initialfile=nombre_archivo, parent=self.win)
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