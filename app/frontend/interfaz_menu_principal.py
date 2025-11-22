# app/frontend/interfaz_menu_principal.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)

# --- Permisos ---
try:
    from app.database.permisos import tiene_permiso
except Exception:
    messagebox.showerror("Error Crítico", "No se encontró 'permisos.py'. Los roles no funcionarán.")
    def tiene_permiso(usuario, accion): return True

# --- ¡NUEVO! Sistema de eventos de stock ---
try:
    from app.frontend.stock_event_manager import stock_events
except ImportError:
    print("ADVERTENCIA: No se pudo importar stock_event_manager. Las alertas no se actualizarán automáticamente.")
    class DummyStockEvents:
        def suscribir(self, callback): pass
        def desuscribir(self, callback): pass
        def limpiar(self): pass
    stock_events = DummyStockEvents()

# ===== Imports tolerantes =====
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
ui_historiales       = _safe_import("app.frontend.interfaz_historiales", "Historiales")
ui_gestion_usuarios  = _safe_import("app.frontend.interfaz_gestion_usuarios", "ui_gestion_usuarios")
ui_categorias = _safe_import("app.frontend.interfaz_categorias", "ui_categorias")
ui_gestion_proveedores = _safe_import("app.frontend.interfaz_gestion_proveedores", "ui_gestion_proveedores")

def _abrir_seguro(root: tk.Tk, backend, usuario: dict, fn, nombre: str):
    if not callable(fn):
        messagebox.showinfo("No disponible", f"La pantalla '{nombre}' no está integrada aún.", parent=root)
        return
    try:
        try: fn(root, backend, usuario)
        except TypeError:
            try: fn(root, backend)
            except TypeError: fn(root)
    except Exception as e:
        logger.exception("Error abriendo %s", nombre)
        messagebox.showerror("Error", f"No se pudo abrir '{nombre}':\n{e}", parent=root)


# ===== Estilos =====
def _configurar_estilos(root: tk.Tk):
    style = ttk.Style(root)
    try: style.theme_use("clam")
    except Exception: pass

    azul       = "#2563eb"
    verde      = "#16a34a"
    rojo       = "#ef4444"
    gris_bg    = "#f4f4f8"
    gris_btn   = "#1f2937"
    gris_hover = "#374151"
    foco_power = "#0ea5e9"

    root.configure(bg=gris_bg)

    style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"),
                    foreground="white", background=azul)

    style.configure("Menu.TButton", font=("Segoe UI", 12, "bold"),
                    padding=(18, 10), foreground="white", background=gris_btn)
    style.map("Menu.TButton",
              background=[("active", gris_hover), ("pressed", gris_hover), ("disabled", "#94a3b8")],
              foreground=[("disabled", "#e5e7eb")])

    style.configure("MenuFocus.TButton", font=("Segoe UI", 12, "bold"),
                    padding=(18, 10), foreground="white", background=foco_power)

    style.configure("Hero.TButton", font=("Segoe UI", 18, "bold"),
                    padding=(22, 14), foreground="white", background=verde)
    style.configure("HeroFocus.TButton", font=("Segoe UI", 18, "bold"),
                    padding=(22, 14), foreground="white", background="#128c3a")

    style.configure("Danger.TButton", font=("Segoe UI", 14, "bold"),
                    padding=(12, 8), foreground="white", background=rojo)
    style.map("Danger.TButton", background=[("active", "#dc2626"), ("pressed", "#dc2626")])

    style.configure("Section.TLabelframe", background=gris_bg, borderwidth=0, relief="flat")
    style.configure("Section.TLabelframe.Label", font=("Segoe UI", 12, "bold"),
                    foreground="#111827", background=gris_bg)

    style.configure("StockAlert.TLabel", font=("Segoe UI", 11, "bold"),
                    foreground="#dc2626", background=gris_bg)


def _titulo_superior(root: tk.Tk):
    barra = tk.Frame(root, bg="#2563eb", height=70)
    barra.pack(fill=tk.X)
    ttk.Label(barra, text="SUPERMERCADO DON ATILIO", style="Title.TLabel").pack(pady=14)


# ===== Navegación con flechas =====
class ArrowNavigator:
    def __init__(self, root: tk.Tk, cols: int):
        self.root = root
        self.cols = cols
        self.buttons: list[ttk.Button] = []
        self.index = 0

    def add(self, btn: ttk.Button, focus_style="MenuFocus.TButton", normal_style="Menu.TButton"):
        btn.configure(takefocus=True)
        btn._style_normal = normal_style
        btn._style_focus = focus_style
        btn.bind("<FocusIn>",  lambda e, b=btn: b.configure(style=b._style_focus))
        btn.bind("<FocusOut>", lambda e, b=btn: b.configure(style=b._style_normal))
        self.buttons.append(btn)

    def _menu_activo(self) -> bool:
        fg = self.root.focus_get()
        if not fg:
            return False
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel) and widget.winfo_exists():
                return False
        return fg.winfo_toplevel() is self.root and fg in self.buttons

    def bind_keys(self):
        def safe_move(delta):
            if self._menu_activo():
                self._move(delta)
                return "break"
            return None
        
        self.root.bind("<Up>",        lambda e: safe_move(-self.cols))
        self.root.bind("<Down>",      lambda e: safe_move(+self.cols))
        self.root.bind("<Left>",      lambda e: safe_move(-1))
        self.root.bind("<Right>",     lambda e: safe_move(+1))
        self.root.bind("<Return>",    self._enter)
        self.root.bind("<KP_Enter>",  self._enter)
        self.root.bind("<Escape>",    self._on_escape)

    def _on_escape(self, _):
        if not self._menu_activo():
            return None
        
        respuesta = messagebox.askyesno(
            "Cerrar Sesión",
            "¿Está seguro que desea cerrar sesión?",
            parent=self.root
        )
        if respuesta:
            self.root.destroy()
        return "break"

    def focus_index(self, idx: int):
        if not self.buttons:
            return
        self.index = max(0, min(idx, len(self.buttons) - 1))
        try:
            self.buttons[self.index].focus_set()
        except Exception:
            pass

    def _move(self, delta: int):
        if not self.buttons:
            return
        
        nuevo_indice = self.index + delta
        
        if nuevo_indice < 0:
            nuevo_indice = 0
        elif nuevo_indice >= len(self.buttons):
            nuevo_indice = len(self.buttons) - 1
        
        self.focus_index(nuevo_indice)

    def _enter(self, _):
        if not self._menu_activo():
            return None
        try:
            self.buttons[self.index].invoke()
        except Exception:
            self.root.bell()
        return "break"


# ===== UI principal =====
def crear_menu_principal(root: tk.Tk, backend, usuario: dict) -> None:
    try: root.state('zoomed')
    except tk.TclError: root.geometry("1024x700")

    root.title(f"🛒 Supermercado Don Atilio - Menú Principal (Usuario: {usuario.get('nombre','')} - Rol: {usuario.get('id_rol','')})")
    root.configure(bg="#f4f4f8")
    root.resizable(True, True)

    _configurar_estilos(root)
    _titulo_superior(root)

    # Contenedor central
    center = tk.Frame(root, bg=root["bg"])
    center.pack(pady=8)

    nav = ArrowNavigator(root, cols=2)

    # --- Botón VENTA PRIMERO ---
    hero_wrap = tk.Frame(center, bg=root["bg"])
    hero_wrap.grid(row=0, column=0, pady=6)

    btn_venta = None
    if tiene_permiso(usuario, 'realizar_ventas'):
        btn_venta = ttk.Button(
            hero_wrap, text="💳  VENTA",
            style="Hero.TButton",
            command=lambda: _abrir_seguro(root, backend, usuario, ui_venta, "Venta")
        )
        btn_venta.pack(fill="x", padx=0, pady=0)
        nav.add(btn_venta, focus_style="HeroFocus.TButton", normal_style="Hero.TButton")

    # --- Sección: OPERACIONES DIARIAS ---
    frame_ops = ttk.Labelframe(center, text="OPERACIONES DIARIAS", style="Section.TLabelframe")
    frame_ops.grid(row=1, column=0, pady=4)
    ops = tk.Frame(frame_ops, bg=root["bg"])
    ops.pack(padx=6, pady=6)

    def add_btn(parent, text, fn, permiso, col, row):
        if not tiene_permiso(usuario, permiso): return None
        b = ttk.Button(parent, text=text, style="Menu.TButton",
                       command=lambda: _abrir_seguro(root, backend, usuario, fn, text),
                       width=24)
        b.grid(row=row, column=col, padx=18, pady=6)
        nav.add(b)
        return b

    btn_compra = add_btn(ops, "🛒 Registrar Compra", ui_compra, 'registrar_compras', 0, 0)
    btn_ctacte = add_btn(ops, "🏦 Cuenta Corriente", ui_cuenta_corriente, 'gestionar_cuenta_corriente', 1, 0)

    # --- Sección: GESTIÓN ---
    frame_g = ttk.Labelframe(center, text="GESTIÓN", style="Section.TLabelframe")
    frame_g.grid(row=2, column=0, pady=4)
    gest = tk.Frame(frame_g, bg=root["bg"])
    gest.pack(padx=6, pady=6)

    btn_inv  = add_btn(gest, "📦 Inventario", ui_inventario, 'ver_inventario', 0, 0)
    btn_abm  = add_btn(gest, "🧰 Productos (ABM)", ui_productos, 'ver_productos', 1, 0)
    btn_hist = add_btn(gest, "🧾 Historiales", ui_historiales, 'ver_ventas', 0, 1)
    btn_tot  = add_btn(gest, "📊 Generador de Totales", ui_reportes, 'ver_reportes', 1, 1)
    btn_cli  = add_btn(gest, "👥 Clientes", ui_gestion_clientes, 'ver_clientes', 0, 2)
    btn_prov = add_btn(gest, "🚚 Proveedores", ui_gestion_proveedores, 'ver_proveedores', 1, 1)
    btn_usr  = add_btn(gest, "⚙️ Usuarios", ui_gestion_usuarios, 'ver_usuarios', 1, 2)
    btn_cat = add_btn(gest, "🏷️ Categorías", ui_categorias, 'ver_productos', 0, 3)
    

    # Ancho fijo para botón venta
    if btn_venta:
        btn_venta.configure(width=50)

    # --- Footer CON ALERTA POR EVENTOS ---
    footer = tk.Frame(root, bg=root["bg"])
    footer.pack(fill=tk.X, side=tk.BOTTOM, pady=4)

    # Crear el label de alerta (inicialmente vacío)
    lbl_alerta = ttk.Label(footer, text="", style="StockAlert.TLabel")
    lbl_alerta.pack(pady=2)

    # --- ¡SISTEMA DE EVENTOS! Actualización solo cuando cambia el stock ---
    def actualizar_alerta_stock():
        """
        Verifica el stock bajo y actualiza la alerta.
        Esta función se ejecuta:
        1. Al iniciar el menú
        2. Cada vez que se notifica un cambio de stock (venta/compra/modificación)
        """
        try:
            # Forzar actualización de la ventana
            root.update_idletasks()
            
            if hasattr(backend, "obtener_stock_bajo"):
                stock_bajo = backend.obtener_stock_bajo()
                if stock_bajo and len(stock_bajo) > 0:
                    texto = f"⚠️ ¡Atención! {len(stock_bajo)} producto(s) se encuentran por debajo del stock mínimo."
                    lbl_alerta.config(text=texto)
                    lbl_alerta.pack(pady=2)
                else:
                    lbl_alerta.config(text="")
                    lbl_alerta.pack_forget()
            
            # Forzar re-renderizado
            root.update()
        except Exception as e:
            logger.warning(f"Error verificando stock bajo: {e}")
    
    # Suscribirse a eventos de cambio de stock
    stock_events.suscribir(actualizar_alerta_stock)
    
    # Ejecutar la primera verificación inmediatamente
    actualizar_alerta_stock()
    
    # Limpiar suscripción al cerrar la ventana
    def on_closing():
        stock_events.desuscribir(actualizar_alerta_stock)
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    # --- FIN SISTEMA DE EVENTOS ---

    ttk.Button(footer, text="⛔  Cerrar Sesión", style="Danger.TButton",
               command=on_closing).pack(pady=2)

    # Navegación
    nav.bind_keys()
    if btn_venta:
        nav.focus_index(0)
    else:
        nav.focus_index(0)


def ui_menu_principal(*args, **kwargs) -> None:
    root    = kwargs.get("parent")   or (args[0] if len(args) > 0 else None)
    backend = kwargs.get("backend")  or (args[1] if len(args) > 1 else None)
    usuario = kwargs.get("usuario")  or (args[2] if len(args) > 2 else None)
    if root is None or backend is None or usuario is None:
        raise TypeError("ui_menu_principal requiere (root/parent, backend, usuario).")
    crear_menu_principal(root, backend, usuario)