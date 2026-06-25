# app/frontend/interfaz_caja.py
import tkinter as tk
import customtkinter as ctk
import logging
from app.frontend import custom_dialogs as messagebox
from app.frontend.theme_config import get_color, preparar_ventana, centrar_y_mostrar_ventana

logger = logging.getLogger(__name__)

def ui_caja_supervisor(parent, backend, usuario):
    """Panel de Cajas Activas exclusivo para el Encargado de Turno (Supervisor)"""
    win = ctk.CTkToplevel(parent)
    win.title("👁️ Panel de Cajas Activas - Turno Actual")
    win.geometry("850x550")
    preparar_ventana(win)
    win.configure(fg_color=get_color("bg_root"))
    
    # Header
    fr_header = ctk.CTkFrame(win, fg_color="transparent")
    fr_header.pack(fill="x", padx=20, pady=20)
    
    ctk.CTkLabel(fr_header, text="Cajas Activas en el Turno", font=("Segoe UI", 24, "bold"), text_color=get_color("text_primary")).pack(side="left")
    
    btn_actualizar = ctk.CTkButton(fr_header, text="🔄 Actualizar", font=("Segoe UI", 12, "bold"), width=120, height=35)
    btn_actualizar.pack(side="right")
    
    # Contenedor Scrolleable de las cajas
    container = ctk.CTkScrollableFrame(win, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    def cerrar_caja_ajena(id_session, nombre_vendedor):
        # Confirmación
        if messagebox.mostrar_confirmacion(
            "Cierre Forzado", 
            f"¿Confirmar cierre de caja de {nombre_vendedor}?\n\nEsta acción registrará en auditoría que usted cerró la caja.",
            parent=win
        ):
            try:
                if hasattr(backend, "cerrar_caja_por_supervisor"):
                    backend.cerrar_caja_por_supervisor(id_session, usuario['id_usuario'])
                    messagebox.mostrar_exito("Éxito", f"La caja de {nombre_vendedor} ha sido cerrada forzosamente.", parent=win)
                    cargar_cajas()
                else:
                    messagebox.mostrar_info(
                        "En Desarrollo", 
                        "La función backend.cerrar_caja_por_supervisor() aún no está implementada en BD.", 
                        parent=win
                    )
            except Exception as e:
                logger.error(f"Fallo al cerrar caja remota: {e}")
                messagebox.mostrar_error("Error", f"Fallo al cerrar caja: {e}", parent=win)

    def cargar_cajas():
        for widget in container.winfo_children():
            widget.destroy()
            
        try:
            # Reutilizamos este método que ya extrae las sesiones abiertas con sus acumulados
            if hasattr(backend, "obtener_sesiones_abiertas_con_totales"):
                sesiones = backend.obtener_sesiones_abiertas_con_totales()
            else:
                sesiones = []
                
            if not sesiones:
                ctk.CTkLabel(container, text="No hay cajas abiertas en este momento.", font=("Segoe UI", 16, "italic"), text_color=get_color("text_secondary")).pack(pady=40)
                return
                
            for s in sesiones:
                vendedor = s.get('vendedor', 'Desconocido')
                hora_apertura_raw = s.get('fecha_apertura')
                if hora_apertura_raw and hasattr(hora_apertura_raw, 'strftime'):
                    hora_apertura = hora_apertura_raw.strftime("%d/%m/%Y %H:%M:%S")
                else:
                    try:
                        from datetime import datetime
                        hora_apertura = datetime.strptime(str(hora_apertura_raw), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
                    except:
                        hora_apertura = str(hora_apertura_raw) if hora_apertura_raw else '---'
                monto = s.get('monto_acumulado', 0.0)
                ventas = s.get('cantidad_ventas', 0)
                id_session = s.get('id_session')
                
                # Tarjeta de Caja
                frm_card = ctk.CTkFrame(container, fg_color=get_color("bg_surface"), corner_radius=10, 
                                        border_color="#e5e7eb" if ctk.get_appearance_mode()=="Light" else "#374151", border_width=1)
                frm_card.pack(fill="x", pady=10, ipady=10)
                
                # Info Izquierda (Vendedor y Hora)
                frm_info = ctk.CTkFrame(frm_card, fg_color="transparent")
                frm_info.pack(side="left", fill="both", expand=True, padx=20)
                
                ctk.CTkLabel(frm_info, text=f"👤 {vendedor} (Caja {id_session})", font=("Segoe UI", 18, "bold"), text_color=get_color("text_primary")).pack(anchor="w", pady=(5, 5))
                ctk.CTkLabel(frm_info, text=f"🕒 Apertura: {hora_apertura}", font=("Segoe UI", 13), text_color=get_color("text_secondary")).pack(anchor="w")
                
                # Info Centro (Montos)
                frm_stats = ctk.CTkFrame(frm_card, fg_color="transparent")
                frm_stats.pack(side="left", padx=40)
                
                ctk.CTkLabel(frm_stats, text=f"Monto Acumulado:\n${monto:,.2f}", font=("Segoe UI", 14, "bold"), text_color="#10b981", justify="center").pack(side="left", padx=20)
                ctk.CTkLabel(frm_stats, text=f"Ventas:\n{ventas}", font=("Segoe UI", 14, "bold"), text_color="#3b82f6", justify="center").pack(side="left", padx=20)
                
                # Acciones Derecha
                frm_acc = ctk.CTkFrame(frm_card, fg_color="transparent")
                frm_acc.pack(side="right", padx=20)
                
                ctk.CTkButton(
                    frm_acc, 
                    text="🔒 Cerrar caja", 
                    fg_color="#ef4444", 
                    hover_color="#dc2626", 
                    font=("Segoe UI", 13, "bold"),
                    command=lambda i=id_session, v=vendedor: cerrar_caja_ajena(i, v)
                ).pack(pady=10)
                
        except Exception as e:
            logger.exception("Error al cargar cajas")
            ctk.CTkLabel(container, text=f"Error cargando cajas: {e}", text_color="#ef4444").pack()

    btn_actualizar.configure(command=cargar_cajas)
    cargar_cajas()
    
    centrar_y_mostrar_ventana(win)
    win.grab_set()

def ui_caja_router(parent, backend, usuario, **kwargs):
    """
    Router principal para el botón del menú 'Control de Caja'.
    Si el usuario es Administrador (rol 1), redirige a su dashboard especial.
    Si el usuario es Supervisor (rol 3), se muestra el panel de cajas del turno.
    De lo contrario (Vendedor), delega al módulo interfaz_caja_operativa para su caja.
    """
    id_rol = usuario.get('id_rol')
    
    if id_rol == 1:
        try:
            from app.frontend.interfaz_dashboard_admin import ui_dashboard_admin
            ui_dashboard_admin(parent, backend, usuario)
        except ImportError:
            messagebox.mostrar_error("En Construcción", "El Dashboard de Administrador está siendo construido.", parent=parent)
    elif id_rol == 3:
        ui_caja_supervisor(parent, backend, usuario)
    else:
        try:
            from app.frontend.interfaz_caja_operativa import ui_caja_operativa
            ui_caja_operativa(parent, backend, usuario)
        except ImportError:
            messagebox.mostrar_error("Error", "No se encontró el módulo de caja nativo.", parent=parent)
