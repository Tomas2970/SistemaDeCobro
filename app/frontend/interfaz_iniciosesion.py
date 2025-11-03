# app/frontend/interfaz_iniciosesion.py
import tkinter as tk
from tkinter import messagebox

def ui_login(parent: tk.Misc, backend):
    win = tk.Toplevel(parent)
    win.title("Inicio de Sesión - Don Atilio")
    win.geometry("500x280")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    usuario_logeado = None

    tk.Label(win, text="Usuario:", bg="#f4f4f8").place(x=40, y=80)
    entry_usuario = tk.Entry(win, width=30); entry_usuario.place(x=150, y=80)
    
    tk.Label(win, text="Contraseña:", bg="#f4f4f8").place(x=40, y=120)
    entry_contrasena = tk.Entry(win, width=30, show="*"); entry_contrasena.place(x=150, y=120)

    def iniciar_sesion(event=None): # Añadimos 'event=None' para que acepte la llamada del bind
        nonlocal usuario_logeado
        usuario = entry_usuario.get().strip()
        contrasena = entry_contrasena.get().strip()
        
        if not usuario or not contrasena:
            messagebox.showwarning("Campos vacíos", "Complete todos los campos.")
            return
            
        usuario_db = backend.verificar_contraseña(usuario, contrasena)
        
        if usuario_db:
            usuario_logeado = usuario_db
            win.destroy()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")
            entry_contrasena.delete(0, tk.END) # Limpia la contraseña incorrecta

    def salir():
        win.destroy()

    # --- ¡CAMBIO! ---
    # Hacemos que la tecla "Enter" llame a la función 'iniciar_sesion'
    entry_usuario.bind("<Return>", lambda e: entry_contrasena.focus()) # Enter en usuario pasa a contraseña
    entry_contrasena.bind("<Return>", iniciar_sesion) # Enter en contraseña inicia sesión

    tk.Button(win, text="Iniciar Sesión", bg="#4CAF50", fg="white", width=15, command=iniciar_sesion).place(x=150, y=180)
    tk.Button(win, text="Salir", bg="#f44336", fg="white", width=10, command=salir).place(x=320, y=180)

    # Pone el foco en el primer campo de texto
    entry_usuario.focus()

    win.grab_set()
    win.wait_window()
    return usuario_logeado