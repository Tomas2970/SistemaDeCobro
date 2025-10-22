# app/frontend/interfaz_menu_principal.py
import tkinter as tk
from tkinter import messagebox
from app.database.permisos_wrapper import tiene_permiso
from app.frontend.interfaz_venta import ui_venta
from app.frontend.interfaz_inventario import ui_inventario
from app.frontend.interfaz_compra import ui_compra
from app.frontend.interfaz_registrarcliente import ui_registrar_cliente
from app.frontend.interfaz_reportes import ui_reportes
from app.frontend.interfaz_iniciosesion import ui_login
from app.frontend.interfaz_productos import ui_productos  # ABM

def ui_menu_principal(parent: tk.Misc, backend, usuario: dict) -> None:
    for w in parent.winfo_children():
        w.destroy()

    root = parent  # alias

    header = tk.Frame(root, bg="#2563eb", height=84)
    header.pack(fill=tk.X)
    tk.Label(
        header,
        text="🛒 Supermercado Don Atilio - Menú Principal",
        bg="#2563eb", fg="white", font=("Arial", 18, "bold"), pady=16
    ).pack()
    tk.Label(
        header,
        text=f"Usuario: {usuario.get('nombre','')}  |  Rol: {usuario.get('id_rol','')}",
        bg="#2563eb", fg="white", font=("Arial", 10)
    ).pack()

    menu = tk.Frame(root, bg="white", padx=50, pady=30)
    menu.pack(pady=30)

    def add_btn(text, cmd):
        tk.Button(
            menu, text=text, command=cmd, width=28, height=2,
            font=("Arial", 12, "bold"), bg="#2563eb", fg="white",
            relief="flat", cursor="hand2"
        ).pack(pady=10)

    if tiene_permiso(usuario, 'realizar_ventas'):
        add_btn("🧾 Realizar Venta", lambda: ui_venta(root, backend, usuario))
    if tiene_permiso(usuario, 'ver_inventario'):
        add_btn("📦 Inventario", lambda: ui_inventario(root, backend, usuario))
    if tiene_permiso(usuario, 'registrar_compras'):
        add_btn("🛍️ Compras", lambda: ui_compra(root, backend, usuario))
    if tiene_permiso(usuario, 'crear_clientes'):
        add_btn("👤 Registrar Cliente", lambda: ui_registrar_cliente(root, backend, usuario))
    if tiene_permiso(usuario, 'ver_reportes'):
        add_btn("📊 Reportes", lambda: ui_reportes(root, backend, usuario))
    if tiene_permiso(usuario, 'ver_inventario'):
        add_btn("🧰 Productos (ABM)", lambda: ui_productos(root, backend, usuario))

    def cerrar_sesion():
        if not messagebox.askyesno("Cerrar sesión", "¿Volver al inicio de sesión?"):
            return
        root.withdraw()
        nuevo = ui_login(root, backend)
        if nuevo:
            root.deiconify()
            ui_menu_principal(root, backend, nuevo)
        else:
            root.destroy()

    tk.Button(
        root, text="🔒 Cerrar Sesión", command=cerrar_sesion,
        bg="#ef4444", fg="white", font=("Arial", 11, "bold"),
        relief="flat", width=18
    ).pack(side=tk.BOTTOM, pady=16)
