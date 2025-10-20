import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps  

def interfaz_inventario():
    ventana = tk.Tk()
    ventana.title("Interfaz de Inventario")
    ventana.geometry("550x320")
    ventana.config(bg="#f4f4f8")
    ventana.resizable(False, False)

    def mostrar_eslogan(event=None):
        messagebox.showinfo("Don Atilio", "Gracias por confiar en Don Atilio")

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
    entry_bd = 1

    x_label = 30
    x_entry = 150
    y = 60
    separacion = 35

    tk.Label(
        ventana,
        text="Consultar Inventario",
        font=("Helvetica", 16, "bold"),
        bg="#f4f4f8",
        fg="#333"
    ).place(x=20, y=20)

    tk.Label(ventana, text="Categoría:", bg="#f4f4f8", font=label_font).place(x=x_label, y=y)
    entry_categoria = tk.Entry(ventana, width=30, bg=entry_bg, bd=entry_bd)
    entry_categoria.place(x=x_entry, y=y)
    y += separacion

    tk.Label(ventana, text="Producto:", bg="#f4f4f8", font=label_font).place(x=x_label, y=y)
    entry_producto = tk.Entry(ventana, width=30, bg=entry_bg, bd=entry_bd)
    entry_producto.place(x=x_entry, y=y)
    y += separacion

    tk.Label(ventana, text="Stock Actual:", bg="#f4f4f8", font=label_font).place(x=x_label, y=y)
    entry_stock = tk.Entry(ventana, width=30, bg=entry_bg, bd=entry_bd)
    entry_stock.place(x=x_entry, y=y)
    y += separacion

    tk.Label(ventana, text="Precio Unitario:", bg="#f4f4f8", font=label_font).place(x=x_label, y=y)
    entry_precio = tk.Entry(ventana, width=30, bg=entry_bg, bd=entry_bd)
    entry_precio.place(x=x_entry, y=y)
    y += separacion + 20

    # ---- Botones Buscar e Imprimir con marco negro ----
    btn_buscar = tk.Button(
        ventana,
        text="Buscar",
        bg="#2196F3",
        fg="white",
        font=("Helvetica", 10, "bold"),
        bd=1,
        relief="solid",
        highlightthickness=2,
        highlightbackground="black",
        width=15
    )
    btn_buscar.place(x=120, y=y)

    btn_imprimir = tk.Button(
        ventana,
        text="Imprimir",
        bg="#4CAF50",
        fg="white",
        font=("Helvetica", 10, "bold"),
        bd=1,
        relief="solid",
        highlightthickness=2,
        highlightbackground="black",
        width=15
    )
    btn_imprimir.place(x=300, y=y)

    ventana.mainloop()

if __name__ == "__main__":
    interfaz_inventario()