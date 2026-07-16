# app/frontend/interfaz_auditoria.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog
import customtkinter as ctk
import json
import csv
from datetime import datetime, timedelta
from typing import Optional

from app.frontend import custom_dialogs as messagebox
from app.frontend.theme_config import get_color, preparar_ventana, centrar_y_mostrar_ventana, aplicar_tema_ventana, configurar_estilo_treeview
from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
from app.frontend.componentes_ui import SelectorFecha

MAPEO_ACCIONES = {
    "CREAR_USUARIO": "➕ Usuario creado",
    "DESACTIVAR_USUARIO": "❌ Usuario desactivado",
    "REACTIVAR_USUARIO": "♻️ Usuario reactivado",
    "RESETEAR_PASSWORD": "🔑 Contraseña restablecida",
    "MODIFICAR_USUARIO": "✏️ Usuario modificado",
    "CREAR_PRODUCTO": "➕ Producto creado",
    "MODIFICAR_PRODUCTO": "✏️ Producto modificado",
    "DESACTIVAR_PRODUCTO": "❌ Producto desactivado",
    "AJUSTE_STOCK_MANUAL": "📦 Ajuste de stock",
    "CREAR_CLIENTE": "➕ Cliente creado",
    "MODIFICAR_LIMITE_CREDITO_CLIENTE": "💳 Límite de crédito modificado",
    "DESACTIVAR_CLIENTE": "❌ Cliente desactivado",
    "REACTIVAR_CLIENTE": "♻️ Cliente reactivado",
    "CREAR_PROVEEDOR": "➕ Proveedor creado",
    "DESACTIVAR_PROVEEDOR": "❌ Proveedor desactivado",
    "REACTIVAR_PROVEEDOR": "♻️ Proveedor reactivado",
    "CIERRE_CAJA_SUPERVISOR": "🔒 Cierre forzado de caja",
    "CIERRE_CAJA": "🔒 Cierre de caja",
    "EXPORTAR_HISTORIAL": "📤 Exportación de historial",
    "DESACTIVAR_CATEGORIA": "❌ Categoría desactivada",
    "REACTIVAR_CATEGORIA": "♻️ Categoría reactivada",
    "CREAR_TESORERIA_AUTOMATICA": "🏦 Tesorería del día creada automáticamente",
    "APROBACION_TRANSFERENCIA": "✅ Transferencia a Tesorería autorizada",
    "ANULAR_VENTA": "🚫 Venta anulada",
    "ANULAR_COMPRA": "🚫 Compra anulada",
    "APERTURA_CAJA": "🔓 Apertura de caja",
    "TRANSFERENCIA_CAJA": "🔄 Transferencia entre cajas",
    "TRANSFERENCIA_TESORERIA": "🏦 Transferencia a Tesorería",
    "EDITAR_PROVEEDOR": "✏️ Proveedor modificado"
}

INV_MAPEO_ACCIONES = {v: k for k, v in MAPEO_ACCIONES.items()}

# Grupos temáticos para el dropdown de filtro (más compacto que listar las 29 acciones)
GRUPOS_ACCIONES = {
    "Todas": [],
    "➕ Altas": ["CREAR_USUARIO", "CREAR_PRODUCTO", "CREAR_CLIENTE", "CREAR_PROVEEDOR"],
    "❌ Bajas": ["DESACTIVAR_USUARIO", "DESACTIVAR_PRODUCTO", "DESACTIVAR_CLIENTE", "DESACTIVAR_PROVEEDOR", "DESACTIVAR_CATEGORIA"],
    "♻️ Reactivaciones": ["REACTIVAR_USUARIO", "REACTIVAR_CLIENTE", "REACTIVAR_PROVEEDOR", "REACTIVAR_CATEGORIA"],
    "✏️ Modificaciones": ["MODIFICAR_USUARIO", "MODIFICAR_PRODUCTO", "MODIFICAR_LIMITE_CREDITO_CLIENTE", "EDITAR_PROVEEDOR", "RESETEAR_PASSWORD", "AJUSTE_STOCK_MANUAL"],
    "🔒 Caja y Turnos": ["APERTURA_CAJA", "CIERRE_CAJA", "CIERRE_CAJA_SUPERVISOR"],
    "💸 Movimientos de Dinero": ["TRANSFERENCIA_CAJA", "TRANSFERENCIA_TESORERIA", "APROBACION_TRANSFERENCIA", "CREAR_TESORERIA_AUTOMATICA"],
    "🚫 Anulaciones": ["ANULAR_VENTA", "ANULAR_COMPRA"],
    "📤 Exportaciones": ["EXPORTAR_HISTORIAL"],
}

class InterfazAuditoria:
    def __init__(self, parent, backend, usuario_actual: dict):
        self.parent = parent
        self.backend = backend
        self.usuario_actual = usuario_actual
        
        # Colores
        self.col_bg = get_color("bg_root")
        self.col_card = get_color("bg_surface")
        self.col_text = get_color("text_primary")
        self.col_border = "#2d3748"
        
        self.win = ctk.CTkToplevel(parent)
        preparar_ventana(self.win)
        self.win.title("Bitácora del Sistema")
        self.win.geometry("1200x750")
        self.win.minsize(1050, 650)
        
        configurar_estilo_treeview()
        
        self.pag_size = 50
        self.pag_aud = 0
        self.total_aud = 0
        
        # Estado del selector de usuario
        self.usuario_sel: dict = {"id": None, "nombre": "Todos"}
        self.usuarios_raw: list = []
        
        self.crear_widgets()
        self.cargar_filtros()
        self.cargar_datos()
        
        configurar_navegacion_ventana(self.win)
        self.win.transient(parent)
        centrar_y_mostrar_ventana(self.win)
        self.win.grab_set()

    def crear_widgets(self):
        # Título
        ctk.CTkLabel(self.win, text="🔒 Bitácora de Auditoría Administrativa", font=("Segoe UI", 20, "bold"), text_color=self.col_text).pack(pady=(20, 10))
        
        # --- FILTROS ---
        frame_filtros = ctk.CTkFrame(self.win, fg_color=self.col_card, corner_radius=10, border_color=self.col_border, border_width=1)
        frame_filtros.pack(fill="x", padx=20, pady=10)
        
        # Primera fila de filtros
        row1 = ctk.CTkFrame(frame_filtros, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(row1, text="Usuario:", font=("Segoe UI", 12)).pack(side="left", padx=(10, 5))
        frm_usr = ctk.CTkFrame(row1, fg_color="transparent")
        frm_usr.pack(side="left", padx=5)
        self.lbl_usuario_sel = ctk.CTkLabel(
            frm_usr, text="Todos", font=("Segoe UI", 12, "bold"),
            text_color=get_color("text_primary"), width=150, anchor="w"
        )
        self.lbl_usuario_sel.pack(side="left", padx=(0, 5))
        ctk.CTkButton(
            frm_usr, text="🔍", width=35, height=28,
            fg_color="#3b82f6", hover_color="#2563eb",
            command=self._abrir_selector_usuario
        ).pack(side="left")
        
        ctk.CTkLabel(row1, text="Acción:", font=("Segoe UI", 12)).pack(side="left", padx=(20, 5))
        self.combo_accion = ctk.CTkOptionMenu(row1, width=250, font=("Segoe UI", 12))
        self.combo_accion.pack(side="left", padx=5)
        
        ctk.CTkLabel(row1, text="Desde:", font=("Segoe UI", 12)).pack(side="left", padx=(20, 5))
        self.entry_desde = SelectorFecha(row1)
        self.entry_desde.pack(side="left", padx=5)
        
        ctk.CTkLabel(row1, text="Hasta:", font=("Segoe UI", 12)).pack(side="left", padx=(20, 5))
        self.entry_hasta = SelectorFecha(row1)
        self.entry_hasta.pack(side="left", padx=5)
        
        # Segunda fila de botones
        row2 = ctk.CTkFrame(frame_filtros, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(5, 10))
        
        # Atajos de fecha
        ctk.CTkButton(row2, text="Hoy", command=self.atajo_hoy, width=80, fg_color="#4b5563", hover_color="#374151").pack(side="left", padx=(10, 5))
        ctk.CTkButton(row2, text="Últimos 7 días", command=self.atajo_7dias, width=120, fg_color="#4b5563", hover_color="#374151").pack(side="left", padx=5)
        ctk.CTkButton(row2, text="Este mes", command=self.atajo_mes, width=100, fg_color="#4b5563", hover_color="#374151").pack(side="left", padx=5)
        
        # Acciones de filtrado y exportación
        self.btn_exportar = ctk.CTkButton(row2, text="📄 Exportar CSV", command=self.exportar_csv, width=130, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 12, "bold"))
        self.btn_exportar.pack(side="right", padx=(10, 10))
        
        self.btn_limpiar = ctk.CTkButton(row2, text="🧹 Limpiar", command=self.limpiar_filtros, width=100, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 12))
        self.btn_limpiar.pack(side="right", padx=5)
        
        self.btn_filtrar = ctk.CTkButton(row2, text="🔍 Aplicar Filtros", command=self.cargar_datos, width=140, fg_color="#3b82f6", hover_color="#2563eb", font=("Segoe UI", 12, "bold"))
        self.btn_filtrar.pack(side="right", padx=5)
        
        # --- TABLA ---
        frame_tabla = ctk.CTkFrame(self.win, fg_color=self.col_card, corner_radius=10, border_color=self.col_border, border_width=1)
        frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        cols = ("Fecha", "Usuario", "Acción", "Entidad", "Resumen")
        self.tree = ttk.Treeview(frame_tabla, columns=cols, show="headings", style="Modern.Treeview")
        
        self.tree.heading("Fecha", text="Fecha")
        self.tree.column("Fecha", width=140, anchor="center")
        
        self.tree.heading("Usuario", text="Usuario")
        self.tree.column("Usuario", width=150)
        
        self.tree.heading("Acción", text="Acción")
        self.tree.column("Acción", width=250)
        
        self.tree.heading("Entidad", text="Entidad")
        self.tree.column("Entidad", width=150, anchor="center")
        
        self.tree.heading("Resumen", text="Resumen")
        self.tree.column("Resumen", width=350)
        
        # Configurar colores de tags para temas claros (o ajustables). CustomTkinter + ttk treeview a veces necesita colores base.
        self.tree.tag_configure("tag_create", background="#e6f4ea", foreground="#000000")
        self.tree.tag_configure("tag_update", background="#e8f0fe", foreground="#000000")
        self.tree.tag_configure("tag_delete", background="#fce8e6", foreground="#000000")
        self.tree.tag_configure("tag_sensitive", background="#fef0d9", foreground="#000000")
        
        self.tree.bind("<Double-1>", self.mostrar_detalle_evento)
        
        ys = ctk.CTkScrollbar(frame_tabla, command=self.tree.yview)
        ys.pack(side="right", fill="y", padx=2, pady=5)
        self.tree.configure(yscrollcommand=ys.set)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Estructura para guardar datos crudos asociados al row id
        self.datos_crudos_tree = {}
        
        # --- PAGINACION ---
        frm_pag_aud = ctk.CTkFrame(self.win, fg_color="transparent")
        frm_pag_aud.pack(fill="x", padx=20, pady=(0, 10))
        
        btn_prev_aud = ctk.CTkButton(frm_pag_aud, text="Anterior", width=80, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), command=self._prev_page_aud)
        btn_prev_aud.pack(side="left", padx=5)
        
        self.lbl_pag_aud = ctk.CTkLabel(frm_pag_aud, text="Página 1", font=("Segoe UI", 12))
        self.lbl_pag_aud.pack(side="left", padx=10)
        
        btn_next_aud = ctk.CTkButton(frm_pag_aud, text="Siguiente", width=80, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), command=self._next_page_aud)
        btn_next_aud.pack(side="left", padx=5)

        # --- BOTONES INFERIORES ---
        frame_btns = ctk.CTkFrame(self.win, fg_color="transparent")
        frame_btns.pack(fill="x", padx=20, pady=(0, 20))
        
        self.btn_cerrar = ctk.CTkButton(frame_btns, text="Cerrar", command=self.win.destroy, fg_color="#4b5563", hover_color="#374151", width=120, font=("Segoe UI", 13, "bold"))
        self.btn_cerrar.pack(side="right")
        
    def atajo_hoy(self):
        hoy = datetime.now()
        self._set_selector_fecha(self.entry_desde, hoy)
        self._set_selector_fecha(self.entry_hasta, hoy)

    def atajo_7dias(self):
        hoy = datetime.now()
        hace_7 = hoy - timedelta(days=7)
        self._set_selector_fecha(self.entry_desde, hace_7)
        self._set_selector_fecha(self.entry_hasta, hoy)

    def atajo_mes(self):
        hoy = datetime.now()
        primero = hoy.replace(day=1)
        self._set_selector_fecha(self.entry_desde, primero)
        self._set_selector_fecha(self.entry_hasta, hoy)
        
    def _set_selector_fecha(self, selector, fecha):
        if hasattr(selector.entrada, 'set_date'):
            selector.entrada.set_date(fecha)
        else:
            selector.entrada.delete(0, tk.END)
            selector.entrada.insert(0, fecha.strftime("%d/%m/%Y"))
        
    def cargar_filtros(self):
        try:
            # Cargar Usuarios (lista cruda para el popup de búsqueda)
            self.usuarios_raw = self.backend.obtener_usuarios_con_rol()
            
            # Cargar grupos temáticos (más compacto que las 29 acciones individuales)
            self.combo_accion.configure(values=list(GRUPOS_ACCIONES.keys()))
            self.combo_accion.set("Todas")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando filtros: {e}", parent=self.win)

    def _abrir_selector_usuario(self):
        """Abre un popup modal con Treeview y búsqueda en tiempo real para seleccionar usuario."""
        popup = ctk.CTkToplevel(self.win)
        preparar_ventana(popup)
        popup.title("Seleccionar Usuario")
        popup.geometry("500x530")
        configurar_navegacion_ventana(popup)

        var_pat = tk.StringVar()
        ctk.CTkLabel(
            popup, text="Buscar Usuario (ID/Nombre):",
            font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")
        ).pack(pady=(15, 5), padx=15, anchor="w")
        ent = ctk.CTkEntry(
            popup, textvariable=var_pat, font=("Segoe UI", 13),
            height=40, placeholder_text="Nombre o ID..."
        )
        ent.pack(fill="x", padx=15, pady=5)

        frame_list = ctk.CTkFrame(
            popup, fg_color=self.col_card, corner_radius=10,
            border_color=self.col_border, border_width=1
        )
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
                if i != "opt_all":
                    tree_sel.delete(i)
            for u in filas:
                tree_sel.insert("", "end", values=[u.get('id_usuario', ''), u.get('nombre', '')])

        render(self.usuarios_raw)

        def filtrar(*_):
            q = var_pat.get().strip().lower()
            if not q:
                render(self.usuarios_raw)
                return
            filtrados = [
                u for u in self.usuarios_raw
                if q in str(u.get('id_usuario', '')).lower() or q in u.get('nombre', '').lower()
            ]
            render(filtrados)

        var_pat.trace_add("write", filtrar)

        def tomar(event=None):
            sel_id = tree_sel.focus()
            if not sel_id:
                return
            if sel_id == "opt_all":
                self.usuario_sel["id"] = None
                self.usuario_sel["nombre"] = "Todos"
            else:
                vals = tree_sel.item(sel_id, "values")
                if not vals:
                    return
                try:
                    self.usuario_sel["id"] = int(vals[0])
                except (ValueError, TypeError):
                    self.usuario_sel["id"] = None
                self.usuario_sel["nombre"] = vals[1]
            self.lbl_usuario_sel.configure(text=self.usuario_sel["nombre"])
            popup.destroy()

        tree_sel.bind("<Double-1>", tomar)
        tree_sel.bind("<Return>", tomar)

        btn_frm = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frm.pack(fill="x", side="bottom", padx=15, pady=(5, 15))
        ctk.CTkButton(
            btn_frm, text="Cancelar", command=popup.destroy,
            fg_color="#ef4444", hover_color="#dc2626",
            font=("Segoe UI", 13, "bold"), width=150, height=45
        ).pack(side="left", padx=10)
        ctk.CTkButton(
            btn_frm, text="✓ Seleccionar", command=tomar,
            fg_color="#10b981", hover_color="#059669",
            font=("Segoe UI", 14, "bold"), width=180, height=45
        ).pack(side="right", padx=10)

        popup.after(100, lambda: ent.focus_set())
        centrar_y_mostrar_ventana(popup)
        popup.grab_set()
        popup.transient(self.win)
        self.win.wait_window(popup)
            
    def limpiar_filtros(self):
        self.usuario_sel["id"] = None
        self.usuario_sel["nombre"] = "Todos"
        self.lbl_usuario_sel.configure(text="Todos")
        self.combo_accion.set("Todas")
        if hasattr(self.entry_desde.entrada, 'set_date'):
            # tkcalendar's DateEntry doesn't have an empty state easily, so we set to today
            self._set_selector_fecha(self.entry_desde, datetime.now())
            self._set_selector_fecha(self.entry_hasta, datetime.now())
        else:
            self.entry_desde.entrada.delete(0, tk.END)
            self.entry_hasta.entrada.delete(0, tk.END)
        self.cargar_datos()
        
    def procesar_resumen(self, accion: str, ant: str, nue: str) -> str:
        """Genera el texto corto que aparece en la columna Resumen de la tabla."""
        if not nue and not ant: return "Acción registrada"
        try:
            d_ant = json.loads(ant) if ant else {}
            d_nue = json.loads(nue) if nue else {}
            _map_roles = {1: 'Administrador', 2: 'Vendedor', 3: 'Supervisor'}

            # ── Usuarios ──────────────────────────────────────
            if accion == "CREAR_USUARIO":
                rol_id = d_nue.get('id_rol', '?')
                rol = _map_roles.get(int(rol_id), f'Rol #{rol_id}') if str(rol_id).isdigit() else f'Rol #{rol_id}'
                nombre = d_nue.get('nombre', '')
                return f"Nuevo usuario «{nombre}» registrado como {rol}"
            if accion == "DESACTIVAR_USUARIO":
                nombre = d_ant.get('nombre', '') or d_nue.get('nombre', '')
                return f"Usuario «{nombre}» desactivado"
            if accion == "REACTIVAR_USUARIO":
                nombre = d_nue.get('nombre', '') or d_ant.get('nombre', '')
                return f"Usuario «{nombre}» reactivado"
            if accion == "RESETEAR_PASSWORD":
                nombre = d_nue.get('nombre', '') or d_ant.get('nombre', '')
                return f"Contraseña de «{nombre}» restablecida manualmente"
            if accion == "MODIFICAR_USUARIO":
                cambios_usr = []
                for k, v in d_nue.items():
                    if k in d_ant and str(d_ant[k]) != str(v):
                        k_am = "Rol" if k == 'id_rol' else k.replace('_', ' ').capitalize()
                        v_a = _map_roles.get(int(d_ant[k]), f'#{d_ant[k]}') if k == 'id_rol' and str(d_ant[k]).isdigit() else d_ant[k]
                        v_n = _map_roles.get(int(v), f'#{v}') if k == 'id_rol' and str(v).isdigit() else v
                        cambios_usr.append(f"{k_am}: {v_a} → {v_n}")
                return " | ".join(cambios_usr) if cambios_usr else "Datos de usuario modificados"

            # ── Productos ─────────────────────────────────────
            if accion == "CREAR_PRODUCTO":
                nombre = d_nue.get('nombre', 'Desconocido')
                precio = d_nue.get('precio_venta', d_nue.get('precio', 0))
                try: return f"Producto «{nombre}» creado · Precio: ${float(precio):,.2f}"
                except: return f"Producto «{nombre}» creado"
            if accion == "MODIFICAR_PRODUCTO":
                cambios = []
                for campo, label in [('nombre','Nombre'),('precio_venta','Precio'),('stock_minimo','Stock mín.')]:
                    v_a, v_n = d_ant.get(campo), d_nue.get(campo)
                    if v_a is not None and v_n is not None and str(v_a) != str(v_n):
                        cambios.append(f"Precio: ${float(v_a):,.2f} → ${float(v_n):,.2f}" if campo == 'precio_venta' else f"{label}: {v_a} → {v_n}")
                return " | ".join(cambios) if cambios else "Datos del producto modificados"
            if accion == "DESACTIVAR_PRODUCTO":
                return f"Producto «{d_ant.get('nombre', '') or d_nue.get('nombre', '')}» dado de baja"
            if accion == "AJUSTE_STOCK_MANUAL":
                cant_ant = d_ant.get('stock', d_ant.get('cantidad', 0))
                cant_nue = d_nue.get('stock', d_nue.get('cantidad', 0))
                id_prod = d_nue.get('id_producto')
                nombre_prod = "Producto"
                if id_prod:
                    try:
                        prod = self.backend.buscar_producto_por_id(int(id_prod))
                        if prod and prod.get("nombre"): nombre_prod = prod["nombre"]
                    except: pass
                try:
                    diff = int(cant_nue) - int(cant_ant)
                    return f"Stock «{nombre_prod}»: {cant_ant} → {cant_nue} ({'+' if diff>0 else ''}{diff})"
                except: return f"Stock «{nombre_prod}»: {cant_ant} → {cant_nue}"

            # ── Clientes ──────────────────────────────────────
            if accion == "CREAR_CLIENTE":
                nombre = d_nue.get('nombre', 'Desconocido')
                try: return f"Cliente «{nombre}» registrado · Límite: ${float(d_nue.get('limite_credito',0)):,.2f}"
                except: return f"Cliente «{nombre}» registrado"
            if accion == "MODIFICAR_LIMITE_CREDITO_CLIENTE":
                return f"Límite de crédito: ${float(d_ant.get('limite_credito',0)):,.2f} → ${float(d_nue.get('limite_credito',0)):,.2f}"
            if accion == "DESACTIVAR_CLIENTE":
                return f"Cliente «{d_ant.get('nombre','') or d_nue.get('nombre','')}» desactivado"
            if accion == "REACTIVAR_CLIENTE":
                return f"Cliente «{d_nue.get('nombre','') or d_ant.get('nombre','')}» reactivado"

            # ── Proveedores ───────────────────────────────────
            if accion == "CREAR_PROVEEDOR":
                nombre = d_nue.get('nombre', 'Desconocido')
                empresa = d_nue.get('empresa', '')
                return f"Proveedor «{nombre}» ({empresa}) dado de alta" if empresa else f"Proveedor «{nombre}» dado de alta"
            if accion == "DESACTIVAR_PROVEEDOR":
                return f"Proveedor «{d_ant.get('nombre','') or d_nue.get('nombre','')}» desactivado"
            if accion == "REACTIVAR_PROVEEDOR":
                return f"Proveedor «{d_nue.get('nombre','') or d_ant.get('nombre','')}» reactivado"
            if accion == "EDITAR_PROVEEDOR":
                return f"Datos del proveedor «{d_ant.get('nombre','') or d_nue.get('nombre','')}» modificados"

            # ── Categorías ────────────────────────────────────
            if accion == "DESACTIVAR_CATEGORIA":
                return f"Categoría «{d_ant.get('nombre','') or d_nue.get('nombre','')}» desactivada"
            if accion == "REACTIVAR_CATEGORIA":
                return f"Categoría «{d_nue.get('nombre','') or d_ant.get('nombre','')}» reactivada"

            # ── Caja ──────────────────────────────────────────
            if accion == "APERTURA_CAJA":
                monto = d_nue.get('monto_inicial', d_nue.get('monto', 0))
                try: return f"Caja abierta con fondo inicial de ${float(monto):,.2f}"
                except: return "Apertura de caja registrada"
            if accion in ("CIERRE_CAJA", "CIERRE_CAJA_SUPERVISOR"):
                diferencia = d_nue.get('diferencia')
                contado = d_nue.get('contado', d_nue.get('efectivo_contado'))
                if diferencia is not None and contado is not None:
                    dif_f = float(diferencia)
                    estado = "✅ Sin diferencia" if dif_f == 0 else ("⬆️ Sobrante" if dif_f > 0 else "⬇️ Faltante")
                    return f"Contado: ${float(contado):,.2f} | Diferencia: ${abs(dif_f):,.2f} {estado}"
                if accion == "CIERRE_CAJA_SUPERVISOR":
                    return f"Cierre forzado por supervisor · Motivo: {d_nue.get('motivo','Sin especificar')}"
                return "Cierre de caja registrado"

            # ── Ventas / Compras ──────────────────────────────
            if accion == "ANULAR_VENTA":
                id_v = d_nue.get('id_venta', d_ant.get('id_venta', '?'))
                motivo = d_nue.get('motivo', 'Sin especificar')
                return f"Venta #{id_v} anulada · Motivo: {motivo}"
            if accion == "ANULAR_COMPRA":
                id_c = d_nue.get('id_compra', d_ant.get('id_compra', '?'))
                motivo = d_nue.get('motivo', 'Sin especificar')
                return f"Compra #{id_c} anulada · Motivo: {motivo}"

            # ── Transferencias / Tesorería ────────────────────
            if accion in ("TRANSFERENCIA_CAJA", "TRANSFERENCIA_TESORERIA", "APROBACION_TRANSFERENCIA"):
                monto = d_nue.get('monto', 0)
                def _res_caja(id_caja):
                    if not id_caja or str(id_caja) == '?': return "Caja desconocida"
                    try:
                        sess = self.backend.obtener_session_por_id(int(id_caja))
                        if sess:
                            if sess.get('tipo_caja') == 'administrativa': return "Tesorería"
                            id_u = sess.get('id_usuario')
                            if id_u:
                                for u in getattr(self, 'usuarios_raw', []):
                                    if u.get('id_usuario') == id_u: return f"Caja de {u.get('nombre')}"
                        return f"Caja #{id_caja}"
                    except: return f"Caja #{id_caja}"
                origen = _res_caja(d_nue.get('origen', d_nue.get('id_session_origen', '?')))
                destino = _res_caja(d_nue.get('destino', d_nue.get('id_session_destino', '?')))
                return f"${float(monto):,.2f} · De: {origen} → A: {destino}"
            if accion == "CREAR_TESORERIA_AUTOMATICA":
                return "Tesorería del día creada automáticamente por el sistema"
            if accion == "EXPORTAR_HISTORIAL":
                return "Historial exportado a CSV"

            # Fallback
            return "Acción registrada"
        except Exception:
            return "Acción registrada"
    def determinar_tag_accion(self, accion: str) -> str:
        if accion.startswith("CREAR"): return "tag_create"
        if accion.startswith("DESACTIVAR"): return "tag_delete"
        if accion.startswith("CIERRE") or "LIMITE" in accion: return "tag_sensitive"
        return "tag_update" # Por defecto azul para modificaciones/reactivaciones/ajustes

    def validar_y_convertir_fecha(self, fecha_str: str) -> Optional[str]:
        if not fecha_str.strip():
            return None
        try:
            dt = datetime.strptime(fecha_str.strip(), "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Formato de fecha inválido: {fecha_str}. Use dd/mm/aaaa.")

    def resolver_entidad(self, tabla: str, id_reg: str) -> str:
        if not id_reg:
            return tabla
            
        try:
            id_num = int(id_reg)
        except ValueError:
            return f"{tabla} #{id_reg}"

        if tabla in ("Inventario", "Producto"):
            try:
                prod = self.backend.buscar_producto_por_id(id_num)
                if prod and prod.get("nombre"):
                    return f"Producto: {prod['nombre']}"
            except Exception:
                pass

        elif tabla == "Usuario":
            for u in getattr(self, 'usuarios_raw', []):
                if u.get('id_usuario') == id_num:
                    return f"Usuario: {u.get('nombre')}"

        elif tabla == "caja_session":
            try:
                sess = self.backend.obtener_session_por_id(id_num)
                if sess:
                    if sess.get('tipo_caja') == 'administrativa':
                        return "Tesorería"
                    id_u = sess.get('id_usuario')
                    if id_u:
                        for u in getattr(self, 'usuarios_raw', []):
                            if u.get('id_usuario') == id_u:
                                return f"Caja de {u.get('nombre')}"
            except Exception:
                pass

        return f"{tabla} #{id_num}"

    def cargar_datos(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.datos_crudos_tree.clear()
            
        id_user = self.usuario_sel["id"]
        acc_sel = self.combo_accion.get()
        desde_str = self.entry_desde.get_date_str()
        hasta_str = self.entry_hasta.get_date_str()
        
        # Mapear grupo seleccionado a lista de acciones técnicas (o None para todas)
        acciones_del_grupo = GRUPOS_ACCIONES.get(acc_sel, [])
        # Para el backend, si el grupo tiene una sola acción la pasamos directo;
        # si tiene varias, filtramos client-side después de traer todos los registros.
        accion_tecnica = acciones_del_grupo[0] if len(acciones_del_grupo) == 1 else None
            
        try:
            fecha_desde = self.validar_y_convertir_fecha(desde_str)
            fecha_hasta = self.validar_y_convertir_fecha(hasta_str)
            
            if fecha_desde and fecha_hasta:
                if fecha_desde > fecha_hasta:
                    messagebox.showwarning("Fechas Inválidas", "La fecha 'Desde' no puede ser mayor que 'Hasta'.", parent=self.win)
                    return
        except ValueError as ve:
            messagebox.showwarning("Error de Formato", str(ve), parent=self.win)
            return
            
        try:
            limit = self.pag_size
            offset = self.pag_aud * self.pag_size
            self.total_aud = self.backend.contar_bitacora_acciones(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, id_usuario=id_user, accion=accion_tecnica)
            registros = self.backend.obtener_bitacora_acciones(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, id_usuario=id_user, accion=accion_tecnica, limit=limit, offset=offset)
            
            # Filtro client-side para grupos con múltiples acciones
            acciones_del_grupo = GRUPOS_ACCIONES.get(acc_sel, [])
            if len(acciones_del_grupo) > 1:
                registros = [r for r in registros if r.get('accion') in acciones_del_grupo]
            
            for r in registros:
                fecha = str(r.get('fecha'))[:16] # "2024-01-01 15:30"
                usr = r.get('usuario_nombre') or 'Sistema'
                acc = r.get('accion') or 'Desconocida'
                tabla = r.get('tabla_afectada') or ''
                id_reg = r.get('id_registro') or ''
                entidad = self.resolver_entidad(tabla, id_reg) if id_reg else tabla
                
                acc_amigable = MAPEO_ACCIONES.get(acc, acc)
                resumen = self.procesar_resumen(acc, r.get('datos_anteriores'), r.get('datos_nuevos'))
                
                resumen_corto = resumen
                if len(resumen) > 60:
                    resumen_corto = resumen[:57] + "..."
                
                tag = self.determinar_tag_accion(acc)
                
                item_id = self.tree.insert("", tk.END, values=(fecha, usr, acc_amigable, entidad, resumen_corto), tags=(tag,))
                
                # Guardamos los datos crudos para el doble clic
                self.datos_crudos_tree[item_id] = {
                    "fecha": fecha,
                    "usuario": usr,
                    "accion": acc_amigable,
                    "accion_raw": acc,  # código técnico para generar detalle
                    "entidad": entidad,
                    "datos_anteriores": r.get('datos_anteriores'),
                    "datos_nuevos": r.get('datos_nuevos')
                }
                
            if hasattr(self, 'lbl_pag_aud'):
                tot_pages = max(1, (self.total_aud + self.pag_size - 1) // self.pag_size)
                self.lbl_pag_aud.configure(text=f"Página {self.pag_aud + 1} de {tot_pages} ({self.total_aud} registros)")
                
        except Exception as e:
            logger.error(f"Error cargar_datos auditoria: {e}")
            messagebox.showerror("Error", f"Ocurrió un error al cargar datos:\n{e}", parent=self.win)

    def _prev_page_aud(self):
        if self.pag_aud > 0:
            self.pag_aud -= 1
            self.cargar_datos()
            
    def _next_page_aud(self):
        tot_pages = max(1, (self.total_aud + self.pag_size - 1) // self.pag_size)
        if self.pag_aud < tot_pages - 1:
            self.pag_aud += 1
            self.cargar_datos()

    def mostrar_detalle_evento(self, event):
        item_id = self.tree.focus()
        if not item_id: return
        
        datos = self.datos_crudos_tree.get(item_id)
        if not datos: return
        
        modal = ctk.CTkToplevel(self.win)
        preparar_ventana(modal)
        modal.title("Detalle del Evento")
        modal.geometry("500x500")
        modal.transient(self.win)
        centrar_y_mostrar_ventana(modal)
        modal.grab_set()
        
        ctk.CTkLabel(modal, text="🔍 Detalle Completo", font=("Segoe UI", 18, "bold"), text_color=self.col_text).pack(pady=10)
        
        frame_info = ctk.CTkFrame(modal, fg_color="transparent")
        frame_info.pack(fill="x", padx=20, pady=5)
        
        def add_info_row(parent, label, value):
            r = ctk.CTkFrame(parent, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=label, font=("Segoe UI", 12, "bold"), width=80, anchor="w", text_color=self.col_text).pack(side="left")
            ctk.CTkLabel(r, text=value, font=("Segoe UI", 12), anchor="w", justify="left", text_color=self.col_text).pack(side="left", fill="x", expand=True)

        add_info_row(frame_info, "Evento:", datos["accion"])
        add_info_row(frame_info, "Usuario:", datos["usuario"])
        add_info_row(frame_info, "Fecha:", datos["fecha"])
        add_info_row(frame_info, "Entidad:", datos["entidad"])
        
        ctk.CTkLabel(modal, text="📋 Detalle de la acción:", font=("Segoe UI", 14, "bold"), anchor="w", text_color=self.col_text).pack(fill="x", padx=20, pady=(15, 5))

        txt_cambios = ctk.CTkTextbox(modal, font=("Segoe UI", 13), fg_color=self.col_card, text_color=self.col_text, border_color=self.col_border, border_width=1)
        txt_cambios.pack(fill="both", expand=True, padx=20, pady=5)

        try:
            d_ant = json.loads(datos["datos_anteriores"]) if datos["datos_anteriores"] else {}
            d_nue = json.loads(datos["datos_nuevos"]) if datos["datos_nuevos"] else {}
            accion_raw = datos.get("accion_raw", "")
            fecha_evento = datos.get("fecha", "")
            entidad_evento = datos.get("entidad", "")
            texto = self._generar_texto_detalle(accion_raw, d_ant, d_nue, fecha_evento, entidad_evento)
            txt_cambios.insert("1.0", texto)
        except Exception as e:
            txt_cambios.insert("1.0", f"Error al procesar los detalles: {e}")

        txt_cambios.configure(state="disabled")

        ctk.CTkButton(modal, text="Cerrar", command=modal.destroy, fg_color="#4b5563", hover_color="#374151", width=100).pack(pady=15)
            
    def _generar_texto_detalle(self, accion_raw: str, d_ant: dict, d_nue: dict,
                               fecha_evento: str = "", entidad_evento: str = "") -> str:
        """Genera texto narrativo en lenguaje claro para el popup de detalle de la Bitácora."""
        _map_roles = {1: 'Administrador', 2: 'Vendedor', 3: 'Supervisor'}
        map_u = {u.get('id_usuario'): u.get('nombre') for u in getattr(self, 'usuarios_raw', [])}

        def fmt_m(v):
            try: return f"${float(v):,.2f}"
            except: return str(v) if v is not None else "—"

        def fmt_u(uid):
            try: return map_u.get(int(uid), f"Usuario #{uid}")
            except: return str(uid) if uid else "—"

        def fmt_r(rid):
            try: return _map_roles.get(int(rid), f"Rol #{rid}")
            except: return str(rid) if rid else "—"

        def res_caja(id_caja):
            if not id_caja or str(id_caja) == '?': return "—"
            try:
                sess = self.backend.obtener_session_por_id(int(id_caja))
                if sess:
                    if sess.get('tipo_caja') == 'administrativa': return "Tesorería"
                    id_u = sess.get('id_usuario')
                    if id_u:
                        n = map_u.get(id_u)
                        if n: return f"Caja de {n}"
                return f"Caja #{id_caja}"
            except: return f"Caja #{id_caja}"

        L = []

        # ── USUARIOS ──────────────────────────────────────────────────────────
        if accion_raw == "CREAR_USUARIO":
            nombre = d_nue.get('nombre', '—')
            rol = fmt_r(d_nue.get('id_rol'))
            L += [f"Se creó el usuario «{nombre}» con el rol de {rol}.", "",
                  f"  Nombre de usuario:  {nombre}",
                  f"  Rol asignado:       {rol}"]

        elif accion_raw == "DESACTIVAR_USUARIO":
            nombre = d_ant.get('nombre', d_nue.get('nombre', '—'))
            L += [f"El usuario «{nombre}» fue desactivado.", "",
                  "  ⚠️  Este usuario no puede iniciar sesión hasta que sea reactivado."]

        elif accion_raw == "REACTIVAR_USUARIO":
            nombre = d_nue.get('nombre', d_ant.get('nombre', '—'))
            L += [f"El usuario «{nombre}» fue reactivado.", "",
                  "  ✅  El usuario puede volver a iniciar sesión con normalidad."]

        elif accion_raw == "RESETEAR_PASSWORD":
            # El nombre viene del campo entidad (ej: "Usuario: valentina") porque el JSON
            # no siempre almacena el nombre directamente
            nombre = d_nue.get('nombre', d_ant.get('nombre', ''))
            if not nombre or nombre == '—':
                # Extraer de entidad_evento: "Usuario: valentina" → "valentina"
                if ':' in entidad_evento:
                    nombre = entidad_evento.split(':', 1)[-1].strip()
                else:
                    nombre = entidad_evento.strip() or '—'
            L += [f"La contraseña del usuario «{nombre}» fue restablecida por un administrador.", "",
                  "  🔑  El usuario debe usar la nueva contraseña la próxima vez que inicie sesión."]

        elif accion_raw == "MODIFICAR_USUARIO":
            nombre = d_nue.get('nombre', d_ant.get('nombre', '—'))
            L += [f"Se modificaron datos del usuario «{nombre}».", ""]
            for k, label in [('nombre', 'Nombre'), ('id_rol', 'Rol')]:
                v_a, v_n = d_ant.get(k), d_nue.get(k)
                if v_a is not None and v_n is not None and str(v_a) != str(v_n):
                    if k == 'id_rol':
                        v_a, v_n = fmt_r(v_a), fmt_r(v_n)
                    L.append(f"  {label}: {v_a}  →  {v_n}")
            if len(L) == 2:
                L.append("  (Sin cambios detectados en los campos registrados)")

        # ── PRODUCTOS ─────────────────────────────────────────────────────────
        elif accion_raw == "CREAR_PRODUCTO":
            nombre = d_nue.get('nombre', '—')
            precio = fmt_m(d_nue.get('precio_venta', d_nue.get('precio', 0)))
            stock_min = d_nue.get('stock_minimo', '—')
            L += [f"Se creó el producto «{nombre}».", "",
                  f"  Precio de venta:  {precio}",
                  f"  Stock mínimo:     {stock_min}"]

        elif accion_raw == "MODIFICAR_PRODUCTO":
            nombre = d_nue.get('nombre', d_ant.get('nombre', '—'))
            L += [f"Se modificaron datos del producto «{nombre}».", ""]
            for k, label in [('nombre','Nombre'),('precio_venta','Precio de venta'),('stock_minimo','Stock mínimo')]:
                v_a, v_n = d_ant.get(k), d_nue.get(k)
                if v_a is not None and v_n is not None and str(v_a) != str(v_n):
                    L.append(f"  {label}: {fmt_m(v_a)}  →  {fmt_m(v_n)}" if k == 'precio_venta' else f"  {label}: {v_a}  →  {v_n}")
            if len(L) == 2:
                L.append("  (Sin cambios detectados en los campos registrados)")

        elif accion_raw == "DESACTIVAR_PRODUCTO":
            nombre = d_ant.get('nombre', d_nue.get('nombre', '—'))
            L += [f"El producto «{nombre}» fue dado de baja del sistema.", "",
                  "  ⚠️  El producto no aparecerá más en el punto de venta ni en búsquedas."]

        elif accion_raw == "AJUSTE_STOCK_MANUAL":
            cant_ant = d_ant.get('stock', d_ant.get('cantidad', '—'))
            cant_nue = d_nue.get('stock', d_nue.get('cantidad', '—'))
            id_prod = d_nue.get('id_producto')
            nombre_prod = "—"
            if id_prod:
                try:
                    prod = self.backend.buscar_producto_por_id(int(id_prod))
                    if prod and prod.get("nombre"): nombre_prod = prod["nombre"]
                except: pass
            try:
                diff = int(cant_nue) - int(cant_ant)
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                diff_label = "⬆️  Ingreso de mercadería" if diff > 0 else "⬇️  Retiro o corrección de stock"
            except:
                diff_str, diff_label = "—", ""
            L += [f"Se ajustó el stock del producto «{nombre_prod}».", "",
                  f"  Stock anterior:  {cant_ant}",
                  f"  Stock nuevo:     {cant_nue}",
                  f"  Diferencia:      {diff_str}  {diff_label}"]

        # ── CLIENTES ──────────────────────────────────────────────────────────
        elif accion_raw == "CREAR_CLIENTE":
            nombre = d_nue.get('nombre', '—')
            limite = fmt_m(d_nue.get('limite_credito', 0))
            L += [f"Se registró el cliente «{nombre}».", "",
                  f"  Nombre:              {nombre}",
                  f"  Límite de crédito:   {limite}"]

        elif accion_raw == "MODIFICAR_LIMITE_CREDITO_CLIENTE":
            o = fmt_m(d_ant.get('limite_credito', 0))
            n = fmt_m(d_nue.get('limite_credito', 0))
            L += ["Se modificó el límite de crédito del cliente.", "",
                  f"  Límite anterior:  {o}",
                  f"  Límite nuevo:     {n}"]

        elif accion_raw == "DESACTIVAR_CLIENTE":
            nombre = d_ant.get('nombre', d_nue.get('nombre', '—'))
            L += [f"El cliente «{nombre}» fue desactivado.", "",
                  "  ⚠️  El cliente no puede comprar en cuenta corriente mientras esté inactivo."]

        elif accion_raw == "REACTIVAR_CLIENTE":
            nombre = d_nue.get('nombre', d_ant.get('nombre', '—'))
            L += [f"El cliente «{nombre}» fue reactivado.", "",
                  "  ✅  El cliente puede operar con normalidad."]

        # ── PROVEEDORES ───────────────────────────────────────────────────────
        elif accion_raw == "CREAR_PROVEEDOR":
            nombre = d_nue.get('nombre', '—')
            empresa = d_nue.get('empresa', '')
            L += [f"Se dio de alta al proveedor «{nombre}».", "",
                  f"  Nombre de contacto:  {nombre}"]
            if empresa: L.append(f"  Empresa:             {empresa}")

        elif accion_raw == "DESACTIVAR_PROVEEDOR":
            nombre = d_ant.get('nombre', d_nue.get('nombre', '—'))
            L += [f"El proveedor «{nombre}» fue desactivado.", "",
                  "  ⚠️  No aparece disponible para nuevas compras."]

        elif accion_raw == "REACTIVAR_PROVEEDOR":
            nombre = d_nue.get('nombre', d_ant.get('nombre', '—'))
            L += [f"El proveedor «{nombre}» fue reactivado.", "",
                  "  ✅  El proveedor puede volver a utilizarse para nuevas compras."]

        elif accion_raw == "EDITAR_PROVEEDOR":
            nombre = d_ant.get('nombre', d_nue.get('nombre', '—'))
            L += [f"Se modificaron datos del proveedor «{nombre}».", ""]
            for k, label in [('nombre','Nombre'),('empresa','Empresa'),('telefono','Teléfono'),('email','Email'),('direccion','Dirección')]:
                v_a, v_n = d_ant.get(k), d_nue.get(k)
                if v_a is not None and v_n is not None and str(v_a) != str(v_n):
                    L.append(f"  {label}: {v_a}  →  {v_n}")
            if len(L) == 2: L.append("  (Sin cambios detectados en los campos registrados)")

        # ── CATEGORÍAS ────────────────────────────────────────────────────────
        elif accion_raw == "DESACTIVAR_CATEGORIA":
            nombre = d_ant.get('nombre', d_nue.get('nombre', '—'))
            L += [f"La categoría «{nombre}» fue desactivada.", "",
                  "  ⚠️  Los productos de esta categoría siguen activos."]

        elif accion_raw == "REACTIVAR_CATEGORIA":
            nombre = d_nue.get('nombre', d_ant.get('nombre', '—'))
            L += [f"La categoría «{nombre}» fue reactivada."]

        # ── CAJA ──────────────────────────────────────────────────────────────
        elif accion_raw == "APERTURA_CAJA":
            monto = fmt_m(d_nue.get('monto_inicial', d_nue.get('monto', 0)))
            abierto_por = fmt_u(d_nue.get('abierto_por', d_nue.get('id_usuario')))
            L += ["Se abrió una caja de turno.", "",
                  f"  Fondo inicial:  {monto}",
                  f"  Abierto por:    {abierto_por}"]

        elif accion_raw in ("CIERRE_CAJA", "CIERRE_CAJA_SUPERVISOR"):
            diferencia = d_nue.get('diferencia')
            contado = d_nue.get('contado', d_nue.get('efectivo_contado'))
            esperado = d_nue.get('esperado', d_nue.get('efectivo_esperado'))
            cerrado_por = fmt_u(d_nue.get('cerrado_por'))
            motivo_cierre = d_nue.get('motivo', '')
            encabezado = "⚠️  Caja cerrada de forma forzada por el supervisor." if accion_raw == "CIERRE_CAJA_SUPERVISOR" else "Se cerró la caja del turno."
            L += [encabezado, ""]
            if esperado is not None: L.append(f"  Efectivo esperado:  {fmt_m(esperado)}")
            if contado is not None:  L.append(f"  Efectivo contado:   {fmt_m(contado)}")
            if diferencia is not None:
                dif_f = float(diferencia)
                estado = "✅ Sin diferencia" if dif_f == 0 else (f"⬆️ Sobrante de {fmt_m(abs(dif_f))}" if dif_f > 0 else f"⬇️ Faltante de {fmt_m(abs(dif_f))}")
                L.append(f"  Diferencia:         {fmt_m(diferencia)}  ({estado})")
            if cerrado_por and cerrado_por != "—":
                L += ["", f"  Cerrado por:  {cerrado_por}"]
            if motivo_cierre:
                L.append(f"  Motivo:       {motivo_cierre}")

        # ── VENTAS / COMPRAS ──────────────────────────────────────────────────
        elif accion_raw == "ANULAR_VENTA":
            motivo = d_nue.get('motivo', 'Sin especificar')
            autorizado = fmt_u(d_nue.get('autorizado_por', d_nue.get('id_usuario')))
            # Formatear la fecha del evento para que sea legible
            fecha_legible = fecha_evento
            try:
                dt = datetime.strptime(fecha_evento, "%Y-%m-%d %H:%M")
                fecha_legible = dt.strftime("%d/%m/%Y a las %H:%M")
            except Exception:
                pass
            L += [f"Se anuló una venta realizada el {fecha_legible}.", "",
                  f"  Motivo:          {motivo}",
                  f"  Autorizado por:  {autorizado}",
                  "",
                  "  ℹ️  Podés encontrar esta operación en el Historial de Ventas",
                  "      filtrando por esa fecha y hora.",
                  "  ℹ️  El stock de los productos fue repuesto automáticamente."]

        elif accion_raw == "ANULAR_COMPRA":
            motivo = d_nue.get('motivo', 'Sin especificar')
            autorizado = fmt_u(d_nue.get('autorizado_por', d_nue.get('id_usuario')))
            fecha_legible = fecha_evento
            try:
                dt = datetime.strptime(fecha_evento, "%Y-%m-%d %H:%M")
                fecha_legible = dt.strftime("%d/%m/%Y a las %H:%M")
            except Exception:
                pass
            L += [f"Se anuló una compra registrada el {fecha_legible}.", "",
                  f"  Motivo:          {motivo}",
                  f"  Autorizado por:  {autorizado}",
                  "",
                  "  ℹ️  Podés encontrar esta operación en el Historial de Compras",
                  "      filtrando por esa fecha y hora."]

        # ── TRANSFERENCIAS / TESORERÍA ────────────────────────────────────────
        elif accion_raw in ("TRANSFERENCIA_CAJA", "TRANSFERENCIA_TESORERIA", "APROBACION_TRANSFERENCIA"):
            monto = fmt_m(d_nue.get('monto', 0))
            origen = res_caja(d_nue.get('origen', d_nue.get('id_session_origen')))
            destino = res_caja(d_nue.get('destino', d_nue.get('id_session_destino')))
            autorizado = fmt_u(d_nue.get('autorizado_por', d_nue.get('id_autorizador')))
            concepto = d_nue.get('concepto', d_nue.get('descripcion', ''))
            encabezado = {
                "APROBACION_TRANSFERENCIA": "Transferencia de dinero autorizada.",
                "TRANSFERENCIA_TESORERIA":  "Dinero transferido a la Tesorería del sistema.",
                "TRANSFERENCIA_CAJA":       "Transferencia de dinero entre cajas.",
            }.get(accion_raw, "Transferencia de dinero.")
            L += [encabezado, "",
                  f"  Origen:   {origen}",
                  f"  Destino:  {destino}",
                  f"  Monto:    {monto}"]
            if autorizado and autorizado != "—": L += ["", f"  Autorizado por:  {autorizado}"]
            if concepto: L.append(f"  Concepto:        {concepto}")

        elif accion_raw == "CREAR_TESORERIA_AUTOMATICA":
            L += ["El sistema creó automáticamente la Tesorería del día.", "",
                  "  ℹ️  Este proceso ocurre automáticamente al inicio de cada jornada operativa."]

        elif accion_raw == "EXPORTAR_HISTORIAL":
            L += ["Se exportó el historial de auditoría a un archivo CSV.", "",
                  "  ℹ️  La exportación fue realizada desde la Bitácora del sistema."]

        else:
            L += ["Acción registrada en el sistema.", ""]
            campos_mostrados = 0
            for k, v in d_nue.items():
                if v is not None and str(v).strip():
                    L.append(f"  {k.replace('_',' ').capitalize()}: {v}")
                    campos_mostrados += 1
            if campos_mostrados == 0:
                L.append("  (Sin detalles adicionales disponibles)")

        return "\n".join(L)

    def exportar_csv(self):
        id_user = self.usuario_sel["id"]
        acc_sel = self.combo_accion.get()
        desde_str = self.entry_desde.get_date_str()
        hasta_str = self.entry_hasta.get_date_str()
        
        accion_tecnica = None
        if acc_sel != "Todas":
            accion_tecnica = INV_MAPEO_ACCIONES.get(acc_sel, acc_sel)
            
        try:
            fecha_desde = self.validar_y_convertir_fecha(desde_str)
            fecha_hasta = self.validar_y_convertir_fecha(hasta_str)
        except ValueError as ve:
            messagebox.showwarning("Error de Formato", str(ve), parent=self.win)
            return

        filepath = filedialog.asksaveasfilename(
            parent=self.win,
            title="Exportar CSV Completo",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"auditoria_completa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not filepath: return
        
        def _do_export():
            try:
                registros = self.backend.obtener_bitacora_acciones(
                    fecha_desde=fecha_desde, 
                    fecha_hasta=fecha_hasta, 
                    id_usuario=id_user, 
                    accion=accion_tecnica,
                    limit=100000, # Maximos registros exportables de un golpe
                    offset=0
                )
                
                if not registros:
                    if self.win.winfo_exists():
                        self.win.after(0, lambda: messagebox.showinfo("Exportar", "No hay datos para exportar con los filtros actuales.", parent=self.win))
                    return

                with open(filepath, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Fecha", "Usuario", "Acción", "Entidad", "Resumen"])
                    
                    for r in registros:
                        fecha = str(r.get('fecha'))[:16]
                        usr = r.get('usuario_nombre') or 'Sistema'
                        acc = r.get('accion') or 'Desconocida'
                        tabla = r.get('tabla_afectada') or ''
                        id_reg = r.get('id_registro') or ''
                        entidad = self.resolver_entidad(tabla, id_reg) if id_reg else tabla
                        acc_amigable = MAPEO_ACCIONES.get(acc, acc)
                        resumen = self.procesar_resumen(acc, r.get('datos_anteriores'), r.get('datos_nuevos'))
                        writer.writerow([fecha, usr, acc_amigable, entidad, resumen])
                        
                if self.win.winfo_exists():
                    self.win.after(0, lambda: messagebox.showinfo("Éxito", "Exportación completada correctamente.", parent=self.win))
            except Exception as e:
                if self.win.winfo_exists():
                    self.win.after(0, lambda: messagebox.showerror("Error", f"Ocurrió un error al exportar:\n{e}", parent=self.win))

        import threading
        threading.Thread(target=_do_export, daemon=True).start()

def ui_auditoria(parent, backend, usuario_actual):
    InterfazAuditoria(parent, backend, usuario_actual)
