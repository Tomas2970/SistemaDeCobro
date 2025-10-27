# app/frontend/interfaz_menu_principal.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)

# ===== Imports de pantallas (con tolerancia a nombres distintos) =====
# Inventario
try:
    from app.frontend.interfaz_inventario import ui_inventario
except Exception:
    ui_inventario = None

# Productos (ABM)
try:
    from app.frontend.interfaz_productos import ui_productos
except Exception:
    ui_productos = None

# Venta
try:
    from app.frontend.interfaz_venta import ui_venta
except Exception:
    ui_venta = None

# Reportes
try:
    from app.frontend.interfaz_reportes import ui_reportes
except Exception:
    ui_reportes = None

# Registrar Cliente (tolerar nombres distintos)
ui_registrar_cliente = None
try:
    from app.frontend.interfaz_registrarcliente import ui_registrarcliente as _u1
    ui_registrar_cliente = _u1
except Exception:
    try:
        from app.frontend.interfaz_registrarcliente import ui_registrar_cliente as _u2
        ui_registrar_cliente = _u2
    except Exception:
        ui_registrar_cliente = None

# Cuenta Corriente (si no existe, mostramos mensaje)
ui_cuenta_corriente = None
try:
    from app.frontend.interfaz_cuentacorriente import ui_cuenta_corriente as _u3
    ui_cuenta_corriente = _u3
except Exception:
    ui_cuenta_corriente = None


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
            fn(root, backend, usuario)  # mayoría pide los 3
        except TypeError:
            try:
                fn(root, backend)       # algunas no usan 'usuario'
            except TypeError:
                fn(root)                # último intento
    except Exception as e:
        logger.exception("Error abriendo %s", nombre)
        messagebox.showerror("Error", f"No se pudo abrir '{nombre}':\n{e}", parent=root)


def _configurar_estilos(root: tk.Tk):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Paleta
    primary = "#2563eb"
    success = "#16a34a"
    danger = "#ef4444"
    neutral = "#334155"

    style.configure("Title.TLabel", font=("Helvetica", 16, "bold"), foreground="white", background=primary)
    style.configure("Sub.TLabel", font=("Helvetica", 10), foreground="#111827", background="#f4f4f8")

    # Botón base
    style.configure("Menu.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8), foreground="white", background=neutral)
    style.map("Menu.TButton",
              background=[("active", "#475569")], foreground=[("disabled", "#cbd5e1")])

    # Variantes
    style.configure("Primary.Menu.TButton", background=primary)
    style.map("Primary.Menu.TButton", background=[("active", "#1d4ed8")])

    style.configure("Success.Menu.TButton", background=success)
    style.map("Success.Menu.TButton", background=[("active", "#15803d")])

    style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"),
                    padding=(10, 6), foreground="white", background=danger)
    style.map("Danger.TButton", background=[("active", "#dc2626")])


def crear_menu_principal(root: tk.Tk, backend, usuario: dict) -> None:
    # Ventana
    root.title("🛒 Supermercado Don Atilio - Menú Principal")
    root.geometry("760x560")
    root.configure(bg="#f4f4f8")
    root.resizable(False, False)

    _configurar_estilos(root)

    # Header
    header = tk.Frame(root, bg="#2563eb", height=68)
    header.pack(fill=tk.X)
    ttk.Label(header, text="Supermercado Don Atilio — Menú Principal", style="Title.TLabel").pack(pady=16)

    # Info usuario
    ttk.Label(
        root,
        text=f"Usuario: {usuario.get('nombre','')}  |  Rol: {usuario.get('id_rol','')}",
        style="Sub.TLabel",
    ).pack(pady=(8, 2))

    # Contenedor botones
    cont = tk.Frame(root, bg="#f4f4f8")
    cont.pack(expand=True, pady=8)

    # Botones (grid 3×2)
    btns = [
        ("📦 Inventario", lambda: _abrir_seguro(root, backend, usuario, ui_inventario, "Inventario"), "Menu.TButton"),
        ("🧰 Productos (ABM)", lambda: _abrir_seguro(root, backend, usuario, ui_productos, "Productos"), "Primary.Menu.TButton"),
        ("🧾 Reportes", lambda: _abrir_seguro(root, backend, usuario, ui_reportes, "Reportes"), "Menu.TButton"),
        ("💳 Venta", lambda: _abrir_seguro(root, backend, usuario, ui_venta, "Venta"), "Success.Menu.TButton"),
        ("➕ Registrar cliente", lambda: _abrir_seguro(root, backend, usuario, ui_registrar_cliente, "Registrar cliente"), "Menu.TButton"),
        ("🏦 Cuenta corriente", lambda: _abrir_seguro(root, backend, usuario, ui_cuenta_corriente, "Cuenta corriente"), "Menu.TButton"),
    ]

    for i, (text, cmd, sty) in enumerate(btns):
        r, c = divmod(i, 2)
        ttk.Button(cont, text=text, style=sty, command=cmd, width=26).grid(row=r, column=c, padx=14, pady=12)

    # Cerrar sesión
    ttk.Button(root, text="⛔ Cerrar sesión", style="Danger.TButton",
               command=lambda: root.destroy()).pack(pady=14)


# Alias compat para mains antiguos
def ui_menu_principal(*args, **kwargs) -> None:
    root = kwargs.get("parent") or (args[0] if len(args) > 0 else None)
    backend = kwargs.get("backend") or (args[1] if len(args) > 1 else None)
    usuario = kwargs.get("usuario") or (args[2] if len(args) > 2 else None)
    if root is None or backend is None or usuario is None:
        raise TypeError("ui_menu_principal requiere (root/parent, backend, usuario).")
    crear_menu_principal(root, backend, usuario)
