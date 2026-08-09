# app/frontend/broadcast_manager.py
"""
Motor de polling y notificación para mensajes Broadcast.

Arquitectura v2 – polling por cursor de ID:
  - Reemplaza el flag `leido` por seguimiento local del último id_mensaje visto.
    Cada cliente guarda su propio cursor en memoria (_cursor[0]); la BD nunca
    recibe UPDATEs de lectura por polling.
    Esto resuelve el bug donde el primer usuario que polleaba marcaba el mensaje
    como leído para todos los demás, impidiendo que el resto lo recibiera.
  - Al iniciar sesión, el cursor se fija en MAX(id_mensaje) actual para no
    re-entregar mensajes históricos.
  - El admin emisor queda excluido automáticamente de recibir sus propios mensajes.
  - Los temporizadores after() se guardan siempre en _broadcast_after_id para
    cancelarlos limpiamente en detener_polling_broadcast().
  - Se captura tk.TclError en todas las rutas que accedan a widgets, evitando
    crashes al cerrar la sesión mientras hay toasts o polling activo.
"""
import tkinter as tk
import customtkinter as ctk
import threading
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────
# TOAST DE BROADCAST (notificación violeta)
# ─────────────────────────────────────────────────────
_TOAST_HEIGHT = 110          # Alto reservado por toast en pantalla
_TOAST_WIDTH  = 320
_TOAST_MARGIN = 10           # Separación entre toasts apilados

class ToastBroadcast:
    """
    Notificación Toast para mensajes del Administrador.
    Aparece apilada hacia abajo desde la esquina superior derecha,
    con fade-in / fade-out y auto-destrucción tras 8 segundos.
    """
    def __init__(self, parent, mensaje: str, slot: int = 0):
        """
        Args:
            parent:  Widget raíz del que hereda la ventana.
            mensaje: Texto a mostrar.
            slot:    Posición vertical (0 = más arriba). Permite apilar sin solapar.
        """
        try:
            self.toast = ctk.CTkToplevel(parent)
        except Exception:
            return  # Si el padre ya fue destruido, no hacer nada

        self.toast.overrideredirect(True)
        self.toast.attributes("-topmost", True)
        self.toast.configure(fg_color="#8b5cf6")

        ctk.CTkLabel(
            self.toast,
            text="📢 Mensaje del Administrador",
            font=("Segoe UI", 15, "bold"),
            text_color="white",
        ).pack(padx=15, pady=(10, 0), anchor="w")

        ctk.CTkLabel(
            self.toast,
            text=mensaje,
            font=("Segoe UI", 13),
            text_color="white",
            wraplength=280,
            justify="left",
        ).pack(padx=15, pady=(5, 10), anchor="w")

        try:
            screen_width = parent.winfo_screenwidth()
        except Exception:
            screen_width = 1920

        y_offset = 60 + slot * (_TOAST_HEIGHT + _TOAST_MARGIN)
        x_pos    = screen_width - _TOAST_WIDTH - 20

        self.toast.geometry(f"{_TOAST_WIDTH}x{_TOAST_HEIGHT}+{x_pos}+{y_offset}")
        self.toast.attributes("-alpha", 0.0)

        self._fade_in()
        self.toast.after(8000, self._fade_out)

    # ── animaciones ──────────────────────────────────
    def _fade_in(self):
        try:
            if self.toast.winfo_exists():
                alpha = self.toast.attributes("-alpha")
                if alpha < 0.95:
                    self.toast.attributes("-alpha", alpha + 0.1)
                    self.toast.after(30, self._fade_in)
        except (tk.TclError, Exception):
            pass  # Widget destruido durante la animación; ignorar silenciosamente

    def _fade_out(self):
        try:
            if self.toast.winfo_exists():
                alpha = self.toast.attributes("-alpha")
                if alpha > 0.0:
                    self.toast.attributes("-alpha", alpha - 0.1)
                    self.toast.after(30, self._fade_out)
                else:
                    self.toast.destroy()
        except (tk.TclError, Exception):
            pass  # Widget destruido durante la animación; ignorar silenciosamente


# ─────────────────────────────────────────────────────
# COLA DE TOASTS
# ─────────────────────────────────────────────────────
class _ToastQueue:
    """
    Cola FIFO de mensajes pendientes de mostrar.
    Muestra hasta MAX_SLOTS toasts simultáneos apilados verticalmente.
    Cuando un slot queda libre, despacha el siguiente mensaje de la cola.
    """
    MAX_SLOTS = 4

    def __init__(self, parent):
        self.parent = parent
        self._queue: list[str] = []
        self._slots: list[bool] = [False] * self.MAX_SLOTS  # True = ocupado

    def encolar(self, mensajes: list[str]) -> None:
        self._queue.extend(mensajes)
        self._despachar()

    def _despachar(self) -> None:
        while self._queue:
            slot = self._slot_libre()
            if slot is None:
                break
            msg = self._queue.pop(0)
            self._slots[slot] = True
            self._mostrar(msg, slot)

    def _slot_libre(self) -> int | None:
        for i, ocupado in enumerate(self._slots):
            if not ocupado:
                return i
        return None

    def _mostrar(self, mensaje: str, slot: int) -> None:
        try:
            if not self.parent.winfo_exists():
                self._slots[slot] = False
                return
        except (tk.TclError, Exception):
            self._slots[slot] = False
            return

        toast = ToastBroadcast(self.parent, mensaje, slot)

        # Liberar slot cuando el toast se destruya, luego despachar pendientes
        _duracion_total_ms = 8000 + _TOAST_HEIGHT * 30 + 300  # fade_out + margen

        def _liberar_slot():
            self._slots[slot] = False
            self._despachar()

        try:
            if hasattr(toast, 'toast') and toast.toast.winfo_exists():
                toast.toast.after(_duracion_total_ms, _liberar_slot)
        except (tk.TclError, Exception):
            self._slots[slot] = False


# ─────────────────────────────────────────────────────
# POLLING
# ─────────────────────────────────────────────────────
_POLLING_INTERVAL_MS = 15_000  # 15 segundos entre ciclos
_POLLING_INITIAL_MS  =  5_000  # Primera verificación a los 5 s del arranque


def iniciar_polling_broadcast(parent, usuario: dict, backend) -> None:
    """
    Arranca el ciclo de polling de mensajes broadcast para el usuario dado.

    Arquitectura v2 (polling por cursor de ID):
        - No marca mensajes como 'leídos' en la BD. Cada cliente lleva su propio
          cursor _cursor[0] en memoria. Esto permite que múltiples usuarios
          reciban el mismo broadcast sin que uno borre el estado del otro.
        - Antes del primer ciclo, inicializa _cursor[0] con MAX(id_mensaje) actual
          en un hilo daemon para no bloquear la UI y no re-entregar históricos.

    Args:
        parent:  Widget raíz (normalmente root_app).
        usuario: Diccionario de sesión {'id_usuario': int, 'id_rol': int, ...}.
        backend: Instancia de BackendAdapter. Se usa para consultar mensajes y
                 obtener el cursor inicial.

    Comportamiento:
        - Evita dobles arranques mediante el atributo _broadcast_polling_activo.
        - Guarda el ID del último after() en _broadcast_after_id para poder
          cancelarlo limpiamente al cerrar sesión (ver detener_polling_broadcast).
        - El admin (id_rol == 1) queda excluido de recibir sus propios mensajes.
    """
    # Guard: evitar doble arranque dentro de la misma sesión
    if getattr(parent, "_broadcast_polling_activo", False):
        return

    parent._broadcast_polling_activo = True
    parent._broadcast_after_id = None

    id_rol      = usuario.get("id_rol")
    id_usuario  = usuario.get("id_usuario")
    # Si el usuario es admin, su propio id se excluye como emisor
    excluir_admin = id_usuario if id_rol == 1 else None

    cola = _ToastQueue(parent)

    # Cursor local: lista de un elemento para ser mutable dentro de closures.
    # _cursor[0] almacena el id_mensaje más alto ya entregado al cliente.
    _cursor = [0]

    # ── Inicialización del cursor (hilo daemon) ────────────────────────────
    def _inicializar_cursor():
        """
        Obtiene MAX(id_mensaje) actual y fija el cursor para evitar re-entregar
        mensajes históricos. Solo luego agenda el primer ciclo en el hilo principal.
        """
        try:
            max_id = backend.obtener_ultimo_id_broadcast()
            _cursor[0] = max_id
        except Exception as e:
            logger.warning("polling broadcast – inicializar cursor: %s", e)
            # En caso de error, dejamos _cursor[0] = 0 (recibirá todos los mensajes).

        # Agendar el primer ciclo en el hilo principal de Tkinter
        try:
            if parent.winfo_exists():
                parent._broadcast_after_id = parent.after(
                    _POLLING_INITIAL_MS, _ciclo_polling
                )
        except (tk.TclError, Exception) as e:
            logger.error("iniciar_polling_broadcast: no se pudo agendar el primer ciclo: %s", e)
            parent._broadcast_polling_activo = False

    # ── Verificación en hilo secundario ───────────────────────────────────
    def _check_en_hilo():
        """
        Ejecutado en un daemon thread: consulta la BD con el cursor actual
        y, si hay mensajes nuevos, los pasa al hilo principal para mostrarlos.
        """
        try:
            mensajes = backend.obtener_mensajes_no_leidos(
                id_rol, id_usuario,
                excluir_id_admin=excluir_admin,
                ultimo_id=_cursor[0],
            )
        except Exception as e:
            logger.error("polling broadcast – obtener_mensajes_no_leidos: %s", e)
            return

        if not mensajes:
            return

        # Avanzar el cursor al id más alto recibido en este ciclo
        nuevo_id = max(m["id_mensaje"] for m in mensajes)
        _cursor[0] = nuevo_id

        textos = [m["contenido"] for m in mensajes]
        
        textos_normales = []
        force_logout = False
        for t in textos:
            if t.startswith("SYS:FORCE_LOGOUT"):
                force_logout = True
            else:
                textos_normales.append(t)

        # Volver al hilo principal para mostrar toasts y ejecutar comandos del sistema
        try:
            if parent.winfo_exists():
                if force_logout:
                    def _do_logout():
                        from app.frontend.custom_dialogs import mostrar_info
                        mostrar_info("Sesión Terminada", "Su sesión ha sido cerrada remotamente o sus permisos han cambiado.", parent=parent)
                        parent.quit()
                    parent.after(0, _do_logout)
                elif textos_normales:
                    parent.after(0, lambda t=textos_normales: cola.encolar(t))
        except (tk.TclError, Exception):
            pass  # Ventana ya destruida; ignorar

    # ── Ciclo principal ────────────────────────────────────────────────────
    def _ciclo_polling():
        """Callback ejecutado por Tkinter en el hilo principal cada _POLLING_INTERVAL_MS."""
        try:
            if not parent.winfo_exists():
                # La ventana fue destruida: detener el ciclo silenciosamente
                parent._broadcast_polling_activo = False
                parent._broadcast_after_id = None
                return
        except (tk.TclError, Exception):
            return  # El widget fue destruido; salir sin intentar más operaciones

        # Lanzar verificación en hilo secundario para no bloquear la UI
        threading.Thread(target=_check_en_hilo, daemon=True).start()

        # Reencolar y guardar referencia para poder cancelar
        try:
            parent._broadcast_after_id = parent.after(_POLLING_INTERVAL_MS, _ciclo_polling)
        except (tk.TclError, Exception):
            parent._broadcast_polling_activo = False
            parent._broadcast_after_id = None

    # Iniciar el cursor en un hilo daemon para no bloquear el arranque de la UI
    threading.Thread(target=_inicializar_cursor, daemon=True).start()


def detener_polling_broadcast(parent) -> None:
    """
    Cancela el ciclo de polling activo y libera los atributos del widget.
    Debe llamarse al cerrar sesión para evitar timers huérfanos.
    """
    after_id = getattr(parent, "_broadcast_after_id", None)
    if after_id:
        try:
            parent.after_cancel(after_id)
        except (tk.TclError, Exception):
            pass
    parent._broadcast_after_id       = None
    parent._broadcast_polling_activo = False
