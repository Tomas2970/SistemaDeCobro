# app/frontend/interfaz_menu_principal.py
import customtkinter as ctk
from app.frontend import custom_dialogs as messagebox
from app.frontend.custom_dialogs import mostrar_confirmacion, mostrar_advertencia, mostrar_error, mostrar_info
import logging
from app.database.permisos import tiene_permiso
from app.frontend.stock_event_manager import stock_events
from app.frontend.broadcast_manager import iniciar_polling_broadcast, detener_polling_broadcast

logger = logging.getLogger(__name__)

# ===== Imports Dinámicos =====
def _safe_import(path, name):
    try:
        mod = __import__(path, fromlist=[name])
        return getattr(mod, name)
    except Exception:
        return None

ui_inventario        = _safe_import("app.frontend.interfaz_inventario", "ui_inventario")
ui_productos         = _safe_import("app.frontend.interfaz_productos", "ui_productos")
ui_venta             = _safe_import("app.frontend.interfaz_venta", "ui_venta")
ui_reportes          = _safe_import("app.frontend.interfaz_reportes", "ui_reportes")
ui_gestion_clientes  = _safe_import("app.frontend.interfaz_gestion_clientes", "ui_gestion_clientes")
ui_cuenta_corriente  = _safe_import("app.frontend.interfaz_cuenta_corriente", "ui_cuenta_corriente")
ui_compra            = _safe_import("app.frontend.interfaz_compra", "ui_compra")
ui_historiales       = _safe_import("app.frontend.interfaz_historiales", "ui_historiales")
ui_gestion_usuarios  = _safe_import("app.frontend.interfaz_gestion_usuarios", "ui_gestion_usuarios")
ui_categorias        = _safe_import("app.frontend.interfaz_categorias", "ui_categorias")
ui_gestion_proveedores = _safe_import("app.frontend.interfaz_gestion_proveedores", "ui_gestion_proveedores")
ui_dashboard_admin   = _safe_import("app.frontend.interfaz_dashboard_admin", "ui_dashboard_admin")
ui_caja_router       = _safe_import("app.frontend.interfaz_caja", "ui_caja_router")
def _abrir_seguro(root, backend, usuario, fn, nombre, **kwargs):
    if not callable(fn):
        mostrar_info("No disponible", f"La pantalla '{nombre}' no está integrada.", parent=root)
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
        mostrar_error("Error", f"Error al abrir {nombre}:\n{e}", parent=root)
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

def ui_menu_principal(parent, backend, usuario):
    # Iniciar polling global de broadcasts (corre independientemente del módulo abierto)
    iniciar_polling_broadcast(parent, usuario, backend)

    id_rol = usuario.get('id_rol')
    
    if id_rol == 3:
        ui_dashboard_supervisor = _safe_import("app.frontend.interfaz_dashboard_supervisor", "ui_dashboard_supervisor")
        if ui_dashboard_supervisor:
            ui_dashboard_supervisor(parent, backend, usuario)
            return
    elif id_rol == 1:
        ui_dashboard_admin = _safe_import("app.frontend.interfaz_dashboard_admin", "ui_dashboard_admin")
        if ui_dashboard_admin:
            ui_dashboard_admin(parent, backend, usuario)
            return

    win = parent
    win.title(f"🛒 Sistema de Cobros - Don Atilio")
    
    try:
        win.state('zoomed')
    except Exception:
        ancho, alto = 1100, 700
        win.update_idletasks()
        x = (win.winfo_screenwidth() - ancho) // 2
        y = (win.winfo_screenheight() - alto) // 2
        win.geometry(f"{ancho}x{alto}+{x}+{y}")
        
    win.resizable(True, True)

    def on_main_focus(event):
        if event.widget == win:
            if hasattr(win, '_ventanas_modulos'):
                for ventana in win._ventanas_modulos.values():
                    if ventana and ventana.winfo_exists():
                        ventana.lift()
                        try:
                            ventana.focus_force()
                        except Exception:
                            pass
    win.bind("<FocusIn>", on_main_focus)


    # Colores Opción A (Clásico corporativo)
    color_bg = "#f3f4f6" if ctk.get_appearance_mode() == "Light" else "#111827"
    color_sidebar = "#1e3a8a" # Azul muy oscuro y profesional
    color_cards = "#ffffff" if ctk.get_appearance_mode() == "Light" else "#1f2937"
    
    win.configure(fg_color=color_bg)

    # ==========================================
    # SIDEBAR (Panel Izquierdo)
    # ==========================================
    sidebar = ctk.CTkFrame(win, width=260, fg_color=color_sidebar, corner_radius=0)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    # Botón de cerrar sesión al fondo
    def cerrar_sesion(*_):
        caja_abierta = backend.obtener_session_abierta(id_usuario=usuario['id_usuario'])
        if caja_abierta:
            mostrar_advertencia("Caja Abierta", "Debes cerrar tu caja antes de salir.")
            return
        if mostrar_confirmacion("Cerrar Sesión", "¿Seguro que deseas salir del sistema?"):
            stock_events.desuscribir(check_stock)
            detener_polling_broadcast(win)
            # Cancelar el timer de verificación de sesión para que no dispare
            # el error "Sesión expirada" en la pantalla de login posterior
            after_id = getattr(win, '_verificar_sesion_after_id', None)
            if after_id:
                try:
                    win.after_cancel(after_id)
                except Exception:
                    pass
            win._verificar_sesion_after_id = None
            win.quit()

    ctk.CTkButton(sidebar, text="⛔ Cerrar Sesión", fg_color="#ef4444", hover_color="#b91c1c", 
                  font=("Segoe UI", 13, "bold"), height=40, command=cerrar_sesion).pack(side="bottom", fill="x", padx=20, pady=30)

    ctk.CTkLabel(sidebar, text="🛒", font=("Segoe UI", 72), text_color="white").pack(pady=(40, 5))
    ctk.CTkLabel(sidebar, text="Sistema de Cobros", font=("Segoe UI", 18, "bold"), text_color="white").pack()
    ctk.CTkLabel(sidebar, text="Don Atilio", font=("Segoe UI", 14), text_color="#bfdbfe").pack(pady=(0, 20))

    # Perfil
    rol_text = {1: 'Admin', 2: 'Vendedor', 3: 'Supervisor'}.get(usuario.get('id_rol'), 'Usuario')
    user_frame = ctk.CTkFrame(sidebar, fg_color="#2563eb", corner_radius=8)
    user_frame.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkLabel(user_frame, text=f"👤 {usuario.get('nombre')}", font=("Segoe UI", 15, "bold"), text_color="white").pack(pady=(12, 0))
    ctk.CTkLabel(user_frame, text=rol_text, font=("Segoe UI", 12), text_color="#dbeafe").pack(pady=(0, 12))

    # Alerta de Stock (Tarjeta Roja Gigante)
    alert_frame = ctk.CTkFrame(sidebar, fg_color="#ef4444", corner_radius=8, cursor="hand2")
    lbl_alerta_titulo = ctk.CTkLabel(alert_frame, text="⚠️ ALERTA STOCK", font=("Segoe UI", 14, "bold"), text_color="white", cursor="hand2")
    lbl_alerta_titulo.pack(pady=(15, 5))
    lbl_alerta_txt = ctk.CTkLabel(alert_frame, text="", font=("Segoe UI", 36, "bold"), text_color="white", cursor="hand2")
    lbl_alerta_txt.pack(pady=(0, 0))
    lbl_alerta_desc = ctk.CTkLabel(alert_frame, text="productos críticos", font=("Segoe UI", 13), text_color="#fecaca", cursor="hand2")
    lbl_alerta_desc.pack(pady=(0, 15))
    
    def on_alerta_doble_clic(event):
        if not tiene_permiso(usuario, 'ver_inventario'):
            mostrar_advertencia("Acceso Denegado", "No tienes permisos para ver el inventario.", parent=win)
            return
        _abrir_seguro(win, backend, usuario, ui_inventario, "Inventario", filtro_stock_bajo=True)

    alert_frame.bind("<Double-1>", on_alerta_doble_clic)
    lbl_alerta_titulo.bind("<Double-1>", on_alerta_doble_clic)
    lbl_alerta_txt.bind("<Double-1>", on_alerta_doble_clic)
    lbl_alerta_desc.bind("<Double-1>", on_alerta_doble_clic)
    
    def check_stock():
        try:
            win.update_idletasks()
            if hasattr(backend, "obtener_stock_bajo"):
                bajos = backend.obtener_stock_bajo()
                if bajos:
                    lbl_alerta_txt.configure(text=f"{len(bajos)}")
                    # Lo empaquetamos con fill="x" y pady alto para que ocupe y adorne el hueco
                    alert_frame.pack(fill="x", padx=20, pady=(40, 0))
                else:
                    alert_frame.pack_forget()
        except: pass

    stock_events.suscribir(check_stock)
    check_stock()
    
    # ==========================================
    # MAIN AREA (Panel Derecho)
    # ==========================================
    main_area = ctk.CTkFrame(win, fg_color="transparent")
    main_area.pack(side="right", fill="both", expand=True)
    
    # Venta > Caja > Compras > Cta Cte > Inventario > Proveedores > Clientes > Categorías > Reportes > Historiales > Usuarios
    todos_botones = [
        ("💵 POS Venta", "realizar_ventas", ui_venta, {}, True),
        ("📦 Control de Caja", 'abrir_caja', ui_caja_router, {}, False),
        ("🛒 Registrar Compra", "registrar_compras", ui_compra, {}, False),
        
        ("📚 Cuenta Corriente", 'gestionar_cuenta_corriente', ui_cuenta_corriente, {}, False),
        ("📦 Inventario", "ver_inventario", ui_inventario, {}, False),
        ("🚚 Proveedores", 'ver_proveedores', ui_gestion_proveedores, {}, False),

        ("👥 Clientes", 'ver_clientes', ui_gestion_clientes, {}, False),
        ("🏷️ Categorías", 'gestionar_categorias', ui_categorias, {}, False),
        ("📊 Reportes Ventas", 'ver_reportes', ui_reportes, {'modo_vista': 'reportes'}, False),
        
        ("🧾 Historiales", 'ver_ventas', ui_historiales, {}, False),
        ("⚙️ Usuarios", 'ver_usuarios', ui_gestion_usuarios, {}, False)
    ]

    # ==========================================
    # MODO VENDEDOR / OTROS (Botones en Grid)
    # ==========================================
    # Título del panel
    encabezado = ctk.CTkFrame(main_area, fg_color="transparent", height=80)
    encabezado.pack(fill="x", padx=50, pady=(40, 10))
    ctk.CTkLabel(encabezado, text="Panel de Control General", font=("Segoe UI", 28, "bold"), text_color="#1f2937" if ctk.get_appearance_mode()=="Light" else "white").pack(side="left")

    # Contenedor Blanco Estilo Tarjeta donde viven los botones
    card_container = ctk.CTkFrame(main_area, fg_color=color_cards, corner_radius=15, border_width=1, border_color="#e5e7eb" if ctk.get_appearance_mode()=="Light" else "#374151")
    card_container.pack(fill="both", expand=True, padx=50, pady=(0, 40))

    # Grid de 3 columnas
    grid_frame = ctk.CTkFrame(card_container, fg_color="transparent")
    grid_frame.pack(fill="both", expand=True, padx=40, pady=40)
    
    for i in range(3): grid_frame.grid_columnconfigure(i, weight=1)

    r, c = 0, 0
    for texto, permiso, funcion, kwargs, action_hero in todos_botones:
        if not tiene_permiso(usuario, permiso): continue
        
        if action_hero:
            btn_color = "#10b981" # Verde
            hov_color = "#059669"
            txt_color = "white"
        else:
            btn_color = "#f3f4f6" if ctk.get_appearance_mode()=="Light" else "#374151"
            hov_color = "#e5e7eb" if ctk.get_appearance_mode()=="Light" else "#4b5563"
            txt_color = "#1f2937" if ctk.get_appearance_mode()=="Light" else "white"

        cmd = lambda t=texto, f=funcion, k=kwargs: _abrir_seguro(win, backend, usuario, f, t, **k)
        b = ctk.CTkButton(grid_frame, text=texto, font=("Segoe UI", 15, "bold"), 
                          fg_color=btn_color, hover_color=hov_color, text_color=txt_color,
                          height=60, corner_radius=10, command=cmd)
        
        b.grid(row=r, column=c, padx=15, pady=20, sticky="ew")
        
        c += 1
        if c >= 3:
            c = 0
            r += 1

    def verificar_estado_usuario():
        if not win.winfo_exists():
            return
        try:
            if hasattr(backend, "obtener_usuario_por_id"):
                user_db = backend.obtener_usuario_por_id(usuario['id_usuario'])
                if user_db:
                    rol_modificado = user_db.get('id_rol') != usuario.get('id_rol')
                    cuenta_desactivada = user_db.get('activo', 1) == 0
                    
                    token_db = user_db.get('token_sesion')
                    token_local = usuario.get('token_sesion')
                    sesion_invalida = (token_local and token_db != token_local)
                    
                    if rol_modificado or cuenta_desactivada or sesion_invalida:
                        stock_events.desuscribir(check_stock)
                        if rol_modificado:
                            mensaje = "Tu rol fue modificado por un administrador. Por favor iniciá sesión nuevamente."
                        elif cuenta_desactivada:
                            mensaje = "Tu cuenta fue desactivada. Por favor contactá a un administrador."
                        else:
                            mensaje = "Tu sesión ha expirado o iniciaste sesión en otro dispositivo."
                        
                        mostrar_advertencia(
                            "Sesión Expirada", 
                            mensaje,
                            parent=win
                        )
                        win.quit()
                        return
        except Exception as e:
            logger.error(f"Error al verificar estado del usuario: {e}")

        # Guardar el ID del timer para poder cancelarlo limpiamente al cerrar sesión
        if win.winfo_exists():
            win._verificar_sesion_after_id = win.after(5000, verificar_estado_usuario)

    # Iniciar ciclo de verificación y guardar su ID
    win._verificar_sesion_after_id = win.after(5000, verificar_estado_usuario)

    win.protocol("WM_DELETE_WINDOW", cerrar_sesion)
    win.deiconify()
    win.mainloop()
    
    if win.winfo_exists():
        for widget in win.winfo_children(): widget.destroy()