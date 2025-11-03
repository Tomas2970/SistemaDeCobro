# app/frontend/interfaz_menu_principal.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)

# --- ¡Importa la lógica de permisos! ---
try:
    # (Buscamos el archivo en app/permisos.py)
    from app.database.permisos import tiene_permiso 
except ImportError:
    # (Si falla, probamos en app/database/permisos.py)
    try:
        from app.database.permisos import tiene_permiso
    except ImportError:
        messagebox.showerror("Error Crítico", "No se encontró 'permisos.py'. Los roles no funcionarán.")
        def tiene_permiso(usuario, accion):
            return True 

# ===== Imports de pantallas =====
try:
    from app.frontend.interfaz_inventario import ui_inventario
except Exception:
    ui_inventario = None
try:
    from app.frontend.interfaz_productos import ui_productos
except Exception:
    ui_productos = None
try:
    from app.frontend.interfaz_venta import ui_venta
except Exception:
    ui_venta = None
try:
    from app.frontend.interfaz_reportes import ui_reportes
except Exception:
    ui_reportes = None
try:
    from app.frontend.interfaz_gestion_clientes import ui_gestion_clientes
except Exception:
    ui_gestion_clientes = None
try:
    from app.frontend.interfaz_cuenta_corriente import ui_cuenta_corriente
except Exception:
    ui_cuenta_corriente = None
try:
    from app.frontend.interfaz_compra import ui_compra
except Exception:
    ui_compra = None
try:
    from app.frontend.interfaz_historiales import ui_historiales
except Exception:
    ui_historiales = None
try:
    from app.frontend.interfaz_gestion_usuarios import ui_gestion_usuarios
except Exception:
    ui_gestion_usuarios = None


# ===== Helper para abrir ventanas sin romper =====
def _abrir_seguro(root: tk.Tk, backend, usuario: dict, fn, nombre: str):
    if not callable(fn):
        messagebox.showinfo(
            "No disponible",
            f"La pantalla '{nombre}' todavía no está integrada.\nPodés agregarla más tarde.",
            parent=root,
        )
        return
    try:
        try:
            fn(root, backend, usuario) 
        except TypeError:
            try:
                fn(root, backend) 
            except TypeError:
                fn(root)
    except Exception as e:
        logger.exception("Error abriendo %s", nombre)
        messagebox.showerror("Error", f"No se pudo abrir '{nombre}':\n{e}", parent=root)


# ===== Configuración de Estilos (Con colores) =====
def _configurar_estilos(root: tk.Tk):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    primary = "#2563eb"
    success = "#16a34a"
    danger = "#ef4444"
    neutral = "#334155"
    style.configure("Title.TLabel", font=("Helvetica", 16, "bold"), foreground="white", background=primary)
    style.configure("Sub.TLabel", font=("Helvetica", 10), foreground="#111827", background="#f4f4f8")
    style.configure("Menu.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8), foreground="white", background=neutral)
    style.map("Menu.TButton",
              background=[("active", "#475569"), ("disabled", "#94a3b8")], 
              foreground=[("disabled", "#e2e8f0")])
    style.configure("Primary.Menu.TButton", background=primary)
    style.map("Primary.Menu.TButton", background=[("active", "#1d4ed8"), ("disabled", "#94a3b8")])
    style.configure("Success.Menu.TButton", background=success)
    style.map("Success.Menu.TButton", background=[("active", "#15803d"), ("disabled", "#94a3b8")])
    style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"),
                    padding=(10, 6), foreground="white", background=danger)
    style.map("Danger.TButton", background=[("active", "#dc2626")])


def crear_menu_principal(root: tk.Tk, backend, usuario: dict) -> None:
    
    try:
        root.state('zoomed') # Inicia maximizado
    except tk.TclError:
        root.geometry("1024x768") 
            
    root.title(f"🛒 Supermercado Don Atilio - Menú Principal (Usuario: {usuario.get('nombre','')} - Rol: {usuario.get('id_rol','')})") 
    root.configure(bg="#f4f4f8")
    root.resizable(True, True)

    _configurar_estilos(root)

    # Header
    header = tk.Frame(root, bg="#2563eb", height=68)
    header.pack(fill=tk.X)
    ttk.Label(header, text="Supermercado Don Atilio — Menú Principal", style="Title.TLabel").pack(pady=16)

    # Contenedor botones (centrado)
    cont = tk.Frame(root, bg="#f4f4f8")
    cont.pack(expand=True)

    # Lista de botones
    botones_config = [
        ("📦 Inventario", 
         lambda: _abrir_seguro(root, backend, usuario, ui_inventario, "Inventario"), 
         "Menu.TButton", 
         'ver_inventario'),
         
        ("🧰 Productos (ABM)", 
         lambda: _abrir_seguro(root, backend, usuario, ui_productos, "Productos"), 
         "Primary.Menu.TButton", 
         'ver_productos'),
         
        ("💳 Venta", 
         lambda: _abrir_seguro(root, backend, usuario, ui_venta, "Venta"), 
         "Success.Menu.TButton", 
         'realizar_ventas'),
         
        ("🛒 Registrar Compra", 
         lambda: _abrir_seguro(root, backend, usuario, ui_compra, "Compra"), 
         "Menu.TButton", 
         'registrar_compras'),
         
        ("🧾 Reportes", 
         lambda: _abrir_seguro(root, backend, usuario, ui_reportes, "Reportes"), 
         "Menu.TButton", 
         'ver_reportes'),
         
        ("📋 Historiales (Venta/Compra)", 
         lambda: _abrir_seguro(root, backend, usuario, ui_historiales, "Historiales"), 
         "Menu.TButton", 
         'ver_ventas'),
         
        ("🧑‍🤝‍🧑 Gestión de Clientes", 
         lambda: _abrir_seguro(root, backend, usuario, ui_gestion_clientes, "Gestión de Clientes"), 
         "Menu.TButton", 
         'ver_clientes'),
         
        ("🏦 Cuenta corriente", 
         lambda: _abrir_seguro(root, backend, usuario, ui_cuenta_corriente, "Cuenta corriente"), 
         "Menu.TButton", 
         'gestionar_cuenta_corriente'),
         
        ("⚙️ Gestión de Usuarios", 
         lambda: _abrir_seguro(root, backend, usuario, ui_gestion_usuarios, "Gestión de Usuarios"), 
         "Menu.TButton", 
         'ver_usuarios'),
    ]

    for i, (text, cmd, sty, permiso) in enumerate(botones_config):
        r, c = divmod(i, 2)
        
        estado_btn = "normal" if tiene_permiso(usuario, permiso) else "disabled"
        
        btn = ttk.Button(cont, text=text, style=sty, command=cmd, width=28, state=estado_btn)
        btn.grid(row=r, column=c, padx=20, pady=15)

    # Cerrar sesión (Vuelve al login)
    ttk.Button(root, text="⛔ Cerrar sesión", style="Danger.TButton",
               command=root.destroy).pack(pady=20)


# Alias compat para mains antiguos
def ui_menu_principal(*args, **kwargs) -> None:
    root = kwargs.get("parent") or (args[0] if len(args) > 0 else None)
    backend = kwargs.get("backend") or (args[1] if len(args) > 1 else None)
    usuario = kwargs.get("usuario") or (args[2] if len(args) > 2 else None)
    if root is None or backend is None or usuario is None:
        raise TypeError("ui_menu_principal requiere (root/parent, backend, usuario).")
    crear_menu_principal(root, backend, usuario)
