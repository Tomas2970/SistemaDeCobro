# app/frontend/interfaz_compra.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Listbox, Scrollbar, SINGLE, simpledialog
from PIL import Image, ImageTk, ImageOps
import os # Importar OS
from app.frontend.interfaz_crear_proveedor import ui_crear_proveedor
from app.frontend.interfaz_gestion_proveedores import ui_gestion_proveedores

def ui_compra(parent: tk.Misc, backend, usuario: dict):
    
    # --- Datos en memoria ---
    proveedor_seleccionado: dict | None = None
    carrito: list[dict] = []

    # --- Configuración de la ventana ---
    win = tk.Toplevel(parent)
    win.title("Registrar Compra a Proveedor")
    win.geometry("780x600")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # --- ¡CAMBIO! Ruta de imagen corregida ---
    try:
        # Busca la imagen en la carpeta raíz del proyecto
        script_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(script_dir, '..', '..', 'Don atilio.png')
        
        original_img = Image.open(img_path).resize((90, 90))
        bordered_img = ImageOps.expand(original_img, border=2, fill='black')
        img = ImageTk.PhotoImage(bordered_img)
        lbl_img = tk.Label(win, image=img, bg="#f4f4f8")
        lbl_img.image = img # Guardar referencia
        lbl_img.place(x=670, y=10)
    except Exception as e:
        print(f"Error al cargar imagen 'Don atilio.png': {e}") 

    # --- Título ---
    tk.Label(win, text="Registrar Compra", bg="#f4f4f8", fg="#333",
             font=("Helvetica", 14, "bold")).place(x=20, y=20)

    # ==========================================
    # 1. SELECCIÓN DE PROVEEDOR
    # ==========================================
    
    tk.Label(win, text="Proveedor:", bg="#f4f4f8", font=("Helvetica", 10, "bold")).place(x=30, y=70)
    lbl_proveedor = tk.Label(win, text="(Ninguno seleccionado)", bg="#f4f4f8", fg="blue", font=("Helvetica", 10))
    lbl_proveedor.place(x=120, y=70)

    def abrir_selector_proveedor():
        nonlocal proveedor_seleccionado
        try:
            proveedores = backend.obtener_proveedores(incluir_inactivos=False)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar proveedores.\n{e}", parent=win)
            return
        
        if not proveedores:
            messagebox.showinfo("Sin Proveedores", "No hay proveedores activos creados. Use el botón '+ Crear'", parent=win)
            return

        sel = Toplevel(win); sel.title("Seleccionar Proveedor"); sel.geometry("400x300"); sel.config(bg="#f4f4f8")
        
        frame = tk.Frame(sel); frame.pack(expand=True, fill="both", padx=10, pady=10)
        sc = Scrollbar(frame); sc.pack(side="right", fill="y")
        lst = Listbox(frame, selectmode=SINGLE, yscrollcommand=sc.set, width=50, height=12)
        lst.pack(side="left", fill="both", expand=True); sc.config(command=lst.yview)
        
        for p in proveedores:
            lst.insert(tk.END, f"{p.get('id_proveedor')} | {p.get('nombre')}")
        
        def tomar():
            nonlocal proveedor_seleccionado
            sel_idx = lst.curselection()
            if not sel_idx: return
            
            id_prov = int(lst.get(sel_idx[0]).split("|")[0].strip())
            proveedor_seleccionado = next((p for p in proveedores if p.get('id_proveedor') == id_prov), None)
            
            if proveedor_seleccionado:
                lbl_proveedor.config(text=proveedor_seleccionado.get('nombre'))
            sel.destroy()
            
        tk.Button(sel, text="Seleccionar", command=tomar, bg="#4CAF50", fg="white").pack(pady=8)
        sel.grab_set(); sel.transient(win)

    tk.Button(win, text="Elegir...", command=abrir_selector_proveedor).place(x=400, y=65)
    tk.Button(win, text="+ Crear", command=lambda: ui_crear_proveedor(win, backend)).place(x=470, y=65)
    tk.Button(win, text="Gestionar Proveedores", command=lambda: ui_gestion_proveedores(win, backend)).place(x=540, y=65)


    # ==========================================
    # 2. SELECCIÓN DE PRODUCTOS
    # ==========================================
    
    tk.Label(win, text="Agregar Productos:", bg="#f4f4f8", font=("Helvetica", 10, "bold")).place(x=30, y=120)

    def abrir_selector_producto():
        if not proveedor_seleccionado:
            messagebox.showwarning("Atención", "Primero debe seleccionar un proveedor.", parent=win)
            return
            
        sel = Toplevel(win); sel.title("Seleccionar Producto"); sel.geometry("400x300"); sel.config(bg="#f4f4f8")
        tk.Label(sel, text="Buscar producto:", bg="#f4f4f8").pack(pady=5)
        var_pat = tk.StringVar(); ent = tk.Entry(sel, textvariable=var_pat, width=40); ent.pack(pady=4); ent.focus_set()
        
        frame = tk.Frame(sel); frame.pack(expand=True, fill="both", padx=10, pady=10)
        sc = Scrollbar(frame); sc.pack(side="right", fill="y")
        lst = Listbox(frame, selectmode=SINGLE, yscrollcommand=sc.set, width=50, height=12)
        lst.pack(side="left", fill="both", expand=True); sc.config(command=lst.yview)
        
        data = backend.obtener_productos_full()
        def render(filas): lst.delete(0, tk.END); [lst.insert(tk.END, f"{c.get('id_producto','')} | {c.get('nombre','')}") for c in filas]
        render(data)
        
        def filtrar(*_):
            q = var_pat.get().strip().lower()
            if not q: render(data); return
            filtrados = [p for p in data if q in str(p.get('nombre','')).lower() or q == str(p.get('id_producto'))]
            render(filtrados)
        var_pat.trace_add("write", filtrar)

        def tomar():
            sel_idx = lst.curselection()
            if not sel_idx: return
            
            id_prod = int(lst.get(sel_idx[0]).split("|")[0].strip())
            producto = next((p for p in data if p.get('id_producto') == id_prod), None)
            sel.destroy() 
            
            if producto:
                agregar_al_carrito(producto) 
            
        tk.Button(sel, text="Seleccionar", command=tomar, bg="#4CAF50", fg="white").pack(pady=8)
        sel.grab_set(); sel.transient(win)

    def agregar_al_carrito(producto: dict):
        cantidad = simpledialog.askinteger("Cantidad", f"¿Cuántas unidades de '{producto.get('nombre')}'?",
                                           parent=win, minvalue=1)
        if not cantidad:
            return

        precio_costo = simpledialog.askfloat("Precio de Costo", f"Ingrese el PRECIO DE COSTO por unidad:",
                                             parent=win, minvalue=0.01)
        if precio_costo is None: 
            return
            
        carrito.append({
            'id_producto': producto.get('id_producto'),
            'nombre': producto.get('nombre'),
            'cantidad': cantidad,
            'precio_costo': precio_costo
        })
        refrescar_carrito()

    tk.Button(win, text="+ Agregar Producto al Carrito", command=abrir_selector_producto, bg="#03A9F4", fg="white").place(x=170, y=115)

    # ==========================================
    # 3. CARRITO (Treeview)
    # ==========================================
    
    cols = ["ID", "Producto", "Cantidad", "Costo Unit.", "Subtotal"]
    tree = ttk.Treeview(win, columns=cols, show="headings", height=12)
    tree.place(x=30, y=160, width=720)
    
    for c in cols: tree.heading(c, text=c)
    tree.column("ID", width=70, anchor="center")
    tree.column("Producto", width=300)
    tree.column("Cantidad", width=100, anchor="e")
    tree.column("Costo Unit.", width=120, anchor="e")
    tree.column("Subtotal", width=120, anchor="e")

    ys = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
    tree.configure(yscroll=ys.set); ys.place(x=750, y=160, height=tree.cget('height')*19)

    def refrescar_carrito():
        for i in tree.get_children():
            tree.delete(i)
        
        total_compra = 0.0
        for item in carrito:
            subtotal = item['cantidad'] * item['precio_costo']
            total_compra += subtotal
            tree.insert("", tk.END, values=[
                item['id_producto'],
                item['nombre'],
                item['cantidad'],
                f"$ {item['precio_costo']:.2f}",
                f"$ {subtotal:.2f}"
            ])

    def quitar_del_carrito():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Atención", "Seleccione un producto de la lista para quitar.", parent=win)
            return
            
        item_values = tree.item(selected_item[0], "values")
        if not item_values: return 
        
        item_id = int(item_values[0]) 
        
        item_a_quitar = next((item for item in carrito if item['id_producto'] == item_id), None)
        if item_a_quitar:
            carrito.remove(item_a_quitar)
        
        tree.delete(selected_item[0])

    tk.Button(win, text="Quitar Seleccionado", command=quitar_del_carrito, bg="#f44336", fg="white").place(x=30, y=440)

    # ==========================================
    # 4. GUARDAR O CANCELAR
    # ==========================================

    def guardar_compra():
        if not proveedor_seleccionado:
            messagebox.showerror("Error", "Debe seleccionar un proveedor.", parent=win)
            return
        if not carrito:
            messagebox.showerror("Error", "El carrito está vacío. Debe agregar al menos un producto.", parent=win)
            return
            
        id_usuario = usuario.get("id_usuario")
        id_prov = proveedor_seleccionado.get("id_proveedor")

        try:
            id_compra = backend.insertar_compra(id_usuario=id_usuario, id_proveedor=id_prov)
            if not id_compra:
                messagebox.showerror("Error Fatal", "No se pudo crear el registro de Compra.", parent=win)
                return

            for item in carrito:
                backend.insertar_detalle_compra(
                    id_compra=id_compra,
                    id_producto=item['id_producto'],
                    cantidad=item['cantidad'],
                    precio_costo=item['precio_costo']
                )
            
            messagebox.showinfo("Éxito", f"Compra #{id_compra} registrada correctamente.\nEl stock ha sido actualizado.", parent=win)
            win.destroy()

        except Exception as e:
            messagebox.showerror("Error al Guardar", f"Ocurrió un error:\n{e}", parent=win)


    tk.Button(win, text="Guardar Compra", bg="#4CAF50", fg="white",
              font=("Helvetica", 10, "bold"), width=18, command=guardar_compra).place(x=250, y=550)

    tk.Button(win, text="Cancelar", bg="#f44336", fg="white",
              font=("Helvetica", 10, "bold"), width=15, command=win.destroy).place(x=420, y=550)

    win.grab_set()