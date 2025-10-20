import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps

def interfaz_login(backend):
    ventana = tk.Tk()
    ventana.title("Inicio de Sesión - Don Atilio")
    ventana.geometry("500x280")
    ventana.config(bg="#f4f4f8")
    ventana.resizable(False, False)

    usuario_logeado = None  # Guarda el usuario validado

    def iniciar_sesion():
        nonlocal usuario_logeado
        usuario = entry_usuario.get().strip()
        contrasena = entry_contrasena.get().strip()

        if not usuario or not contrasena:
            messagebox.showwarning("Campos vacíos", "Por favor, complete todos los campos.")
            return

        # Validar usuario desde la base de datos
        usuario_db = backend.verificar_contraseña(usuario, contrasena)

        if usuario_db:
            usuario_logeado = usuario_db
            messagebox.showinfo("Inicio de sesión", f"Bienvenido, {usuario_db['nombre']}")
            ventana.destroy()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

    def salir():
        ventana.destroy()

    # ============================
    # Imagen decorativa (opcional)
    # ============================
    try:
        original_img = Image.open("Don atilio.png")
        resized_img = original_img.resize((80, 80))
        bordered_img = ImageOps.expand(resized_img, border=2, fill='black')
        img = ImageTk.PhotoImage(bordered_img)
        lbl_img = tk.Label(ventana, image=img, bg="#f4f4f8")
        lbl_img.image = img
        lbl_img.place(x=400, y=10)
    except Exception as e:
        print("No se pudo cargar la imagen:", e)

    # ============================
    # Campos del formulario
    # ============================
    tk.Label(ventana, text="Usuario:", bg="#f4f4f8").place(x=40, y=80)
    entry_usuario = tk.Entry(ventana, width=30)
    entry_usuario.place(x=150, y=80)

    tk.Label(ventana, text="Contraseña:", bg="#f4f4f8").place(x=40, y=120)
    entry_contrasena = tk.Entry(ventana, width=30, show="*")
    entry_contrasena.place(x=150, y=120)

    # ============================
    # Botones
    # ============================
    tk.Button(
        ventana,
        text="Iniciar Sesión",
        bg="#4CAF50",
        fg="white",
        width=15,
        command=iniciar_sesion
    ).place(x=150, y=180)

    tk.Button(
        ventana,
        text="Salir",
        bg="#f44336",
        fg="white",
        width=10,
        command=salir
    ).place(x=320, y=180)

    ventana.mainloop()
    return usuario_logeado
