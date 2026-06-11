# app/frontend/autorizacion.py
# ============================================
# Módulo centralizado de autorización HÍBRIDO (Remoto + Físico)
# Patrón "Supervisor Override" para acciones restringidas
# ============================================
import tkinter as tk
import logging
from app.frontend import custom_dialogs as messagebox

logger = logging.getLogger(__name__)

try:
    from app.frontend.theme_config import get_color, preparar_ventana, centrar_y_mostrar_ventana
except ImportError:
    def get_color(k): return "#000000"
    def preparar_ventana(w): pass
    def centrar_y_mostrar_ventana(w): pass


# =========================================================
# HELPERS DE BASE DE DATOS (Aislados para no tocar otros archivos)
# =========================================================
def _obtener_conexion():
    """Intenta obtener una conexión directa a la BD."""
    try:
        from app.database import DB
        return DB.conectar()
    except Exception as e:
        logger.error(f"Fallo al importar/conectar BD en autorizacion: {e}")
        return None

def _asegurar_tabla_autorizaciones():
    """Crea la tabla de autorizaciones si no existe."""
    conexion = _obtener_conexion()
    if conexion:
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS autorizaciones_pendientes (
                    id_solicitud INT AUTO_INCREMENT PRIMARY KEY,
                    id_vendedor INT,
                    id_caja INT,
                    tipo_operacion VARCHAR(100),
                    motivo TEXT,
                    estado VARCHAR(50) DEFAULT 'PENDIENTE',
                    id_autorizador INT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conexion.commit()
            cursor.close()
            conexion.close()
            return True
        except Exception as e:
            logger.error(f"Fallo al asegurar tabla autorizaciones: {e}")
            if conexion.is_connected():
                conexion.close()
    return False

def _insertar_solicitud(id_vendedor, id_caja, tipo_operacion, motivo):
    """Inserta una solicitud y devuelve el ID generado."""
    conexion = _obtener_conexion()
    if conexion:
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                INSERT INTO autorizaciones_pendientes 
                (id_vendedor, id_caja, tipo_operacion, motivo) 
                VALUES (%s, %s, %s, %s)
            """, (id_vendedor, id_caja, tipo_operacion, motivo))
            id_insertado = cursor.lastrowid
            conexion.commit()
            cursor.close()
            conexion.close()
            return id_insertado
        except Exception as e:
            logger.error(f"Fallo al insertar solicitud: {e}")
            if conexion.is_connected():
                conexion.close()
    return None

def _verificar_estado_solicitud(id_solicitud):
    """Consulta el estado actual de una solicitud."""
    conexion = _obtener_conexion()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT estado, id_autorizador FROM autorizaciones_pendientes WHERE id_solicitud = %s", (id_solicitud,))
            res = cursor.fetchone()
            cursor.close()
            conexion.close()
            return res
        except Exception as e:
            logger.error(f"Fallo al verificar solicitud: {e}")
            if conexion.is_connected():
                conexion.close()
    return None

def _marcar_solicitud_local(id_solicitud, id_autorizador):
    """Marca la solicitud como resuelta localmente para que el admin deje de verla."""
    conexion = _obtener_conexion()
    if conexion:
        try:
            cursor = conexion.cursor()
            cursor.execute("UPDATE autorizaciones_pendientes SET estado='APROBADA_LOCALMENTE', id_autorizador=%s WHERE id_solicitud=%s", (id_autorizador, id_solicitud))
            conexion.commit()
            cursor.close()
            conexion.close()
        except Exception:
            if conexion.is_connected():
                conexion.close()


# =========================================================
# LÓGICA DE INTERFAZ HÍBRIDA
# =========================================================
def solicitar_autorizacion_supervisor(parent, backend, usuario_actual, callback_exito=None, roles_permitidos=(1, 3), 
                                      tipo_operacion="Operación Restringida", motivo="Autorización de supervisor requerida"):
    """
    Muestra el modal híbrido de autorización.
    1. Detecta red (intentando crear la solicitud en la BD).
    2. Si hay red, inicia Polling Remoto.
    3. Al mismo tiempo, expone el método Físico (ingreso de PIN/usuario).
    4. Si se ingresa el PIN local, sobreescribe el estado remoto.
    """
    import customtkinter as ctk
    
    # Intento de registro en BD (Detección de conectividad automática)
    hay_red = _asegurar_tabla_autorizaciones()
    id_solicitud = None
    
    if hay_red:
        id_vend = usuario_actual.get('id_usuario') if usuario_actual else 0
        # Idealmente el id_caja se saca de la sesión actual, acá pasamos 0 o se podría mejorar si el frontend lo provee
        id_solicitud = _insertar_solicitud(id_vend, 0, tipo_operacion, motivo)
    
    modo_remoto_activo = (id_solicitud is not None)

    popup = ctk.CTkToplevel(parent)
    popup.title("🔓 Autorización Híbrida")
    popup.geometry("450x480" if modo_remoto_activo else "400x380")
    preparar_ventana(popup)
    popup.resizable(False, False)
    popup.transient(parent)
    
    frm_main = ctk.CTkFrame(popup, fg_color=get_color("bg_surface"), corner_radius=15)
    frm_main.pack(fill="both", expand=True, padx=20, pady=20)
    
    # --- SECCIÓN REMOTA ---
    if modo_remoto_activo:
        lbl_status = ctk.CTkLabel(frm_main, text="⏳ Esperando Autorización Remota...", 
                                  font=("Segoe UI", 16, "bold"), text_color="#f59e0b")
        lbl_status.pack(pady=(15, 5))
        
        ctk.CTkLabel(frm_main, text="El administrador ha sido notificado en su panel.", 
                     font=("Segoe UI", 12), text_color=get_color("text_secondary")).pack(pady=(0, 10))
                     
        # Separador
        div = ctk.CTkFrame(frm_main, height=2, fg_color="#e5e7eb" if ctk.get_appearance_mode()=="Light" else "#374151")
        div.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(frm_main, text="O alternativamente (Modo Físico):", 
                     font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).pack(pady=(5, 10))
    else:
        # Fallback Automático si la DB no responde
        ctk.CTkLabel(frm_main, text="Autorización Presencial Requerida", 
                     font=("Segoe UI", 16, "bold"), text_color=get_color("text_primary")).pack(pady=(20, 5))
        ctk.CTkLabel(frm_main, text="⚠️ (Sin conexión de red - Modo Remoto Inactivo)", 
                     font=("Segoe UI", 11, "italic"), text_color="#ef4444").pack(pady=(0, 15))
    
    # --- SECCIÓN FÍSICA (Siempre disponible) ---
    ctk.CTkLabel(frm_main, text="Credencial o Usuario Administrador:", font=("Segoe UI", 12), text_color=get_color("text_secondary")).pack(anchor="w", padx=40)
    entry_user = ctk.CTkEntry(frm_main, font=("Segoe UI", 13), width=280, height=35, placeholder_text="Escanee o escriba...")
    entry_user.pack(pady=(2, 10))
    entry_user.focus_set()
    
    ctk.CTkLabel(frm_main, text="Contraseña / PIN:", font=("Segoe UI", 12), text_color=get_color("text_secondary")).pack(anchor="w", padx=40)
    entry_pass = ctk.CTkEntry(frm_main, show="●", font=("Segoe UI", 13), width=280, height=35, placeholder_text="••••••••")
    entry_pass.pack(pady=(2, 20))
    
    # --- LÓGICA DE CONTROL ---
    polling_activo = modo_remoto_activo
    
    def detener_polling():
        nonlocal polling_activo
        polling_activo = False

    def chequear_estado_remoto():
        if not polling_activo or not popup.winfo_exists():
            return
            
        estado_db = _verificar_estado_solicitud(id_solicitud)
        if estado_db:
            estado = estado_db.get('estado')
            if estado == 'APROBADA':
                detener_polling()
                popup.grab_release()
                popup.destroy()
                # Simulamos autorizador para el callback con los datos de la DB
                autorizador_remoto = {'id_usuario': estado_db.get('id_autorizador'), 'nombre': 'Aprobación Remota', 'id_rol': 1}
                if callback_exito:
                    parent.after(100, lambda: callback_exito(autorizador_remoto))
                return
            elif estado == 'RECHAZADA':
                detener_polling()
                messagebox.showerror("Rechazada", "El Administrador ha denegado la solicitud.", parent=popup)
                popup.grab_release()
                popup.destroy()
                return
                
        # Repetir polling
        popup.after(1500, chequear_estado_remoto)

    def procesar_aprobacion_local(autorizador):
        detener_polling()
        if modo_remoto_activo:
            _marcar_solicitud_local(id_solicitud, autorizador.get('id_usuario'))
        popup.grab_release()
        popup.destroy()
        if callback_exito:
            parent.after(100, lambda: callback_exito(autorizador))

    def validar_usuario_o_codigo(event=None):
        u_nom = entry_user.get().strip()
        if not u_nom: return
        try:
            autorizador = backend.buscar_usuario_por_codigo(u_nom)
            if autorizador and autorizador.get('id_rol') in roles_permitidos:
                procesar_aprobacion_local(autorizador)
                return
        except Exception:
            pass
        entry_pass.focus_set()

    def validar_local():
        u_nom = entry_user.get().strip()
        u_pass = entry_pass.get().strip()
        if not u_nom or not u_pass:
            messagebox.showwarning("Atención", "Ingrese credenciales completas", parent=popup)
            return
        try:
            autorizador = backend.verificar_contraseña(u_nom, u_pass)
            if autorizador and autorizador.get('id_rol') in roles_permitidos:
                procesar_aprobacion_local(autorizador)
            else:
                messagebox.showerror("Error", "Permisos insuficientes o credenciales incorrectas.", parent=popup)
                entry_pass.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Fallo de validación: {e}", parent=popup)
    
    # --- BOTONES ---
    frm_btns = ctk.CTkFrame(popup, fg_color="transparent")
    frm_btns.pack(pady=(0, 15))
    
    ctk.CTkButton(frm_btns, text="✓ Aprobar (Físico)", fg_color=get_color("button_primary"), hover_color=get_color("button_primary_hover"),
                  font=("Segoe UI", 12, "bold"), width=140, height=40, command=validar_local).pack(side="left", padx=10)
    
    def cancelar():
        detener_polling()
        if modo_remoto_activo:
            try:
                conexion = _obtener_conexion()
                if conexion:
                    c = conexion.cursor()
                    c.execute("UPDATE autorizaciones_pendientes SET estado='CANCELADA' WHERE id_solicitud=%s", (id_solicitud,))
                    conexion.commit()
                    conexion.close()
            except: pass
        popup.destroy()

    ctk.CTkButton(frm_btns, text="Cancelar Solicitud", fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"),
                  font=("Segoe UI", 12), width=130, height=40, command=cancelar).pack(side="left", padx=10)

    # --- BINDINGS Y ARRANQUE ---
    entry_user.bind("<Return>", validar_usuario_o_codigo)
    entry_pass.bind("<Return>", lambda e: validar_local())
    
    centrar_y_mostrar_ventana(popup)
    
    if modo_remoto_activo:
        popup.after(1500, chequear_estado_remoto) # Iniciar polling
        
    popup.grab_set()
