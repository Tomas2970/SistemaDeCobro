import tkinter as tk
from tkinter import messagebox
from database.permisos import tiene_permiso
from frontend.interfaz_venta import interfaz_venta
from frontend.interfaz_inventario import interfaz_inventario
from frontend.interfaz_compra import interfaz_compra
from frontend.interfaz_registrarcliente import registrar_cliente
from frontend.interfaz_gestionusuario import interfaz_gestion_usuarios
from frontend.interfaz_reportes import interfaz_reportes

def interfaz_menu_principal(backend, usuario):
    """Menú principal del sistema según el rol del usuario"""
    ventana = tk.Tk()
    ventana.title(f"🏪 Sistema de Cobro - Bienvenido {usuario['nombre']}")
    ventana.geometry("900x600")
    ventana.config(bg="#f4f4f8")

    # ==============================
    # HEADER
    # ==============================
    frame_header = tk.Frame(ventana, bg="#2563eb", height=70)
    frame_header.pack(fill=tk.X)

    tk.Label(
        frame_header,
        text=f"🛒 Supermercado Don Atilio - Menú Principal",
        bg="#2563eb",
        fg="white",
        font=("Arial", 18, "bold"),
        pady=20
    ).pack()

    tk.Label(
        frame_header,
        text=f"Usuario: {usuario['nombre']}  |  Rol: {usuario['id_rol']}",
        bg="#2563eb",
        fg="white",
        font=("Arial", 10)
    ).pack()

    # ==============================
    # MENÚ DE OPCIONES
    # ==============================
    frame_menu = tk.Frame(ventana, bg="white", padx=50, pady=30)
    frame_menu.pack(pady=40)

    # BOTONES DINÁMICOS SEGÚN PERMISOS
    botones = []

    if tiene_permiso(usuario, 'realizar_ventas'):
        botones.append(("🧾 Realizar Venta", lambda: interfaz_venta(backend, usuario)))

    if tiene_permiso(usuario, 'ver_inventario'):
        botones.append(("📦 Inventario", lambda: interfaz_inventario(backend, usuario)))

    if tiene_permiso(usuario, 'registrar_compras'):
        botones.append(("🛍️ Compras", lambda: interfaz_compra(backend, usuario)))

    if tiene_permiso(usuario, 'crear_clientes'):
        botones.append(("👤 Registrar Cliente", lambda: registrar_cliente(backend, usuario)))

    if tiene_permiso(usuario, 'ver_usuarios'):
        botones.append(("👥 Gestión de Usuarios", lambda: interfaz_gestion_usuarios(backend, usuario)))

    if tiene_permiso(usuario, 'ver_reportes'):
        botones.append(("📊 Reportes", lambda: interfaz_reportes(backend, usuario)))

    # Mostrar botones
    for texto, comando in botones:
        tk.Button(
            frame_menu,
            text=texto,
            command=comando,
            width=25,
            height=2,
            font=("Arial", 12, "bold"),
            bg="#2563eb",
            fg="white",
            relief="flat",
            cursor="hand2"
        ).pack(pady=10)

    # ==============================
    # BOTÓN CERRAR SESIÓN
    # ==============================
    def cerrar_sesion():
        if messagebox.askyesno("Cerrar sesión", "¿Desea cerrar sesión y volver al inicio?"):
            ventana.destroy()
            from frontend.interfaz_iniciosesion import interfaz_login
            interfaz_login(backend)

    tk.Button(
        ventana,
        text="🔒 Cerrar Sesión",
        command=cerrar_sesion,
        bg="#ef4444",
        fg="white",
        font=("Arial", 11, "bold"),
        relief="flat",
        width=18
    ).pack(side=tk.BOTTOM, pady=20)

    ventana.mainloop()
