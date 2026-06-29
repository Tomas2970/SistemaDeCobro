# app/frontend/interfaz_dashboard_supervisor.py
import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import logging
from app.frontend.theme_config import get_color
from app.frontend import custom_dialogs as messagebox
from app.database.permisos import tiene_permiso

logger = logging.getLogger(__name__)

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
ui_caja_router       = _safe_import("app.frontend.interfaz_caja", "ui_caja_router")
ui_compra            = _safe_import("app.frontend.interfaz_compra", "ui_compra")
ui_historiales       = _safe_import("app.frontend.interfaz_historiales", "ui_historiales")
ui_cuenta_corriente  = _safe_import("app.frontend.interfaz_cuenta_corriente", "ui_cuenta_corriente")

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

class InterfazDashboardSupervisor:
    def __init__(self, parent, backend, usuario):
        self.parent = parent
        self.backend = backend
        self.usuario = usuario
        self.win = parent
        self._polling_job = None
        self.crear_interfaz()

    def crear_interfaz(self):
        self.win.title("👁️ Encargado de Turno - Panel de Control")
        try:
            self.win.state('zoomed')
        except Exception:
            self.win.geometry("1200x700")
            
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
        sidebar = ctk.CTkFrame(self.win, width=250, fg_color="#1e3a8a", corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Empaquetamos el botón de cerrar sesión primero (side="bottom") para que siempre esté visible
        ctk.CTkButton(sidebar, text="⛔ Cerrar Sesión", fg_color="#ef4444", hover_color="#b91c1c", 
                      font=("Segoe UI", 13, "bold"), height=40, command=self.cerrar_sesion).pack(side="bottom", fill="x", padx=20, pady=20)

        ctk.CTkLabel(sidebar, text="🛡️", font=("Segoe UI", 50), text_color="white").pack(pady=(30, 0))
        ctk.CTkLabel(sidebar, text="Panel de Supervisor", font=("Segoe UI", 16, "bold"), text_color="white").pack()
        ctk.CTkLabel(sidebar, text=f"👤 {self.usuario.get('nombre')}", font=("Segoe UI", 14), text_color="#bfdbfe").pack(pady=(5, 30))

        # Módulos permitidos explícitos
        modulos = [
            ("📦 Inventario",          "ver_inventario",   ui_inventario,          {}),
            ("🛒 Registrar Compra",     "registrar_compras",ui_compra,              {}),
            ("📚 Cuenta Corriente",    "gestionar_cuenta_corriente", ui_cuenta_corriente, {}),
            ("👥 Clientes",             'ver_clientes',     ui_gestion_clientes,    {}),
            ("🚚 Proveedores",          'ver_proveedores',  ui_gestion_proveedores, {}),
            ("📊 Reportes del Día",     'ver_reportes',     ui_reportes,            {'modo_vista': 'reportes'}),
            ("📦 Control de Caja",      'abrir_caja',       ui_caja_router,         {}),
            # Historial limitado a los últimos DIAS_HISTORIAL_SUPERVISOR días
            ("🧾 Historial (7 días)",   'ver_ventas',       ui_historiales,         {'max_dias_atras': 7}),
        ]

        for texto, permiso, fn, kwargs in modulos:
            if tiene_permiso(self.usuario, permiso):
                cmd = lambda t=texto, f=fn, kw=kwargs: _abrir_seguro(self.win, self.backend, self.usuario, f, t, **kw)
                ctk.CTkButton(sidebar, text=texto, fg_color="transparent", hover_color="#2563eb",
                              font=("Segoe UI", 13, "bold"), anchor="w", height=40, command=cmd).pack(fill="x", padx=10, pady=2)


        # ====== CONTENEDOR PRINCIPAL ======
        main_container = ctk.CTkFrame(self.win, fg_color="transparent")
        main_container.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        main_container.grid_columnconfigure(0, weight=6) # 60% izquierda (Cajas)
        main_container.grid_columnconfigure(1, weight=4) # 40% derecha (Alertas y Acciones)
        main_container.grid_rowconfigure(0, weight=1)

        # --- SECCIÓN IZQUIERDA: CAJAS ACTIVAS ---
        self.frm_cajas = ctk.CTkScrollableFrame(main_container, fg_color=get_color("bg_surface"), corner_radius=15, 
                                                border_color="#e2e8f0" if ctk.get_appearance_mode()=="Light" else "#1e293b", border_width=1)
        self.frm_cajas.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(self.frm_cajas, text="🏪 Cajas Activas del Turno", font=("Segoe UI", 18, "bold"), text_color=get_color("text_primary")).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(self.frm_cajas, text="Monitoreo en tiempo real de operaciones y rendimiento", font=("Segoe UI", 12), text_color=get_color("text_secondary")).pack(anchor="w", padx=15, pady=(0, 15))
        
        self.container_tarjetas_cajas = ctk.CTkFrame(self.frm_cajas, fg_color="transparent")
        self.container_tarjetas_cajas.pack(fill="both", expand=True, padx=10)

        # --- SECCIÓN DERECHA: ALERTAS ---
        frm_derecha = ctk.CTkFrame(main_container, fg_color="transparent")
        frm_derecha.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        frm_derecha.grid_columnconfigure(0, weight=1)
        frm_derecha.grid_rowconfigure(0, weight=1) # 100% Alertas

        # 2. PANEL DE ALERTAS
        self.frm_alertas = ctk.CTkScrollableFrame(frm_derecha, fg_color=get_color("bg_surface"), corner_radius=15,
                                                  border_color="#e2e8f0" if ctk.get_appearance_mode()=="Light" else "#1e293b", border_width=1)
        self.frm_alertas.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        ctk.CTkLabel(self.frm_alertas, text="🔔 Alertas del Turno", font=("Segoe UI", 16, "bold"), text_color=get_color("text_primary")).pack(anchor="w", padx=15, pady=(15, 10))
        self.container_alertas = ctk.CTkFrame(self.frm_alertas, fg_color="transparent")
        self.container_alertas.pack(fill="both", expand=True, padx=10)

        # Iniciar ciclo de actualización
        self.refresh_dashboard()
        
        self.win.deiconify()
        self.win.mainloop()
        
        # LIMPIEZA POST-SESIÓN
        if self.win.winfo_exists():
            try:
                for widget in self.win.winfo_children():
                    try:
                        widget.destroy()
                    except Exception:
                        pass
            except Exception:
                pass

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
        self._actualizar_cajas()
        self._actualizar_alertas()
        self._polling_job = self.win.after(10000, self.refresh_dashboard)

    def _actualizar_cajas(self):
        try:
            for widget in self.container_tarjetas_cajas.winfo_children():
                widget.destroy()
        except Exception:
            return
            
        try:
            if hasattr(self.backend, "obtener_sesiones_abiertas_con_totales"):
                sesiones = self.backend.obtener_sesiones_abiertas_con_totales(tipo_caja='turno')
            else:
                sesiones = []
                
            print(f"DEBUG (Supervisor): _actualizar_cajas ejecutado. Cajas encontradas: {len(sesiones)}")
                
            if not sesiones:
                ctk.CTkLabel(self.container_tarjetas_cajas, text="No hay cajas de turno abiertas en este momento", 
                             font=("Segoe UI", 14, "italic"), text_color=get_color("text_secondary")).pack(pady=40)
                return
                
            ahora = datetime.now()
                
            for s in sesiones:
                vendedor = s.get('vendedor', 'Desconocido')
                str_apertura = s.get('fecha_apertura', '')
                monto = s.get('monto_acumulado', 0.0)
                ventas = s.get('cantidad_ventas', 0)
                
                # Tarjeta con color azul oscuro institucional
                frm_card = ctk.CTkFrame(self.container_tarjetas_cajas, fg_color="#1e3a8a", corner_radius=10, 
                                        border_color="#3b82f6", border_width=1)
                frm_card.pack(fill="x", pady=8, ipady=5)
                
                frm_header = ctk.CTkFrame(frm_card, fg_color="transparent")
                frm_header.pack(fill="x", padx=15, pady=(10, 5))
                
                # Textos forzados a colores claros para máximo contraste sobre el fondo oscuro
                ctk.CTkLabel(frm_header, text=f"👤 {vendedor}", font=("Segoe UI", 16, "bold"), text_color="#ffffff").pack(side="left")
                
                try:
                    if hasattr(str_apertura, 'strftime'):
                        texto_apertura = str_apertura.strftime('%d/%m/%Y %H:%M:%S')
                    else:
                        texto_apertura = datetime.strptime(str(str_apertura), "%Y-%m-%d %H:%M:%S").strftime('%d/%m/%Y %H:%M:%S')
                except Exception:
                    texto_apertura = str(str_apertura)
                ctk.CTkLabel(frm_header, text=f"Apertura: {texto_apertura}", font=("Segoe UI", 11), text_color="#cbd5e1").pack(side="right", padx=10)
                
                frm_body = ctk.CTkFrame(frm_card, fg_color="transparent")
                frm_body.pack(fill="x", padx=15, pady=(5, 10))
                
                frm_monto = ctk.CTkFrame(frm_body, fg_color="transparent")
                frm_monto.pack(side="left", fill="both", expand=True)
                ctk.CTkLabel(frm_monto, text="Monto Turno", font=("Segoe UI", 11), text_color="#cbd5e1").pack()
                ctk.CTkLabel(frm_monto, text=f"${monto:,.2f}", font=("Segoe UI", 20, "bold"), text_color="#34d399").pack()
                
                frm_ventas = ctk.CTkFrame(frm_body, fg_color="transparent")
                frm_ventas.pack(side="left", fill="both", expand=True)
                ctk.CTkLabel(frm_ventas, text="Operaciones", font=("Segoe UI", 11), text_color="#cbd5e1").pack()
                ctk.CTkLabel(frm_ventas, text=f"{ventas}", font=("Segoe UI", 20, "bold"), text_color="#60a5fa").pack()
                
                # --- BOTÓN CERRAR CAJA ---
                frm_acciones_caja = ctk.CTkFrame(frm_body, fg_color="transparent")
                frm_acciones_caja.pack(side="right", fill="both", expand=False)
                
                def cmd_forzar_cierre(id_sess=s.get('id_session'), vend=vendedor):
                    if messagebox.mostrar_confirmacion("⚠️ Forzar Cierre", f"¿Estás seguro que deseas cerrar forzosamente la caja de {vend}?\n\nEl sistema la marcará como cerrada y el usuario no podrá realizar más ventas hasta que abra una caja nueva.", parent=self.win):
                        if hasattr(self.backend, "cerrar_caja_por_supervisor"):
                            exito = self.backend.cerrar_caja_por_supervisor(id_sess, self.usuario.get('id_usuario'), "Cierre Forzado por Supervisor")
                            if exito:
                                messagebox.mostrar_info("Éxito", f"La caja de {vend} ha sido cerrada.", parent=self.win)
                                self.refresh_dashboard()
                            else:
                                messagebox.mostrar_error("Error", "No se pudo cerrar la caja.", parent=self.win)
                        else:
                            messagebox.mostrar_error("Error", "Función no disponible en el backend.", parent=self.win)

                ctk.CTkButton(frm_acciones_caja, text="⛔ Forzar Cierre", font=("Segoe UI", 12, "bold"), 
                              fg_color="#ef4444", hover_color="#b91c1c", width=110, height=35, 
                              command=cmd_forzar_cierre).pack(side="right", pady=5)

                
        except Exception as e:
            logger.error(f"Error actualizando cajas: {e}")

    def _actualizar_alertas(self):
        try:
            for widget in self.container_alertas.winfo_children():
                widget.destroy()
        except Exception:
            return
            
        hay_alertas = False

        def crear_alerta(icono, texto, color_bg, color_fg, on_double_click=None):
            f = ctk.CTkFrame(self.container_alertas, fg_color=color_bg, corner_radius=8)
            f.pack(fill="x", pady=4, padx=5)
            lbl_ico = ctk.CTkLabel(f, text=icono, font=("Segoe UI", 16))
            lbl_ico.pack(side="left", padx=10, pady=10)
            lbl_txt = ctk.CTkLabel(f, text=texto, font=("Segoe UI", 12, "bold"), text_color=color_fg, wraplength=280, justify="left")
            lbl_txt.pack(side="left", padx=(0, 10), pady=10)
            
            if on_double_click:
                f.bind("<Double-Button-1>", on_double_click)
                lbl_ico.bind("<Double-Button-1>", on_double_click)
                lbl_txt.bind("<Double-Button-1>", on_double_click)
                # Opcional: Cambiar el cursor para indicar que es clickeable
                f.configure(cursor="hand2")
                lbl_ico.configure(cursor="hand2")
                lbl_txt.configure(cursor="hand2")
            
        try:
            if hasattr(self.backend, "obtener_stock_bajo"):
                stock_bajo = self.backend.obtener_stock_bajo()
                if stock_bajo:
                    hay_alertas = True
                    def cmd_stock(e):
                        _abrir_seguro(self.win, self.backend, self.usuario, ui_inventario, "Inventario", filtro_stock_bajo=True)
                    crear_alerta("⚠️", f"{len(stock_bajo)} productos con stock crítico.", "#fef2f2" if ctk.get_appearance_mode()=="Light" else "#7f1d1d", "#dc2626" if ctk.get_appearance_mode()=="Light" else "#fca5a5", on_double_click=cmd_stock)
            
            if hasattr(self.backend, "obtener_historial_movimientos_caja"):
                hoy = datetime.now().strftime("%Y-%m-%d")
                movs = self.backend.obtener_historial_movimientos_caja(hoy, hoy)
                devoluciones = [m for m in movs if m.get('motivo') == 'devolucion_efectivo']
                if devoluciones:
                    hay_alertas = True
                    ult_dev = devoluciones[-1]
                    crear_alerta("🔄", f"Devolución reciente: ${ult_dev.get('monto', 0)} ({ult_dev.get('descripcion', '')})", "#fffbeb" if ctk.get_appearance_mode()=="Light" else "#78350f", "#d97706" if ctk.get_appearance_mode()=="Light" else "#fcd34d")
            
            if hasattr(self.backend, "obtener_sesiones_abiertas_con_totales"):
                sesiones = self.backend.obtener_sesiones_abiertas_con_totales(tipo_caja='turno')
                ahora = datetime.now()
                for s in sesiones:
                    fecha_str = s.get('fecha_ultima_venta') or s.get('fecha_apertura')
                    if fecha_str:
                        try:
                            f_ult = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
                            if (ahora - f_ult).total_seconds() > 1800:
                                hay_alertas = True
                                crear_alerta("💤", f"Caja {s.get('vendedor')} sin actividad por >30 min.", "#eff6ff" if ctk.get_appearance_mode()=="Light" else "#1e3a8a", "#2563eb" if ctk.get_appearance_mode()=="Light" else "#93c5fd")
                        except: pass
                        
        except Exception as e:
            logger.error(f"Error cargando alertas: {e}")
            
        if not hay_alertas:
            ctk.CTkLabel(self.container_alertas, text="✅ Todo en orden. No hay alertas activas.", 
                         font=("Segoe UI", 13), text_color=get_color("text_secondary")).pack(pady=30)

def ui_dashboard_supervisor(parent, backend, usuario):
    InterfazDashboardSupervisor(parent, backend, usuario)
