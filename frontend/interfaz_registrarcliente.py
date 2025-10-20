import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps

def registrar_cliente(backend, usuario):
    """
    Abre una ventana Toplevel para registrar un cliente.
    - backend: módulo database.DB (para llamar a funciones de BD)
    - usuario: dict del usuario logueado (por si querés auditar)
    """
    ventana = tk.Toplevel()
    ventana.title("Registrar Cliente")
    ventana.geometry("500x300")
    ventana.config(bg="#f4f4f8")
    ventana.resizable(False, False)

    # --- acciones ---
    def on_guardar():
        nombre = entry_nombre.get().strip()
        direccion = entry_direccion.get().strip()
        telefono = entry_telefono.get().strip()
        email = entry_email.get().strip()

        if not nombre or not direccion or not telefono or not email:
            messagebox.showwarning("Campos vacíos", "Por favor, complete todos los campos.")
            return

        # Guarda en la base de datos (usa DB.py)
        try:
            nuevo_id = backend.insertar_cliente(nombre, direccion, telefono, email)
            if nuevo_id:
                messagebox.showinfo("Cliente guardado", f"Cliente creado con ID {nuevo_id}")
                ventana.destroy()
            else:
                messagebox.showerror("Error", "No se pudo guardar el cliente.")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar cliente:\n{e}")
            return

    def on_cancelar():
        ventana.destroy()

    def mostrar_eslogan(_event=None):
        messagebox.showinfo("Don Atilio", "Gracias por confiar en Don Atilio")

    # --- imagen/logo opcional ---
    try:
        original_img = Image.open("Don atilio.png")
        resized_img = original_img.resize((90, 90))
        bordered_img = ImageOps.expand(resized_img, border=2, fill='black')
        img = ImageTk.PhotoImage(bordered_img)
        lbl_img = tk.Label(ventana, image=img, bg="#f4f4f8", cursor="hand2")
        lbl_img.image = img  # evitar GC
        lbl_img.place(x=395, y=5)
        lbl_img.bind("<Button-1>", mostrar_eslogan)
    except Exception as e:
        print("Error al cargar la imagen:", e)

    # --- UI ---
    tk.Label(ventana, text="Registrar Cliente", font=("Helvetica", 16, "bold"), bg="#f4f4f8", fg="#333").place(x=20, y=10)

    label_font = ("Helvetica", 10)
    entry_bg = "#ffffff"
    entry_bd = 1

    tk.Label(ventana, text="Nombre:", bg="#f4f4f8", font=label_font).place(x=40, y=60)
    entry_nombre = tk.Entry(ventana, width=30, bg=entry_bg, bd=entry_bd)
    entry_nombre.place(x=130, y=60)

    tk.Label(ventana, text="Dirección:", bg="#f4f4f8", font=label_font).place(x=40, y=95)
    entry_direccion = tk.Entry(ventana, width=30, bg=entry_bg, bd=entry_bd)
    entry_direccion.place(x=130, y=95)

    tk.Label(ventana, text="Teléfono:", bg="#f4f4f8", font=label_font).place(x=40, y=130)
    entry_telefono = tk.Entry(ventana, width=30, bg=entry_bg, bd=entry_bd)
    entry_telefono.place(x=130, y=130)

    tk.Label(ventana, text="Email:", bg="#f4f4f8", font=label_font).place(x=40, y=165)
    entry_email = tk.Entry(ventana, width=30, bg=entry_bg, bd=entry_bd)
    entry_email.place(x=130, y=165)

    boton_estilo = {
        "font": ("Helvetica", 10, "bold"),
        "width": 15,
        "bd": 1,
        "relief": "solid"
    }

    btn_guardar = tk.Button(ventana, text="Guardar Datos", bg="#4CAF50", fg="white", command=on_guardar, **boton_estilo)
    btn_guardar.place(x=80, y=220)

    btn_cancelar = tk.Button(ventana, text="Cancelar", bg="#f44336", fg="white", command=on_cancelar, **boton_estilo)
    btn_cancelar.place(x=240, y=220)

    # ❌ IMPORTANTE: NO LLAMAR ventana.mainloop() AQUÍ
    # El mainloop se ejecuta solo en main.py
