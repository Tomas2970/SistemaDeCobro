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

# --- Eventos de Stock ---
try:
    from app.frontend.stock_event_manager import stock_events
except ImportError:
    class DummyStockEvents:
        def suscribir(self, cb): pass
        def desuscribir(self, cb): pass
    stock_events = DummyStockEvents()

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

def _abrir_seguro(root, backend, usuario, fn, nombre, **kwargs):
    if not callable(fn):
        messagebox.showinfo("No disponible", f"La pantalla '{nombre}' no está integrada.", parent=root)
        return
    try:
        try: fn(root, backend, usuario, **kwargs)
        except TypeError: fn(root, backend)
    except Exception as e:
        logger.exception(f"Error abriendo {nombre}")
        messagebox.showerror("Error", f"Error al abrir {nombre}:\n{e}", parent=root)

# ===== Estilos =====
def _configurar_estilos(root):
    style = ttk.Style(root)
    try: style.theme_use("clam")
    except: pass
    
    azul, verde, rojo = "#2563eb", "#16a34a", "#ef4444"
    gris_bg, gris_btn = "#f4f4f8", "#1f2937"

    root.configure(bg=gris_bg)
    style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), foreground="white", background=azul)
    style.configure("Menu.TButton", font=("Segoe UI", 12, "bold"), padding=10, foreground="white", background=gris_btn)
    style.map("Menu.TButton", background=[("active", "#374151")])
    style.configure("Hero.TButton", font=("Segoe UI", 18, "bold"), padding=15, foreground="white", background=verde)
    style.map("Hero.TButton", background=[("active", "#15803d")])
    style.configure("Danger.TButton", font=("Segoe UI", 12, "bold"), foreground="white", background=rojo)
    style.configure("Section.TLabelframe", background=gris_bg, borderwidth=0)
    style.configure("Section.TLabelframe.Label", font=("Segoe UI", 12, "bold"), background=gris_bg, foreground="#111827")
    style.configure("StockAlert.TLabel", font=("Segoe UI", 11, "bold"), foreground="#dc2626", background=gris_bg)

# ===== UI Principal =====
def crear_menu_principal(root: tk.Tk, backend, usuario: dict) -> None:
    try: root.state('zoomed')
    except: root.geometry("1024x700")
    
    rol_id = usuario.get('id_rol')
    root.title(f"🛒 Supermercado Don Atilio - Usuario: {usuario.get('nombre')} (Rol: {rol_id})")
    _configurar_estilos(root)

    # Header
    header = tk.Frame(root, bg="#2563eb", height=70)
    header.pack(fill=tk.X)
    ttk.Label(header, text="SUPERMERCADO DON ATILIO", style="Title.TLabel").pack(pady=15)

    # Contenedor Central
    center = tk.Frame(root, bg="#f4f4f8")
    center.pack(pady=10)

    # 1. Botón GIGANTE de Venta
    if tiene_permiso(usuario, 'realizar_ventas'):
        btn_venta = ttk.Button(center, text="💳  REALIZAR VENTA", style="Hero.TButton",
                               command=lambda: _abrir_seguro(root, backend, usuario, ui_venta, "Venta"))
        btn_venta.grid(row=0, column=0, pady=15, ipadx=20)

    # 2. Sección OPERACIONES DIARIAS
    frm_ops = ttk.Labelframe(center, text="OPERACIONES DIARIAS", style="Section.TLabelframe")
    frm_ops.grid(row=1, column=0, pady=5)
    
    perm_cc = 'gestionar_cuenta_corriente' if tiene_permiso(usuario, 'gestionar_cuenta_corriente') else 'ver_cuenta_corriente'

    # --- CAMBIO: Se quitó "Reportes Ventas" de aquí ---
    botones_ops = [
        ("📦 Control de Caja", ui_reportes, 'abrir_caja', {'modo_vista': 'caja'}),
        ("🛒 Registrar Compra", ui_compra, 'registrar_compras', {}),
        ("📚 Cuenta Corriente", ui_cuenta_corriente, perm_cc, {})
    ]
    
    frame_grid_ops = tk.Frame(frm_ops, bg="#f4f4f8")
    frame_grid_ops.pack()
    
    col = 0
    for item in botones_ops:
        texto, funcion, permiso, args = item
        if tiene_permiso(usuario, permiso):
            b = ttk.Button(frame_grid_ops, text=texto, style="Menu.TButton", width=25,
                           command=lambda f=funcion, t=texto, kw=args: _abrir_seguro(root, backend, usuario, f, t, **kw))
            b.grid(row=0, column=col, padx=10, pady=5)
            col += 1

    # 3. Sección GESTIÓN
    frm_gest = ttk.Labelframe(center, text="GESTIÓN", style="Section.TLabelframe")
    frm_gest.grid(row=2, column=0, pady=15)
    
    frame_grid_gest = tk.Frame(frm_gest, bg="#f4f4f8")
    frame_grid_gest.pack()

    # --- CAMBIO: Se agregó "Reportes Ventas" aquí ---
    botones_gestion = [
        ("📦 Inventario", ui_inventario, 'ver_inventario', {}),
        ("🧰 Productos (ABM)", ui_productos, 'ver_productos', {}),
        ("🧾 Historiales", ui_historiales, 'ver_ventas', {}),
        ("🚚 Proveedores", ui_gestion_proveedores, 'ver_proveedores', {}),
        ("👥 Clientes", ui_gestion_clientes, 'ver_clientes', {}),
        ("🏷️ Categorías", ui_categorias, 'gestionar_categorias', {}), 
        ("⚙️ Usuarios", ui_gestion_usuarios, 'ver_usuarios', {}),
        # Nuevo lugar para Reportes:
        ("📊 Reportes Ventas", ui_reportes, 'ver_reportes', {'modo_vista': 'reportes'}) 
    ]

    row, col = 0, 0
    MAX_COLS = 2
    
    for item in botones_gestion:
        texto, funcion, permiso, args = item
        if tiene_permiso(usuario, permiso):
            btn = ttk.Button(frame_grid_gest, text=texto, style="Menu.TButton", width=25,
                             command=lambda f=funcion, t=texto, kw=args: _abrir_seguro(root, backend, usuario, f, t, **kw))
            btn.grid(row=row, column=col, padx=15, pady=8)
            
            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1

    # Footer
    footer = tk.Frame(root, bg="#f4f4f8")
    footer.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
    
    lbl_alerta = ttk.Label(footer, text="", style="StockAlert.TLabel")
    
    def check_stock():
        try:
            root.update_idletasks()
            if hasattr(backend, "obtener_stock_bajo"):
                bajos = backend.obtener_stock_bajo()
                if bajos:
                    lbl_alerta.config(text=f"⚠️ ¡Atención! {len(bajos)} productos con stock bajo.")
                    lbl_alerta.pack(pady=5)
                else:
                    lbl_alerta.pack_forget()
        except: pass

    stock_events.suscribir(check_stock)
    check_stock()

    def cerrar_sesion():
        caja_abierta = backend.obtener_session_abierta(id_usuario=usuario['id_usuario'])
        if caja_abierta:
            messagebox.showwarning("⚠️ Caja Abierta", "Debes cerrar tu caja antes de salir.", parent=root)
            return
        stock_events.desuscribir(check_stock)
        root.destroy()

    ttk.Button(footer, text="⛔ Cerrar Sesión", style="Danger.TButton", command=cerrar_sesion).pack(pady=5)
    root.protocol("WM_DELETE_WINDOW", cerrar_sesion)

def ui_menu_principal(parent, backend, usuario):
    crear_menu_principal(parent, backend, usuario)