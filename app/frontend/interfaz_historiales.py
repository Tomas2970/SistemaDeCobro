# app/frontend/interfaz_historiales.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog 
from typing import Optional, Any
from datetime import date, datetime, timedelta 
import logging
import csv 

logger = logging.getLogger(__name__)

# --- Helpers de formato de fecha ---
def _formatear_fecha_para_sql(fecha_str: str) -> str | None:
    if not fecha_str:
        return None
    try:
        fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
        return fecha_obj.strftime("%Y-%m-%d")
    except ValueError:
        return None 
        
def _formatear_fecha_para_ui(fecha_sql: Any) -> str:
    if not fecha_sql:
        return ""
    try:
        fecha_obj = datetime.fromisoformat(str(fecha_sql)) 
        return fecha_obj.strftime("%d/%m/%Y %H:%M")
    except Exception:
        try:
            fecha_obj = datetime.strptime(str(fecha_sql), "%Y-%m-%d")
            return fecha_obj.strftime("%d/%m/%Y")
        except Exception:
            return str(fecha_sql)
            
def _fmt_mon(val: Any) -> str:
    try: return f"$ {float(val):,.2f}"
    except: return "$ 0.00"


# --- Clase helper para Entry con placeholder ---
class EntryConPlaceholder(tk.Entry):
    """Entry con texto placeholder que desaparece al hacer foco"""
    
    def __init__(self, master=None, placeholder="", color='grey', **kwargs):
        super().__init__(master, **kwargs)
        
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']
        
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        
        self._poner_placeholder()
    
    def _poner_placeholder(self):
        if not self.get():
            self.insert(0, self.placeholder)
            self['fg'] = self.placeholder_color
    
    def _on_focus_in(self, event):
        if self['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self['fg'] = self.default_fg_color
    
    def _on_focus_out(self, event):
        if not self.get():
            self._poner_placeholder()
    
    def get(self):
        content = super().get()
        if content == self.placeholder:
            return ""
        return content


class Historiales:
    def __init__(self, parent: tk.Misc, backend, usuario: dict, filtro_fecha: str | None = None):
        self.backend = backend
        self.usuario = usuario
        self.filtro_fecha_default = filtro_fecha
        
        self.win = tk.Toplevel(parent)
        self.win.title("📋 Historiales")
        
        # Calcular altura según pantalla
        screen_height = self.win.winfo_screenheight()
        altura_ventana = min(680, screen_height - 100)
        
        self.win.geometry(f"980x{altura_ventana}")
        self.win.config(bg="#f4f4f8")
        self.win.resizable(False, False)
        
        # Centrar ventana
        self.win.update_idletasks()
        x = (self.win.winfo_screenwidth() // 2) - (980 // 2)
        y = (self.win.winfo_screenheight() // 2) - (altura_ventana // 2)
        self.win.geometry(f"980x{altura_ventana}+{x}+{y}")

        self.vendedor_ids = [None]
        self.cliente_ids = [None]
        self.proveedor_ids = [None]

        self.notebook = ttk.Notebook(self.win)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_ventas = ttk.Frame(self.notebook)
        self.tab_compras = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_ventas, text="Historial de Ventas")
        self.notebook.add(self.tab_compras, text="Historial de Compras")

        self._crear_tab_ventas()
        self._crear_tab_compras()

        self.cargar_filtros_ventas()
        self.cargar_filtros_compras()
        
        self.buscar_ventas()
        self.buscar_compras()
        
        if self.filtro_fecha_default:
            self.notebook.select(self.tab_ventas)
        
        self.win.grab_set()

    # ===================================================================
    # PESTAÑA 1: HISTORIAL DE VENTAS
    # ===================================================================
    def _crear_tab_ventas(self):
        frm_filtros = tk.Frame(self.tab_ventas, bg="#f4f4f8", padx=10, pady=10)
        frm_filtros.pack(fill=tk.X)

        # --- Fila 1 ---
        tk.Label(frm_filtros, text="Desde:", bg="#f4f4f8", font=("Segoe UI", 9)).grid(row=0, column=0, padx=(5,2))
        self.ent_desde_v = EntryConPlaceholder(frm_filtros, placeholder="DD/MM/AAAA", width=12, font=("Segoe UI", 9))
        self.ent_desde_v.grid(row=0, column=1, padx=2)

        tk.Label(frm_filtros, text="Hasta:", bg="#f4f4f8", font=("Segoe UI", 9)).grid(row=0, column=2, padx=(10,2))
        self.ent_hasta_v = EntryConPlaceholder(frm_filtros, placeholder="DD/MM/AAAA", width=12, font=("Segoe UI", 9))
        self.ent_hasta_v.grid(row=0, column=3, padx=2)

        # Poner fechas por defecto
        if self.filtro_fecha_default:
            self.ent_desde_v.delete(0, tk.END)
            self.ent_desde_v.insert(0, self.filtro_fecha_default)
            self.ent_desde_v['fg'] = self.ent_desde_v.default_fg_color
            self.ent_hasta_v.delete(0, tk.END)
            self.ent_hasta_v.insert(0, self.filtro_fecha_default)
            self.ent_hasta_v['fg'] = self.ent_hasta_v.default_fg_color
        else:
            self.ent_desde_v.delete(0, tk.END)
            self.ent_desde_v.insert(0, f"01/{date.today().month:02d}/{date.today().year}")
            self.ent_desde_v['fg'] = self.ent_desde_v.default_fg_color
            self.ent_hasta_v.delete(0, tk.END)
            self.ent_hasta_v.insert(0, date.today().strftime("%d/%m/%Y"))
            self.ent_hasta_v['fg'] = self.ent_hasta_v.default_fg_color

        tk.Label(frm_filtros, text="Vendedor:", bg="#f4f4f8", font=("Segoe UI", 9)).grid(row=0, column=4, padx=(10,2))
        self.cb_vendedor_v = ttk.Combobox(frm_filtros, state="readonly", width=18, font=("Segoe UI", 9))
        self.cb_vendedor_v.grid(row=0, column=5, padx=2)

        # --- Fila 2 ---
        tk.Label(frm_filtros, text="Cliente:", bg="#f4f4f8", font=("Segoe UI", 9)).grid(row=1, column=0, padx=(5,2), pady=(5,0))
        self.cb_cliente_v = ttk.Combobox(frm_filtros, state="readonly", width=18, font=("Segoe UI", 9))
        self.cb_cliente_v.grid(row=1, column=1, padx=2, pady=(5,0))
        
        btn_buscar = tk.Button(frm_filtros, text="🔎 Buscar", command=self.buscar_ventas, 
                             bg="#03A9F4", fg="white", width=10, font=("Segoe UI", 9, "bold"))
        btn_buscar.grid(row=1, column=2, padx=(10, 8), pady=(5,0))
        
        btn_exportar_v = tk.Button(frm_filtros, text="📊 CSV", 
                                 command=self.exportar_a_csv, 
                                 bg="#16a34a", fg="white", 
                                 font=("Segoe UI", 9, "bold"),
                                 width=8)
        btn_exportar_v.grid(row=1, column=3, padx=2, pady=(5,0))
        
        # --- Fin Filtros ---
        
        frm_maestro = tk.LabelFrame(self.tab_ventas, text="Ventas Realizadas", bg="#f4f4f8", padx=10, pady=10, font=("Segoe UI", 9, "bold"))
        frm_maestro.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        cols_m = ("ID", "Fecha", "Cliente", "Vendedor", "Total", "Estado", "Tipo Pago")
        self.tree_maestro_v = ttk.Treeview(frm_maestro, columns=cols_m, show="headings", height=9)
        self.tree_maestro_v.pack(side="left", fill="both", expand=True)

        ys_m = ttk.Scrollbar(frm_maestro, orient="vertical", command=self.tree_maestro_v.yview)
        ys_m.pack(side="right", fill="y")
        self.tree_maestro_v.configure(yscrollcommand=ys_m.set)

        for c in cols_m: self.tree_maestro_v.heading(c, text=c)
        self.tree_maestro_v.column("ID", width=60, anchor="center")
        self.tree_maestro_v.column("Fecha", width=140)
        self.tree_maestro_v.column("Cliente", width=180)
        self.tree_maestro_v.column("Vendedor", width=180)
        self.tree_maestro_v.column("Total", width=100, anchor="e")
        self.tree_maestro_v.column("Estado", width=80, anchor="center")
        self.tree_maestro_v.column("Tipo Pago", width=100, anchor="center")
        
        self.tree_maestro_v.bind("<<TreeviewSelect>>", self.mostrar_detalle_venta)

        self.frm_detalle_v = tk.LabelFrame(self.tab_ventas, text="Detalle de la Venta Seleccionada", bg="#f4f4f8", padx=10, pady=10, font=("Segoe UI", 9, "bold"))
        self.frm_detalle_v.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        cols_d = ("ID Prod", "Producto", "Código Barras", "Cant", "P. Unit", "Subtotal")
        self.tree_detalle_v = ttk.Treeview(self.frm_detalle_v, columns=cols_d, show="headings", height=5)
        self.tree_detalle_v.pack(side="left", fill="both", expand=True)

        ys_d = ttk.Scrollbar(self.frm_detalle_v, orient="vertical", command=self.tree_detalle_v.yview)
        ys_d.pack(side="right", fill="y")
        self.tree_detalle_v.configure(yscrollcommand=ys_d.set)

        for c in cols_d: self.tree_detalle_v.heading(c, text=c)
        self.tree_detalle_v.column("ID Prod", width=60, anchor="center")
        self.tree_detalle_v.column("Producto", width=250)
        self.tree_detalle_v.column("Código Barras", width=150)
        self.tree_detalle_v.column("Cant", width=60, anchor="e")
        self.tree_detalle_v.column("P. Unit", width=100, anchor="e")
        self.tree_detalle_v.column("Subtotal", width=100, anchor="e")

    def cargar_filtros_ventas(self):
        try:
            vendedores = self.backend.obtener_vendedores() or []
            v_nombres = ["(Todos)"] + [v.get("nombre", "") for v in vendedores]
            self.vendedor_ids = [None] + [v.get("id_usuario") for v in vendedores]
            self.cb_vendedor_v["values"] = v_nombres
            self.cb_vendedor_v.current(0)
            
            clientes = self.backend.listar_clientes() or []
            c_nombres = ["(Todos)", "(Consumidor Final)"] + [c.get("nombre", "") for c in clientes]
            self.cliente_ids = [None, 0] + [c.get("id_cliente") for c in clientes]
            self.cb_cliente_v["values"] = c_nombres
            self.cb_cliente_v.current(0)
        except Exception as e:
            logger.error(f"Error cargando filtros (Ventas): {e}")

    def buscar_ventas(self):
        for i in self.tree_maestro_v.get_children(): self.tree_maestro_v.delete(i)
        for i in self.tree_detalle_v.get_children(): self.tree_detalle_v.delete(i)
        self.frm_detalle_v.config(text="Detalle de la Venta Seleccionada") 
            
        try:
            desde_sql = _formatear_fecha_para_sql(self.ent_desde_v.get().strip())
            hasta_sql = _formatear_fecha_para_sql(self.ent_hasta_v.get().strip())
            
            if (self.ent_desde_v.get().strip() and not desde_sql) or (self.ent_hasta_v.get().strip() and not hasta_sql):
                messagebox.showerror("Formato Inválido", "Use el formato DD/MM/AAAA para las fechas.", parent=self.win)
                return

            id_vend = self.vendedor_ids[self.cb_vendedor_v.current()]
            id_cli = self.cliente_ids[self.cb_cliente_v.current()]
            
            ventas = self.backend.obtener_ventas_maestro(
                fecha_desde=desde_sql,
                fecha_hasta=hasta_sql,
                id_vendedor=id_vend,
                id_cliente=id_cli
            )
            
            for v in ventas:
                self.tree_maestro_v.insert("", tk.END, values=[
                    v.get('id_venta'),
                    _formatear_fecha_para_ui(v.get('fecha')),
                    v.get('cliente') or "Consumidor Final",
                    v.get('vendedor') or "N/A",
                    _fmt_mon(v.get('total')),
                    v.get('estado'),
                    v.get('tipo_pago')
                ])
        except Exception as e:
            logger.exception("Error buscando ventas")
            messagebox.showerror("Error", f"No se pudieron cargar las ventas:\n{e}", parent=self.win)

    def mostrar_detalle_venta(self, event=None):
        for i in self.tree_detalle_v.get_children(): self.tree_detalle_v.delete(i)
        seleccion = self.tree_maestro_v.selection()
        if not seleccion: 
            self.frm_detalle_v.config(text="Detalle de la Venta Seleccionada")
            return
            
        item_seleccionado = seleccion[0]
        id_venta = self.tree_maestro_v.item(item_seleccionado, "values")[0]
        
        self.frm_detalle_v.config(text=f"Detalle de la Venta Seleccionada [ID: {id_venta}]")
        
        try:
            detalles = self.backend.obtener_venta_detalle(int(id_venta))
            for d in detalles:
                self.tree_detalle_v.insert("", tk.END, values=[
                    d.get('id_producto') or "N/A",
                    d.get('nombre_producto') or "(Producto eliminado)",
                    d.get('codigo_barras') or "",
                    d.get('cantidad'),
                    _fmt_mon(d.get('precio_unitario')),
                    _fmt_mon(d.get('subtotal'))
                ])
        except Exception as e:
            logger.exception("Error mostrando detalle de venta")

    # ===================================================================
    # PESTAÑA 2: HISTORIAL DE COMPRAS
    # ===================================================================
    def _crear_tab_compras(self):
        frm_filtros = tk.Frame(self.tab_compras, bg="#f4f4f8", padx=10, pady=10)
        frm_filtros.pack(fill=tk.X)

        # --- Fila 1 ---
        tk.Label(frm_filtros, text="Desde:", bg="#f4f4f8", font=("Segoe UI", 9)).grid(row=0, column=0, padx=(5,2))
        self.ent_desde_c = EntryConPlaceholder(frm_filtros, placeholder="DD/MM/AAAA", width=12, font=("Segoe UI", 9))
        self.ent_desde_c.grid(row=0, column=1, padx=2)
        self.ent_desde_c.delete(0, tk.END)
        self.ent_desde_c.insert(0, f"01/{date.today().month:02d}/{date.today().year}")
        self.ent_desde_c['fg'] = self.ent_desde_c.default_fg_color

        tk.Label(frm_filtros, text="Hasta:", bg="#f4f4f8", font=("Segoe UI", 9)).grid(row=0, column=2, padx=(10,2))
        self.ent_hasta_c = EntryConPlaceholder(frm_filtros, placeholder="DD/MM/AAAA", width=12, font=("Segoe UI", 9))
        self.ent_hasta_c.grid(row=0, column=3, padx=2)
        self.ent_hasta_c.delete(0, tk.END)
        self.ent_hasta_c.insert(0, date.today().strftime("%d/%m/%Y"))
        self.ent_hasta_c['fg'] = self.ent_hasta_c.default_fg_color

        # --- Fila 2 ---
        tk.Label(frm_filtros, text="Proveedor:", bg="#f4f4f8", font=("Segoe UI", 9)).grid(row=1, column=0, padx=(5,2), pady=(5,0))
        self.cb_proveedor_c = ttk.Combobox(frm_filtros, state="readonly", width=28, font=("Segoe UI", 9))
        self.cb_proveedor_c.grid(row=1, column=1, padx=2, columnspan=2, pady=(5,0)) # columnspan para alinear

        btn_buscar = tk.Button(frm_filtros, text="🔎 Buscar", command=self.buscar_compras, 
                             bg="#03A9F4", fg="white", width=10, font=("Segoe UI", 9, "bold"))
        btn_buscar.grid(row=1, column=3, padx=(10, 8), pady=(5,0))
        
        btn_exportar_c = tk.Button(frm_filtros, text="📊 CSV", 
                                 command=self.exportar_a_csv, 
                                 bg="#16a34a", fg="white", 
                                 font=("Segoe UI", 9, "bold"),
                                 width=8)
        btn_exportar_c.grid(row=1, column=4, padx=2, pady=(5,0))
        
        # --- Fin Filtros ---
        
        frm_maestro = tk.LabelFrame(self.tab_compras, text="Compras Realizadas", bg="#f4f4f8", padx=10, pady=10, font=("Segoe UI", 9, "bold"))
        frm_maestro.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        cols_m = ("ID", "Fecha", "Proveedor", "Total", "Estado", "Registró")
        self.tree_maestro_c = ttk.Treeview(frm_maestro, columns=cols_m, show="headings", height=9)
        self.tree_maestro_c.pack(side="left", fill="both", expand=True)

        ys_m = ttk.Scrollbar(frm_maestro, orient="vertical", command=self.tree_maestro_c.yview)
        ys_m.pack(side="right", fill="y")
        self.tree_maestro_c.configure(yscrollcommand=ys_m.set)

        for c in cols_m: self.tree_maestro_c.heading(c, text=c)
        self.tree_maestro_c.column("ID", width=60, anchor="center")
        self.tree_maestro_c.column("Fecha", width=140)
        self.tree_maestro_c.column("Proveedor", width=250)
        self.tree_maestro_c.column("Total", width=100, anchor="e")
        self.tree_maestro_c.column("Estado", width=80, anchor="center")
        self.tree_maestro_c.column("Registró", width=150)
        
        self.tree_maestro_c.bind("<<TreeviewSelect>>", self.mostrar_detalle_compra)

        self.frm_detalle_c = tk.LabelFrame(self.tab_compras, text="Detalle de la Compra Seleccionada", bg="#f4f4f8", padx=10, pady=10, font=("Segoe UI", 9, "bold"))
        self.frm_detalle_c.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        cols_d = ("ID Prod", "Producto", "Código Barras", "Cant", "Costo Unit", "Subtotal")
        self.tree_detalle_c = ttk.Treeview(self.frm_detalle_c, columns=cols_d, show="headings", height=5)
        self.tree_detalle_c.pack(side="left", fill="both", expand=True)

        ys_d = ttk.Scrollbar(self.frm_detalle_c, orient="vertical", command=self.tree_detalle_c.yview)
        ys_d.pack(side="right", fill="y")
        self.tree_detalle_c.configure(yscrollcommand=ys_d.set)

        for c in cols_d: self.tree_detalle_c.heading(c, text=c)
        self.tree_detalle_c.column("ID Prod", width=60, anchor="center")
        self.tree_detalle_c.column("Producto", width=250)
        self.tree_detalle_c.column("Código Barras", width=150)
        self.tree_detalle_c.column("Cant", width=60, anchor="e")
        self.tree_detalle_c.column("Costo Unit", width=100, anchor="e")
        self.tree_detalle_c.column("Subtotal", width=100, anchor="e")

    def cargar_filtros_compras(self):
        try:
            proveedores = self.backend.obtener_proveedores(incluir_inactivos=True) or []
            p_nombres = ["(Todos)"] + [p.get("nombre", "") for p in proveedores]
            self.proveedor_ids = [None] + [p.get("id_proveedor") for p in proveedores]
            self.cb_proveedor_c["values"] = p_nombres
            self.cb_proveedor_c.current(0)
        except Exception as e:
            logger.error(f"Error cargando filtros (Compras): {e}")

    def buscar_compras(self):
        for i in self.tree_maestro_c.get_children(): self.tree_maestro_c.delete(i)
        for i in self.tree_detalle_c.get_children(): self.tree_detalle_c.delete(i)
        self.frm_detalle_c.config(text="Detalle de la Compra Seleccionada") 
            
        try:
            desde_sql = _formatear_fecha_para_sql(self.ent_desde_c.get().strip())
            hasta_sql = _formatear_fecha_para_sql(self.ent_hasta_c.get().strip())
            
            if (self.ent_desde_c.get().strip() and not desde_sql) or (self.ent_hasta_c.get().strip() and not hasta_sql):
                messagebox.showerror("Formato Inválido", "Use el formato DD/MM/AAAA para las fechas.", parent=self.win)
                return

            id_prov = self.proveedor_ids[self.cb_proveedor_c.current()]
            
            compras = self.backend.obtener_compras_maestro(
                fecha_desde=desde_sql,
                fecha_hasta=hasta_sql,
                id_proveedor=id_prov
            )
            
            for c in compras:
                self.tree_maestro_c.insert("", tk.END, values=[
                    c.get('id_compra'),
                    _formatear_fecha_para_ui(c.get('fecha')),
                    c.get('proveedor') or "N/A",
                    _fmt_mon(c.get('total')),
                    c.get('estado'),
                    c.get('usuario') or "N/A"
                ])
        except Exception as e:
            logger.exception("Error buscando compras")
            messagebox.showerror("Error", f"No se pudieron cargar las compras:\n{e}", parent=self.win)

    def mostrar_detalle_compra(self, event=None):
        for i in self.tree_detalle_c.get_children(): self.tree_detalle_c.delete(i)
        seleccion = self.tree_maestro_c.selection()
        if not seleccion: 
            self.frm_detalle_c.config(text="Detalle de la Compra Seleccionada")
            return
            
        item_seleccionado = seleccion[0]
        id_compra = self.tree_maestro_c.item(item_seleccionado, "values")[0]
        
        self.frm_detalle_c.config(text=f"Detalle de la Compra Seleccionada [ID: {id_compra}]")
        
        try:
            detalles = self.backend.obtener_compra_detalle(int(id_compra))
            for d in detalles:
                self.tree_detalle_c.insert("", tk.END, values=[
                    d.get('id_producto') or "N/A",
                    d.get('nombre_producto') or "(Producto eliminado)",
                    d.get('codigo_barras') or "",
                    d.get('cantidad'),
                    _fmt_mon(d.get('precio_unitario')),
                    _fmt_mon(d.get('subtotal'))
                ])
        except Exception as e:
            logger.exception("Error mostrando detalle de compra")

    # ===================================================================
    # FUNCIÓN DE EXPORTACIÓN
    # ===================================================================
    def exportar_a_csv(self):
        try:
            tab_id = self.notebook.index(self.notebook.select())
            
            hoy = datetime.now().strftime("%d-%m-%Y")
            
            if tab_id == 0: 
                tree_maestro = self.tree_maestro_v
                tree_detalle = self.tree_detalle_v
                default_filename = f"historial_ventas_{hoy}.csv"
            else: 
                tree_maestro = self.tree_maestro_c
                tree_detalle = self.tree_detalle_c
                default_filename = f"historial_compras_{hoy}.csv"

            if not tree_maestro.get_children():
                messagebox.showinfo("Nada que exportar", "La tabla de historial está vacía.", parent=self.win)
                return

            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("Archivo CSV (delimitado por punto y coma)", "*.csv"), ("Todos los archivos", "*.*")],
                initialfile=default_filename, 
                title="Guardar como CSV"
            )
            
            if not filepath:
                return 

            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';') 
                
                columnas_maestro = tree_maestro['columns']
                writer.writerow(columnas_maestro)
                
                for item_id in tree_maestro.get_children():
                    valores = tree_maestro.item(item_id, 'values')
                    writer.writerow(valores)
                
                writer.writerow([])
                writer.writerow(["--- Detalle (de la fila seleccionada) ---"])
                
                columnas_detalle = tree_detalle['columns']
                writer.writerow(columnas_detalle)
                
                if tree_detalle.get_children():
                    for item_id in tree_detalle.get_children():
                        valores = tree_detalle.item(item_id, 'values')
                        writer.writerow(valores)
                else:
                    writer.writerow(["(No se seleccionó ninguna fila del maestro para ver el detalle)"])

            messagebox.showinfo("Éxito", f"Datos exportados correctamente a:\n{filepath}", parent=self.win)
        except Exception as e:
            logger.exception("Error al exportar CSV")
            messagebox.showerror("Error", f"No se pudo exportar el archivo CSV:\n{e}", parent=self.win)