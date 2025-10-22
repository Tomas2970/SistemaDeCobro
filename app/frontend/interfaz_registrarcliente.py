import tkinter as tk
from tkinter import messagebox

def ui_registrar_cliente(parent: tk.Misc, backend, usuario: dict) -> None:
    win = tk.Toplevel(parent)
    win.title("Registrar Cliente")
    win.geometry("500x300")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    def on_guardar():
        nombre = entry_nombre.get().strip()
        direccion = entry_direccion.get().strip()
        telefono = entry_telefono.get().strip()
        email = entry_email.get().strip()
        if not all([nombre, direccion, telefono, email]):
            messagebox.showwarning("Campos vacíos", "Complete todos los campos.")
            return
        try:
            nuevo_id = backend.insertar_cliente(nombre, direccion, telefono, email)
            if nuevo_id:
                messagebox.showinfo("Cliente guardado", f"Cliente creado con ID {nuevo_id}")
                win.destroy()
            else:
                messagebox.showerror("Error", "No se pudo guardar el cliente.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar cliente:\n{e}")

    tk.Label(win, text="Nombre:", bg="#f4f4f8").place(x=40, y=60)
    entry_nombre = tk.Entry(win, width=30); entry_nombre.place(x=130, y=60)
    tk.Label(win, text="Dirección:", bg="#f4f4f8").place(x=40, y=95)
    entry_direccion = tk.Entry(win, width=30); entry_direccion.place(x=130, y=95)
    tk.Label(win, text="Teléfono:", bg="#f4f4f8").place(x=40, y=130)
    entry_telefono = tk.Entry(win, width=30); entry_telefono.place(x=130, y=130)
    tk.Label(win, text="Email:", bg="#f4f4f8").place(x=40, y=165)
    entry_email = tk.Entry(win, width=30); entry_email.place(x=130, y=165)

    tk.Button(win, text="Guardar Datos", bg="#4CAF50", fg="white", command=on_guardar).place(x=80, y=220)
    tk.Button(win, text="Cancelar", bg="#f44336", fg="white", command=lambda: win.destroy()).place(x=240, y=220)
    win.grab_set()
