import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk, ImageOps

def interfaz_gestion_usuarios():
    ventana = tk.Tk()
    ventana.title("Gestión de Usuarios")
    ventana.geometry("550x240")
    ventana.config(bg="#f4f4f8")
    ventana.resizable(False, False)

    # Función para mostrar eslogan al hacer click en la imagen
    def mostrar_eslogan(event=None):
        messagebox.showinfo("Don Atilio", "Gracias por confiar en Don Atilio")

    # Cargar imagen
    try:
        original_img = Image.open("Don atilio.png")
        resized_img = original_img.resize((90, 90))
        bordered_img = ImageOps.expand(resized_img, border=2, fill='black')
        img = ImageTk.PhotoImage(bordered_img)

        lbl_img = tk.Label(ventana, image=img, bg="#f4f4f8", cursor="hand2")
        lbl_img.image = img
        lbl_img.place(x=445, y=5)
        lbl_img.bind("<Button-1>", mostrar_eslogan)
    except Exception as e:
        print("Error al cargar la imagen:", e)

    label_font = ("Helvetica", 10)
    entry_bg = "#ffffff"

    # ---- Título ----
    tk.Label(ventana, text="Gestión de Usuarios", bg="#f4f4f8", fg="#333",
             font=("Helvetica", 12, "bold")).place(x=20, y=10)

    # ---- Nombre y Contraseña ----
    tk.Label(ventana, text="Nombre:", bg="#f4f4f8", font=label_font).place(x=30, y=50)
    entry_nombre = tk.Entry(ventana, width=20, bg=entry_bg)
    entry_nombre.place(x=110, y=50)

    tk.Label(ventana, text="Contraseña:", bg="#f4f4f8", font=label_font).place(x=30, y=80)
    entry_contra = tk.Entry(ventana, width=20, bg=entry_bg, show="*")
    entry_contra.place(x=110, y=80)

    # ---- Rol con combobox ----
    tk.Label(ventana, text="Rol:", bg="#f4f4f8", font=label_font).place(x=30, y=110)
    roles = ["Administrador", "Vendedor"]
    combo_rol = ttk.Combobox(ventana, values=roles, state="readonly", width=17)
    combo_rol.place(x=110, y=110)

    # ---- Botones de acciones con bordes ----
    btn_crear = tk.Button(
        ventana, text="Crear Usuario",
        bg="#4CAF50", fg="white",
        font=("Helvetica", 9, "bold"),
        bd=1, relief="solid",
        highlightthickness=2, highlightbackground="#388E3C",
        width=15
    )
    btn_crear.place(x=30, y=160)

    btn_editar = tk.Button(
        ventana, text="Editar Usuario",
        bg="#FFC107", fg="black",
        font=("Helvetica", 9, "bold"),
        bd=1, relief="solid",
        highlightthickness=2, highlightbackground="#FFA000",
        width=15
    )
    btn_editar.place(x=200, y=160)

    btn_eliminar = tk.Button(
        ventana, text="Eliminar Usuario",
        bg="#F44336", fg="white",
        font=("Helvetica", 9, "bold"),
        bd=1, relief="solid",
        highlightthickness=2, highlightbackground="#D32F2F",
        width=15
    )
    btn_eliminar.place(x=370, y=160)

    ventana.mainloop()

if __name__ == "__main__":
    interfaz_gestion_usuarios()