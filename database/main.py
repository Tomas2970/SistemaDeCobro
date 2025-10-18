import tkinter as tk
from tkinter import messagebox
from DB import verificar_contraseña  # Tu función de DB

def intentar_login():
    usuario = entry_usuario.get()
    contraseña = entry_contraseña.get()
    
    if not usuario or not contraseña:
        messagebox.showwarning("Error", "Por favor ingrese usuario y contraseña")
        return

    usuario_db = verificar_contraseña(usuario, contraseña)
    if usuario_db:
        messagebox.showinfo("Éxito", f"Bienvenido {usuario_db['nombre']} ({usuario_db['rol']})")
        # Aquí podrías llamar a la siguiente pantalla, por ejemplo:
        mostrar_frame(frame_menu_principal)
    else:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")

def mostrar_frame(frame):
    frame.tkraise()

root = tk.Tk()
root.title("Sistema de Cobro - Login")
root.geometry("400x200")

# --------------------- Frames ---------------------
frame_login = tk.Frame(root)
frame_menu_principal = tk.Frame(root)  # Frame siguiente, vacío por ahora

for frame in (frame_login, frame_menu_principal):
    frame.grid(row=0, column=0, sticky="nsew")

# --------------------- Frame Login ---------------------
tk.Label(frame_login, text="Usuario:").pack(pady=(20, 5))
entry_usuario = tk.Entry(frame_login)
entry_usuario.pack()

tk.Label(frame_login, text="Contraseña:").pack(pady=(10, 5))
entry_contraseña = tk.Entry(frame_login, show="*")
entry_contraseña.pack()

tk.Button(frame_login, text="Iniciar Sesión", command=intentar_login).pack(pady=20)

# --------------------- Frame Menu Principal ---------------------
tk.Label(frame_menu_principal, text="MENÚ PRINCIPAL").pack(pady=20)
tk.Button(frame_menu_principal, text="Cerrar sesión", command=lambda: mostrar_frame(frame_login)).pack()

# Mostrar frame inicial
mostrar_frame(frame_login)

root.mainloop()
