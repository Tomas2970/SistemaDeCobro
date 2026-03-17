# app/frontend/interfaz_inventario.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, filedialog
from typing import List, Dict, Any, Optional
import logging
import csv
from datetime import datetime

# Reconstruir imports basados en tu código
try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
    from app.database.permisos import tiene_permiso, puede_ajustar_inventario_manual
    from app.frontend.stock_event_manager import stock_events
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass
    def tiene_permiso(u, a): return True
    def puede_ajustar_inventario_manual(u): return True
    class DummyStockEvents:
        def suscribir(self, cb): pass
        def desuscribir(self, cb): pass
    stock_events = DummyStockEvents()

try:
    from app.frontend.interfaz_productos import ui_productos
    from app.frontend.componentes_ui import EntryDecimal
except ImportError:
    ui_productos = None
    EntryDecimal = ttk.Entry


logger = logging.getLogger(__name__)

# --- Funciones de Formato ---
def _fmt_stock(val: Any, es_pesable: bool = False) -> str:
    try:
        val = float(val)
        if es_pesable or val % 1 != 0:
            return f"{val:,.3f} kg"
        return f"{int(val):,} un"
    except: return "0 un"
def _fmt_mon(val: Any) -> str:
    try: return f"$ {float(val):,.2f}"
    except: return "$ 0.00"
def _fmt_porc(val: Any) -> str:
    try: return f"{float(val):.2f} %"
    except: return "0.00 %"

# --- Lógica de la interfaz ---
class UIInventario:
    def __init__(self, parent: tk.Misc, backend, usuario: dict):
        self.backend = backend
        self.usuario = usuario
        self.win = tk.Toplevel(parent)
        self.win.title("📦 Gestión de Inventario")
        self.win.geometry("1000x650") # 🔥 TAMAÑO REDUCIDO
        self.win.config(bg="#f4f4f8")
        self.can_ajustar_manual = puede_ajustar_inventario_manual(usuario)
        
        self.productos_cache = []
        self.cat_map = {}
        self.var_filtrar_stock_bajo = tk.BooleanVar(value=False)

        # 🔥 ESTILOS MODERNOS
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("Modern.Treeview",
                        background="#ffffff",
                        foreground="#1f2937",
                        rowheight=32,
                        fieldbackground="#ffffff",
                        borderwidth=0,
                        font=('Segoe UI', 10))

        style.configure("Modern.Treeview.Heading",
                        background="#f3f4f6",
                        foreground="#374151",
                        relief="flat",
                        borderwidth=1,
                        font=('Segoe UI', 10, 'bold'))

        style.map("Modern.Treeview.Heading",
                  background=[('active', '#e5e7eb')])

        self._crear_widgets()
        self._cargar_categorias_para_filtro()
        self.cargar_todo()

        stock_events.suscribir(self.cargar_todo)
        
        configurar_navegacion_ventana(self.win)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self.win.grab_set()
        self.win.after(100, lambda: self.entry_busqueda.focus_set())

    def _on_close(self):
        stock_events.desuscribir(self.cargar_todo)
        self.win.destroy()

    def _crear_widgets(self):
        # 1. Header (Búsqueda y Filtros)
        frm_header = tk.Frame(self.win, bg="#e0f2fe", padx=15, pady=10)
        frm_header.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(frm_header, text="🔍 Buscar (ID, Cód., Nombre):", bg="#e0f2fe", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.var_busqueda = tk.StringVar()
        self.entry_busqueda = tk.Entry(frm_header, textvariable=self.var_busqueda, width=30)
        self.entry_busqueda.pack(side=tk.LEFT, padx=5)
        self.var_busqueda.trace_add("write", self._filtrar_lista) 
        
        tk.Label(frm_header, text="Categoría:", bg="#e0f2fe", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(20, 5))
        self.cb_categoria = ttk.Combobox(frm_header, state="readonly", width=20)
        self.cb_categoria.pack(side=tk.LEFT, padx=5)
        self.cb_categoria.bind("<<ComboboxSelected>>", self._filtrar_lista)
        
        # Botón Stock Bajo como CHECKBOX DE FILTRO
        tk.Checkbutton(frm_header, text="🚨 Stock Bajo", 
                       variable=self.var_filtrar_stock_bajo, 
                       command=self._filtrar_lista,
                       bg="#e0f2fe", fg="#ef4444", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=20)
        
        # 🔥 BOTÓN EXPORTAR CSV
        tk.Button(
            frm_header, 
            text="📊 Exportar CSV", 
            command=self._exportar_csv,
            bg="#f59e0b", # NARANJA_ESPECIAL
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2",
            activebackground="#d97706"
        ).pack(side=tk.RIGHT, padx=5)
        
        # 2. Tabla (Treeview)
        frm_lista = tk.Frame(self.win, bg="#f4f4f8", padx=10)
        frm_lista.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 🔥 USAR ESTILO MODERN.TREEVIEW
        cols = ("ID", "Nombre", "Categoría", "Stock", "Stock Min.", "Precio Venta")
        self.tree = ttk.Treeview(frm_lista, columns=cols, show="headings", style="Modern.Treeview")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ys = ttk.Scrollbar(frm_lista, orient="vertical", command=self.tree.yview)
        ys.pack(side="right", fill=tk.Y)
        self.tree.configure(yscrollcommand=ys.set)
        
        for c in cols: self.tree.heading(c, text=c)
        # 🔥 ANCHOS AJUSTADOS
        self.tree.column("ID", width=0, minwidth=0, stretch=False)
        self.tree.column("Nombre", width=350)
        self.tree.column("Categoría", width=200)
        self.tree.column("Stock", width=120, anchor="e")
        self.tree.column("Stock Min.", width=120, anchor="e")
        self.tree.column("Precio Venta", width=120, anchor="e")

        self.tree.tag_configure('bajo', background='#fee2e2') # Fondo rojo claro
        self.tree.bind("<Double-1>", self._on_doble_clic)

        # 3. Footer (Botones y Ajuste Manual)
        frm_footer = tk.Frame(self.win, bg="#f4f4f8", padx=10, pady=10)
        frm_footer.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 🔥 BOTÓN NUEVO PRODUCTO
        tk.Button(
            frm_footer, 
            text="➕ Nuevo Producto", 
            command=lambda: self._abrir_abm_productos(None), 
            bg="#10b981", # VERDE_CONFIRMAR
            fg="white", 
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground="#059669"
        ).pack(side=tk.LEFT, padx=10)
        
        # 🔥 BOTÓN CERRAR
        tk.Button(
            frm_footer, 
            text="Cancelar", 
            command=self.win.destroy, 
            bg="#6b7280", # GRIS_SECUNDARIO
            fg="white", 
            font=("Segoe UI", 10),
            relief="flat",
            padx=15,
            pady=10,
            cursor="hand2",
            activebackground="#4b5563"
        ).pack(side=tk.RIGHT, padx=10)


    def _cargar_categorias_para_filtro(self):
        try:
            cats = self.backend.obtener_categorias()
            self.cat_map = {c['nombre']: c['id_categoria'] for c in cats}
            self.cb_categoria['values'] = ["(Todas)"] + list(self.cat_map.keys())
            self.cb_categoria.current(0)
        except Exception as e:
            logger.error(f"Error cargando categorías: {e}")

    def cargar_todo(self):
        try:
            self.productos_cache = self.backend.obtener_productos_full()
            self._filtrar_lista()
        except Exception as e:
            logger.error(f"Error cargando inventario: {e}")
            messagebox.showerror("Error", f"Error cargando inventario: {e}")

    def _resolver_busqueda(self, q: str) -> List[Dict[str, Any]]:
        q = q.strip()
        if not q:
            return self.productos_cache or []

        # Si parece un código de barras (solo números) o es muy corto, intentar búsqueda exacta primero
        if q.isdigit():
            resultado_unico = self.backend.buscar_producto_inteligente(q)
            if resultado_unico:
                return [resultado_unico]
        
        # Para texto siempre filtrar el cache completo por nombre (permite múltiples resultados)
        q_lower = q.lower()
        return [p for p in self.productos_cache if q_lower in p.get('nombre', '').lower()]

    def _filtrar_lista(self, *args):
        for i in self.tree.get_children(): self.tree.delete(i)
        
        query = self.var_busqueda.get()
        cat_sel_nombre = self.cb_categoria.get()
        cat_id_filtro = self.cat_map.get(cat_sel_nombre)
        
        productos_filtrados = self._resolver_busqueda(query)
        
        if cat_id_filtro:
            productos_filtrados = [p for p in productos_filtrados if p.get('id_categoria') == cat_id_filtro]
        
        # 3. Filtrar por Stock Bajo (NUEVA LÓGICA DE FILTRO)
        if self.var_filtrar_stock_bajo.get():
            productos_filtrados = [
                p for p in productos_filtrados 
                if float(p.get('stock', 0)) <= int(p.get('stock_minimo', 0))
            ]

        # 4. Llenar Treeview
        for p in productos_filtrados:
            stock = float(p.get('stock', 0.0))
            minimo = int(p.get('stock_minimo', 0))
            es_pesable = bool(p.get('es_pesable', False))
            
            tag = 'bajo' if stock <= minimo else ''
            
            self.tree.insert("", tk.END, values=[
                p.get('id_producto'),
                p.get('nombre'),
                p.get('nombre_categoria') or "-",
                _fmt_stock(stock, es_pesable),
                f"{minimo} un",
                _fmt_mon(p.get('precio')),
                # Quitamos Margen y Pesable de los values
            ], tags=(tag,))

    def _abrir_abm_productos(self, id_prod: Optional[int]):
        """Función helper para abrir el ABM de producto"""
        if not ui_productos:
            messagebox.showinfo("Error", "Módulo de gestión de productos no disponible.")
            return
            
        if not tiene_permiso(self.usuario, 'crear_productos') and not tiene_permiso(self.usuario, 'editar_productos'):
            messagebox.showwarning(
                "Acceso Denegado", 
                "⚠️ Su rol solo permite la consulta del inventario. No puede modificar o crear productos.", 
                parent=self.win
            )
            return

        try:
            ui_productos(
                parent=self.win,
                backend=self.backend,
                usuario=self.usuario,
                id_producto_a_cargar=id_prod, 
                callback_on_save=self.cargar_todo 
            )
        except Exception as e:
            logger.error(f"Error abriendo UI Productos: {e}")
            messagebox.showerror("Error", f"Fallo al abrir ABM de Producto:\n{e}")

    def _on_doble_clic(self, event):
        sel = self.tree.selection()
        if not sel: 
            return # Solo abre si hay algo seleccionado
        
        item = sel[0]
        id_prod_str = self.tree.item(item, "values")[0]
        
        try:
            id_prod = int(id_prod_str)
            self._abrir_abm_productos(id_prod) # 🔥 Abre directamente en modo edición
        except ValueError:
             messagebox.showwarning("Error", "Selección inválida.", parent=self.win)
             return


    # 🔥 ELIMINAMOS _mostrar_stock_bajo (La funcionalidad es ahora _filtrar_lista con checkbox)
    # 🔥 ELIMINAMOS _aplicar_ajuste (Funcionalidad eliminada)

    def _exportar_csv(self):
        try:
            if not self.tree.get_children():
                messagebox.showinfo(
                    "Nada que exportar",
                    "La tabla de inventario está vacía.",
                    parent=self.win,
                )
                return

            hoy = datetime.now().strftime("%d-%m-%Y")
            default_filename = f"reporte_inventario_vista_{hoy}.csv"

            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("Archivo CSV (delimitado por coma/punto y coma)", "*.csv")],
                initialfile=default_filename,
                title="Guardar como CSV",
            )

            if not filepath:
                return

            cols_visibles = [self.tree.heading(c)['text'] for c in self.tree['columns']]

            with open(filepath, "w", newline="", encoding="utf-8-sig") as f: # utf-8-sig para compatibilidad con Excel
                writer = csv.writer(f, delimiter=";") # Usar ; como delimitador
                writer.writerow(cols_visibles)
                
                for item_id in self.tree.get_children():
                    row = self.tree.item(item_id, "values")
                    clean_row = [str(x).replace('.', ',').strip() if isinstance(x, (float, str)) and '$' not in str(x) else str(x).strip() for x in row]
                    writer.writerow(clean_row)

            messagebox.showinfo(
                "Exportado",
                f"Archivo guardado exitosamente.",
                parent=self.win,
            )
        except Exception as e:
            messagebox.showerror(
                "Exportar",
                f"No se pudo exportar el archivo:\n{e}",
                parent=self.win,
            )

def ui_inventario(parent: tk.Misc, backend, usuario: dict):
    UIInventario(parent, backend, usuario)