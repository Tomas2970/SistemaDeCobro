from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, filedialog
from app.frontend import custom_dialogs as messagebox
from app.frontend.theme_config import THEME_COLORS, get_color, aplicar_tema_ventana, configurar_estilo_notebook, configurar_estilo_treeview, preparar_ventana, centrar_y_mostrar_ventana
from typing import Optional, Any
from datetime import date, datetime, timedelta
import logging
import csv

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
    from app.database.permisos import tiene_permiso, DIAS_HISTORIAL_SUPERVISOR
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass
    def tiene_permiso(u, a): return True
    DIAS_HISTORIAL_SUPERVISOR = 7

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
        texto = str(fecha_sql)
        if len(texto) >= 10 and "-" in texto[:10]:
            partes = texto[:10].split("-")
            if len(partes) == 3:
                return f"{partes[2]}/{partes[1]}/{partes[0]}" + texto[10:]
        return texto

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
                 filtro_cliente_id: int | None = None,
                 max_dias_atras: int | None = None):

        self.backend = backend
        self.usuario = usuario

        # --- Restricción de rango por rol ---
        # Si el llamador pasa max_dias_atras, se respeta. Si no, se aplica el
        # límite automático para Supervisores (id_rol == 3).
        id_rol = usuario.get('id_rol')
        if max_dias_atras is not None:
            self._max_dias = max_dias_atras
        elif id_rol == 3:  # Supervisor
            self._max_dias = DIAS_HISTORIAL_SUPERVISOR
        else:
            self._max_dias = None  # Sin restricción (Admin / Vendedor)

        self._fecha_minima: date | None = (
            date.today() - timedelta(days=self._max_dias) if self._max_dias is not None else None
        )
        
        self.win = ctk.CTkToplevel(parent)
        preparar_ventana(self.win)
        self.win.title("📋 Historiales del Sistema")
        
        altura = 720 
        self.win.geometry(f"1300x{altura}")
        
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        configurar_estilo_treeview()

        frm_header = ctk.CTkFrame(self.win, fg_color=get_color("accent_primary"), corner_radius=0)
        frm_header.pack(fill="x")
        ctk.CTkLabel(frm_header, text="HISTORIALES DEL SISTEMA", font=("Segoe UI", 18, "bold"), text_color="white").pack(pady=15)

        # Banner de restricción — visible solo para Supervisores
        if self._fecha_minima is not None:
            frm_banner = ctk.CTkFrame(self.win, fg_color="#1e3a8a", corner_radius=0)
            frm_banner.pack(fill="x")
            ctk.CTkLabel(
                frm_banner,
                text=f"🔒  Acceso limitado — Encargado de Turno — Últimos {self._max_dias} días  "
                     f"(desde {self._fecha_minima.strftime('%d/%m/%Y')})",
                font=("Segoe UI", 12, "bold"),
                text_color="#bfdbfe"
            ).pack(pady=6)

        self.vendedores_raw = []
        self.clientes_raw = []
        self.proveedores_raw = []
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
        self.usuario_caja_sel = {"id": None, "nombre": "(Todos)"}
        
        # Estado de Paginación
        self.pag_size = 50
        self.pag_ventas = 0
        self.total_ventas = 0
        self.pag_compras = 0
        self.total_compras = 0
        self.pag_pagos = 0
        self.total_pagos = 0
        self.pag_caja = 0
        self.total_caja = 0
        
        # cargar_datos_combos se difiere drásticamente para que la ventana CTk se renderice fluidamente antes de bloquear mysql
        self.win.after(100, self.cargar_datos_combos)

        # Footer global (botones secundarios a la izquierda y cerrar a la derecha)
        frm_footer = ctk.CTkFrame(self.win, fg_color="transparent")
        frm_footer.pack(fill="x", padx=10, side=tk.BOTTOM)
        
        frm_footer_left = ctk.CTkFrame(frm_footer, fg_color="transparent")
        frm_footer_left.pack(side=tk.LEFT, pady=10)
        
        self.btn_exportar = ctk.CTkButton(frm_footer_left, text="📊 Exportar", command=self.exportar_a_csv_dinamico, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 13, "bold"), width=120)
        self.btn_exportar.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_anular = ctk.CTkButton(frm_footer_left, text="🗑️ Anular", command=self.anular_accion_ui, fg_color="#ef4444", hover_color="#dc2626", font=("Segoe UI", 13, "bold"), width=120)
        self.btn_anular.pack(side=tk.LEFT)
        
        if not tiene_permiso(self.usuario, 'cancelar_ventas'):
            self.btn_anular.configure(state="disabled", fg_color="gray")

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
        centrar_y_mostrar_ventana(self.win)
        self.win.grab_set()
        
    def exportar_a_csv_dinamico(self):
        try:
            idx = self.notebook.index(self.notebook.select())
            self.exportar_a_csv(idx)
        except Exception:
            pass

    def anular_accion_ui(self):
        try:
            idx = self.notebook.index(self.notebook.select())
            if idx == 0:
                self.anular_venta_ui()
            elif idx == 1:
                self.anular_compra_ui()
            else:
                messagebox.showwarning("No soportado", "No se puede anular en esta pestaña.", parent=self.win)
        except Exception:
            pass

    def anular_compra_ui(self):
        sel = self.tree_maestro_c.selection()
        if not sel:
            messagebox.showwarning("Atención", "Por favor, seleccione la compra que desea anular.", parent=self.win)
            return

        vals = self.tree_maestro_c.item(sel[0], "values")
        if not vals or vals[0] == "Aviso":
            return

        id_compra = int(vals[0])
        estado = vals[5]
        total = vals[4]
        medio_pago = vals[6]

        if estado == "cancelada":
            messagebox.showwarning("Atención", "Esta compra ya se encuentra anulada/cancelada.", parent=self.win)
            return

        motivo_resultado = {"valor": None, "confirmado": False}

        dlg = ctk.CTkToplevel(self.win)
        preparar_ventana(dlg)
        dlg.title("Confirmar Anulación de Compra")
        dlg.geometry("520x330")
        dlg.grab_set()
        dlg.transient(self.win)

        frm_header_dlg = ctk.CTkFrame(dlg, fg_color="#ef4444", corner_radius=0)
        frm_header_dlg.pack(fill="x")
        ctk.CTkLabel(
            frm_header_dlg,
            text="⚠️  ANULAR COMPRA  ⚠️",
            font=("Segoe UI", 16, "bold"),
            text_color="white"
        ).pack(pady=12)

        frm_body = ctk.CTkFrame(dlg, fg_color="transparent")
        frm_body.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(
            frm_body,
            text=f"Compra #{id_compra}  ·  Total: {total}  ·  Medio: {medio_pago}",
            font=("Segoe UI", 13, "bold"),
            text_color=get_color("text_primary")
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            frm_body,
            text="Esta acción descontará el stock ingresado. Si el pago fue a cuenta corriente "
                 "se revertirá la deuda. Si fue en efectivo/tarjeta, se ingresará el dinero en caja.",
            font=("Segoe UI", 11),
            text_color=get_color("text_secondary"),
            justify="left",
            wraplength=460
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            frm_body,
            text="Motivo de anulación (obligatorio):",
            font=("Segoe UI", 12, "bold"),
            text_color=get_color("text_primary")
        ).pack(anchor="w")

        entry_motivo = ctk.CTkEntry(
            frm_body,
            font=("Segoe UI", 12),
            height=36,
            placeholder_text="Ej: Error de proveedor, devolución..."
        )
        entry_motivo.pack(fill="x", pady=(4, 0))

        frm_btns = ctk.CTkFrame(dlg, fg_color="transparent")
        frm_btns.pack(fill="x", padx=20, pady=(0, 15))

        def _confirmar():
            motivo_texto = entry_motivo.get().strip()
            if not motivo_texto:
                entry_motivo.configure(border_color="#ef4444")
                entry_motivo.focus_set()
                return
            motivo_resultado["valor"] = motivo_texto
            motivo_resultado["confirmado"] = True
            dlg.destroy()

        def _cancelar():
            dlg.destroy()

        ctk.CTkButton(
            frm_btns, text="Cancelar", command=_cancelar,
            fg_color=get_color("button_secondary"),
            hover_color=get_color("button_secondary_hover"),
            font=("Segoe UI", 13, "bold"), width=150, height=38
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            frm_btns, text="✓ Confirmar Anulación", command=_confirmar,
            fg_color="#ef4444", hover_color="#dc2626",
            font=("Segoe UI", 13, "bold"), width=200, height=38
        ).pack(side="right")

        entry_motivo.after(150, entry_motivo.focus_set)
        dlg.bind("<Return>", lambda e: _confirmar())
        dlg.bind("<Escape>", lambda e: _cancelar())

        centrar_y_mostrar_ventana(dlg)
        self.win.wait_window(dlg)

        if not motivo_resultado["confirmado"]:
            return

        try:
            exito = self.backend.anular_compra(
                id_compra,
                self.usuario['id_usuario'],
                motivo_resultado["valor"]
            )
            if exito:
                messagebox.showinfo(
                    "Éxito",
                    f"La Compra #{id_compra} ha sido anulada correctamente.\n",
                    parent=self.win
                )
                self.buscar_compras()
        except ValueError as ve:
            messagebox.showwarning("No se pudo anular", str(ve), parent=self.win)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo anular la compra:\n{e}", parent=self.win)

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
        preparar_ventana(popup)
        popup.title(f"Seleccionar {tipo}")
        popup.geometry("500x550")
        
        configurar_navegacion_ventana(popup)

        var_pat = tk.StringVar()
        ctk.CTkLabel(popup, text=f"Buscar {tipo} (ID/Nombre):", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).pack(pady=(15,5), padx=15, anchor="w")
        ent = ctk.CTkEntry(popup, textvariable=var_pat, font=("Segoe UI", 13), height=40, placeholder_text="Nombre o ID...")
        ent.pack(fill="x", padx=15, pady=5)
        
        frame_list = ctk.CTkFrame(popup, fg_color=get_color("bg_surface"), corner_radius=10, border_color=get_color("border_color"), border_width=1)
        frame_list.pack(expand=True, fill="both", padx=15, pady=10)
        
        cols = ("ID", "Nombre")
        tree_sel = ttk.Treeview(frame_list, columns=cols, show="headings", style="Modern.Treeview", height=12)
        
        sc = ctk.CTkScrollbar(frame_list, command=tree_sel.yview)
        sc.pack(side="right", fill="y", padx=(0, 5), pady=5)
        tree_sel.configure(yscrollcommand=sc.set)
        tree_sel.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
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
        centrar_y_mostrar_ventana(popup)
        popup.grab_set()
        popup.transient(self.win)
        self.win.wait_window(popup)

    def _on_rango_change(self, seleccion, selector_desde, selector_hasta):
        _aplicar_filtro_rapido_logic(seleccion, selector_desde.widget_entrada, selector_hasta.widget_entrada)

    def cargar_datos_combos(self):
        def _bg_load():
            try:
                # 1. Consultar base de datos en segundo plano
                vends = self.backend.obtener_vendedores() or []
                clis = self.backend.listar_clientes() or []
                provs = self.backend.obtener_proveedores(incluir_inactivos=True) or []
                
                # 2. Preparar estructuras de datos
                v_nombres = ["(Todos)"] + [v.get("nombre", "") for v in vends]
                v_ids = [None] + [v.get("id_usuario") for v in vends]
                
                c_nombres = ["(Todos)", "(Consumidor Final)"] + [c.get("nombre", "") for c in clis]
                c_ids = [None, 0] + [c.get("id_cliente") for c in clis]
                
                c_nombres_p = ["(Todos)"] + [c.get("nombre", "") for c in clis]
                c_ids_p = [None] + [c.get("id_cliente") for c in clis]
                
                p_nombres = ["(Todos)"] + [p.get("nombre", "") for p in provs]
                p_ids = [None] + [p.get("id_proveedor") for p in provs]
                p_map_id = {p['id_proveedor']: p for p in provs} 
                p_map_nombre = {p['nombre']: p for p in provs}
                
                # 3. Asignar y actualizar la UI de forma segura en el hilo principal
                def _update_ui():
                    self.vendedores_raw = vends
                    self.clientes_raw = clis
                    self.proveedores_raw = provs
                    
                    self.vendedor_nombres = v_nombres
                    self.vendedor_ids = v_ids
                    self.cliente_nombres = c_nombres
                    self.cliente_ids = c_ids
                    self.cliente_nombres_pagos = c_nombres_p
                    self.cliente_ids_pagos = c_ids_p
                    self.proveedor_nombres = p_nombres
                    self.proveedor_ids = p_ids
                    self.proveedores_map_id = p_map_id
                    self.proveedores_map_nombre = p_map_nombre
                    
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
                
                if self.win.winfo_exists():
                    self.win.after(0, _update_ui)
            except Exception as e:
                logger.error(f"Error asíncrono en cargar_datos_combos: {e}")

        import threading
        threading.Thread(target=_bg_load, daemon=True).start()

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
                self.vendedor_sel['id'] = f_vend
                self.vendedor_sel['nombre'] = self.vendedor_nombres[idx]
                if hasattr(self, 'lbl_vendedor_v'):
                    self.lbl_vendedor_v.configure(text=self.vendedor_nombres[idx])
            except: pass
            
        self.filtro_venta_id = f_vta
        self.filtro_compra_id = f_comp
        self.filtro_cliente_id = f_cli

        self.pag_ventas = 0
        self.win.after(400, self.buscar_ventas)
        self.loaded_flags[0] = True

    def on_tab_change(self, event):
        idx = self.notebook.index(self.notebook.select())
        tab_text = self.notebook.tab(idx, "text")
        
        # Ocultar o deshabilitar botón Anular según pestaña
        if "Ventas" in tab_text or "Compras" in tab_text:
            if tiene_permiso(self.usuario, 'cancelar_ventas'):
                self.btn_anular.configure(state="normal", fg_color="#ef4444")
            else:
                self.btn_anular.configure(state="disabled", fg_color="gray")
        else:
            self.btn_anular.configure(state="disabled", fg_color="gray")
        
        if "Ventas" in tab_text: 
            self.pag_ventas = 0
            self.buscar_ventas()
        elif "Compras" in tab_text: 
            self.pag_compras = 0
            self.buscar_compras()
        elif "Pagos" in tab_text: 
            self.pag_pagos = 0
            self.buscar_pagos()
        elif "Caja" in tab_text: 
            self.pag_caja = 0
            self.buscar_caja()

    def _crear_tab_ventas(self):
        # Usar self.bg_ventas como padre en lugar de self.tab_ventas
        frm = ctk.CTkFrame(self.bg_ventas, fg_color="transparent")
        frm.pack(fill="x", padx=10, pady=(2, 5))

        # Asignar peso para que los buscadores absorban espacio restante de forma fluida
        frm.grid_columnconfigure(7, weight=1)
        frm.grid_columnconfigure(9, weight=1)

        # 1. Filtro Rango
        ctk.CTkLabel(frm, text="Rango:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=0, padx=3, sticky="e")
        cb_rango = ctk.CTkOptionMenu(frm, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Este Mes", "Mes Pasado"], 
                                     command=lambda v: self._on_rango_change(v, self.fecha_desde_v, self.fecha_hasta_v),
                                     width=130, fg_color=get_color("bg_pop"), button_color=get_color("bg_pop"))
        cb_rango.set("Personalizado")
        cb_rango.grid(row=0, column=1, padx=3)

        # 2. Fecha Desde
        ctk.CTkLabel(frm, text="Desde:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=2, padx=3, sticky="e")
        self.fecha_desde_v = SelectorFecha(frm)
        self.fecha_desde_v.grid(row=0, column=3, padx=3)
        self.fecha_desde_v.widget_entrada.delete(0, tk.END)
        self.fecha_desde_v.widget_entrada.insert(0, f"01/{date.today().month:02d}/{date.today().year}")

        # 3. Fecha Hasta
        ctk.CTkLabel(frm, text="Hasta:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=4, padx=3, sticky="e")
        self.fecha_hasta_v = SelectorFecha(frm)
        self.fecha_hasta_v.grid(row=0, column=5, padx=3)
        self.fecha_hasta_v.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_v.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        
        cb_rango.bind("<<ComboboxSelected>>", lambda e: _aplicar_filtro_rapido_logic(cb_rango.get(), self.fecha_desde_v.widget_entrada, self.fecha_hasta_v.widget_entrada))

        # 4. Buscador Vendedor (Encapsulado en sub-frame)
        ctk.CTkLabel(frm, text="Vendedor:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=6, padx=(10, 3), sticky="e")
        frm_vendedor = ctk.CTkFrame(frm, fg_color="transparent")
        frm_vendedor.grid(row=0, column=7, padx=3, sticky="w")
        
        es_vendedor = self.usuario.get('id_rol') == 2
        texto_vendedor = self.usuario.get('nombre') if es_vendedor else "(Todos)"
        
        self.lbl_vendedor_v = ctk.CTkLabel(frm_vendedor, text=texto_vendedor, font=("Segoe UI", 12), text_color=get_color("text_secondary"), anchor="w")
        self.lbl_vendedor_v.pack(side="left", padx=(0, 5))
        
        if es_vendedor:
            self.vendedor_sel['id'] = self.usuario.get('id_usuario')
            self.vendedor_sel['nombre'] = texto_vendedor
            btn_vendedor = ctk.CTkButton(frm_vendedor, text="🔍", width=35, height=30, fg_color="gray", state="disabled")
        else:
            btn_vendedor = ctk.CTkButton(frm_vendedor, text="🔍", width=35, height=30, fg_color="#3b82f6", 
                                         command=lambda: self._abrir_selector_entidad("Vendedor", self.vendedor_sel, self.vendedores_raw, self.lbl_vendedor_v))
        btn_vendedor.pack(side="left")

        # 5. Buscador Cliente (Encapsulado en sub-frame)
        ctk.CTkLabel(frm, text="Cliente:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=8, padx=(10, 3), sticky="e")
        frm_cliente = ctk.CTkFrame(frm, fg_color="transparent")
        frm_cliente.grid(row=0, column=9, padx=3, sticky="w")
        
        self.lbl_cliente_v = ctk.CTkLabel(frm_cliente, text="(Todos)", font=("Segoe UI", 12), text_color=get_color("text_secondary"), anchor="w")
        self.lbl_cliente_v.pack(side="left", padx=(0, 5))
        
        btn_cliente = ctk.CTkButton(frm_cliente, text="🔍", width=35, height=30, fg_color="#3b82f6", 
                                   command=lambda: self._abrir_selector_entidad("Cliente", self.cliente_sel, self.clientes_raw, self.lbl_cliente_v))
        btn_cliente.pack(side="left")

        # 6. Botones de Acción (Grupo alineado a la derecha)
        frm_acciones = ctk.CTkFrame(frm, fg_color="transparent")
        frm_acciones.grid(row=0, column=10, padx=(15, 0), sticky="e")
        
        btn_buscar = self.crear_boton_accion(frm_acciones, "🔍 Buscar", self.buscar_ventas, "#3b82f6", width=8)
        btn_buscar.pack(side="left", padx=3)
        
        btn_limpiar = self.crear_boton_accion(frm_acciones, "🧹 Limpiar", self._limpiar_filtros_ventas, "#6b7280", width=8)
        btn_limpiar.pack(side="left", padx=3)
        
        cols = ("ID", "Fecha", "Cliente", "Vendedor", "Total", "Estado", "Pago")
        
        # Frame contenedor para Ventas Maestro + Scrollbar
        frm_maestro_v_cont = ctk.CTkFrame(self.bg_ventas, fg_color="transparent")
        frm_maestro_v_cont.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tree_maestro_v = ttk.Treeview(frm_maestro_v_cont, columns=cols, show="headings", height=5, style="Modern.Treeview") 
        ys_maestro_v = ctk.CTkScrollbar(frm_maestro_v_cont, command=self.tree_maestro_v.yview)
        ys_maestro_v.pack(side="right", fill="y")
        try:
            from app.frontend.componentes_ui import configurar_scrollbar_coherente
            configurar_scrollbar_coherente(ys_maestro_v)
        except ImportError: pass
        
        self.tree_maestro_v.configure(yscrollcommand=ys_maestro_v.set)
        self.tree_maestro_v.pack(side="left", fill="both", expand=True)
        
        for c in cols: self.tree_maestro_v.heading(c, text=c)
        self.tree_maestro_v.column("ID", width=0, stretch=False)
        self.tree_maestro_v.configure(displaycolumns=("Fecha", "Cliente", "Vendedor", "Total", "Estado", "Pago"))
        self.tree_maestro_v.column("Total", anchor="e") 
        self.tree_maestro_v.bind("<<TreeviewSelect>>", self.mostrar_detalle_venta)

        # Controles de paginación Ventas
        frm_pag_v = ctk.CTkFrame(self.bg_ventas, fg_color="transparent")
        frm_pag_v.pack(fill="x", padx=10, pady=(0, 5))
        
        btn_prev_v = ctk.CTkButton(frm_pag_v, text="Anterior", width=80, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), command=self._prev_page_ventas)
        btn_prev_v.pack(side="left", padx=5)
        
        self.lbl_pag_ventas = ctk.CTkLabel(frm_pag_v, text="Página 1", font=("Segoe UI", 12))
        self.lbl_pag_ventas.pack(side="left", padx=10)
        
        btn_next_v = ctk.CTkButton(frm_pag_v, text="Siguiente", width=80, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), command=self._next_page_ventas)
        btn_next_v.pack(side="left", padx=5)

        cols_d = ("Prod", "Código", "Cant", "P. Unit", "Subtotal")
        
        # Frame contenedor para Ventas Detalle + Scrollbar
        frm_detalle_v_cont = ctk.CTkFrame(self.bg_ventas, fg_color="transparent")
        frm_detalle_v_cont.pack(fill="both", expand=True, padx=10, pady=(0,10))
        
        self.tree_detalle_v = ttk.Treeview(frm_detalle_v_cont, columns=cols_d, show="headings", height=8, style="Modern.Treeview") 
        ys_detalle_v = ctk.CTkScrollbar(frm_detalle_v_cont, command=self.tree_detalle_v.yview)
        ys_detalle_v.pack(side="right", fill="y")
        try:
            configurar_scrollbar_coherente(ys_detalle_v)
        except: pass
        
        self.tree_detalle_v.configure(yscrollcommand=ys_detalle_v.set)
        self.tree_detalle_v.pack(side="left", fill="both", expand=True)
        
        for c in cols_d: self.tree_detalle_v.heading(c, text=c)
        self.tree_detalle_v.column("P. Unit", anchor="e")
        self.tree_detalle_v.column("Subtotal", anchor="e")

    def anular_venta_ui(self):
        sel = self.tree_maestro_v.selection()
        if not sel:
            messagebox.showwarning("Atención", "Por favor, seleccione la venta que desea anular.", parent=self.win)
            return

        vals = self.tree_maestro_v.item(sel[0], "values")
        if not vals or vals[0] == "Aviso":
            return

        id_venta = int(vals[0])
        estado = vals[5]
        total = vals[4]

        if estado == "cancelada":
            messagebox.showwarning("Atención", "Esta venta ya se encuentra anulada/cancelada.", parent=self.win)
            return

        # --- Diálogo de motivo + confirmación ---
        motivo_resultado = {"valor": None, "confirmado": False}

        dlg = ctk.CTkToplevel(self.win)
        preparar_ventana(dlg)
        dlg.title("Confirmar Anulación de Venta")
        dlg.geometry("520x330")
        dlg.grab_set()
        dlg.transient(self.win)

        # Encabezado
        frm_header_dlg = ctk.CTkFrame(dlg, fg_color="#ef4444", corner_radius=0)
        frm_header_dlg.pack(fill="x")
        ctk.CTkLabel(
            frm_header_dlg,
            text="⚠️  ANULAR VENTA  ⚠️",
            font=("Segoe UI", 16, "bold"),
            text_color="white"
        ).pack(pady=12)

        # Cuerpo
        frm_body = ctk.CTkFrame(dlg, fg_color="transparent")
        frm_body.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(
            frm_body,
            text=f"Venta #{id_venta}  ·  Total: {total}",
            font=("Segoe UI", 13, "bold"),
            text_color=get_color("text_primary")
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            frm_body,
            text="Esta acción restituirá el stock y revertirá el saldo en cuenta corriente\n"
                 "si el pago fue en esa modalidad. La operación es IRREVERSIBLE.",
            font=("Segoe UI", 11),
            text_color=get_color("text_secondary"),
            justify="left",
            wraplength=460
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            frm_body,
            text="Motivo de anulación (obligatorio):",
            font=("Segoe UI", 12, "bold"),
            text_color=get_color("text_primary")
        ).pack(anchor="w")

        entry_motivo = ctk.CTkEntry(
            frm_body,
            font=("Segoe UI", 12),
            height=36,
            placeholder_text="Ej: Error de carga, doble cobro, pedido cliente..."
        )
        entry_motivo.pack(fill="x", pady=(4, 0))

        # Botones
        frm_btns = ctk.CTkFrame(dlg, fg_color="transparent")
        frm_btns.pack(fill="x", padx=20, pady=(0, 15))

        def _confirmar():
            motivo_texto = entry_motivo.get().strip()
            if not motivo_texto:
                entry_motivo.configure(border_color="#ef4444")
                entry_motivo.focus_set()
                return
            motivo_resultado["valor"] = motivo_texto
            motivo_resultado["confirmado"] = True
            dlg.destroy()

        def _cancelar():
            dlg.destroy()

        ctk.CTkButton(
            frm_btns, text="Cancelar", command=_cancelar,
            fg_color=get_color("button_secondary"),
            hover_color=get_color("button_secondary_hover"),
            font=("Segoe UI", 13, "bold"), width=150, height=38
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            frm_btns, text="✓ Confirmar Anulación", command=_confirmar,
            fg_color="#ef4444", hover_color="#dc2626",
            font=("Segoe UI", 13, "bold"), width=200, height=38
        ).pack(side="right")

        entry_motivo.after(150, entry_motivo.focus_set)
        dlg.bind("<Return>", lambda e: _confirmar())
        dlg.bind("<Escape>", lambda e: _cancelar())

        centrar_y_mostrar_ventana(dlg)
        self.win.wait_window(dlg)

        if not motivo_resultado["confirmado"]:
            return

        # --- Ejecutar anulación ---
        try:
            exito = self.backend.anular_venta(
                id_venta,
                self.usuario['id_usuario'],
                motivo_resultado["valor"]
            )
            if exito:
                messagebox.showinfo(
                    "Éxito",
                    f"La Venta #{id_venta} ha sido anulada correctamente.\n"
                    "El stock fue restituido y la cuenta corriente fue revertida si correspondía.",
                    parent=self.win
                )
                self.buscar_ventas()
        except ValueError as ve:
            messagebox.showwarning("No se pudo anular", str(ve), parent=self.win)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo anular la venta:\n{e}", parent=self.win)



    def _clampear_fecha(self, fecha_sql: str | None) -> str | None:
        """Si hay fecha_minima activa y la fecha es anterior, devuelve la mínima permitida."""
        if fecha_sql is None or self._fecha_minima is None:
            return fecha_sql
        try:
            f = date.fromisoformat(fecha_sql)
            if f < self._fecha_minima:
                return self._fecha_minima.isoformat()
        except Exception:
            pass
        return fecha_sql

    def buscar_ventas(self):
        # 1. Limpiar UI
        if not self.win.winfo_exists():
            return
        for i in self.tree_maestro_v.get_children(): self.tree_maestro_v.delete(i)
        for i in self.tree_detalle_v.get_children(): self.tree_detalle_v.delete(i)
        
        # 2. Hilo para busqueda larga
        def _fetch():
            try:
                d_sql = self._clampear_fecha(self.fecha_desde_v.get_date_sql())
                h_sql = self.fecha_hasta_v.get_date_sql()
                es_vendedor = self.usuario.get('id_rol') == 2
                id_vend = self.usuario.get('id_usuario') if es_vendedor else self.vendedor_sel['id']
                id_cli = self.cliente_sel['id']
                
                limit = self.pag_size
                offset = self.pag_ventas * self.pag_size
                self.total_ventas = self.backend.contar_ventas_maestro(d_sql, h_sql, id_cli, id_vend)
                ventas = self.backend.obtener_ventas_maestro(d_sql, h_sql, id_cli, id_vend, limit=limit, offset=offset)
                
                # 3. Actualizar UI en hilo principal
                if self.win.winfo_exists():
                    self.win.after(0, lambda: self._update_tree_ventas(ventas))
            except Exception as e:
                if self.win.winfo_exists():
                    self.win.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def _update_tree_ventas(self, ventas):
        if not self.win.winfo_exists():
            return
        try:
            for v in ventas:
                self.tree_maestro_v.insert("", tk.END, values=[
                    v.get('id_venta'), _formatear_fecha_para_ui(v.get('fecha')),
                    v.get('cliente') or "Consumidor Final", v.get('vendedor'),
                    _fmt_mon(v.get('total')), v.get('estado'), v.get('tipo_pago')
                ])
            if hasattr(self, 'lbl_pag_ventas'):
                tot_pages = max(1, (self.total_ventas + self.pag_size - 1) // self.pag_size)
                self.lbl_pag_ventas.configure(text=f"Página {self.pag_ventas + 1} de {tot_pages} ({self.total_ventas} registros)")
        except Exception as e:
            logger.error(f"Error en update_tree_ventas: {e}")
        except tk.TclError:
            pass

    def _prev_page_ventas(self):
        if self.pag_ventas > 0:
            self.pag_ventas -= 1
            self.buscar_ventas()
            
    def _next_page_ventas(self):
        tot_pages = max(1, (self.total_ventas + self.pag_size - 1) // self.pag_size)
        if self.pag_ventas < tot_pages - 1:
            self.pag_ventas += 1
            self.buscar_ventas()

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

    def _limpiar_filtros_ventas(self):
        hoy = date.today()
        self.fecha_desde_v.widget_entrada.delete(0, tk.END)
        self.fecha_desde_v.widget_entrada.insert(0, f"01/{hoy.month:02d}/{hoy.year}")
        self.fecha_hasta_v.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_v.widget_entrada.insert(0, hoy.strftime("%d/%m/%Y"))
        
        es_vendedor = self.usuario.get('id_rol') == 2
        if not es_vendedor:
            self.vendedor_sel['id'] = None
            self.vendedor_sel['nombre'] = "(Todos)"
            if hasattr(self, 'lbl_vendedor_v'):
                self.lbl_vendedor_v.configure(text="(Todos)")
                
        self.cliente_sel['id'] = None
        self.cliente_sel['nombre'] = "(Todos)"
        if hasattr(self, 'lbl_cliente_v'):
            self.lbl_cliente_v.configure(text="(Todos)")
            
        self.buscar_ventas()

    def mostrar_detalle_compra(self, event=None):
        for i in self.tree_detalle_c.get_children(): self.tree_detalle_c.delete(i)
        sel = self.tree_maestro_c.selection()
        if not sel: return
        id_c = self.tree_maestro_c.item(sel[0], "values")[0]
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
        except Exception: pass


    def _crear_tab_compras(self):
        frm = ctk.CTkFrame(self.bg_compras, fg_color="transparent")
        frm.pack(fill="x", padx=10, pady=(2, 5))

        # Asignar peso para que los buscadores absorban espacio restante de forma fluida
        frm.grid_columnconfigure(7, weight=1)
        frm.grid_columnconfigure(9, weight=1)

        # 1. Filtro Rango
        ctk.CTkLabel(frm, text="Rango:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=0, padx=3, sticky="e")
        cb_rango = ctk.CTkOptionMenu(frm, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Este Mes", "Mes Pasado"], 
                                     command=lambda v: self._on_rango_change(v, self.fecha_desde_c, self.fecha_hasta_c),
                                     width=130, fg_color=get_color("bg_pop"), button_color=get_color("bg_pop"))
        cb_rango.set("Personalizado")
        cb_rango.grid(row=0, column=1, padx=3)

        # 2. Fecha Desde
        ctk.CTkLabel(frm, text="Desde:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=2, padx=3, sticky="e")
        self.fecha_desde_c = SelectorFecha(frm)
        self.fecha_desde_c.grid(row=0, column=3, padx=3)
        self.fecha_desde_c.widget_entrada.delete(0, tk.END)
        self.fecha_desde_c.widget_entrada.insert(0, f"01/{date.today().month:02d}/{date.today().year}")

        # 3. Fecha Hasta
        ctk.CTkLabel(frm, text="Hasta:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=4, padx=3, sticky="e")
        self.fecha_hasta_c = SelectorFecha(frm)
        self.fecha_hasta_c.grid(row=0, column=5, padx=3)
        self.fecha_hasta_c.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_c.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))

        # 4. Buscador Proveedor (Encapsulado en sub-frame)
        ctk.CTkLabel(frm, text="Proveedor:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=6, padx=(10, 3), sticky="e")
        frm_proveedor = ctk.CTkFrame(frm, fg_color="transparent")
        frm_proveedor.grid(row=0, column=7, padx=3, sticky="w")
        
        self.lbl_proveedor_c = ctk.CTkLabel(frm_proveedor, text="(Todos)", font=("Segoe UI", 12), text_color=get_color("text_secondary"), anchor="w")
        self.lbl_proveedor_c.pack(side="left", padx=(0, 5))
        
        btn_proveedor = ctk.CTkButton(frm_proveedor, text="🔍", width=35, height=30, fg_color="#3b82f6", 
                                      command=lambda: self._abrir_selector_entidad("Proveedor", self.proveedor_sel, self.proveedores_raw, self.lbl_proveedor_c))
        btn_proveedor.pack(side="left")

        # 5. Buscador Vendedor (Encapsulado en sub-frame)
        ctk.CTkLabel(frm, text="Vendedor:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=8, padx=(10, 3), sticky="e")
        frm_usuario_c = ctk.CTkFrame(frm, fg_color="transparent")
        frm_usuario_c.grid(row=0, column=9, padx=3, sticky="w")
        
        es_vendedor = self.usuario.get('id_rol') == 2
        texto_usuario_c = self.usuario.get('nombre') if es_vendedor else "(Todos)"
        
        self.lbl_usuario_c = ctk.CTkLabel(frm_usuario_c, text=texto_usuario_c, font=("Segoe UI", 12), text_color=get_color("text_secondary"), anchor="w")
        self.lbl_usuario_c.pack(side="left", padx=(0, 5))
        
        if es_vendedor:
            self.usuario_c_sel['id'] = self.usuario.get('id_usuario')
            self.usuario_c_sel['nombre'] = texto_usuario_c
            btn_usuario = ctk.CTkButton(frm_usuario_c, text="🔍", width=35, height=30, fg_color="gray", state="disabled")
        else:
            btn_usuario = ctk.CTkButton(frm_usuario_c, text="🔍", width=35, height=30, fg_color="#3b82f6", 
                                        command=lambda: self._abrir_selector_entidad("Vendedor", self.usuario_c_sel, self.vendedores_raw, self.lbl_usuario_c))
        btn_usuario.pack(side="left")

        # 6. Botones de Acción (Grupo alineado a la derecha)
        frm_acciones = ctk.CTkFrame(frm, fg_color="transparent")
        frm_acciones.grid(row=0, column=10, padx=(15, 0), sticky="e")
        
        btn_buscar = self.crear_boton_accion(frm_acciones, "🔍 Buscar", self.buscar_compras, "#3b82f6", width=8)
        btn_buscar.pack(side="left", padx=3)
        
        btn_limpiar = self.crear_boton_accion(frm_acciones, "🧹 Limpiar", self._limpiar_filtros_compras, "#6b7280", width=8)
        btn_limpiar.pack(side="left", padx=3)

        cols = ("ID", "Fecha", "Empresa", "CUIT", "Total", "Estado", "Pago", "Vendedor")
        
        # Frame contenedor para Compras Maestro + Scrollbar
        frm_maestro_c_cont = ctk.CTkFrame(self.bg_compras, fg_color="transparent")
        frm_maestro_c_cont.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tree_maestro_c = ttk.Treeview(frm_maestro_c_cont, columns=cols, show="headings", height=5, style="Modern.Treeview")
        ys_maestro_c = ctk.CTkScrollbar(frm_maestro_c_cont, command=self.tree_maestro_c.yview)
        ys_maestro_c.pack(side="right", fill="y")
        try:
            from app.frontend.componentes_ui import configurar_scrollbar_coherente
            configurar_scrollbar_coherente(ys_maestro_c)
        except: pass
        
        self.tree_maestro_c.configure(yscrollcommand=ys_maestro_c.set)
        self.tree_maestro_c.pack(side="left", fill="both", expand=True)
        
        for c in cols: self.tree_maestro_c.heading(c, text=c)
        self.tree_maestro_c.column("ID", width=0, stretch=False)
        self.tree_maestro_c.configure(displaycolumns=("Fecha", "Empresa", "CUIT", "Total", "Estado", "Pago", "Vendedor"))
        self.tree_maestro_c.column("Total", anchor="e")
        self.tree_maestro_c.column("Estado", width=100, anchor="center")
        self.tree_maestro_c.column("Pago", width=100, anchor="center")
        self.tree_maestro_c.column("Empresa", width=160)
        self.tree_maestro_c.column("CUIT", width=110, anchor="center")
        self.tree_maestro_c.bind("<<TreeviewSelect>>", self.mostrar_detalle_compra)

        # Controles de paginación Compras
        frm_pag_c = ctk.CTkFrame(self.bg_compras, fg_color="transparent")
        frm_pag_c.pack(fill="x", padx=10, pady=(0, 5))
        
        btn_prev_c = ctk.CTkButton(frm_pag_c, text="Anterior", width=80, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), command=self._prev_page_compras)
        btn_prev_c.pack(side="left", padx=5)
        
        self.lbl_pag_compras = ctk.CTkLabel(frm_pag_c, text="Página 1", font=("Segoe UI", 12))
        self.lbl_pag_compras.pack(side="left", padx=10)
        
        btn_next_c = ctk.CTkButton(frm_pag_c, text="Siguiente", width=80, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), command=self._next_page_compras)
        btn_next_c.pack(side="left", padx=5)

        cols_d = ("Prod", "Código", "Cant", "Costo", "Precio Venta Asignado", "Subtotal")
        
        # Frame contenedor para Compras Detalle + Scrollbar
        frm_detalle_c_cont = ctk.CTkFrame(self.bg_compras, fg_color="transparent")
        frm_detalle_c_cont.pack(fill="both", expand=True, padx=10, pady=(0,10))
        
        self.tree_detalle_c = ttk.Treeview(frm_detalle_c_cont, columns=cols_d, show="headings", height=8, style="Modern.Treeview")
        ys_detalle_c = ctk.CTkScrollbar(frm_detalle_c_cont, command=self.tree_detalle_c.yview)
        ys_detalle_c.pack(side="right", fill="y")
        try:
            configurar_scrollbar_coherente(ys_detalle_c)
        except: pass
        
        self.tree_detalle_c.configure(yscrollcommand=ys_detalle_c.set)
        self.tree_detalle_c.pack(side="left", fill="both", expand=True)
        
        for c in cols_d: self.tree_detalle_c.heading(c, text=c)
        self.tree_detalle_c.column("Costo", anchor="e", width=100)
        self.tree_detalle_c.column("Precio Venta Asignado", anchor="e", width=100)
        self.tree_detalle_c.column("Subtotal", anchor="e", width=100)

    def buscar_compras(self):
        # 1. Limpiar UI
        if not self.win.winfo_exists():
            return
        for i in self.tree_maestro_c.get_children(): self.tree_maestro_c.delete(i)
        for i in self.tree_detalle_c.get_children(): self.tree_detalle_c.delete(i)
        
        # 2. Hilo para busqueda
        def _fetch():
            try:
                d_sql = self._clampear_fecha(self.fecha_desde_c.get_date_sql())
                h_sql = self.fecha_hasta_c.get_date_sql()
                id_prov_filtro = self.proveedor_sel['id']
                
                limit = self.pag_size
                offset = self.pag_compras * self.pag_size
                self.total_compras = self.backend.contar_compras_maestro(d_sql, h_sql, id_prov_filtro)
                compras = self.backend.obtener_compras_maestro(d_sql, h_sql, id_prov_filtro, limit=limit, offset=offset)
                
                es_vendedor = self.usuario.get('id_rol') == 2
                nombre_usuario_sel = self.usuario.get('nombre') if es_vendedor else self.usuario_c_sel['nombre']
                if nombre_usuario_sel != "(Todos)":
                    compras = [c for c in compras if c.get('usuario') == nombre_usuario_sel]
                    
                # 3. Actualizar UI
                if self.win.winfo_exists():
                    self.win.after(0, lambda: self._update_tree_compras(compras))
            except Exception as e:
                if self.win.winfo_exists():
                    self.win.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def _update_tree_compras(self, compras):
        if not self.win.winfo_exists():
            return
        try:
            prov_map = self.proveedores_map_nombre
            for c in compras:
                medio = c.get('medio_pago') or '-'
                prov_data = prov_map.get(c.get('proveedor'), {})
                cuit_val = prov_data.get('cuit', '-')
                empresa_val = prov_data.get('empresa') or c.get('proveedor') or '-'
                self.tree_maestro_c.insert("", tk.END, values=[
                    c.get('id_compra'), _formatear_fecha_para_ui(c.get('fecha')),
                    empresa_val, cuit_val, _fmt_mon(c.get('total')),
                    c.get('estado'), medio, c.get('usuario')
                ])
            if hasattr(self, 'lbl_pag_compras'):
                tot_pages = max(1, (self.total_compras + self.pag_size - 1) // self.pag_size)
                self.lbl_pag_compras.configure(text=f"Página {self.pag_compras + 1} de {tot_pages} ({self.total_compras} registros)")
        except Exception as e:
            logger.error(f"Error update_tree_compras: {e}")
        except tk.TclError:
            pass

    def _prev_page_compras(self):
        if self.pag_compras > 0:
            self.pag_compras -= 1
            self.buscar_compras()
            
    def _next_page_compras(self):
        tot_pages = max(1, (self.total_compras + self.pag_size - 1) // self.pag_size)
        if self.pag_compras < tot_pages - 1:
            self.pag_compras += 1
            self.buscar_compras()

    def _limpiar_filtros_compras(self):
        hoy = date.today()
        self.fecha_desde_c.widget_entrada.delete(0, tk.END)
        self.fecha_desde_c.widget_entrada.insert(0, f"01/{hoy.month:02d}/{hoy.year}")
        self.fecha_hasta_c.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_c.widget_entrada.insert(0, hoy.strftime("%d/%m/%Y"))
        
        self.proveedor_sel['id'] = None
        self.proveedor_sel['nombre'] = "(Todos)"
        if hasattr(self, 'lbl_proveedor_c'):
            self.lbl_proveedor_c.configure(text="(Todos)")
            
        es_vendedor = self.usuario.get('id_rol') == 2
        if not es_vendedor:
            self.usuario_c_sel['id'] = None
            self.usuario_c_sel['nombre'] = "(Todos)"
            if hasattr(self, 'lbl_usuario_c'):
                self.lbl_usuario_c.configure(text="(Todos)")
                
        self.buscar_compras()

    def _crear_tab_pagos(self):
        frm = ctk.CTkFrame(self.bg_pagos, fg_color="transparent")
        frm.pack(fill="x", padx=10, pady=(2, 5))

        # Asignar peso para que los buscadores absorban espacio restante de forma fluida
        frm.grid_columnconfigure(7, weight=1)
        frm.grid_columnconfigure(9, weight=1)

        # 1. Filtro Rango
        ctk.CTkLabel(frm, text="Rango:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=0, padx=3, sticky="e")
        cb_rango = ctk.CTkOptionMenu(frm, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Este Mes", "Mes Pasado"], 
                                     command=lambda v: self._on_rango_change(v, self.fecha_desde_p, self.fecha_hasta_p),
                                     width=130, fg_color=get_color("bg_pop"), button_color=get_color("bg_pop"))
        cb_rango.set("Personalizado")
        cb_rango.grid(row=0, column=1, padx=3)

        # 2. Fecha Desde
        ctk.CTkLabel(frm, text="Desde:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=2, padx=3, sticky="e")
        self.fecha_desde_p = SelectorFecha(frm)
        self.fecha_desde_p.grid(row=0, column=3, padx=3)
        self.fecha_desde_p.widget_entrada.delete(0, tk.END)
        self.fecha_desde_p.widget_entrada.insert(0, f"01/{date.today().month:02d}/{date.today().year}")

        # 3. Fecha Hasta
        ctk.CTkLabel(frm, text="Hasta:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=4, padx=3, sticky="e")
        self.fecha_hasta_p = SelectorFecha(frm)
        self.fecha_hasta_p.grid(row=0, column=5, padx=3)
        self.fecha_hasta_p.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_p.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))

        # 4. Buscador Cliente (Encapsulado en sub-frame)
        ctk.CTkLabel(frm, text="Cliente:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=6, padx=(10, 3), sticky="e")
        frm_cliente_p = ctk.CTkFrame(frm, fg_color="transparent")
        frm_cliente_p.grid(row=0, column=7, padx=3, sticky="w")
        
        self.lbl_cliente_p = ctk.CTkLabel(frm_cliente_p, text="(Todos)", font=("Segoe UI", 12), text_color=get_color("text_secondary"), anchor="w")
        self.lbl_cliente_p.pack(side="left", padx=(0, 5))
        
        btn_cliente = ctk.CTkButton(frm_cliente_p, text="🔍", width=35, height=30, fg_color="#3b82f6", 
                                    command=lambda: self._abrir_selector_entidad("Cliente", self.cliente_p_sel, self.clientes_raw, self.lbl_cliente_p))
        btn_cliente.pack(side="left")

        # 5. Buscador Usuario (Encapsulado en sub-frame)
        ctk.CTkLabel(frm, text="Usuario:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=8, padx=(10, 3), sticky="e")
        frm_usuario_p = ctk.CTkFrame(frm, fg_color="transparent")
        frm_usuario_p.grid(row=0, column=9, padx=3, sticky="w")
        
        self.lbl_usuario_p = ctk.CTkLabel(frm_usuario_p, text="(Todos)", font=("Segoe UI", 12), text_color=get_color("text_secondary"), anchor="w")
        self.lbl_usuario_p.pack(side="left", padx=(0, 5))
        
        btn_usuario = ctk.CTkButton(frm_usuario_p, text="🔍", width=35, height=30, fg_color="#3b82f6", 
                                    command=lambda: self._abrir_selector_entidad("Usuario", self.usuario_p_sel, self.vendedores_raw, self.lbl_usuario_p))
        btn_usuario.pack(side="left")

        # 6. Botones de Acción (Grupo alineado a la derecha)
        frm_acciones = ctk.CTkFrame(frm, fg_color="transparent")
        frm_acciones.grid(row=0, column=10, padx=(15, 0), sticky="e")
        
        btn_buscar = self.crear_boton_accion(frm_acciones, "🔍 Buscar", self.buscar_pagos, "#3b82f6", width=8)
        btn_buscar.pack(side="left", padx=3)
        
        btn_limpiar = self.crear_boton_accion(frm_acciones, "🧹 Limpiar", self._limpiar_filtros_pagos, "#6b7280", width=8)
        btn_limpiar.pack(side="left", padx=3)

        cols = ("Fecha", "Cliente", "Monto", "Método", "Usuario")
        
        # Frame contenedor para Pagos + Scrollbar
        frm_pagos_cont = ctk.CTkFrame(self.bg_pagos, fg_color="transparent")
        frm_pagos_cont.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tree_pagos = ttk.Treeview(frm_pagos_cont, columns=cols, show="headings", height=15, style="Modern.Treeview")
        ys_pagos = ctk.CTkScrollbar(frm_pagos_cont, command=self.tree_pagos.yview)
        ys_pagos.pack(side="right", fill="y")
        try:
            from app.frontend.componentes_ui import configurar_scrollbar_coherente
            configurar_scrollbar_coherente(ys_pagos)
        except: pass
        
        self.tree_pagos.configure(yscrollcommand=ys_pagos.set)
        self.tree_pagos.pack(side="left", fill="both", expand=True)
        
        for c in cols: self.tree_pagos.heading(c, text=c)
        self.tree_pagos.column("Fecha", width=150, anchor="center")
        self.tree_pagos.column("Cliente", width=300, anchor="w")
        self.tree_pagos.column("Monto", anchor="e", width=120)
        self.tree_pagos.column("Método", width=150, anchor="center")
        self.tree_pagos.column("Usuario", width=150, anchor="center")

        # Controles de paginación Pagos
        frm_pag_p = ctk.CTkFrame(self.bg_pagos, fg_color="transparent")
        frm_pag_p.pack(fill="x", padx=10, pady=(0, 5))
        
        btn_prev_p = ctk.CTkButton(frm_pag_p, text="Anterior", width=80, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), command=self._prev_page_pagos)
        btn_prev_p.pack(side="left", padx=5)
        
        self.lbl_pag_pagos = ctk.CTkLabel(frm_pag_p, text="Página 1", font=("Segoe UI", 12))
        self.lbl_pag_pagos.pack(side="left", padx=10)
        
        btn_next_p = ctk.CTkButton(frm_pag_p, text="Siguiente", width=80, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), command=self._next_page_pagos)
        btn_next_p.pack(side="left", padx=5)

    def buscar_pagos(self):
        # 1. Limpiar UI
        if not self.win.winfo_exists():
            return
        for i in self.tree_pagos.get_children(): self.tree_pagos.delete(i)
        
        # 2. Hilo para busqueda
        def _fetch():
            try:
                d_sql = self._clampear_fecha(self.fecha_desde_p.get_date_sql())
                h_sql = self.fecha_hasta_p.get_date_sql()
                id_cli = self.cliente_p_sel['id']
                id_usuario = self.usuario_p_sel['id']
                
                if hasattr(self, 'filtro_cliente_id') and self.filtro_cliente_id:
                    id_cli = self.filtro_cliente_id
                    self.filtro_cliente_id = None
                
                limit = self.pag_size
                offset = self.pag_pagos * self.pag_size
                self.total_pagos = self.backend.contar_pagos_maestro(d_sql, h_sql, id_cli, id_usuario)
                pagos = self.backend.obtener_pagos_maestro(d_sql, h_sql, id_cli, id_usuario, limit=limit, offset=offset)
                
                # 3. Actualizar UI
                if self.win.winfo_exists():
                    self.win.after(0, lambda: self._update_tree_pagos(pagos))
            except Exception as e:
                if self.win.winfo_exists():
                    self.win.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        import threading
        threading.Thread(target=_fetch, daemon=True).start()


    def _update_tree_pagos(self, pagos):
        if not self.win.winfo_exists():
            return
        try:
            for p in pagos:
                self.tree_pagos.insert("", tk.END, values=[
                    _formatear_fecha_para_ui(p.get('fecha')),
                    p.get('cliente_nombre'), _fmt_mon(p.get('monto')),
                    p.get('metodo'), p.get('usuario_nombre')
                ])
            if hasattr(self, 'lbl_pag_pagos'):
                tot_pages = max(1, (self.total_pagos + self.pag_size - 1) // self.pag_size)
                self.lbl_pag_pagos.configure(text=f"Página {self.pag_pagos + 1} de {tot_pages} ({self.total_pagos} registros)")
        except tk.TclError:
            pass

    def _prev_page_pagos(self):
        if self.pag_pagos > 0:
            self.pag_pagos -= 1
            self.buscar_pagos()
            
    def _next_page_pagos(self):
        tot_pages = max(1, (self.total_pagos + self.pag_size - 1) // self.pag_size)
        if self.pag_pagos < tot_pages - 1:
            self.pag_pagos += 1
            self.buscar_pagos()

    def _limpiar_filtros_pagos(self):
        hoy = date.today()
        self.fecha_desde_p.widget_entrada.delete(0, tk.END)
        self.fecha_desde_p.widget_entrada.insert(0, f"01/{hoy.month:02d}/{hoy.year}")
        self.fecha_hasta_p.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_p.widget_entrada.insert(0, hoy.strftime("%d/%m/%Y"))
        
        self.cliente_p_sel['id'] = None
        self.cliente_p_sel['nombre'] = "(Todos)"
        if hasattr(self, 'lbl_cliente_p'):
            self.lbl_cliente_p.configure(text="(Todos)")
            
        self.usuario_p_sel['id'] = None
        self.usuario_p_sel['nombre'] = "(Todos)"
        if hasattr(self, 'lbl_usuario_p'):
            self.lbl_usuario_p.configure(text="(Todos)")
            
        self.buscar_pagos()

    def _crear_tab_caja(self):
        frm = ctk.CTkFrame(self.bg_caja, fg_color="transparent")
        frm.pack(fill="x", padx=10, pady=(2, 5))
        
        # Asignar peso para que los OptionMenus absorban espacio restante de forma fluida
        frm.grid_columnconfigure(7, weight=1)
        frm.grid_columnconfigure(9, weight=1)

        # 1. Filtro Rango
        ctk.CTkLabel(frm, text="Rango:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=0, padx=3, sticky="e")
        cb_rango = ctk.CTkOptionMenu(frm, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Este Mes", "Mes Pasado"], 
                                     command=lambda v: self._on_rango_change(v, self.fecha_desde_cj, self.fecha_hasta_cj),
                                     width=130, fg_color=get_color("bg_pop"), button_color=get_color("bg_pop"))
        cb_rango.set("Personalizado")
        cb_rango.grid(row=0, column=1, padx=3)

        # 2. Fecha Desde
        ctk.CTkLabel(frm, text="Desde:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=2, padx=3, sticky="e")
        self.fecha_desde_cj = SelectorFecha(frm)
        self.fecha_desde_cj.grid(row=0, column=3, padx=3)
        self.fecha_desde_cj.widget_entrada.delete(0, tk.END)
        self.fecha_desde_cj.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))

        # 3. Fecha Hasta
        ctk.CTkLabel(frm, text="Hasta:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=4, padx=3, sticky="e")
        self.fecha_hasta_cj = SelectorFecha(frm)
        self.fecha_hasta_cj.grid(row=0, column=5, padx=3)
        self.fecha_hasta_cj.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_cj.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        
        cb_rango.bind("<<ComboboxSelected>>", lambda e: _aplicar_filtro_rapido_logic(cb_rango.get(), self.fecha_desde_cj.widget_entrada, self.fecha_hasta_cj.widget_entrada))
        
        # Definir diccionario de filtros de caja
        self.opciones_filtro_caja = {
            "(Todo)": (None, None),
            "🛒 Ventas": ('ingreso', "venta"),
            "💰 Cobros Cta. Cte.": ('ingreso', "cobro_cta_cte"),
            "📦 Compras": ('egreso', "compra_efectivo"),
            "📦 Compras Cta. Cte.": ('egreso', "compra_cuenta_corriente"),
            "🚚 Pagos a Prov.": ('egreso', "pago_proveedor"),
            "🟢 Aperturas": (None, "apertura_caja"),
            "🔒 Cierres": (None, "cierre_caja"),
            "🔻 Retiros/Ajustes": ('egreso', ["retiro_caja", "ajuste_negativo"]),
            "💸 Gastos Varios": ('egreso', "gasto_vario")
        }

        # 4. Selector Filtro Rápido (Mostrar)
        ctk.CTkLabel(frm, text="Mostrar:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=6, padx=(10, 3), sticky="e")
        self.cb_filtro_rapido_cj = ctk.CTkOptionMenu(frm, values=list(self.opciones_filtro_caja.keys()), width=180,
                                                    fg_color=get_color("bg_pop"), button_color=get_color("bg_pop"))
        self.cb_filtro_rapido_cj.set("(Todo)")
        self.cb_filtro_rapido_cj.grid(row=0, column=7, padx=3, sticky="ew")

        # 4.5. Selector Tipo de Caja
        ctk.CTkLabel(frm, text="Caja:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=8, padx=(10, 3), sticky="e")
        self.cb_tipo_caja = ctk.CTkOptionMenu(frm, values=["Ambas", "Cajas de turno", "Tesorería"], width=130,
                                              fg_color=get_color("bg_pop"), button_color=get_color("bg_pop"))
        self.cb_tipo_caja.set("Ambas")
        self.cb_tipo_caja.grid(row=0, column=9, padx=3, sticky="ew")

        # 5. Selector Usuario (Refactored to Advanced Search with Lupa for consistency)
        ctk.CTkLabel(frm, text="Usuario:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=10, padx=(10, 3), sticky="e")
        frm_usuario_cj = ctk.CTkFrame(frm, fg_color="transparent")
        frm_usuario_cj.grid(row=0, column=11, padx=3, sticky="w")
        
        es_vendedor = self.usuario.get('id_rol') == 2
        texto_usuario_cj = self.usuario.get('nombre') if es_vendedor else "(Todos)"
        
        self.lbl_usuario_cj = ctk.CTkLabel(frm_usuario_cj, text=texto_usuario_cj, font=("Segoe UI", 12), text_color=get_color("text_secondary"), anchor="w")
        self.lbl_usuario_cj.pack(side="left", padx=(0, 5))
        
        if es_vendedor:
            self.usuario_caja_sel['id'] = self.usuario.get('id_usuario')
            self.usuario_caja_sel['nombre'] = texto_usuario_cj
            self.btn_usuario_cj = ctk.CTkButton(frm_usuario_cj, text="🔍", width=35, height=30, fg_color="gray", state="disabled")
        else:
            self.btn_usuario_cj = ctk.CTkButton(frm_usuario_cj, text="🔍", width=35, height=30, fg_color="#3b82f6", 
                                                command=lambda: self._abrir_selector_entidad("Usuario", self.usuario_caja_sel, self.vendedores_raw, self.lbl_usuario_cj))
        self.btn_usuario_cj.pack(side="left")
        
        # 6. Botones de Acción
        frm_acciones = ctk.CTkFrame(frm, fg_color="transparent")
        frm_acciones.grid(row=0, column=12, padx=(15, 0), sticky="e")
        
        btn_buscar = self.crear_boton_accion(frm_acciones, "🔍 Buscar", self.buscar_caja, "#3b82f6", width=8)
        btn_buscar.pack(side="left", padx=3)
        
        btn_limpiar = self.crear_boton_accion(frm_acciones, "🧹 Limpiar", self._limpiar_filtros_caja, "#6b7280", width=8)
        btn_limpiar.pack(side="left", padx=3)
        
        cols = ("Fecha", "Usuario", "Tipo", "Motivo", "Monto", "Descripción")
        
        # Frame contenedor para Caja + Scrollbar
        frm_caja_cont = ctk.CTkFrame(self.bg_caja, fg_color="transparent")
        frm_caja_cont.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree_caja = ttk.Treeview(frm_caja_cont, columns=cols, show="headings", height=10, style="Modern.Treeview")
        ys_caja = ctk.CTkScrollbar(frm_caja_cont, command=self.tree_caja.yview)
        ys_caja.pack(side="right", fill="y")
        try:
            from app.frontend.componentes_ui import configurar_scrollbar_coherente
            configurar_scrollbar_coherente(ys_caja)
        except: pass
        
        self.tree_caja.configure(yscrollcommand=ys_caja.set)
        self.tree_caja.pack(side="left", fill="both", expand=True)
        
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

        # Controles de paginación Caja
        frm_pag_cj = ctk.CTkFrame(self.bg_caja, fg_color="transparent")
        frm_pag_cj.pack(fill="x", padx=10, pady=(0, 5))
        
        btn_prev_cj = ctk.CTkButton(frm_pag_cj, text="Anterior", width=80, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), command=self._prev_page_caja)
        btn_prev_cj.pack(side="left", padx=5)
        
        self.lbl_pag_caja = ctk.CTkLabel(frm_pag_cj, text="Página 1", font=("Segoe UI", 12))
        self.lbl_pag_caja.pack(side="left", padx=10)
        
        btn_next_cj = ctk.CTkButton(frm_pag_cj, text="Siguiente", width=80, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), command=self._next_page_caja)
        btn_next_cj.pack(side="left", padx=5)

    def buscar_caja(self):
        if not self.win.winfo_exists():
            return
        for i in self.tree_caja.get_children(): self.tree_caja.delete(i)
        
        def _fetch_caja():
            try:
                d_sql = self._clampear_fecha(self.fecha_desde_cj.get_date_sql())
                h_sql = self.fecha_hasta_cj.get_date_sql()
                
                seleccion = self.cb_filtro_rapido_cj.get()
                tipo_filtro, motivo_filtro = self.opciones_filtro_caja.get(seleccion, (None, None))
                
                db_tipo = tipo_filtro
                db_motivo = motivo_filtro
                
                # Conjuntos para filtrado local post-consulta
                MOTIVOS_VENTA = {'venta_efectivo', 'venta_transferencia', 'venta_tarjeta', 'venta_cuenta_corriente', 'venta_debito', 'venta_qr'}
                MOTIVOS_COBRO_CTA = {'pago_cuenta_corriente_efectivo', 'pago_cuenta_corriente_transferencia', 
                                      'pago_cuenta_corriente_tarjeta', 'cobro_cuenta_corriente', 'cobro_cta_cte'}
                
                # Para filtros agrupados ("venta" y "cobro_cta_cte") pedimos solo por tipo al backend
                # y filtramos por motivo localmente para capturar todas las variantes
                if motivo_filtro in ("venta", "cobro_cta_cte"):
                    db_motivo = None  # No filtrar por motivo en el backend
                elif seleccion == "(Todo)":
                    db_tipo = None
                    db_motivo = None

                es_vendedor = self.usuario.get('id_rol') == 2
                id_usuario = None
                if es_vendedor:
                    id_usuario = self.usuario.get('id_usuario')
                else:
                    try:
                        if self.usuario_caja_sel['id'] is not None and self.usuario_caja_sel['id'] != '-':
                            id_usuario = int(self.usuario_caja_sel['id'])
                    except: pass
                    
                tipo_caja_ui = self.cb_tipo_caja.get()
                tipo_caja_db = None
                if tipo_caja_ui == "Cajas de turno": tipo_caja_db = "turno"
                elif tipo_caja_ui == "Tesorería": tipo_caja_db = "administrativa"

                limit = self.pag_size
                offset = self.pag_caja * self.pag_size
                self.total_caja = self.backend.contar_historial_movimientos_caja(d_sql, h_sql, db_tipo, db_motivo, id_usuario, tipo_caja=tipo_caja_db)
                movimientos = self.backend.obtener_historial_movimientos_caja(
                    fecha_desde=d_sql,
                    fecha_hasta=h_sql,
                    tipo=db_tipo,
                    motivo=db_motivo,
                    id_usuario=id_usuario,
                    tipo_caja=tipo_caja_db,
                    limit=limit,
                    offset=offset
                )
                
                def _update_ui():
                    if not self.win.winfo_exists():
                        return
                    def _formatear_fecha(f):
                        if not f: return ""
                        try: return f.strftime("%d/%m/%Y %H:%M")
                        except:
                            texto = str(f)
                            if len(texto) >= 10 and "-" in texto[:10]:
                                partes = texto[:10].split("-")
                                if len(partes) == 3:
                                    return f"{partes[2]}/{partes[1]}/{partes[0]}" + texto[10:]
                            return texto

                    for mov in movimientos:
                        motivo_raw = mov.get('motivo') or ''
                        
                        # Filtrado local para grupos de motivos
                        if motivo_filtro == "venta" and motivo_raw not in MOTIVOS_VENTA and not motivo_raw.startswith('venta'):
                            continue
                        if motivo_filtro == "cobro_cta_cte" and motivo_raw not in MOTIVOS_COBRO_CTA and 'cuenta_corriente' not in motivo_raw and 'cta_cte' not in motivo_raw:
                            continue
                        # Para filtros específicos (no agrupados, no Todo), ocultar aperturas y cierres
                        if motivo_filtro and motivo_filtro not in ("venta", "cobro_cta_cte", "apertura_caja", "cierre_caja") and motivo_raw in ('apertura_caja', 'cierre_caja'):
                            if not isinstance(motivo_filtro, list) or motivo_raw not in motivo_filtro:
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
                            'compra_efectivo': '🛒 Compra',
                            'compra_cuenta_corriente': '🛒 Compra Cta. Cte.',
                            'gasto_vario': '💸 Gasto Vario',
                            'retiro_caja': '🔻 Retiro/Ajuste',  
                            'devolucion_efectivo': '↩️ Reembolso',
                            'ajuste_positivo': '🔺 Ajuste (+)',
                            'ajuste_negativo': '🔻 Ajuste (-)',
                            'otro': '❓ Otro'
                        }
                        
                        if motivo_raw and motivo_raw not in mapeo_motivos and motivo_raw.startswith('venta'):
                            motivo_txt = '🛒 Venta'
                        else:
                            motivo_txt = mapeo_motivos.get(motivo_raw, motivo_raw.replace('_', ' ').title() if motivo_raw else '-')
                        
                        desc_val = mov.get('descripcion')
                        descripcion = (desc_val if desc_val else '').strip() or '-'
                        if es_cierre:
                            obs_val = mov.get('observaciones_cierre')
                            obs_manual = (obs_val if obs_val else '').strip()
                            if obs_manual:
                                # Se concatena el resumen del sistema con la observación del usuario
                                descripcion = f"{descripcion} | Obs: {obs_manual}"
                        
                        if len(descripcion) > 50:
                            descripcion = descripcion[:47] + "..."
                            
                        tipo_caja_val = mov.get('tipo_caja', 'turno') or 'turno'
                        tipo_caja_abrev = 'Admin' if tipo_caja_val == 'administrativa' else 'Turno'
                        descripcion = f"[{tipo_caja_abrev}] {descripcion}"
                        
                        self.tree_caja.insert("", tk.END, values=(
                            _formatear_fecha(mov['fecha_hora']),
                            mov['usuario_nombre'],
                            tipo_visual,
                            motivo_txt,
                            _fmt_mon(mov['monto']),
                            descripcion
                        ), tags=(tag,))
                        
                    if hasattr(self, 'lbl_pag_caja'):
                        tot_pages = max(1, (self.total_caja + self.pag_size - 1) // self.pag_size)
                        self.lbl_pag_caja.configure(text=f"Página {self.pag_caja + 1} de {tot_pages} ({self.total_caja} registros)")
                
                if self.win.winfo_exists():
                    self.win.after(0, _update_ui)
            except Exception as e:
                logger.error(f"Error cargando caja: {e}")
                if self.win.winfo_exists():
                    self.win.after(0, lambda: messagebox.showerror("Error", str(e)))

        import threading
        threading.Thread(target=_fetch_caja, daemon=True).start()

    def _prev_page_caja(self):
        if self.pag_caja > 0:
            self.pag_caja -= 1
            self.buscar_caja()
            
    def _next_page_caja(self):
        tot_pages = max(1, (self.total_caja + self.pag_size - 1) // self.pag_size)
        if self.pag_caja < tot_pages - 1:
            self.pag_caja += 1
            self.buscar_caja()
        
    def _limpiar_filtros_caja(self):
        hoy = date.today()
        self.fecha_desde_cj.widget_entrada.delete(0, tk.END)
        self.fecha_desde_cj.widget_entrada.insert(0, hoy.strftime("%d/%m/%Y"))
        self.fecha_hasta_cj.widget_entrada.delete(0, tk.END)
        self.fecha_hasta_cj.widget_entrada.insert(0, hoy.strftime("%d/%m/%Y"))
        
        self.cb_filtro_rapido_cj.set("(Todo)")
        
        es_vendedor = self.usuario.get('id_rol') == 2
        if not es_vendedor:
            self.usuario_caja_sel['id'] = None
            self.usuario_caja_sel['nombre'] = "(Todos)"
            if hasattr(self, 'lbl_usuario_cj'):
                self.lbl_usuario_cj.configure(text="(Todos)")
                
        self.buscar_caja()
        
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

        b1 = ctk.CTkButton(dialog, text="📄 Exportar Resumen de Ventas", command=lambda: set_sel("maestro"), height=40)
        b1.pack(fill="x", padx=30, pady=(5, 0))
        ctk.CTkLabel(dialog, text="1 renglón por operación. Ideal para ver totales.", text_color="gray", font=("Arial", 11)).pack(pady=(0, 10))

        b2 = ctk.CTkButton(dialog, text="🔍 Exportar Venta Seleccionada", command=lambda: set_sel("detalle"), height=40)
        b2.pack(fill="x", padx=30, pady=(5, 0))
        ctk.CTkLabel(dialog, text="Lista de productos de la fila seleccionada.", text_color="gray", font=("Arial", 11)).pack(pady=(0, 10))

        b3 = ctk.CTkButton(dialog, text="📑 Exportar Todas las Ventas con Detalles", command=lambda: set_sel("ambos"), height=40)
        b3.pack(fill="x", padx=30, pady=(10, 5))
        ctk.CTkLabel(dialog, text="Sábana de datos completa con todos los productos.", text_color="gray", font=("Arial", 11)).pack(pady=(0, 20))

        dialog.transient(self.win)
        dialog.grab_set()
        self.win.wait_window(dialog)
        return seleccion["valor"]

    def _guardar_csv_simple(self, tree: ttk.Treeview, nombre_archivo: str, datos_reemplazo=None):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Excel CSV", "*.csv")], initialfile=nombre_archivo, parent=self.win)
        if not path: return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f, delimiter=';')
                w.writerow([tree.heading(c)['text'] for c in tree['columns']])
                
                if datos_reemplazo is not None:
                    for item in datos_reemplazo: w.writerow(item)
                else:
                    for item in tree.get_children(): w.writerow(tree.item(item, 'values'))
            messagebox.showinfo("Éxito", "Archivo exportado correctamente.", parent=self.win)
        except PermissionError:
            messagebox.showerror(
                "Archivo en Uso",
                "No se pudo escribir en el archivo porque está siendo utilizado por otra aplicación (ej. Microsoft Excel).\n\nPor favor, cierra el archivo e intenta nuevamente.",
                parent=self.win
            )
        except Exception as e:
            from app.frontend.manejador_errores import ManejadorErroresUI
            ManejadorErroresUI.manejar_error(e, parent=self.win, contexto="exportación")

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

            messagebox.showinfo("Éxito", "Reporte generado con contexto correctamente.", parent=self.win)
        except PermissionError:
            messagebox.showerror(
                "Archivo en Uso",
                "No se pudo escribir en el archivo porque está siendo utilizado por otra aplicación (ej. Microsoft Excel).\n\nPor favor, cierra el archivo e intenta nuevamente.",
                parent=self.win
            )
        except Exception as e:
            logger.error(f"Error csv combinado: {e}")
            from app.frontend.manejador_errores import ManejadorErroresUI
            ManejadorErroresUI.manejar_error(e, parent=self.win, contexto="exportación")

    def _registrar_auditoria_exportacion(self, tab_id: int) -> None:
        """Registra en la Bitácora del sistema que el usuario exportó un historial."""
        try:
            nombres = {0: "ventas", 1: "compras", 2: "pagos", 3: "caja"}
            tipo = nombres.get(tab_id, "desconocido")
            # Obtener el rango de fechas según la pestaña activa
            selectores = {
                0: (self.fecha_desde_v, self.fecha_hasta_v),
                1: (self.fecha_desde_c, self.fecha_hasta_c),
                2: (self.fecha_desde_p, self.fecha_hasta_p),
                3: (getattr(self, 'fecha_desde_cj', None), getattr(self, 'fecha_hasta_cj', None)),
            }
            sel_desde, sel_hasta = selectores.get(tab_id, (None, None))
            desde = sel_desde.get_date_sql() if sel_desde else None
            hasta = sel_hasta.get_date_sql() if sel_hasta else None

            if hasattr(self.backend, '_registrar_auditoria'):
                self.backend._registrar_auditoria(
                    id_usuario=self.usuario.get('id_usuario'),
                    accion='EXPORTAR_HISTORIAL',
                    tabla_afectada=tipo,
                    datos_nuevos={
                        'tipo': tipo,
                        'desde': desde,
                        'hasta': hasta,
                        'usuario': self.usuario.get('nombre', ''),
                    }
                )
        except Exception as e:
            logger.warning(f"No se pudo registrar auditoría de exportación: {e}")

    def _validar_rango_exportacion(self, d_sql, h_sql, max_dias=31):
        if not d_sql or not h_sql: return
        try:
            from datetime import date
            d = date.fromisoformat(d_sql[:10])
            h = date.fromisoformat(h_sql[:10])
            if (h - d).days > max_dias:
                raise ValueError(f"El rango de fechas supera el límite de {max_dias} días para exportaciones masivas.\nPor favor, exporte por intervalos más cortos (ej. un mes) para evitar problemas de memoria.")
        except ValueError as e:
            if "supera el límite" in str(e): raise

    def _get_datos_completos(self, tab_id):
        if tab_id == 0:
            d_sql = self._clampear_fecha(self.fecha_desde_v.get_date_sql())
            h_sql = self.fecha_hasta_v.get_date_sql()
            self._validar_rango_exportacion(d_sql, h_sql)
            es_vendedor = self.usuario.get('id_rol') == 2
            id_vend = self.usuario.get('id_usuario') if es_vendedor else self.vendedor_sel['id']
            id_cli = self.cliente_sel['id']
            res = self.backend.obtener_ventas_maestro(d_sql, h_sql, id_cli, id_vend, limit=None, offset=0)
            return [[v.get('id_venta'), _formatear_fecha_para_ui(v.get('fecha')), v.get('cliente') or "Consumidor Final", v.get('vendedor'), _fmt_mon(v.get('total')), v.get('estado'), v.get('tipo_pago')] for v in res]
        elif tab_id == 1:
            d_sql = self._clampear_fecha(self.fecha_desde_c.get_date_sql())
            h_sql = self.fecha_hasta_c.get_date_sql()
            self._validar_rango_exportacion(d_sql, h_sql)
            id_prov_filtro = self.proveedor_sel['id']
            compras = self.backend.obtener_compras_maestro(d_sql, h_sql, id_prov_filtro, limit=None, offset=0)
            es_vendedor = self.usuario.get('id_rol') == 2
            nombre_usuario_sel = self.usuario.get('nombre') if es_vendedor else self.usuario_c_sel['nombre']
            if nombre_usuario_sel != "(Todos)":
                compras = [c for c in compras if c.get('usuario') == nombre_usuario_sel]
            prov_map = self.proveedores_map_nombre
            ret = []
            for c in compras:
                medio = c.get('medio_pago') or '-'
                prov_data = prov_map.get(c.get('proveedor'), {})
                ret.append([c.get('id_compra'), _formatear_fecha_para_ui(c.get('fecha')), prov_data.get('empresa') or c.get('proveedor') or '-', prov_data.get('cuit', '-'), _fmt_mon(c.get('total')), c.get('estado'), medio, c.get('usuario')])
            return ret
        elif tab_id == 2:
            d_sql = self._clampear_fecha(self.fecha_desde_p.get_date_sql())
            h_sql = self.fecha_hasta_p.get_date_sql()
            self._validar_rango_exportacion(d_sql, h_sql)
            id_cli = self.cliente_p_sel['id']
            if hasattr(self, 'filtro_cliente_id') and self.filtro_cliente_id: id_cli = self.filtro_cliente_id
            id_usuario = self.usuario_p_sel['id']
            res = self.backend.obtener_pagos_maestro(d_sql, h_sql, id_cli, id_usuario, limit=None, offset=0)
            return [[_formatear_fecha_para_ui(p.get('fecha')), p.get('cliente_nombre'), _fmt_mon(p.get('monto')), p.get('metodo'), p.get('usuario_nombre')] for p in res]
        elif tab_id == 3:
            d_sql = self._clampear_fecha(self.fecha_desde_cj.get_date_sql())
            h_sql = self.fecha_hasta_cj.get_date_sql()
            self._validar_rango_exportacion(d_sql, h_sql)
            seleccion = self.cb_filtro_rapido_cj.get()
            db_tipo, db_motivo = self.opciones_filtro_caja.get(seleccion, (None, None))
            if db_motivo in ("venta", "cobro_cta_cte"): db_motivo = None
            elif seleccion == "(Todo)": db_tipo = db_motivo = None
            es_vendedor = self.usuario.get('id_rol') == 2
            id_usuario = self.usuario.get('id_usuario') if es_vendedor else (int(self.usuario_caja_sel['id']) if self.usuario_caja_sel['id'] and self.usuario_caja_sel['id'] != '-' else None)
            
            tipo_caja_ui = self.cb_tipo_caja.get()
            tipo_caja_db = None
            if tipo_caja_ui == "Cajas de turno": tipo_caja_db = "turno"
            elif tipo_caja_ui == "Tesorería": tipo_caja_db = "administrativa"
            
            res = self.backend.obtener_historial_movimientos_caja(fecha_desde=d_sql, fecha_hasta=h_sql, tipo=db_tipo, motivo=db_motivo, id_usuario=id_usuario, tipo_caja=tipo_caja_db, limit=None, offset=0)
            
            # Formateo simple para CSV
            def _formatear_fecha_csv(f):
                if not f: return ""
                try: return f.strftime("%d/%m/%Y %H:%M")
                except: return str(f)
                
            ret = []
            for mov in res:
                motivo_raw = mov.get('motivo') or ''
                # Filtrado simple
                if seleccion != "(Todo)" and motivo_raw in ('apertura_caja', 'cierre_caja') and db_motivo not in ("venta", "cobro_cta_cte", "apertura_caja", "cierre_caja"): continue
                es_ingreso = (mov.get('tipo') == 'ingreso')
                tipo_visual = "INGRESO" if es_ingreso else "EGRESO"
                if motivo_raw == 'apertura_caja': tipo_visual = "APERTURA"
                elif motivo_raw == 'cierre_caja': tipo_visual = "CIERRE"
                desc = (mov.get('descripcion') or '').strip() or '-'
                ret.append([_formatear_fecha_csv(mov['fecha_hora']), mov['usuario_nombre'], tipo_visual, motivo_raw, _fmt_mon(mov['monto']), desc])
            return ret
        return []

    def exportar_a_csv(self, tab_id):
        hoy = datetime.now().strftime("%d-%m-%Y")
        nombres = {0: "ventas", 1: "compras", 2: "pagos", 3: "caja"}
        nombre_base = f"{nombres.get(tab_id, 'datos')}_{hoy}.csv"

        def _do_export(opcion=None):
            try:
                datos = self._get_datos_completos(tab_id)
                if not datos:
                    if self.win.winfo_exists(): self.win.after(0, lambda: messagebox.showinfo("Aviso", "No hay datos para exportar.", parent=self.win))
                    return

                if tab_id in [2, 3]:
                    tree = self.tree_pagos if tab_id == 2 else self.tree_caja
                    if self.win.winfo_exists(): self.win.after(0, lambda: self._guardar_csv_simple(tree, nombre_base, datos))
                else:
                    tree_m = self.tree_maestro_v if tab_id == 0 else self.tree_maestro_c
                    if opcion == "maestro":
                        if self.win.winfo_exists(): self.win.after(0, lambda: self._guardar_csv_simple(tree_m, f"listado_general_{nombre_base}", datos))
                    elif opcion == "ambos":
                        if self.win.winfo_exists(): self.win.after(0, lambda: self._guardar_csv_combinado(datos, tree_m, tab_id, f"reporte_completo_{nombre_base}", False))
                        
                if self.win.winfo_exists(): self.win.after(0, lambda: self._registrar_auditoria_exportacion(tab_id))
            except Exception as e:
                logger.error(f"Error al exportar a csv: {e}")
                if self.win.winfo_exists(): self.win.after(0, lambda: messagebox.showerror("Error", f"Fallo la exportacion: {e}", parent=self.win))

        if tab_id in [2, 3]:
            import threading
            threading.Thread(target=_do_export, daemon=True).start()
            return

        opcion = self._preguntar_tipo_exportacion()
        if not opcion: return

        if opcion == "detalle":
            tree_m = self.tree_maestro_v if tab_id == 0 else self.tree_maestro_c
            if not tree_m.selection():
                messagebox.showwarning("Selección Requerida", "Por favor, selecciona una transacción del listado primero para exportar su detalle.", parent=self.win)
                return
            sel = tree_m.selection()
            datos_cabecera = tree_m.item(sel[0], 'values')
            self._guardar_csv_combinado([datos_cabecera], tree_m, tab_id, f"detalle_venta_{datos_cabecera[0]}_{nombre_base}", False)
            self._registrar_auditoria_exportacion(tab_id)
        else:
            import threading
            threading.Thread(target=lambda: _do_export(opcion), daemon=True).start()


ui_historiales = Historiales