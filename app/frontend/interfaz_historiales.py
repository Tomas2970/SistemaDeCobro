
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Toplevel, Listbox, SINGLE
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
        
        # Tamaño fijo razonable
        altura = 650 
        self.win.geometry(f"1250x{altura}")
        self.win.config(bg="#f4f4f8")
        
        # 🔥 ESTILOS MODERNOS (Treeview + Headings)
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

        # Datos para combos/selectores
        self.vendedor_ids = [None]
        self.vendedor_nombres = ["(Todos)"]
        self.cliente_ids = [None, 0]
        self.cliente_nombres = ["(Todos)", "(Consumidor Final)"]
        self.proveedor_ids = [None]
        self.proveedor_nombres = ["(Todos)"]
        
        self.cargar_datos_combos()

        # Variables de selección para los nuevos selectores
        self.var_vendedor_v_sel = {"id": None, "nombre": "(Todos)"}
        self.var_cliente_v_sel = {"id": None, "nombre": "(Todos)"}
        self.var_proveedor_c_sel = {"id": None, "nombre": "(Todos)"}
        self.var_usuario_c_sel = {"id": None, "nombre": "(Todos)"}
        self.var_cliente_p_sel = {"id": None, "nombre": "(Todos)"}
        self.var_usuario_p_sel = {"id": None, "nombre": "(Todos)"}
        self.var_usuario_caja_sel = {"id": None, "nombre": "(Todos)"}


        self.notebook = ttk.Notebook(self.win)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_ventas = ttk.Frame(self.notebook)
        self.tab_compras = ttk.Frame(self.notebook)
        self.tab_pagos = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_ventas, text="🛒 Ventas")
        self.notebook.add(self.tab_compras, text="📦 Compras")
        self.notebook.add(self.tab_pagos, text="💰 Pagos Cta. Cte.")

        # Verificar permiso para ver caja
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
        
    # 🔥 HELPER PARA BOTONES UNIFICADOS
    def crear_boton_accion(self, parent, text, command, color, width=12):
        """Helper para crear un botón estandarizado (estética moderna)."""
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
        """Oscurece un color hexadecimal para el activebackground (hover visual)."""
        colors = {
            "#3b82f6": "#2563eb",
            "#10b981": "#059669",
            "#16a34a": "#059669",
            "#03A9F4": "#0288d1",
            "#ef4444": "#dc2626",
            "#f59e0b": "#d97706",
            "#6b7280": "#4b5563"
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
            
            provs = self.backend.obtener_proveedores(incluir_inactivos=True) or []
            self.proveedor_nombres = ["(Todos)"] + [p.get("nombre", "") for p in provs]
            self.proveedor_ids = [None] + [p.get("id_proveedor") for p in provs]
            self.proveedores_map_id = {p['id_proveedor']: p for p in provs} 
            self.proveedores_map_nombre = {p['nombre']: p for p in provs} 
            self.proveedores_list = provs # Lista completa para el selector
        except Exception as e:
            logger.error(f"Error carga combos: {e}")

    def _aplicar_filtros_iniciales(self, f_fecha, f_desde, f_hasta, f_vend, f_vta, f_comp, f_cli):
        # ... (Lógica de fechas y IDs de venta/compra, que no cambian) ...
        if f_fecha:
            self.fecha_desde_v.widget_entrada.delete(0, tk.END); self.fecha_desde_v.widget_entrada.insert(0, f_fecha)
            self.fecha_hasta_v.widget_entrada.delete(0, tk.END); self.fecha_hasta_v.widget_entrada.insert(0, f_fecha)
        elif f_desde and f_hasta:
            self.fecha_desde_v.widget_entrada.delete(0, tk.END); self.fecha_desde_v.widget_entrada.insert(0, f_desde)
            self.fecha_hasta_v.widget_entrada.delete(0, tk.END); self.fecha_hasta_v.widget_entrada.insert(0, f_hasta)
        
        if f_vend:
            try:
                # Inicializar el var_vendedor_v_sel si se pasa un filtro inicial
                idx = self.vendedor_ids.index(f_vend)
                self.var_vendedor_v_sel = {"id": f_vend, "nombre": self.vendedor_nombres[idx]}
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
        
    # --- SELECTOR DE ENTIDAD MODAL ---
    def _crear_selector_entidad(self, tipo: str, var_seleccion: dict, lista_datos: list):
        """Abre un modal para buscar y seleccionar Cliente, Proveedor o Usuario."""
        popup = Toplevel(self.win)
        popup.title(f"Seleccionar {tipo}")
        popup.geometry("600x450")
        popup.config(bg="#f4f4f8")
        
        configurar_navegacion_ventana(popup)

        tk.Label(popup, text=f"Buscar {tipo} (ID/Nombre/DNI/CUIT):", bg="#f4f4f8", font=("Segoe UI", 10)).pack(pady=(10,5))
        var_pat = tk.StringVar()
        ent = tk.Entry(popup, textvariable=var_pat, width=60, font=("Segoe UI", 10))
        ent.pack(pady=5, padx=15, fill=tk.X)
        
        frame_list = tk.Frame(popup)
        frame_list.pack(expand=True, fill="both", padx=15, pady=5)
        sc = tk.Scrollbar(frame_list)
        sc.pack(side="right", fill="y")
        
        cols = ("ID", "Nombre", "Extra")
        tree_sel = ttk.Treeview(frame_list, columns=cols, show="headings", style="Modern.Treeview", height=12)
        tree_sel.pack(side="left", fill="both", expand=True)
        sc.config(command=tree_sel.yview)
        tree_sel.configure(yscrollcommand=sc.set)
        
        tree_sel.column("ID", width=60, anchor="center")
        tree_sel.column("Nombre", width=250, anchor="w")
        tree_sel.column("Extra", width=200, anchor="w")
        tree_sel.heading("ID", text="ID")
        tree_sel.heading("Nombre", text="Nombre")
        tree_sel.heading("Extra", text="DNI/CUIT/Empresa")
        
        # Opcion 'Todos'
        if tipo != "Vendedor/Usuario":
             tree_sel.insert("", "end", iid="opt_all", values=["-", "(Todos)", ""])

        if tipo == "Cliente":
            tree_sel.insert("", "end", iid="opt_cf", values=[0, "(Consumidor Final)", ""])

        def render(filas):
            for i in tree_sel.get_children(): 
                if i not in ["opt_all", "opt_cf"]: tree_sel.delete(i)

            for c in filas:
                if c.get("id_cliente") == 0: continue
                # Formato Cliente
                if 'id_cliente' in c:
                    id_val = c.get('id_cliente')
                    nombre_val = c.get('nombre')
                    extra_val = f"DNI: {c.get('dni') or '-'}"
                # Formato Proveedor
                elif 'id_proveedor' in c:
                    id_val = c.get('id_proveedor')
                    nombre_val = c.get('nombre')
                    extra_val = f"CUIT: {c.get('dni_cuit') or '-'} | Emp: {c.get('empresa') or '-'}"
                # Formato Usuario/Vendedor
                elif 'id_usuario' in c:
                    id_val = c.get('id_usuario')
                    nombre_val = c.get('nombre')
                    extra_val = f"Rol: {c.get('rol_nombre') or '-'}"
                else: continue
                
                tree_sel.insert("", "end", values=[id_val, nombre_val, extra_val])

        render(lista_datos)
        
        def filtrar(*_):
            q = var_pat.get().strip().lower()
            
            if not q:
                render(lista_datos)
                return

            filas_filtradas = []
            for d in lista_datos:
                
                # Campos de búsqueda comunes
                id_match = str(d.get('id_cliente') or d.get('id_proveedor') or d.get('id_usuario', '')).startswith(q)
                nombre_match = q in d.get('nombre', '').lower()
                dni_cuit_match = q in d.get('dni', '').lower() or q in d.get('dni_cuit', '').lower()
                
                if id_match or nombre_match or dni_cuit_match:
                    filas_filtradas.append(d)
                    
            render(filas_filtradas)

        var_pat.trace_add("write", filtrar)

        def tomar(event=None): 
            sel_id = tree_sel.focus()
            if not sel_id: return 
            
            # Caso "Todos"
            if sel_id in ["opt_all", "opt_cf"]:
                if sel_id == "opt_all":
                    var_seleccion["id"] = None
                    var_seleccion["nombre"] = "(Todos)"
                else: # Consumidor Final
                    var_seleccion["id"] = 0
                    var_seleccion["nombre"] = "(Consumidor Final)"
            else:
                vals = tree_sel.item(sel_id, "values")
                if not vals: return
                
                try: id_val = int(vals[0])
                except: id_val = None
                
                var_seleccion["id"] = id_val
                var_seleccion["nombre"] = vals[1]

            # Actualizar la interfaz principal (si es necesario) y cerrar
            popup.destroy()
            if hasattr(self, '_update_ui_sel'): self._update_ui_sel()

        tree_sel.bind("<Double-1>", tomar)
        tree_sel.bind("<Return>", tomar)

        btn_frm = tk.Frame(popup, bg="#f4f4f8")
        btn_frm.pack(pady=10)
        
        # 🔥 BOTONES ESTILO NUEVO
        btn_sel = tk.Button(btn_frm, text="✓ Seleccionar", command=tomar, 
                           bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"),
                           relief="flat", padx=20, pady=8, cursor="hand2",
                           activebackground="#059669")
        btn_sel.pack(side="left", padx=5)
        
        btn_canc = tk.Button(btn_frm, text="Cancelar", command=popup.destroy,
                            bg="#6b7280", fg="white", font=("Segoe UI", 10),
                            relief="flat", padx=15, pady=8, cursor="hand2",
                            activebackground="#4b5563")
        btn_canc.pack(side="left", padx=5)
        
        popup.after(100, lambda: ent.focus_set())
        popup.grab_set()
        popup.transient(self.win)
        self.win.wait_window(popup)
        
        # Se necesita forzar la actualización de la UI tras el modal
        self._update_ui_sel()

    def _update_ui_sel(self):
        """Actualiza la representación visual de las selecciones de entidad."""
        # Pestaña Ventas
        if hasattr(self, 'lbl_vendedor_v'):
            self.lbl_vendedor_v.config(text=self.var_vendedor_v_sel['nombre'])
            self.lbl_cliente_v.config(text=self.var_cliente_v_sel['nombre'])
        # Pestaña Compras
        if hasattr(self, 'lbl_proveedor_c'):
            self.lbl_proveedor_c.config(text=self.var_proveedor_c_sel['nombre'])
            self.lbl_usuario_c.config(text=self.var_usuario_c_sel['nombre'])
        # Pestaña Pagos
        if hasattr(self, 'lbl_cliente_p'):
            self.lbl_cliente_p.config(text=self.var_cliente_p_sel['nombre'])
            self.lbl_usuario_p.config(text=self.var_usuario_p_sel['nombre'])
        # Pestaña Caja
        if hasattr(self, 'lbl_usuario_caja'):
            self.lbl_usuario_caja.config(text=self.var_usuario_caja_sel['nombre'])


    # ----------------------------------------------------------------
    # PESTAÑA VENTAS
    # ----------------------------------------------------------------
    def _crear_tab_ventas(self):
        frm = tk.Frame(self.tab_ventas, bg="#f4f4f8", padx=10, pady=10)
        frm.pack(fill=tk.X)

        # Rango
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

        # Vendedor (Selector Modal)
        tk.Label(frm, text="Vendedor:", bg="#f4f4f8").grid(row=1, column=0, sticky="e", pady=5)
        self.lbl_vendedor_v = tk.Label(frm, text=self.var_vendedor_v_sel['nombre'], bg="#f4f4f8", width=15, anchor="w")
        self.lbl_vendedor_v.grid(row=1, column=1, padx=5, sticky="w")
        self.crear_boton_accion(frm, "Buscar Vendedor", 
                                lambda: self._crear_selector_entidad("Vendedor/Usuario", self.var_vendedor_v_sel, self.backend.obtener_vendedores()), 
                                "#3b82f6", width=15).grid(row=1, column=1, padx=(100,0), sticky="e")
        
        # Cliente (Selector Modal)
        tk.Label(frm, text="Cliente:", bg="#f4f4f8").grid(row=1, column=2, sticky="e")
        self.lbl_cliente_v = tk.Label(frm, text=self.var_cliente_v_sel['nombre'], bg="#f4f4f8", width=15, anchor="w")
        self.lbl_cliente_v.grid(row=1, column=3, padx=5, sticky="w")
        self.crear_boton_accion(frm, "Buscar Cliente", 
                                lambda: self._crear_selector_entidad("Cliente", self.var_cliente_v_sel, self.backend.listar_clientes()), 
                                "#3b82f6", width=15).grid(row=1, column=3, padx=(100,0), sticky="e")

        # 🔥 BOTONES UNIFICADOS (colores modernizados)
        self.crear_boton_accion(frm, "🔍 Buscar", self.buscar_ventas, "#3b82f6", width=10).grid(row=1, column=4, padx=5)
        self.crear_boton_accion(frm, "📊 Exportar", lambda: self.exportar_a_csv(0), "#10b981", width=10).grid(row=1, column=5, padx=5)
        
        cols = ("ID", "Fecha", "Cliente", "Vendedor", "Total", "Estado", "Pago")
        self.tree_maestro_v = ttk.Treeview(self.tab_ventas, columns=cols, show="headings", height=10, style="Modern.Treeview")
        self.tree_maestro_v.pack(fill="both", expand=True, padx=10, pady=5)
        for c in cols: self.tree_maestro_v.heading(c, text=c)
        self.tree_maestro_v.column("ID", width=50, anchor="center")
        self.tree_maestro_v.column("Total", anchor="e") 
        self.tree_maestro_v.bind("<<TreeviewSelect>>", self.mostrar_detalle_venta)


        cols_d = ("Prod", "Código", "Cant", "P. Unit", "Subtotal")
        self.tree_detalle_v = ttk.Treeview(self.tab_ventas, columns=cols_d, show="headings", height=6, style="Modern.Treeview")
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
            
            # Usar la ID de la variable de selección
            id_vend = self.var_vendedor_v_sel['id']
            id_cli = self.var_cliente_v_sel['id']
            
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
    # PESTAÑA COMPRAS (COMPLETA CON PRECIO VENTA HISTÓRICO)
    # ----------------------------------------------------------------
    def _crear_tab_compras(self):
        frm = tk.Frame(self.tab_compras, bg="#f4f4f8", padx=10, pady=10)
        frm.pack(fill=tk.X)

        # Rango y Fechas (No cambian)
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

        # Proveedor (Selector Modal)
        tk.Label(frm, text="Proveedor:", bg="#f4f4f8").grid(row=1, column=0, sticky="e", pady=5)
        self.lbl_proveedor_c = tk.Label(frm, text=self.var_proveedor_c_sel['nombre'], bg="#f4f4f8", width=20, anchor="w")
        self.lbl_proveedor_c.grid(row=1, column=1, columnspan=2, sticky="w", padx=5)
        self.crear_boton_accion(frm, "Buscar Proveedor", 
                                lambda: self._crear_selector_entidad("Proveedor", self.var_proveedor_c_sel, self.proveedores_list), 
                                "#3b82f6", width=15).grid(row=1, column=2, sticky="e")

        # Usuario/Registró (Selector Modal)
        tk.Label(frm, text="Usuario:", bg="#f4f4f8").grid(row=1, column=3, sticky="e")
        self.lbl_usuario_c = tk.Label(frm, text=self.var_usuario_c_sel['nombre'], bg="#f4f4f8", width=15, anchor="w")
        self.lbl_usuario_c.grid(row=1, column=4, padx=5, sticky="w")
        self.crear_boton_accion(frm, "Buscar Usuario", 
                                lambda: self._crear_selector_entidad("Vendedor/Usuario", self.var_usuario_c_sel, self.backend.obtener_vendedores()), 
                                "#3b82f6", width=15).grid(row=1, column=4, padx=(100,0), sticky="e")


        # 🔥 BOTONES UNIFICADOS
        self.crear_boton_accion(frm, "🔍 Buscar", self.buscar_compras, "#3b82f6", width=10).grid(row=1, column=5)
        self.crear_boton_accion(frm, "📊 Exportar", lambda: self.exportar_a_csv(1), "#10b981", width=10).grid(row=1, column=6, padx=5)

        # Maestro (CON COLUMNAS MODIFICADAS)
        cols = ("ID", "Fecha", "Proveedor", "DNI", "Empresa", "CUIT", "Total", "Estado", "Pago", "Usuario")
        self.tree_maestro_c = ttk.Treeview(self.tab_compras, columns=cols, show="headings", height=8, style="Modern.Treeview")
        self.tree_maestro_c.pack(fill="both", expand=True, padx=10, pady=5)
        for c in cols: self.tree_maestro_c.heading(c, text=c)
        self.tree_maestro_c.column("ID", width=50, anchor="center")
        self.tree_maestro_c.column("Total", anchor="e")
        self.tree_maestro_c.column("Estado", width=80, anchor="center")
        self.tree_maestro_c.column("Pago", width=100, anchor="center")
        self.tree_maestro_c.column("Empresa", width=120)
        self.tree_maestro_c.column("DNI", width=80) 
        self.tree_maestro_c.column("CUIT", width=100)
        self.tree_maestro_c.bind("<<TreeviewSelect>>", self.mostrar_detalle_compra)

        # 🔥 DETALLE CON PRECIO VENTA HISTÓRICO
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
            
            # Usar la ID de la variable de selección
            id_prov_filtro = self.var_proveedor_c_sel['id']
            id_usuario_filtro = self.var_usuario_c_sel['id']
            
            if hasattr(self, 'filtro_compra_id') and self.filtro_compra_id:
                compras = [c for c in self.backend.obtener_compras_maestro(None, None, None) 
                            if c['id_compra'] == self.filtro_compra_id]
                self.filtro_compra_id = None
            else:
                compras = self.backend.obtener_compras_maestro(d_sql, h_sql, id_prov_filtro)
            
            prov_map = self.proveedores_map_nombre

            # Filtrar por usuario (si hay un ID seleccionado)
            if id_usuario_filtro:
                try:
                    nombre_usuario_sel = self.var_usuario_c_sel['nombre']
                    compras = [c for c in compras if c.get('usuario') == nombre_usuario_sel]
                except: pass


            for c in compras:
                medio = c.get('medio_pago') or '-'
                prov_data = prov_map.get(c.get('proveedor'), {})
                
                dni_val = prov_data.get('dni', '-')
                cuit_val = prov_data.get('cuit', '-')
                empresa_val = prov_data.get('empresa', '-')

                self.tree_maestro_c.insert("", tk.END, values=[
                    c.get('id_compra'), 
                    _formatear_fecha_para_ui(c.get('fecha')),
                    c.get('proveedor'),
                    dni_val, # DNI Vendedor
                    empresa_val, # Nombre Empresa
                    cuit_val, # CUIT Empresa
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
        

        if self.tree_maestro_c.item(sel[0], "values")[7] == "PAGO DEUDA":
            return
            
        try:
            dets = self.backend.obtener_compra_detalle(int(id_c))
            for d in dets:
                # 🔥 Precio Venta Histórico
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
    # ----------------------------------------------------------------
    # PESTAÑA PAGOS
    # ----------------------------------------------------------------
    def _crear_tab_pagos(self):
        frm = tk.Frame(self.tab_pagos, bg="#f4f4f8", padx=10, pady=10)
        frm.pack(fill=tk.X)

        # Rango y Fechas (No cambian)
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

        # Cliente (Selector Modal)
        tk.Label(frm, text="Cliente:", bg="#f4f4f8").grid(row=1, column=0, sticky="e", pady=5)
        self.lbl_cliente_p = tk.Label(frm, text=self.var_cliente_p_sel['nombre'], bg="#f4f4f8", width=20, anchor="w")
        self.lbl_cliente_p.grid(row=1, column=1, padx=5, sticky="w")
        self.crear_boton_accion(frm, "Buscar Cliente", 
                                lambda: self._crear_selector_entidad("Cliente", self.var_cliente_p_sel, self.backend.listar_clientes()), 
                                "#3b82f6", width=15).grid(row=1, column=1, padx=(100,0), sticky="e")

        # Usuario/Registró (Selector Modal)
        tk.Label(frm, text="Registró:", bg="#f4f4f8").grid(row=1, column=2, sticky="e")
        self.lbl_usuario_p = tk.Label(frm, text=self.var_usuario_p_sel['nombre'], bg="#f4f4f8", width=15, anchor="w")
        self.lbl_usuario_p.grid(row=1, column=3, padx=5, sticky="w")
        self.crear_boton_accion(frm, "Buscar Usuario", 
                                lambda: self._crear_selector_entidad("Vendedor/Usuario", self.var_usuario_p_sel, self.backend.obtener_vendedores()), 
                                "#3b82f6", width=15).grid(row=1, column=3, padx=(100,0), sticky="e")

        # 🔥 BOTONES UNIFICADOS
        self.crear_boton_accion(frm, "🔍 Buscar", self.buscar_pagos, "#3b82f6", width=10).grid(row=1, column=4, padx=5)
        self.crear_boton_accion(frm, "📊 Exportar", lambda: self.exportar_a_csv(2), "#10b981", width=10).grid(row=1, column=5, padx=5)

        cols = ("ID", "Fecha", "Cliente", "Monto", "Método", "Registró")
        self.tree_pagos = ttk.Treeview(self.tab_pagos, columns=cols, show="headings", height=12, style="Modern.Treeview")
        self.tree_pagos.pack(fill="both", expand=True, padx=10, pady=10)
        for c in cols: self.tree_pagos.heading(c, text=c)
        self.tree_pagos.column("ID", width=50, anchor="center")
        self.tree_pagos.column("Monto", anchor="e")

    def buscar_pagos(self):
        for i in self.tree_pagos.get_children(): self.tree_pagos.delete(i)
        try:
            d_sql = self.fecha_desde_p.get_date_sql()
            h_sql = self.fecha_hasta_p.get_date_sql()
            
            # Usar la ID de la variable de selección
            id_cli = self.var_cliente_p_sel['id']
            id_usuario = self.var_usuario_p_sel['id']
            
            if hasattr(self, 'filtro_cliente_id') and self.filtro_cliente_id:
                id_cli = self.filtro_cliente_id
                self.filtro_cliente_id = None
                try: 
                    # Buscar el nombre correspondiente a la ID para actualizar el label
                    cli_data = next((c for c in self.backend.listar_clientes() if c['id_cliente'] == id_cli), None)
                    if cli_data:
                        self.var_cliente_p_sel = {"id": id_cli, "nombre": cli_data['nombre']}
                        self._update_ui_sel()
                    elif id_cli == 0:
                         self.var_cliente_p_sel = {"id": 0, "nombre": "(Consumidor Final)"}
                         self._update_ui_sel()

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
    # PESTAÑA CAJA 
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
        
        # FILA 1: Filtro Inteligente y Usuario
        tk.Label(frm, text="Mostrar:", bg="#f4f4f8").grid(row=1, column=0, sticky="e", pady=5)
        
        self.opciones_filtro_caja = {
            "(Todo)": (None, None),
            "🟢 Aperturas y Cierres": (None, "apertura_cierre"),
            "🛒 Ventas": (None, "venta_efectivo"),
            "💰 Ingresos (Ventas + Cobros)": ("ingreso", None),
            "💸 Egresos (Pagos + Gastos)": ("egreso", None),
            "📦 Pagos a Proveedores": (None, "pago_proveedor"),
            "💵 Pagos de Clientes (Cta. Cte.)": (None, "pago_cuenta_corriente_efectivo"),
            "⚠️ Gastos / Retiros": (None, "otros_egresos")
        }
        
        self.cb_filtro_rapido_cj = ttk.Combobox(frm, values=list(self.opciones_filtro_caja.keys()), state="readonly", width=30)
        self.cb_filtro_rapido_cj.current(0)
        self.cb_filtro_rapido_cj.grid(row=1, column=1, padx=5, sticky="w")

        # Usuario (Selector Modal)
        tk.Label(frm, text="Usuario:", bg="#f4f4f8").grid(row=1, column=2, sticky="e")
        self.lbl_usuario_caja = tk.Label(frm, text=self.var_usuario_caja_sel['nombre'], bg="#f4f4f8", width=15, anchor="w")
        self.lbl_usuario_caja.grid(row=1, column=3, padx=5, sticky="w")
        self.crear_boton_accion(frm, "Buscar Usuario", 
                                lambda: self._crear_selector_entidad("Vendedor/Usuario", self.var_usuario_caja_sel, self.backend.obtener_vendedores()), 
                                "#3b82f6", width=15).grid(row=1, column=3, padx=(100,0), sticky="e")
        
        # 🔥 BOTONES UNIFICADOS
        self.crear_boton_accion(frm, "🔍 Buscar", self.buscar_caja, "#3b82f6", width=10).grid(row=1, column=4, padx=5)
        self.crear_boton_accion(frm, "📊 Exportar", lambda: self.exportar_a_csv(3), "#10b981", width=10).grid(row=1, column=5, padx=5)
        
        cols = ("ID", "Fecha", "Usuario", "Tipo", "Motivo", "Monto", "Desc")
        self.tree_caja = ttk.Treeview(self.tab_caja, columns=cols, show="headings", height=15, style="Modern.Treeview")
        self.tree_caja.pack(fill="both", expand=True, padx=10, pady=10)
        
        for c in cols: self.tree_caja.heading(c, text=c)
        self.tree_caja.column("ID", width=50); self.tree_caja.column("Monto", width=100, anchor="e")
        self.tree_caja.column("Desc", width=250)
        
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
            
            if seleccion == "🟢 Aperturas y Cierres":
                db_tipo = None
                db_motivo = None
            
            if seleccion == "⚠️ Gastos / Retiros":
                db_tipo = "egreso"
                db_motivo = None

            id_usuario = self.var_usuario_caja_sel['id']

            movimientos = self.backend.obtener_historial_movimientos_caja(
                fecha_desde=d_sql,
                fecha_hasta=h_sql,
                tipo=db_tipo,
                motivo=db_motivo,
                id_usuario=id_usuario
            )
            
            # Filtrado fino en memoria para los casos complejos
            if seleccion == "🟢 Aperturas y Cierres":
                movimientos = [m for m in movimientos if m['motivo'] in ('apertura_caja', 'cierre_caja')]
            
            elif seleccion == "⚠️ Gastos / Retiros":
                movimientos = [m for m in movimientos if m['motivo'] in ('gasto_vario', 'retiro_caja')]

            total_ing = 0
            total_egr = 0
            
            def _formatear_fecha(f):
                if not f: return ""
                try: return f.strftime("%d/%m/%Y %H:%M")
                except: return str(f)

            for mov in movimientos:
                es_cierre = (mov.get('tipo') == 'cierre')
                es_ingreso = (mov.get('tipo') == 'ingreso')
                
                tag = 'ingreso' if es_ingreso else 'egreso'
                if es_cierre: tag = 'cierre'
                
                tipo_visual = "➕ INGRESO" if es_ingreso else ("➖ EGRESO" if not es_cierre else "🏁 CIERRE")
                
                motivo_txt = mov['motivo'].replace('_', ' ').title()
                if motivo_txt == "Venta Efectivo": motivo_txt = "🛒 Venta Efectivo"
                if motivo_txt == "Apertura Caja": motivo_txt = "🟢 Apertura de Caja"
                if motivo_txt == "Cierre Caja": motivo_txt = "🏁 Cierre de Caja"
                
                monto = float(mov['monto'])
                if es_ingreso: total_ing += monto
                elif not es_cierre: total_egr += monto
                
                self.tree_caja.insert("", tk.END, values=(
                    mov['id_movimiento'] if not es_cierre else "REF",
                    _formatear_fecha(mov['fecha_hora']),
                    mov['usuario_nombre'],
                    tipo_visual,
                    motivo_txt,
                    _fmt_mon(monto),
                    mov['descripcion']
                ), tags=(tag,))
                
        except Exception as e:
            logger.error(f"Error cargando caja: {e}")
            messagebox.showerror("Error", str(e))
    
# ----------------------------------------------------------------
# FUNCIONES DE EXPORTACIÓN (COMPLETAS)
# ----------------------------------------------------------------

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
                
                # Definición de las columnas de detalle para el CSV
                if tab_id == 0: cols_d = ["Producto", "Código", "Cantidad", "P. Unit", "Subtotal"]
                else: cols_d = ["Producto", "Código", "Cantidad", "Costo", "Precio Venta", "Subtotal"] # Compras tiene una columna extra
                
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
                        # Si usamos el detalle visual, simplemente copiamos los datos visibles
                        filas_productos = items_detalle_visual
                    else:
                        detalles_bd = []
                        if tab_id == 0: 
                            detalles_bd = self.backend.obtener_venta_detalle(int(id_operacion))
                        else: 
                            # Si es PAGO DEUDA, no tiene detalle de productos.
                            if vals_m[7] == "PAGO DEUDA":
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
                                # Columna extra para Precio Venta Histórico en Compras
                                precio_venta = d.get('precio_venta_historico')
                                row_prod.append(_fmt_mon(precio_venta) if precio_venta else "-")
                                
                            row_prod.append(_fmt_mon(d.get('subtotal', 0)))
                            filas_productos.append(row_prod)

                    clean_m = [str(x).strip() for x in vals_m]
                    if filas_productos:
                        for row_prod in filas_productos:
                            clean_prod = [str(x).strip() for x in row_prod]
                            # Rellenar con espacios en blanco si el detalle es más corto (ej. para Ventas)
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

        # 3. Ejecutar lógica
        if opcion == "maestro":
            self._guardar_csv_simple(tree_m, f"listado_general_{nombre_base}")

        elif opcion == "detalle":
            if not tree_m.selection():
                messagebox.showwarning("Atención", "Seleccione una fila primero para ver su detalle.", parent=self.win)
                return
            sel = tree_m.selection()
            datos_cabecera = tree_m.item(sel[0], 'values')
            self._guardar_csv_combinado([datos_cabecera], tree_m, tab_id, f"detalle_venta_{datos_cabecera[0]}_{nombre_base}", False) # Forzamos a ir a DB para exportar el detalle correcto

        elif opcion == "ambos":
            items_maestro = [tree_m.item(i, 'values') for i in tree_m.get_children()]
            self._guardar_csv_combinado(items_maestro, tree_m, tab_id, f"reporte_completo_{nombre_base}", False)
            

ui_historiales = Historiales