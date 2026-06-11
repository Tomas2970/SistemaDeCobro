# app/frontend/broadcast_manager.py
import customtkinter as ctk
import threading
import logging

logger = logging.getLogger(__name__)

def _chequear_y_marcar_mensajes_broadcast(usuario):
    conexion = None
    cursor = None
    try:
        from app.database import DB
        conexion = DB.conectar()
        if not conexion: return []
        cursor = conexion.cursor(dictionary=True)
        
        id_rol = usuario.get('id_rol')
        id_usuario = usuario.get('id_usuario')
        
        cursor.execute("""
            SELECT id_mensaje, contenido 
            FROM mensajes_broadcast 
            WHERE leido = FALSE 
            AND (
                destinatario_tipo = 'todos' OR 
                (destinatario_tipo = 'rol' AND destinatario_id = %s) OR
                (destinatario_tipo = 'usuario' AND destinatario_id = %s)
            )
            ORDER BY timestamp ASC
        """, (id_rol, id_usuario))
        mensajes = cursor.fetchall()
        
        if mensajes:
            ids = [m['id_mensaje'] for m in mensajes]
            format_strings = ','.join(['%s'] * len(ids))
            cursor.execute(f"UPDATE mensajes_broadcast SET leido = TRUE WHERE id_mensaje IN ({format_strings})", tuple(ids))
            conexion.commit()
            
        return [m['contenido'] for m in mensajes]
    except Exception as e:
        logger.error(f"Error checking broadcast messages: {e}")
        return []
    finally:
        try:
            if cursor: cursor.close()
            if conexion: conexion.close()
        except Exception:
            pass

class ToastBroadcast:
    """Notificación Toast para mensajes del administrador."""
    def __init__(self, parent, mensaje):
        import customtkinter as ctk
        self.toast = ctk.CTkToplevel(parent)
        self.toast.overrideredirect(True)
        self.toast.attributes("-topmost", True)
        self.toast.configure(fg_color="#8b5cf6") # Color violeta para admin broadcast
        
        ctk.CTkLabel(self.toast, text="📢 Mensaje del Administrador", font=("Segoe UI", 15, "bold"), text_color="white").pack(padx=15, pady=(10, 0), anchor="w")
        ctk.CTkLabel(self.toast, text=mensaje, font=("Segoe UI", 13), text_color="white", wraplength=280, justify="left").pack(padx=15, pady=(5, 10), anchor="w")
        
        screen_width = parent.winfo_screenwidth()
        width = 320
        height = 100
        x = screen_width - width - 20
        y = 60 # Aparece arriba a la derecha
        
        self.toast.geometry(f"{width}x{height}+{x}+{y}")
        self.toast.attributes("-alpha", 0.0)
        
        self.fade_in()
        self.toast.after(8000, self.fade_out) # 8 segundos para leerlo bien
        
    def fade_in(self):
        try:
            if self.toast.winfo_exists():
                alpha = self.toast.attributes("-alpha")
                if alpha < 0.95:
                    self.toast.attributes("-alpha", alpha + 0.1)
                    self.toast.after(30, self.fade_in)
        except Exception: pass
            
    def fade_out(self):
        try:
            if self.toast.winfo_exists():
                alpha = self.toast.attributes("-alpha")
                if alpha > 0.0:
                    self.toast.attributes("-alpha", alpha - 0.1)
                    self.toast.after(30, self.fade_out)
                else:
                    self.toast.destroy()
        except Exception: pass

def iniciar_polling_broadcast(parent, usuario):
    # Variable para evitar múltiples pollings si se llama varias veces (por ejemplo, al reconectarse)
    if hasattr(parent, '_broadcast_polling_activo') and parent._broadcast_polling_activo:
        return
    parent._broadcast_polling_activo = True

    def polling_mensajes():
        if not parent.winfo_exists(): 
            return
        
        def _check():
            nuevos_mensajes = _chequear_y_marcar_mensajes_broadcast(usuario)
            if nuevos_mensajes and parent.winfo_exists():
                parent.after(0, lambda: _mostrar_mensajes(nuevos_mensajes))
                
        def _mostrar_mensajes(mensajes):
            for i, msg in enumerate(mensajes):
                parent.after(i * 3000, lambda m=msg: ToastBroadcast(parent, m))
                
        threading.Thread(target=_check, daemon=True).start()
        
        # Volver a encolar el polling después de 15 segundos
        parent.after(15000, polling_mensajes)
        
    # Iniciar el primer polling a los 5 segundos
    parent.after(5000, polling_mensajes)
