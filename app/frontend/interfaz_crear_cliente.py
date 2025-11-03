# app/frontend/interfaz_crear_cliente.py
# (Este era el antiguo 'interfaz_registrarcliente.py')
import tkinter as tk
from tkinter import messagebox

def ui_crear_cliente(parent: tk.Misc, backend, usuario: dict):
    win = tk.Toplevel(parent)
    win.title("Crear/Editar Cliente")
    win.geometry("500x340")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    def on_guardar():
        nombre = entry_nombre.get().strip()
        dni = entry_dni.get().strip()
        direccion = entry_direccion.get().strip()
        telefono = entry_telefono.get().strip()
        email = entry_email.get().strip()
        
        if not nombre:
            messagebox.showwarning("Campos vacíos", "El campo 'Nombre' es obligatorio.", parent=win)
            return
        
        try:
            # Esta llamada ahora SÍ coincide con el backend (envía 5 argumentos)
            nuevo_id = backend.insertar_cliente(nombre, dni, direccion, telefono, email)
            
            if nuevo_id:
                messagebox.showinfo("Cliente guardado", f"Cliente '{nombre}' creado con ID {nuevo_id}", parent=win)
                win.destroy()
            else:
                messagebox.showerror("Error", "No se pudo guardar el cliente.\nVerifique que el DNI o Email no estén duplicados.", parent=win)
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar cliente:\n{e}", parent=win)

    tk.Label(win, text="Nombre (*):", bg="#f4f4f8").place(x=40, y=60)
    entry_nombre = tk.Entry(win, width=40); entry_nombre.place(x=130, y=60)
    
    tk.Label(win, text="DNI:", bg="#f4f4f8").place(x=40, y=95)
    entry_dni = tk.Entry(win, width=40); entry_dni.place(x=130, y=95)
    
    tk.Label(win, text="Dirección:", bg="#f4f4f8").place(x=40, y=130)
    entry_direccion = tk.Entry(win, width=40); entry_direccion.place(x=130, y=130)
    
    tk.Label(win, text="Teléfono:", bg="#f4f4f8").place(x=40, y=165)
    entry_telefono = tk.Entry(win, width=40); entry_telefono.place(x=130, y=165)
    
    tk.Label(win, text="Email:", bg="#f4f4f8").place(x=40, y=200)
    entry_email = tk.Entry(win, width=40); entry_email.place(x=130, y=200)

    tk.Button(win, text="Guardar Datos", bg="#4CAF50", fg="white", width=15, command=on_guardar).place(x=130, y=260)
    tk.Button(win, text="Cancelar", bg="#f44336", fg="white", width=15, command=lambda: win.destroy()).place(x=280, y=260)
    
    win.grab_set()
    win.transient(parent) # Asegura que sea un popup