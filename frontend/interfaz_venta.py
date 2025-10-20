import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps

def interfaz_venta():
    ventana = tk.Tk()
    ventana.title("Interfaz de Venta")
    ventana.geometry("500x360")
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
        lbl_img.place(x=395, y=5)
        lbl_img.bind("<Button-1>", mostrar_eslogan)
    except Exception as e:
        print("Error al cargar la imagen:", e)

    label_font = ("Helvetica", 10)
    entry_bg = "#ffffff"
    entry_bd = 1

    def validar_total(nuevo_valor):
        if not nuevo_valor.startswith("$ "):
            return False
        contenido = nuevo_valor[2:]
        if contenido == "":
            return True
        if not all(c in "0123456789." for c in contenido):
            return False
        if contenido.count(".") > 1:
            return False
        return True

    def al_entrar_total(event):
        contenido = entry_total.get()
        if contenido == "$ 0.00":
            entry_total.delete(2, tk.END)

    def al_salir_total(event):
        contenido = entry_total.get()[2:]
        if contenido.strip() == "":
            entry_total.delete(0, tk.END)
            entry_total.insert(0, "$ 0.00")

    def confirmar_venta():
        if not entry_cliente.get().strip():
            messagebox.showwarning("Campos vacíos", "Por favor, complete todos los campos obligatorios.")
        else:
            messagebox.showinfo("Venta confirmada", "La venta se ha registrado correctamente.")

    # Título
    tk.Label(ventana, text="Registrar Venta", font=("Helvetica", 14, "bold"),
             bg="#f4f4f8", fg="#333").place(x=20, y=10)

    # Campos de entrada
    y_inicial = 50
    separacion_y = 40

    # Campos Producto y Cantidad
    tk.Label(ventana, text="Producto:", bg="#f4f4f8", font=label_font).place(x=30, y=y_inicial)
    entry_producto = tk.Entry(ventana, width=30, bg=entry_bg, bd=entry_bd)
    entry_producto.place(x=150, y=y_inicial)

    tk.Label(ventana, text="Cantidad:", bg="#f4f4f8", font=label_font).place(x=30, y=y_inicial + separacion_y)
    entry_cantidad = tk.Entry(ventana, width=30, bg=entry_bg, bd=entry_bd)
    entry_cantidad.place(x=150, y=y_inicial + separacion_y)

    # Botón agregar producto con marco
    y_boton_agregar = y_inicial + 2 * separacion_y
    btn_agregar = tk.Button(
        ventana, text="+ Agregar Producto", bg="#03A9F4", fg="white",
        font=("Helvetica", 10, "bold"), width=15,
        bd=1, relief="solid", cursor="hand2"
    )
    btn_agregar.place(x=30, y=y_boton_agregar)

    # Casilla blanca al costado del botón
    entry_extra = tk.Entry(ventana, width=22, bg=entry_bg, bd=entry_bd)
    entry_extra.place(x=200, y=y_boton_agregar + 2)  # un poco ajustado para alinear

    # Campo Cliente debajo del botón y arriba del Total
    y_cliente = y_boton_agregar + separacion_y
    tk.Label(ventana, text="ID Cliente:", bg="#f4f4f8", font=label_font).place(x=30, y=y_cliente)
    entry_cliente = tk.Entry(ventana, width=30, bg=entry_bg, bd=entry_bd)
    entry_cliente.place(x=150, y=y_cliente)

    # Campo total
    y_total = y_cliente + separacion_y
    tk.Label(ventana, text="Total:", bg="#f4f4f8", font=label_font).place(x=30, y=y_total)
    vcmd = (ventana.register(validar_total), '%P')
    entry_total = tk.Entry(ventana, width=15, justify='center', bg=entry_bg, bd=entry_bd,
                           validate='key', validatecommand=vcmd)
    entry_total.insert(0, "$ 0.00")
    entry_total.place(x=150, y=y_total)
    entry_total.bind("<FocusIn>", al_entrar_total)
    entry_total.bind("<FocusOut>", al_salir_total)

    # Botones Confirmar y Cancelar
    boton_estilo = {
        "font": ("Helvetica", 10, "bold"),
        "width": 15,
        "bd": 1,
        "relief": "solid"
    }
    y_botones = y_total + separacion_y + 10
    tk.Button(
        ventana, text="Confirmar Venta", bg="#4CAF50", fg="white",
        command=confirmar_venta, **boton_estilo
    ).place(x=100, y=y_botones)

    tk.Button(
        ventana, text="Cancelar", bg="#f44336", fg="white",
        command=ventana.destroy, **boton_estilo
    ).place(x=260, y=y_botones)

    ventana.mainloop()

if __name__ == "__main__":
    interfaz_venta()