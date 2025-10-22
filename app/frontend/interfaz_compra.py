import tkinter as tk
from tkinter import messagebox, Toplevel, Listbox, Scrollbar, SINGLE

def ui_compra(parent: tk.Misc, backend, usuario: dict) -> None:
    win = tk.Toplevel(parent)
    win.title("Interfaz de Compra")
    win.geometry("550x420")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)
    # Reusa aquí tu contenido; esta es la envoltura correcta con Toplevel(parent)
    win.grab_set()
