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
    from app.frontend.autorizacion import solicitar_autorizacion_supervisor
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass
    def tiene_permiso(u, a): return True
    def puede_ajustar_inventario_manual(u): return True
    def solicitar_autorizacion_supervisor(p, b, u, c=None): pass
    class DummyStockEvents:
        def suscribir(self, cb): pass
        def desuscribir(self, cb): pass
    stock_events = DummyStockEvents()

try:
    from app.frontend.interfaz_productos import ui_productos
    from app.frontend.componentes_ui import EntryDecimal
except ImportError:
    ui_productos = None
    EntryDecimal = None  # Se resolverá al importar ctk dentro de __init__

try:
    from app.frontend.theme_config import preparar_ventana, centrar_y_mostrar_ventana
except ImportError:
    def preparar_ventana(w): pass
    def centrar_y_mostrar_ventana(w): pass


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
        import customtkinter as ctk
        self.backend = backend
        self.usuario = usuario
        self.win = ctk.CTkToplevel(parent)
        preparar_ventana(self.win)
        self.win.title("📦 Gestión de Inventario")
        self.win.geometry("1100x750")
        try: self.win.state('zoomed')
        except: pass
        self.can_ajustar_manual = puede_ajustar_inventario_manual(usuario)
        
        self.productos_cache = []
        self.cat_map = {}
        self.var_filtrar_stock_bajo = tk.BooleanVar(value=False)

        self._crear_widgets()
        self._cargar_categorias_para_filtro()
        self.cargar_todo()

        stock_events.suscribir(self.cargar_todo)
        
        configurar_navegacion_ventana(self.win)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        if self.win.state() == 'zoomed':
            self.win.deiconify()
        else:
            centrar_y_mostrar_ventana(self.win)
        self.win.grab_set()
        self.win.after(100, lambda: self.entry_busqueda.focus_set())

    def _on_close(self):
        stock_events.desuscribir(self.cargar_todo)
        self.win.destroy()

    def _crear_widgets(self):
        import customtkinter as ctk
        col_card = "#ffffff" if ctk.get_appearance_mode()=="Light" else "#1f2937"
        col_border = "#e5e7eb" if ctk.get_appearance_mode()=="Light" else "#374151"
        font_title = ("Segoe UI", 15, "bold")
        font_normal = ("Segoe UI", 14)

        frm_header = ctk.CTkFrame(self.win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
        frm_header.pack(fill="x", padx=25, pady=(25, 10))
        
        ctk.CTkLabel(frm_header, text="🔍 Buscar Producto:", font=font_title, text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white").pack(side="left", padx=(20, 10), pady=20)
        self.var_busqueda = tk.StringVar()
        
        self.entry_busqueda = ctk.CTkEntry(frm_header, textvariable=self.var_busqueda, font=font_normal, height=45, width=300)
        self.entry_busqueda.pack(side="left", padx=15)
        self.var_busqueda.trace_add("write", self._filtrar_lista) 
        
        ctk.CTkLabel(frm_header, text="Categoría:", font=font_title, text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white").pack(side="left", padx=(30, 10))
        col_opt_bg = "#f3f4f6" if ctk.get_appearance_mode()=="Light" else "#374151"
        col_opt_btn = "#e5e7eb" if ctk.get_appearance_mode()=="Light" else "#4b5563"
        col_opt_hover = "#d1d5db" if ctk.get_appearance_mode()=="Light" else "#6b7280"
        col_opt_text = "#1f2937" if ctk.get_appearance_mode()=="Light" else "#f9fafb"
        self.cb_categoria = ctk.CTkOptionMenu(frm_header, font=font_normal, fg_color=col_opt_bg, button_color=col_opt_btn, button_hover_color=col_opt_hover, text_color=col_opt_text, command=self._filtrar_lista, width=200, height=45)
        self.cb_categoria.pack(side="left", padx=5)
        
        ctk.CTkSwitch(frm_header, text="Stock Bajo / Crítico", variable=self.var_filtrar_stock_bajo, command=self._filtrar_lista, font=font_title, progress_color="#ef4444").pack(side="left", padx=40)
        
        ctk.CTkButton(frm_header, text="📊 Exportar CSV", font=("Segoe UI", 14, "bold"), fg_color="#f59e0b", hover_color="#d97706", width=160, height=45, command=self._exportar_csv).pack(side="right", padx=20)
        
        # 3. Footer (Empacado antes para anclar al fondo)
        frm_footer = ctk.CTkFrame(self.win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
        frm_footer.pack(fill="x", side="bottom", padx=25, pady=(10, 25))
        
        ctk.CTkButton(frm_footer, text="➕ Agregar / Editar Producto", font=("Segoe UI", 16, "bold"), fg_color="#10b981", hover_color="#059669", width=250, height=60, command=lambda: self._abrir_abm_productos(None)).pack(side="left", padx=20, pady=20)
        ctk.CTkButton(frm_footer, text="Cerrar", font=("Segoe UI", 15, "bold"), fg_color="#6b7280", hover_color="#4b5563", width=150, height=55, command=self.win.destroy).pack(side="right", padx=20, pady=20)

        # 2. Tabla (Treeview)
        frm_lista = ctk.CTkFrame(self.win, fg_color=col_card, corner_radius=10, border_color=col_border, border_width=1)
        frm_lista.pack(fill="both", expand=True, padx=25, pady=10)
        
        cols = ("ID", "Nombre", "Categoría", "Stock", "Stock Min.", "Precio Venta")
        self.tree = ttk.Treeview(frm_lista, columns=cols, show="headings", style="Modern.Treeview")
        
        ys = ctk.CTkScrollbar(frm_lista, command=self.tree.yview)
        ys.pack(side="right", fill="y", padx=(0, 5), pady=5)
        self.tree.configure(yscrollcommand=ys.set)
        
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("ID", width=0, stretch=False)
        self.tree.configure(displaycolumns=("Nombre", "Categoría", "Stock", "Stock Min.", "Precio Venta"))
        self.tree.column("Nombre", width=450)
        self.tree.column("Categoría", width=200)
        self.tree.column("Stock", width=120, anchor="center")
        self.tree.column("Stock Min.", width=120, anchor="center")
        self.tree.column("Precio Venta", width=150, anchor="e")

        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.tree.tag_configure('bajo', foreground='#f87171') # Solo texto rojo claro, sin fondo blanco
        self.tree.bind("<Double-1>", self._on_doble_clic)

    def _cargar_categorias_para_filtro(self):
        try:
            cats = self.backend.obtener_categorias()
            self.cat_map = {c['nombre']: c['id_categoria'] for c in cats}
            valores = ["(Todas)"] + list(self.cat_map.keys())
            self.cb_categoria.configure(values=valores)
            if valores: self.cb_categoria.set(valores[0])
        except Exception as e:
            pass

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
                _fmt_stock(minimo, es_pesable),
                _fmt_mon(p.get('precio')),
                # Quitamos Margen y Pesable de los values
            ], tags=(tag,))

    def _abrir_abm_productos(self, id_prod: Optional[int]):
        """Función helper para abrir el ABM de producto"""
        if not ui_productos:
            messagebox.showinfo("Error", "Módulo de gestión de productos no disponible.")
            return

        def _ejecutar_abm(usr):
            try:
                ui_productos(
                    parent=self.win,
                    backend=self.backend,
                    usuario=usr,
                    id_producto_a_cargar=id_prod, 
                    callback_on_save=self.cargar_todo 
                )
            except Exception as e:
                logger.error(f"Error abriendo UI Productos: {e}")
                messagebox.showerror("Error", f"Fallo al abrir ABM de Producto:\n{e}")

        if self.usuario.get('id_rol') in (1, 3):  # Admin o Supervisor → acceso directo
            _ejecutar_abm(self.usuario)
        else:  # Vendedor → pedir credenciales de administrador
            solicitar_autorizacion_supervisor(self.win, self.backend, self.usuario, _ejecutar_abm)

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
                parent=self.win,
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