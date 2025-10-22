import tkinter as tk
from tkinter import messagebox
from app.frontend.interfaz_iniciosesion import ui_login
from app.frontend.interfaz_menu_principal import ui_menu_principal
from app.database.backend_adapter import BackendAdapter

def main() -> None:
    root = tk.Tk()
    root.withdraw()
    backend = BackendAdapter()

    usuario = ui_login(parent=root, backend=backend)
    if not usuario:
        messagebox.showinfo("Salida", "Sesión no iniciada.")
        root.destroy()
        return

    root.deiconify()
    root.title(f"🏪 Sistema de Cobro - Bienvenido {usuario.get('nombre','')}")
    root.geometry("900x600")
    ui_menu_principal(parent=root, backend=backend, usuario=usuario)
    root.mainloop()

if __name__ == "__main__":
    main()
