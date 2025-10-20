import tkinter as tk
from tkinter import messagebox, Toplevel, Listbox, Scrollbar, SINGLE
from PIL import Image, ImageTk, ImageOps

def interfaz_compra():
    ventana = tk.Tk()
    ventana.title("Interfaz de Compra")
    ventana.geometry("550x420")
    ventana.config(bg="#f4f4f8")
    ventana.resizable(False, False)

    def mostrar_eslogan(event=None):
        messagebox.showinfo("Don Atilio", "Gracias por confiar en Don Atilio")

    # Cargar imagen
    try:
        original_img = Image.open("Don atilio.png").resize((90, 90))
        bordered_img = ImageOps.expand(original_img, border=2, fill='black')
        img = ImageTk.PhotoImage(bordered_img)
        lbl_img = tk.Label(ventana, image=img, bg="#f4f4f8", cursor="hand2")
        lbl_img.image = img
        lbl_img.place(x=440, y=5)
        lbl_img.bind("<Button-1>", mostrar_eslogan)
    except Exception as e:
        messagebox.showerror("Error al cargar la imagen", str(e))

    label_font = ("Helvetica", 10)
    entry_bg = "#ffffff"
    entry_bd = 1

    # --- Función para elegir opciones ---
    def abrir_selector(titulo, opciones, entry_var):
        selector = Toplevel(ventana)
        selector.title(titulo)
        selector.geometry("300x300")
        selector.config(bg="#f4f4f8")

        tk.Label(selector, text=f"{titulo}", font=("Helvetica", 12, "bold"), bg="#f4f4f8").pack(pady=5)

        # Campo búsqueda
        search_var = tk.StringVar()
        search_entry = tk.Entry(selector, textvariable=search_var, width=30)
        search_entry.pack(pady=5)

        # Lista de opciones con scrollbar
        frame_lista = tk.Frame(selector)
        frame_lista.pack(expand=True, fill="both")

        scrollbar = Scrollbar(frame_lista)
        scrollbar.pack(side="right", fill="y")

        lista = Listbox(frame_lista, selectmode=SINGLE, yscrollcommand=scrollbar.set, width=35, height=10)
        lista.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=lista.yview)

        # Insertar opciones
        for op in opciones:
            lista.insert(tk.END, op)

        # Filtro dinámico
        def filtrar(*args):
            filtro = search_var.get().lower()
            lista.delete(0, tk.END)
            for op in opciones:
                if filtro in op.lower():
                    lista.insert(tk.END, op)

        search_var.trace("w", filtrar)

        # Botón seleccionar
        def seleccionar():
            seleccion = lista.curselection()
            if seleccion:
                entry_var.set(lista.get(seleccion))
                selector.destroy()
            else:
                messagebox.showwarning("Atención", "Seleccione una opción.")

        tk.Button(selector, text="Seleccionar", command=seleccionar, bg="#4CAF50", fg="white").pack(pady=10)

    # Funciones de botones
    def guardar_datos():
        if not all([
            entry_proveedor.get().strip(),
            entry_usuario.get().strip(),
            producto_var.get().strip(),
            categoria_var.get().strip(),
            entry_cantidad.get().strip(),
            entry_precio.get().strip()
        ]):
            messagebox.showwarning("Campos vacíos", "Por favor, complete todos los campos.")
            return
        messagebox.showinfo("Guardado", "Datos guardados correctamente.")

    def cancelar():
        ventana.destroy()

    def agregar_producto():
        if not all([
            producto_var.get().strip(),
            categoria_var.get().strip(),
            entry_cantidad.get().strip(),
            entry_precio.get().strip()
        ]):
            messagebox.showwarning("Campos vacíos", "Complete todos los campos del producto.")
            return
        messagebox.showinfo(
            "Producto agregado",
            f"Producto: {producto_var.get()}\n"
            f"Categoría: {categoria_var.get()}\n"
            f"Cantidad: {entry_cantidad.get()}\n"
            f"Precio: {entry_precio.get()}\n"
            f"Extra: {entry_extra.get()}"
        )
        producto_var.set("")
        categoria_var.set("")
        entry_cantidad.delete(0, tk.END)
        entry_precio.delete(0, tk.END)
        entry_extra.delete(0, tk.END)

    # Hover effect
    def on_enter(e): e.widget['bg'] = '#0288D1'
    def on_leave(e): e.widget['bg'] = '#03A9F4'

    # Título
    tk.Label(ventana, text="Registrar Compra:", bg="#f4f4f8", fg="#333",
             font=("Helvetica", 12, "bold")).place(x=20, y=20)

    # Campos Proveedor y Usuario
    tk.Label(ventana, text="Proveedor:", bg="#f4f4f8", font=label_font).place(x=30, y=60)
    entry_proveedor = tk.Entry(ventana, bg=entry_bg, bd=entry_bd, width=30)
    entry_proveedor.place(x=150, y=60)

    tk.Label(ventana, text="Usuario:", bg="#f4f4f8", font=label_font).place(x=30, y=90)
    entry_usuario = tk.Entry(ventana, bg=entry_bg, bd=entry_bd, width=30)
    entry_usuario.place(x=150, y=90)

    # Encabezados de producto
    tk.Label(ventana, text="Categoría:", bg="#f4f4f8", font=label_font).place(x=30, y=130)
    tk.Label(ventana, text="Producto:", bg="#f4f4f8", font=label_font).place(x=200, y=130)
    tk.Label(ventana, text="Cantidad:", bg="#f4f4f8", font=label_font).place(x=360, y=130)
    tk.Label(ventana, text="Precio:", bg="#f4f4f8", font=label_font).place(x=460, y=130)

    # Variables de selección
    categoria_var = tk.StringVar()
    producto_var = tk.StringVar()

    # Botones de selección (Categoría y Producto)
    btn_categoria = tk.Button(
        ventana, text="Elegir Categoría", bg="#03A9F4", fg="white",
        font=("Helvetica", 10, "bold"), width=15, bd=1, relief="solid",
        command=lambda: abrir_selector("Elegir Categoría",
                                       ["Lácteos", "Bebidas", "Almacén", "Limpieza", "Carnes", "Verduras"],
                                       categoria_var),
        cursor="hand2"
    )
    btn_categoria.place(x=30, y=155)

    btn_producto = tk.Button(
        ventana, text="Elegir Producto", bg="#03A9F4", fg="white",
        font=("Helvetica", 10, "bold"), width=15, bd=1, relief="solid",
        command=lambda: abrir_selector("Elegir Producto",
                                       ["Leche", "Queso", "Coca Cola", "Fideos", "Detergente", "Carne Molida"],
                                       producto_var),
        cursor="hand2"
    )
    btn_producto.place(x=200, y=155)

    # Mostrar selección en labels
    tk.Label(ventana, textvariable=categoria_var, bg="#f4f4f8", fg="blue").place(x=30, y=185)
    tk.Label(ventana, textvariable=producto_var, bg="#f4f4f8", fg="blue").place(x=200, y=185)

    # Entradas Cantidad y Precio
    entry_cantidad = tk.Entry(ventana, width=10, bg=entry_bg, bd=entry_bd)
    entry_cantidad.place(x=360, y=155)

    entry_precio = tk.Entry(ventana, width=10, bg=entry_bg, bd=entry_bd)
    entry_precio.place(x=460, y=155)

    # Bulto
    tk.Label(ventana, text="Bulto:", bg="#f4f4f8", font=label_font).place(x=230, y=210)
    bulto_var = tk.StringVar(value="NO")
    tk.Radiobutton(ventana, text="SI", variable=bulto_var, value="SI", bg="#f4f4f8").place(x=280, y=210)
    tk.Radiobutton(ventana, text="NO", variable=bulto_var, value="NO", bg="#f4f4f8").place(x=320, y=210)

    tk.Label(ventana, text="Cantidad Bulto:", bg="#f4f4f8", font=label_font).place(x=370, y=210)
    entry_cantidad_bulto = tk.Entry(ventana, width=10, bg=entry_bg, bd=entry_bd)
    entry_cantidad_bulto.place(x=470, y=210)

    # Botón "+ Agregar Producto"
    btn_agregar = tk.Button(
        ventana, text="+ Agregar Producto", bg="#03A9F4", fg="white",
        font=("Helvetica", 10, "bold"), width=15, height=1,
        bd=1, relief="solid", command=agregar_producto, cursor="hand2"
    )
    btn_agregar.place(x=30, y=250)
    btn_agregar.bind("<Enter>", on_enter)
    btn_agregar.bind("<Leave>", on_leave)

    entry_extra = tk.Entry(ventana, width=20, bg=entry_bg, bd=entry_bd)
    entry_extra.place(x=180, y=252)

    # Total
    tk.Label(ventana, text="Total:", bg="#f4f4f8", font=label_font).place(x=30, y=300)
    total_var = tk.StringVar(value="$ 0.00")
    entry_total = tk.Entry(ventana, width=12, justify='left', bg=entry_bg, bd=entry_bd, textvariable=total_var)
    entry_total.place(x=80, y=300)

    # Botones Guardar y Cancelar
    boton_estilo = {"font": ("Helvetica", 10, "bold"), "width": 15, "bd": 1, "relief": "solid"}
    tk.Button(
        ventana, text="Guardar Datos", bg="#4CAF50", fg="white", command=guardar_datos, **boton_estilo
    ).place(x=120, y=350)

    tk.Button(
        ventana, text="Cancelar", bg="#f44336", fg="white", command=cancelar, **boton_estilo
    ).place(x=290, y=350)

    ventana.mainloop()


if __name__ == "__main__":
    interfaz_compra()