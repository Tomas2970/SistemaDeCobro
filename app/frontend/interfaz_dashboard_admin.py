# app/frontend/interfaz_dashboard_admin.py
import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import logging
from app.frontend.theme_config import get_color
from app.frontend import custom_dialogs as messagebox
from app.database.permisos import tiene_permiso
from app.frontend.validaciones_ui import registrar_validadores_teclado_ctk

logger = logging.getLogger(__name__)

# Configuración de límites (idealmente vendrían de la configuración general en BD)
LIMITE_EFECTIVO_CAJA = 100000.0

# Las operaciones de broadcast (enviar y obtener usuarios) se delegaron
# al BackendAdapter (backend.enviar_mensaje_broadcast / backend.obtener_usuarios_activos_para_broadcast)
# para respetar la arquitectura de capas. No hay conexiones directas a DB en este módulo.


# =========================================================
# IMPORTACIONES SEGURAS Y RUTEO
# =========================================================
def _safe_import(path, name):
    try:
        mod = __import__(path, fromlist=[name])
        return getattr(mod, name)
    except Exception:
        return None

ui_inventario        = _safe_import("app.frontend.interfaz_inventario", "ui_inventario")
ui_productos         = _safe_import("app.frontend.interfaz_productos", "ui_productos")
ui_reportes          = _safe_import("app.frontend.interfaz_reportes", "ui_reportes")
ui_gestion_clientes  = _safe_import("app.frontend.interfaz_gestion_clientes", "ui_gestion_clientes")
ui_gestion_proveedores = _safe_import("app.frontend.interfaz_gestion_proveedores", "ui_gestion_proveedores")
ui_historiales       = _safe_import("app.frontend.interfaz_historiales", "ui_historiales")
ui_gestion_usuarios  = _safe_import("app.frontend.interfaz_gestion_usuarios", "ui_gestion_usuarios")
ui_auditoria         = _safe_import("app.frontend.interfaz_auditoria", "ui_auditoria")
ui_tesoreria         = _safe_import("app.frontend.interfaz_tesoreria", "ui_tesoreria")
ui_compra            = _safe_import("app.frontend.interfaz_compra", "ui_compra")
ui_cuenta_corriente  = _safe_import("app.frontend.interfaz_cuenta_corriente", "ui_cuenta_corriente")
ui_categorias        = _safe_import("app.frontend.interfaz_categorias", "ui_categorias")

def _abrir_seguro(root, backend, usuario, fn, nombre, **kwargs):
    if not callable(fn):
        messagebox.mostrar_info("No disponible", f"La pantalla '{nombre}' no está integrada.", parent=root)
        return
        
    if not hasattr(root, '_ventanas_modulos'):
        root._ventanas_modulos = {}
        
    ventana_existente = root._ventanas_modulos.get(nombre)
    if ventana_existente and ventana_existente.winfo_exists():
        ventana_existente.lift()
        try: ventana_existente.focus_force()
        except Exception: pass
        return
        
    hijos_antes = set(root.winfo_children())

    try:
        try: fn(root, backend, usuario, **kwargs)
        except TypeError: fn(root, backend)
    except Exception as e:
        logger.exception(f"Error abriendo {nombre}")
        messagebox.mostrar_error("Error", f"Error al abrir {nombre}:\n{e}", parent=root)
        return

    import tkinter as tk
    import customtkinter as ctk
    hijos_despues = set(root.winfo_children())
    for hijo in (hijos_despues - hijos_antes):
        if isinstance(hijo, (tk.Toplevel, ctk.CTkToplevel)):
            try:
                hijo.transient(root)
            except Exception:
                pass
            root._ventanas_modulos[nombre] = hijo
            break

# =========================================================
# COMPONENTE NOTIFICACIÓN
# =========================================================
class ToastNotification:
    """Notificación Toast proactiva estilo material design."""
    def __init__(self, parent, titulo, mensaje, tipo="info"):
        self.toast = ctk.CTkToplevel(parent)
        self.toast.overrideredirect(True)
        self.toast.attributes("-topmost", True)
        
        # Colores por tipo
        colores = {
            "critico": "#ef4444", # Rojo
            "alerta": "#f59e0b",  # Naranja
            "info": "#3b82f6"     # Azul
        }
        bg_color = colores.get(tipo, colores["info"])
        
        self.toast.configure(fg_color=bg_color)
        
        ctk.CTkLabel(self.toast, text=titulo, font=("Segoe UI", 14, "bold"), text_color="white").pack(padx=15, pady=(10, 0), anchor="w")
        ctk.CTkLabel(self.toast, text=mensaje, font=("Segoe UI", 12), text_color="white", wraplength=250, justify="left").pack(padx=15, pady=(5, 10), anchor="w")
        
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        width = 300
        height = 90
        x = screen_width - width - 20
        y = screen_height - height - 80
        
        self.toast.geometry(f"{width}x{height}+{x}+{y}")
        self.toast.attributes("-alpha", 0.0)
        
        self.fade_in()
        self.toast.after(5000, self.fade_out)
        
    def fade_in(self):
        try:
            if self.toast.winfo_exists():
                alpha = self.toast.attributes("-alpha")
                if alpha < 0.95:
                    self.toast.attributes("-alpha", alpha + 0.1)
                    self.toast.after(30, self.fade_in)
        except Exception:
            pass
            
    def fade_out(self):
        try:
            if self.toast.winfo_exists():
                alpha = self.toast.attributes("-alpha")
                if alpha > 0.0:
                    self.toast.attributes("-alpha", alpha - 0.1)
                    self.toast.after(30, self.fade_out)
                else:
                    self.toast.destroy()
        except Exception:
            pass

# =========================================================
# CLASE PRINCIPAL DEL DASHBOARD ADMIN
# =========================================================
class InterfazDashboardAdmin:
    def __init__(self, parent, backend, usuario):
        self.parent = parent
        self.backend = backend
        self.usuario = usuario
        self.win = parent
        self._polling_job = None
        self.alertas_mostradas = set()
        self.crear_interfaz()

    def crear_interfaz(self):
        self.win.title("👑 Administrador Global - Panel de Control")
        try:
            self.win.state('zoomed')
        except Exception:
            self.win.geometry("1200x750")
            
        self.win.protocol("WM_DELETE_WINDOW", self.cerrar_sesion)
        
        bg_color = get_color("bg_surface") if ctk.get_appearance_mode() == "Light" else "#111827"
        self.win.configure(fg_color=bg_color)

        def on_main_focus(event):
            if event.widget == self.win:
                if hasattr(self.win, '_ventanas_modulos'):
                    for ventana in self.win._ventanas_modulos.values():
                        if ventana and ventana.winfo_exists():
                            ventana.lift()
                            try:
                                ventana.focus_force()
                            except Exception:
                                pass
        self.win.bind("<FocusIn>", on_main_focus)

        # ====== SIDEBAR ======
        color_sidebar = "#1e3a8a"
        sidebar = ctk.CTkFrame(self.win, width=260, fg_color=color_sidebar, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Empaquetamos el botón de cerrar sesión primero (side="bottom") para que siempre esté visible
        ctk.CTkButton(sidebar, text="⛔ Cerrar Sesión", fg_color="#ef4444", hover_color="#b91c1c", 
                      font=("Segoe UI", 13, "bold"), height=40, command=self.cerrar_sesion).pack(side="bottom", fill="x", padx=20, pady=20)

        ctk.CTkLabel(sidebar, text="👑", font=("Segoe UI", 60), text_color="white").pack(pady=(30, 0))
        ctk.CTkLabel(sidebar, text="Administrador Global", font=("Segoe UI", 16, "bold"), text_color="white").pack()
        ctk.CTkLabel(sidebar, text=f"👤 {self.usuario.get('nombre')}", font=("Segoe UI", 14), text_color="#bfdbfe").pack(pady=(5, 30))

        # Opciones del admin solicitadas (estilo supervisor, sin scrollbar)
        modulos = [
            ("🏦 Tesorería", 'ver_tesoreria', ui_tesoreria, {}),
            ("📦 Inventario", "ver_inventario", ui_inventario, {}),
            ("🛒 Registrar Compra", "registrar_compras", ui_compra, {}),
            ("📚 Cuenta Corriente", 'gestionar_cuenta_corriente', ui_cuenta_corriente, {}),
            ("👥 Clientes", 'ver_clientes', ui_gestion_clientes, {}),
            ("🚚 Proveedores", 'ver_proveedores', ui_gestion_proveedores, {}),
            ("🔖 Categorías", 'gestionar_categorias', ui_categorias, {}),
            ("📊 Reportes", 'ver_reportes', ui_reportes, {'modo_vista': 'reportes'}),
            ("🧾 Historiales", 'ver_ventas', ui_historiales, {}),
            ("⚙️ Usuarios", 'ver_usuarios', ui_gestion_usuarios, {}),
            ("🔒 Bitácora", 'ver_usuarios', ui_auditoria, {})
        ]

        for texto, permiso, fn, kw in modulos:
            if tiene_permiso(self.usuario, permiso):
                cmd = lambda t=texto, f=fn, k=kw: _abrir_seguro(self.win, self.backend, self.usuario, f, t, **k)
                ctk.CTkButton(sidebar, text=texto, fg_color="transparent", hover_color="#2563eb",
                              font=("Segoe UI", 13, "bold"), anchor="w", height=40, command=cmd).pack(fill="x", padx=10, pady=2)

        if self.usuario.get("id_rol") == 1:
            ctk.CTkFrame(sidebar, fg_color="#3b82f6", height=1).pack(fill="x", padx=20, pady=10)
            ctk.CTkButton(sidebar, text="💰 Ingreso de Capital", fg_color="#10b981", hover_color="#059669",
                          font=("Segoe UI", 13, "bold"), height=40, command=self._abrir_ingreso_capital).pack(fill="x", padx=10, pady=2)

        # ====== CONTENEDOR PRINCIPAL ======
        main_container = ctk.CTkFrame(self.win, fg_color="transparent")
        main_container.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # --- HEADER KPIs (Estilo Supervisor, idéntico espaciado y tarjetas) ---
        self.fr_kpis = ctk.CTkFrame(main_container, fg_color="transparent")
        self.fr_kpis.pack(fill="x", pady=(0, 20))
        
        for i in range(4): self.fr_kpis.grid_columnconfigure(i, weight=1)
        
        self.kpi_ventas_var = tk.StringVar(value="$0.00")
        self.kpi_efectivo_var = tk.StringVar(value="$0.00")
        self.kpi_tickets_var = tk.StringVar(value="0")
        self.kpi_cajas_var = tk.StringVar(value="0")
        
        def crear_tarjeta_kpi(parent_frame, col, titulo, var, color):
            card = ctk.CTkFrame(parent_frame, fg_color=get_color("bg_surface"), corner_radius=10, border_width=1, border_color="#e5e7eb" if ctk.get_appearance_mode()=="Light" else "#374151")
            card.grid(row=0, column=col, sticky="nsew", padx=5)
            ctk.CTkLabel(card, text=titulo, font=("Segoe UI", 13), text_color=get_color("text_secondary")).pack(pady=(15, 0))
            ctk.CTkLabel(card, textvariable=var, font=("Segoe UI", 22, "bold"), text_color=color).pack(pady=(5, 15))
        
        crear_tarjeta_kpi(self.fr_kpis, 0, "Ventas del Día", self.kpi_ventas_var, "#10b981")
        crear_tarjeta_kpi(self.fr_kpis, 1, "Efectivo Sucursal", self.kpi_efectivo_var, "#3b82f6")
        crear_tarjeta_kpi(self.fr_kpis, 2, "Tickets Emitidos", self.kpi_tickets_var, get_color("text_primary"))
        crear_tarjeta_kpi(self.fr_kpis, 3, "Cajas Activas", self.kpi_cajas_var, "#8b5cf6")

        # DOS COLUMNAS (60/40) para el resto del contenido
        content_container = ctk.CTkFrame(main_container, fg_color="transparent")
        content_container.pack(fill="both", expand=True)
        content_container.grid_columnconfigure(0, weight=6)
        content_container.grid_columnconfigure(1, weight=4)
        content_container.grid_rowconfigure(0, weight=1)
        
        # --- SECCIÓN IZQUIERDA: CAJAS ACTIVAS ---
        self.frm_cajas = ctk.CTkScrollableFrame(content_container, fg_color=get_color("bg_surface"), corner_radius=15, 
                                                border_color="#e2e8f0" if ctk.get_appearance_mode()=="Light" else "#1e293b", border_width=1)
        self.frm_cajas.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(self.frm_cajas, text="🏪 Cajas Activas Globales", font=("Segoe UI", 18, "bold"), text_color=get_color("text_primary")).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(self.frm_cajas, text="Monitoreo en tiempo real de operaciones y rendimiento", font=("Segoe UI", 12), text_color=get_color("text_secondary")).pack(anchor="w", padx=15, pady=(0, 15))
        
        self.container_tarjetas_cajas = ctk.CTkFrame(self.frm_cajas, fg_color="transparent")
        self.container_tarjetas_cajas.pack(fill="both", expand=True, padx=10)

        # --- SECCIÓN DERECHA: LIVE FEED Y ALERTAS ---
        self.frm_derecha = ctk.CTkFrame(content_container, fg_color=get_color("bg_surface"), corner_radius=15,
                                        border_color="#e2e8f0" if ctk.get_appearance_mode()=="Light" else "#1e293b", border_width=1)
        self.frm_derecha.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Header Derecho (Primero para que no sea empujado hacia abajo por las alertas)
        fr_header_feed = ctk.CTkFrame(self.frm_derecha, fg_color="transparent")
        fr_header_feed.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(fr_header_feed, text="🔴 Live Feed", font=("Segoe UI", 18, "bold"), text_color=get_color("text_primary")).pack(side="left")
        
        # Contenedor de Alertas del Dashboard (Debajo del header)
        self.container_alertas_admin = ctk.CTkFrame(self.frm_derecha, fg_color="transparent")
        self.container_alertas_admin.pack(fill="x", padx=10, pady=(0, 5))

        # --- FILTRO POR USUARIO ---
        self.var_filtro_usuario = tk.StringVar(value="Todos los usuarios")
        self.var_usuario_feed_id = tk.IntVar(value=0)
        
        self.combo_filtro_feed = ctk.CTkComboBox(
            fr_header_feed, 
            values=["Todos los usuarios", "Usuario específico"], 
            variable=self.var_filtro_usuario,
            state="readonly",
            width=180,
            command=self._on_filtro_usuario_changed
        )
        self.combo_filtro_feed.pack(side="right")
        
        self.fr_busqueda_usr_feed = ctk.CTkFrame(fr_header_feed, fg_color="transparent")
        
        self.lbl_usuario_feed = ctk.CTkLabel(self.fr_busqueda_usr_feed, text="(Todos)", font=("Segoe UI", 12), text_color=get_color("text_secondary"), anchor="w")
        self.lbl_usuario_feed.pack(side="left", padx=(0, 5))
        
        self.sel_usuario_feed = {"id": 0, "nombre": "(Todos)"}
        
        def _on_seleccionar_feed():
            self.var_usuario_feed_id.set(self.sel_usuario_feed["id"])
            self._actualizar_live_feed()
            
        def _abrir_buscador_feed():
            usuarios_activos_feed = []
            try:
                if hasattr(self.backend, "obtener_usuarios_actividad_hoy"):
                    usuarios_activos_feed = self.backend.obtener_usuarios_actividad_hoy()
            except Exception:
                pass
            self._abrir_selector_entidad("Usuario", self.sel_usuario_feed, usuarios_activos_feed, self.lbl_usuario_feed, _on_seleccionar_feed)
            
        btn_usuario_feed = ctk.CTkButton(self.fr_busqueda_usr_feed, text="🔍", width=35, height=30, fg_color="#3b82f6", command=_abrir_buscador_feed)
        btn_usuario_feed.pack(side="left")

        # Scroll del Live Feed
        self.scroll_feed = ctk.CTkScrollableFrame(self.frm_derecha, fg_color="transparent")
        self.scroll_feed.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Configuración de interfaz de Broadcast
        from tkinter import ttk
        try:
            from app.frontend.theme_config import configurar_estilo_treeview
            configurar_estilo_treeview()
        except: pass

        # Contenedor principal de zona de envío (vertical)
        fr_zona_envio = ctk.CTkFrame(self.frm_derecha, fg_color="transparent")
        fr_zona_envio.pack(fill="x", padx=15, pady=(5, 15))

        # 1. Selector de destinatario (Arriba)
        fr_selector = ctk.CTkFrame(fr_zona_envio, fg_color="transparent")
        fr_selector.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(fr_selector, text="Enviar a:", font=("Segoe UI", 12, "bold")).pack(side="left", pady=5, padx=(0, 10))
        
        var_destinatario = tk.StringVar(value="Todos")
        opciones_dest = ["Todos", "Solo Vendedores", "Solo Supervisores", "Usuario específico"]
        
        combo_destinatario = ctk.CTkComboBox(fr_selector, values=opciones_dest, variable=var_destinatario, state="readonly", width=200)
        combo_destinatario.pack(side="left")

        # Cargar usuarios activos para la búsqueda del selector de destinatario
        usuarios_activos = []
        try:
            admin_id = self.usuario.get("id_usuario", 0)
            usuarios_activos = self.backend.obtener_usuarios_activos_para_broadcast(excluir_id=admin_id)
        except Exception:
            pass


        # 2. Buscador de usuarios (Medio, oculto por defecto)
        fr_busqueda_usr = ctk.CTkFrame(fr_zona_envio, fg_color="transparent")
        var_usuario_seleccionado_id = tk.IntVar(value=0)
        
        lbl_usuario_broadcast = ctk.CTkLabel(fr_busqueda_usr, text="(Todos)", font=("Segoe UI", 12), text_color=get_color("text_secondary"), anchor="w")
        lbl_usuario_broadcast.pack(side="left", padx=(0, 5))
        
        sel_usuario_broadcast = {"id": 0, "nombre": "(Todos)"}
        
        def _on_seleccionar_broadcast():
            var_usuario_seleccionado_id.set(sel_usuario_broadcast["id"])
            
        btn_usuario_broadcast = ctk.CTkButton(fr_busqueda_usr, text="🔍", width=35, height=30, fg_color="#3b82f6", 
                                     command=lambda: self._abrir_selector_entidad("Usuario", sel_usuario_broadcast, usuarios_activos, lbl_usuario_broadcast, _on_seleccionar_broadcast))
        btn_usuario_broadcast.pack(side="left")

        # 3. Campo de texto y botón enviar (Abajo)
        fr_broadcast = ctk.CTkFrame(fr_zona_envio, fg_color="transparent")
        fr_broadcast.pack(side="top", fill="x")
        
        self.var_msg = tk.StringVar()
        entry_msg = ctk.CTkEntry(fr_broadcast, textvariable=self.var_msg, placeholder_text="Mensaje a transmitir...", font=("Segoe UI", 13), height=35)
        entry_msg.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        def _on_cambio_destinatario(valor):
            if valor == "Usuario específico":
                fr_busqueda_usr.pack(before=fr_broadcast, fill="x", pady=(0, 10))
            else:
                fr_busqueda_usr.pack_forget()
                var_usuario_seleccionado_id.set(0)
                sel_usuario_broadcast["id"] = 0
                sel_usuario_broadcast["nombre"] = "(Todos)"
                lbl_usuario_broadcast.configure(text="(Todos)")
                
        combo_destinatario.configure(command=_on_cambio_destinatario)
        
        def ev_enviar_broadcast(event=None):
            msg = self.var_msg.get().strip()
            if not msg: return
            admin_id = self.usuario.get("id_usuario", 0)
            
            dest_str = var_destinatario.get()
            destinatario_tipo = 'todos'
            destinatario_id = None
            
            if dest_str == "Solo Vendedores":
                destinatario_tipo = 'rol'
                destinatario_id = 2
            elif dest_str == "Solo Supervisores":
                destinatario_tipo = 'rol'
                destinatario_id = 3
            elif dest_str == "Usuario específico":
                destinatario_tipo = 'usuario'
                uid = var_usuario_seleccionado_id.get()
                if uid > 0:
                    destinatario_id = uid
                else:
                    messagebox.mostrar_error("Error", "Debe seleccionar un usuario específico de la lista.", parent=self.win)
                    return
                        
            if self.backend.enviar_mensaje_broadcast(msg, admin_id, destinatario_tipo, destinatario_id):
                ToastNotification(self.win, "📢 Broadcast Enviado", "El mensaje fue transmitido.", "info")
                self.var_msg.set("")
            else:
                messagebox.mostrar_error("Error", "No se pudo enviar el mensaje. Compruebe la conexión.", parent=self.win)
                
        btn_enviar = ctk.CTkButton(fr_broadcast, text="Enviar", width=80, height=35, font=("Segoe UI", 12, "bold"), fg_color="#10b981", hover_color="#059669", command=ev_enviar_broadcast)
        btn_enviar.pack(side="right")
        entry_msg.bind("<Return>", ev_enviar_broadcast)

        # Iniciar ciclo de actualización
        self.refresh_dashboard()
        self.win.deiconify()
        self.win.mainloop()
        
        # LIMPIEZA POST-SESIÓN (Evita el bug visual al volver al Login)
        if self.win.winfo_exists():
            for widget in self.win.winfo_children():
                try:
                    widget.destroy()
                except Exception:
                    pass

    # =========================================================
    # LÓGICA DE CONTROL Y EVENTOS
    # =========================================================
    def _abrir_ingreso_capital(self):
        
        dlg = ctk.CTkToplevel(self.win)
        dlg.title("💰 Ingreso de Capital")
        dlg.geometry("400x350")
        dlg.resizable(False, False)
        dlg.transient(self.win)
        dlg.grab_set()
        
        dlg.update_idletasks()
        x = self.win.winfo_x() + (self.win.winfo_width() - 400) // 2
        y = self.win.winfo_y() + (self.win.winfo_height() - 350) // 2
        dlg.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(dlg, text="Registrar Ingreso de Capital", font=("Segoe UI", 18, "bold")).pack(pady=(20, 10))
        ctk.CTkLabel(dlg, text="Este dinero ingresará a la tesorería del día.", font=("Segoe UI", 12), text_color="gray").pack(pady=(0, 20))
        
        frm_inputs = ctk.CTkFrame(dlg, fg_color="transparent")
        frm_inputs.pack(fill="x", padx=30)
        
        ctk.CTkLabel(frm_inputs, text="Monto ($):", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ent_monto = ctk.CTkEntry(frm_inputs, font=("Segoe UI", 14), placeholder_text="0.00")
        registrar_validadores_teclado_ctk(ent_monto, 'decimal', dlg)
        ent_monto.pack(fill="x", pady=(5, 15))
        
        ctk.CTkLabel(frm_inputs, text="Observación / Motivo:", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ent_obs = ctk.CTkEntry(frm_inputs, font=("Segoe UI", 14), placeholder_text="Ej: Aporte socio, Préstamo...")
        ent_obs.pack(fill="x", pady=(5, 20))
        
        def confirmar():
            monto_str = ent_monto.get().strip()
            obs = ent_obs.get().strip()
            
            try:
                monto = float(monto_str)
                if monto <= 0: raise ValueError
            except ValueError:
                messagebox.mostrar_error("Error", "El monto debe ser un número mayor a cero.", parent=dlg)
                return
                
            if not obs:
                messagebox.mostrar_error("Error", "La observación es obligatoria.", parent=dlg)
                return
                
            msg = f"¿Confirmas el ingreso de capital a la tesorería?\n\nMonto: ${monto:,.2f}\nMotivo: {obs}"
            if messagebox.mostrar_confirmacion("Confirmar Ingreso", msg, parent=dlg):
                try:
                    if hasattr(self.backend, 'registrar_ingreso_capital'):
                        exito = self.backend.registrar_ingreso_capital(monto, obs, self.usuario.get("id_usuario"))
                        if exito:
                            messagebox.mostrar_exito("Éxito", f"Se ha registrado el ingreso de ${monto:,.2f} correctamente.", parent=self.win)
                            self.refresh_dashboard()
                            dlg.destroy()
                    else:
                        messagebox.mostrar_error("Error", "Backend no implementa registrar_ingreso_capital.", parent=dlg)
                except Exception as e:
                    messagebox.mostrar_error("Error", f"No se pudo registrar el ingreso:\n{e}", parent=dlg)
                    
        frm_btns = ctk.CTkFrame(dlg, fg_color="transparent")
        frm_btns.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkButton(frm_btns, text="Cancelar", fg_color="#ef4444", hover_color="#dc2626", command=dlg.destroy).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(frm_btns, text="Confirmar", fg_color="#10b981", hover_color="#059669", command=confirmar).pack(side="right", expand=True, padx=(5, 0))

    def cerrar_sesion(self):
        if messagebox.mostrar_confirmacion("Cerrar Sesión", "¿Seguro que deseas salir del sistema?"):
            self.cerrar()

    def cerrar(self):
        if hasattr(self, '_polling_job') and self._polling_job:
            self.win.after_cancel(self._polling_job)
            self._polling_job = None
            
        try:
            from app.frontend.broadcast_manager import detener_polling_broadcast
            detener_polling_broadcast(self.win)
        except Exception:
            pass
            
        self.win.quit()

    def refresh_dashboard(self):
        self._actualizar_cajas_y_kpis()
        self._actualizar_live_feed()
        self._actualizar_alertas_dashboard()

        # Reencolar solo si la ventana sigue existiendo (evita TclError en cierre rápido)
        if self.win.winfo_exists():
            self._polling_job = self.win.after(10000, self.refresh_dashboard)

    def _actualizar_cajas_y_kpis(self):
        try:
            for widget in self.container_tarjetas_cajas.winfo_children():
                widget.destroy()
        except Exception:
            return
            
        try:
            if hasattr(self.backend, "obtener_sesiones_abiertas_con_totales"):
                sesiones = self.backend.obtener_sesiones_abiertas_con_totales()
            else:
                sesiones = []

            logger.debug("_actualizar_cajas_y_kpis ejecutado. Cajas encontradas: %d", len(sesiones))
            
            cajas_turno = [s for s in sesiones if s.get('tipo_caja') != 'administrativa']
            tesoreria = next((s for s in sesiones if s.get('tipo_caja') == 'administrativa'), None)

            self.kpi_cajas_var.set(str(len(cajas_turno)))
            ahora = datetime.now()

            if not cajas_turno:
                ctk.CTkLabel(self.container_tarjetas_cajas, text="No hay cajas de turno abiertas.",
                             font=("Segoe UI", 14, "italic"), text_color=get_color("text_secondary")).pack(pady=40)

            for s in cajas_turno:
                vendedor = s.get('vendedor', 'Desconocido')
                str_apertura = s.get('fecha_apertura', '---')
                monto = float(s.get('monto_acumulado', 0.0))
                ventas = int(s.get('cantidad_ventas', 0))
                id_session = s.get('id_session')
                
                # --- ALERTA PROACTIVA (Exceso de efectivo) ---
                if monto > LIMITE_EFECTIVO_CAJA:
                    alerta_id = f"efectivo_{id_session}_{monto}"
                    if alerta_id not in self.alertas_mostradas:
                        ToastNotification(self.win, "⚠️ Alerta Crítica - Efectivo", f"La Caja de {vendedor} excedió el límite seguro (${monto:,.2f}). Solicite un retiro.", "critico")
                        self.alertas_mostradas.add(alerta_id)
                
                # --- RENDERIZAR TARJETA DE CAJA ESTILO SUPERVISOR ---
                frm_card = ctk.CTkFrame(self.container_tarjetas_cajas, fg_color="#1e3a8a", corner_radius=10, 
                                        border_color="#d1d5db" if ctk.get_appearance_mode()=="Light" else "#475569", border_width=1)
                frm_card.pack(fill="x", pady=8, ipady=5)
                
                frm_header = ctk.CTkFrame(frm_card, fg_color="transparent")
                frm_header.pack(fill="x", padx=15, pady=(10, 5))
                
                ctk.CTkLabel(frm_header, text=f"👤 {vendedor}", font=("Segoe UI", 16, "bold"), text_color="#ffffff").pack(side="left")
                
                try:
                    if hasattr(str_apertura, 'strftime'):
                        texto_apertura = str_apertura.strftime('%d/%m/%Y %H:%M:%S')
                    else:
                        texto_apertura = datetime.strptime(str(str_apertura), "%Y-%m-%d %H:%M:%S").strftime('%d/%m/%Y %H:%M:%S')
                except Exception:
                    texto_apertura = str(str_apertura)
                ctk.CTkLabel(frm_header, text=f"Apertura: {texto_apertura}", font=("Segoe UI", 11), text_color="#ffffff").pack(side="right", padx=10)
                
                frm_body = ctk.CTkFrame(frm_card, fg_color="transparent")
                frm_body.pack(fill="x", padx=15, pady=(5, 10))
                
                frm_monto = ctk.CTkFrame(frm_body, fg_color="transparent")
                frm_monto.pack(side="left", fill="both", expand=True)
                ctk.CTkLabel(frm_monto, text="Efectivo en Caja", font=("Segoe UI", 11), text_color="#ffffff").pack()
                ctk.CTkLabel(frm_monto, text=f"${monto:,.2f}", font=("Segoe UI", 20, "bold"), text_color="#10b981").pack()
                
                frm_ventas = ctk.CTkFrame(frm_body, fg_color="transparent")
                frm_ventas.pack(side="left", fill="both", expand=True)
                ctk.CTkLabel(frm_ventas, text="Operaciones", font=("Segoe UI", 11), text_color="#ffffff").pack()
                ctk.CTkLabel(frm_ventas, text=f"{ventas}", font=("Segoe UI", 20, "bold"), text_color="#60a5fa").pack()
                
                frm_acciones_caja = ctk.CTkFrame(frm_body, fg_color="transparent")
                frm_acciones_caja.pack(side="right", fill="both", expand=False)
                
                def cmd_forzar_cierre(id_sess=id_session, vend=vendedor):
                    if messagebox.mostrar_confirmacion("⚠️ Forzar Cierre", f"¿Estás seguro que deseas cerrar forzosamente la caja de {vend}?\n\nEl sistema la marcará como cerrada y el usuario no podrá realizar más ventas hasta que abra una caja nueva.", parent=self.win):
                        if hasattr(self.backend, "cerrar_caja_por_supervisor"):
                            exito = self.backend.cerrar_caja_por_supervisor(id_sess, self.usuario.get('id_usuario'), "Cierre Forzado por Administrador")
                            if exito:
                                messagebox.mostrar_exito("Éxito", f"La caja de {vend} ha sido cerrada.", parent=self.win)
                                self.refresh_dashboard()
                            else:
                                messagebox.mostrar_error("Error", "No se pudo cerrar la caja.", parent=self.win)
                        else:
                            messagebox.mostrar_error("Error", "Función no disponible en el backend.", parent=self.win)

                ctk.CTkButton(frm_acciones_caja, text="⛔ Forzar Cierre", font=("Segoe UI", 12, "bold"), 
                              fg_color="#ef4444", hover_color="#b91c1c", width=110, height=35, 
                              command=cmd_forzar_cierre).pack(side="right", pady=5)

            # --- RENDERIZAR TESORERÍA APARTE ---
            if tesoreria:
                ctk.CTkFrame(self.container_tarjetas_cajas, height=2, fg_color="#cbd5e1" if ctk.get_appearance_mode()=="Light" else "#334155").pack(fill="x", pady=20, padx=20)
                ctk.CTkLabel(self.container_tarjetas_cajas, text="🏦 Tesorería del Día", font=("Segoe UI", 16, "bold"), text_color=get_color("text_primary")).pack(pady=(0, 10))
                
                frm_tes_card = ctk.CTkFrame(self.container_tarjetas_cajas, fg_color="#10b981", corner_radius=10)
                frm_tes_card.pack(fill="x", pady=8, ipady=5)
                
                monto_tes = float(tesoreria.get('monto_acumulado', 0.0))
                str_apertura_tes = tesoreria.get('fecha_apertura', '---')
                try:
                    if hasattr(str_apertura_tes, 'strftime'):
                        txt_ap_tes = str_apertura_tes.strftime('%d/%m/%Y')
                    else:
                        txt_ap_tes = datetime.strptime(str(str_apertura_tes), "%Y-%m-%d %H:%M:%S").strftime('%d/%m/%Y')
                except Exception:
                    txt_ap_tes = str(str_apertura_tes)

                frm_tes_head = ctk.CTkFrame(frm_tes_card, fg_color="transparent")
                frm_tes_head.pack(fill="x", padx=15, pady=(10, 5))
                ctk.CTkLabel(frm_tes_head, text="Fondo Común Administrativo", font=("Segoe UI", 16, "bold"), text_color="#ffffff").pack(side="left")
                ctk.CTkLabel(frm_tes_head, text=f"Día: {txt_ap_tes}", font=("Segoe UI", 11), text_color="#ffffff").pack(side="right", padx=10)
                
                frm_tes_body = ctk.CTkFrame(frm_tes_card, fg_color="transparent")
                frm_tes_body.pack(fill="x", padx=15, pady=(5, 10))
                ctk.CTkLabel(frm_tes_body, text="Saldo Disponible", font=("Segoe UI", 11), text_color="#ffffff").pack()
                ctk.CTkLabel(frm_tes_body, text=f"${monto_tes:,.2f}", font=("Segoe UI", 24, "bold"), text_color="#ffffff").pack()

            # 2. ACTUALIZAR KPIs
            if hasattr(self.backend, "obtener_kpis_admin"):
                kpis = self.backend.obtener_kpis_admin()
                self.kpi_ventas_var.set(f"${kpis.get('ventas_dia', 0):,.2f}")
                self.kpi_efectivo_var.set(f"${kpis.get('efectivo_total', 0):,.2f}")
                self.kpi_tickets_var.set(str(kpis.get('tickets', 0)))
            else:
                self.kpi_ventas_var.set("$0.00")
                self.kpi_efectivo_var.set("$0.00")
                self.kpi_tickets_var.set("0")
                
        except Exception as e:
            logger.error(f"Error actualizando cajas de admin: {e}")

    def _on_filtro_usuario_changed(self, valor):
        if valor == "Usuario específico":
            self.fr_busqueda_usr_feed.pack(side="right", before=self.combo_filtro_feed, padx=(0, 10))
            if self.var_usuario_feed_id.get() > 0:
                self._actualizar_live_feed()
        else:
            self.fr_busqueda_usr_feed.pack_forget()
            self.var_usuario_feed_id.set(0)
            if hasattr(self, 'sel_usuario_feed'):
                self.sel_usuario_feed = {"id": 0, "nombre": "(Todos)"}
            if hasattr(self, 'lbl_usuario_feed'):
                self.lbl_usuario_feed.configure(text="(Todos)")
            self._actualizar_live_feed()

    def _actualizar_live_feed(self):
        id_usuario_filtro = None
        if self.var_filtro_usuario.get() == "Usuario específico":
            uid = self.var_usuario_feed_id.get()
            if uid > 0:
                id_usuario_filtro = uid

        try:
            for widget in self.scroll_feed.winfo_children():
                widget.destroy()
        except Exception:
            return
            
        if hasattr(self.backend, "obtener_feed_eventos"):
            try:
                eventos = self.backend.obtener_feed_eventos(limit=30, id_usuario=id_usuario_filtro)
            except TypeError:
                eventos = self.backend.obtener_feed_eventos(limit=30)
                
            for ev in eventos:
                self._agregar_evento_feed(ev)
                
            if not eventos and id_usuario_filtro is not None:
                self._agregar_evento_feed({"tipo": "info", "mensaje": f"No hay actividad reciente para {sel}.", "hora": "--:--"})
        else:
            try:
                if len(self.scroll_feed.winfo_children()) == 0:
                    self._agregar_evento_feed({"tipo": "caja", "mensaje": "Esperando conexión con log de eventos...", "hora": "--:--"})
            except Exception:
                pass

    def _agregar_evento_feed(self, evento):
        tipo = evento.get("tipo", "info")
        mensaje = evento.get("mensaje", "")
        hora = evento.get("hora", datetime.now().strftime("%H:%M"))
        
        colores = {
            "venta_grande": ("#10b981", "🟢"),
            "retiro":       ("#f59e0b", "🟠"),
            "error":        ("#ef4444", "🔴"),
            "caja":         ("#3b82f6", "🔵"),
            "info":         (get_color("text_primary"), "⚪")
        }
        color_texto, icono = colores.get(tipo, colores["info"])
        
        fr_ev = ctk.CTkFrame(self.scroll_feed, fg_color="transparent")
        fr_ev.pack(fill="x", pady=4)
        
        ctk.CTkLabel(fr_ev, text=hora, font=("Segoe UI", 11), text_color=get_color("text_secondary"), width=40).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(fr_ev, text=f"{icono} {mensaje}", font=("Segoe UI", 13), text_color=color_texto, wraplength=260, justify="left").pack(side="left", fill="x", expand=True)

    def _actualizar_alertas_dashboard(self):
        try:
            for widget in self.container_alertas_admin.winfo_children():
                widget.destroy()
        except Exception:
            return
            
        def crear_alerta(icono, texto, color_bg, color_fg, on_double_click=None):
            f = ctk.CTkFrame(self.container_alertas_admin, fg_color=color_bg, corner_radius=8)
            f.pack(fill="x", pady=4, padx=5)
            lbl_ico = ctk.CTkLabel(f, text=icono, font=("Segoe UI", 16))
            lbl_ico.pack(side="left", padx=10, pady=10)
            lbl_txt = ctk.CTkLabel(f, text=texto, font=("Segoe UI", 12, "bold"), text_color=color_fg, wraplength=280, justify="left")
            lbl_txt.pack(side="left", padx=(0, 10), pady=10)
            
            if on_double_click:
                f.bind("<Double-Button-1>", on_double_click)
                lbl_ico.bind("<Double-Button-1>", on_double_click)
                lbl_txt.bind("<Double-Button-1>", on_double_click)
                f.configure(cursor="hand2")
                lbl_ico.configure(cursor="hand2")
                lbl_txt.configure(cursor="hand2")
                
        try:
            if hasattr(self.backend, "obtener_stock_bajo"):
                stock_bajo = self.backend.obtener_stock_bajo()
                if stock_bajo:
                    def cmd_stock(e):
                        _abrir_seguro(self.win, self.backend, self.usuario, ui_inventario, "Inventario", filtro_stock_bajo=True)
                    crear_alerta("⚠️", f"{len(stock_bajo)} productos con stock crítico.", "#fef2f2" if ctk.get_appearance_mode()=="Light" else "#7f1d1d", "#dc2626" if ctk.get_appearance_mode()=="Light" else "#fca5a5", on_double_click=cmd_stock)
        except Exception as e:
            logger.error(f"Error cargando alertas dashboard admin (stock): {e}")

        try:
            if hasattr(self.backend, "obtener_clientes_con_deuda"):
                clientes_deuda = self.backend.obtener_clientes_con_deuda()
                if clientes_deuda:
                    def cmd_deuda(e):
                        _abrir_seguro(self.win, self.backend, self.usuario, ui_gestion_clientes, "Clientes")
                    crear_alerta("💳", f"{len(clientes_deuda)} clientes con deuda activa.", "#fffbeb" if ctk.get_appearance_mode()=="Light" else "#78350f", "#d97706" if ctk.get_appearance_mode()=="Light" else "#fcd34d", on_double_click=cmd_deuda)
        except Exception as e:
            logger.error(f"Error cargando alertas dashboard admin (deuda): {e}")

    def _abrir_selector_entidad(self, tipo: str, var_seleccion: dict, lista_datos: list, label_update: ctk.CTkLabel, on_select_callback=None):
        popup = ctk.CTkToplevel(self.win)
        try:
            from app.frontend.theme_config import preparar_ventana, centrar_y_mostrar_ventana
            preparar_ventana(popup)
        except:
            pass
        
        popup.title(f"Seleccionar {tipo}")
        popup.geometry("500x550")
        
        try:
            from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
            configurar_navegacion_ventana(popup)
        except:
            pass

        var_pat = tk.StringVar()
        ctk.CTkLabel(popup, text=f"Buscar {tipo} (ID/Nombre):", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).pack(pady=(15,5), padx=15, anchor="w")
        ent = ctk.CTkEntry(popup, textvariable=var_pat, font=("Segoe UI", 13), height=40, placeholder_text="Nombre o ID...")
        ent.pack(fill="x", padx=15, pady=5)
        
        frame_list = ctk.CTkFrame(popup, fg_color=get_color("bg_surface"), corner_radius=10, border_color=get_color("border_color") if hasattr(get_color, '__call__') else "#e2e8f0", border_width=1)
        frame_list.pack(expand=True, fill="both", padx=15, pady=10)
        
        from tkinter import ttk
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
                var_seleccion["id"] = 0
                var_seleccion["nombre"] = "(Todos)"
            else:
                vals = tree_sel.item(sel_id, "values")
                if not vals: return
                try:
                    var_seleccion["id"] = int(vals[0])
                except:
                    var_seleccion["id"] = vals[0]
                var_seleccion["nombre"] = vals[1]
            label_update.configure(text=var_seleccion["nombre"], text_color=get_color("text_primary"), font=("Segoe UI", 12, "bold"))
            popup.destroy()
            
            if on_select_callback:
                on_select_callback()

        tree_sel.bind("<Double-1>", tomar)
        tree_sel.bind("<Return>", tomar)

        btn_frm = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frm.pack(fill="x", side="bottom", padx=15, pady=(5, 15))
        
        ctk.CTkButton(btn_frm, text="Cancelar", command=popup.destroy, fg_color="#ef4444", hover_color="#dc2626", font=("Segoe UI", 13, "bold"), width=150, height=45).pack(side="left", padx=10)
        ctk.CTkButton(btn_frm, text="✓ Seleccionar", command=tomar, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 14, "bold"), width=180, height=45).pack(side="right", padx=10)
        popup.after(100, lambda: ent.focus_set())
        
        try:
            centrar_y_mostrar_ventana(popup)
        except:
            pass
        popup.grab_set()
        popup.transient(self.win)
        self.win.wait_window(popup)

def ui_dashboard_admin(parent, backend, usuario):
    InterfazDashboardAdmin(parent, backend, usuario)
