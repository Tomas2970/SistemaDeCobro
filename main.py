import tkinter as tk
from tkinter import messagebox
import importlib

try:
    # Conexión dinámica al backend
    backend = importlib.import_module("database.DB")

    conn = backend.conectar()
    if conn.is_connected():
        print("✅ Conectado correctamente a la base de datos MySQL.")
        conn.close()
    else:
        raise Exception("No se pudo establecer la conexión con MySQL.")

except Exception as e:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error de conexión", f"No se pudo conectar a MySQL:\n{e}")
    root.destroy()
    raise SystemExit("No se pudo conectar a la base de datos MySQL. El sistema se cerrará.")


# =============================
# IMPORTAR INTERFACES
# =============================
from frontend.interfaz_iniciosesion import interfaz_login
from frontend.interfaz_menu_principal import interfaz_menu_principal


# =============================
# FUNCIÓN PRINCIPAL
# =============================
def iniciar_sistema():
    """Inicia el sistema: login → menú principal"""
    usuario_logeado = interfaz_login(backend)
    if usuario_logeado:
        interfaz_menu_principal(backend, usuario_logeado)


if __name__ == "__main__":
    iniciar_sistema()
