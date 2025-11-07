# app/frontend/interfaz_compra.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Listbox, Scrollbar, SINGLE, simpledialog
from PIL import Image, ImageTk, ImageOps
import os 
from app.frontend.interfaz_crear_proveedor import ui_crear_proveedor
from app.frontend.interfaz_gestion_proveedores import ui_gestion_proveedores

def ui_compra(parent: tk.Misc, backend, usuario: dict):
    
    proveedor_seleccionado: dict | None = None
    carrito: list[dict] = []

    win = tk.Toplevel(parent)
    win.title("Registrar Compra a Proveedor")
    win.geometry("780x600")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)


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
            def on_gestion_cierra():
                try:
                    proveedores = backend.obtener_proveedores(incluir_inactivos=False)
                    if not proveedores:
                        messagebox.showinfo("Sin Proveedores", "No hay proveedores activos creados. Use el botón '+ Crear'", parent=win)
                        return
                    mostrar_popup_lista(proveedores)
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo recargar proveedores.\n{e}", parent=win)
            
            def mostrar_popup_lista(proveedores: list):
                sel = Toplevel(win); sel.title("Seleccionar Proveedor"); sel.geometry("400x300"); sel.config(bg="#f4f4f8")
                
                frame_lista = tk.Frame(sel); frame_lista.pack(expand=True, fill="both", padx=10, pady=10)
                sc = Scrollbar(frame_lista); sc.pack(side="right", fill="y")
                lst = Listbox(frame_lista, selectmode=SINGLE, yscrollcommand=sc.set, width=50, height=12)
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
                    
                frame_boton = tk.Frame(sel, bg="#f4f4f8")
                frame_boton.pack(fill="x", pady=8)
                tk.Button(frame_boton, text="Seleccionar", command=tomar, bg="#4CAF50", fg="white").pack() 
                
                sel.grab_set(); sel.transient(win)
            
            proveedores_actuales = backend.obtener_proveedores(incluir_inactivos=False)
            if not proveedores_actuales:
                 if messagebox.askyesno("Sin Proveedores", "No hay proveedores activos. ¿Desea crear uno ahora?"):
                     ui_crear_proveedor(win, backend, id_proveedor_a_editar=None) 
                     on_gestion_cierra() 
            else:
                 mostrar_popup_lista(proveedores_actuales)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar proveedores.\n{e}", parent=win)
            return

    tk.Button(win, text="Elegir...", command=abrir_selector_proveedor).place(x=400, y=65)
    
    def abrir_gestion_proveedores():
        nonlocal proveedor_seleccionado
        
        ui_gestion_proveedores(win, backend)
        
        if proveedor_seleccionado:
            try:
                datos_nuevos = backend.obtener_proveedor_para_editar(proveedor_seleccionado.get('id_proveedor'))
                if datos_nuevos and datos_nuevos.get('activo', True): 
                    proveedor_seleccionado = datos_nuevos
                    lbl_proveedor.config(text=proveedor_seleccionado.get('nombre'))
                else:
                    proveedor_seleccionado = None
                    lbl_proveedor.config(text="(Ninguno seleccionado)")
            except Exception:
                proveedor_seleccionado = None
                lbl_proveedor.config(text="(Ninguno seleccionado)")

    def abrir_crear_nuevo():
        ui_crear_proveedor(win, backend, id_proveedor_a_editar=None)
        
    tk.Button(win, text="+ Crear", command=abrir_crear_nuevo).place(x=470, y=65)
    tk.Button(win, text="Gestionar Proveedores", command=abrir_gestion_proveedores).place(x=540, y=65)


    # ==========================================
    # 2. SELECCIÓN DE PRODUCTOS
    # ==========================================
    
    tk.Label(win, text="Agregar Productos:", bg="#f4f4f8", font=("Helvetica", 10, "bold")).place(x=30, y=120)

    def abrir_selector_producto():
        if not proveedor_seleccionado:
            messagebox.showwarning("Atención", "Primero debe seleccionar un proveedor.", parent=win)
            return
            
        id_prov = proveedor_seleccionado.get('id_proveedor')
        nombre_prov = proveedor_seleccionado.get('nombre')
        
        sel = Toplevel(win)
        sel.title(f"Seleccionar Producto para: {nombre_prov}")
        sel.geometry("400x350")
        sel.config(bg="#f4f4f8")
        
        tk.Label(sel, text="Buscar producto:", bg="#f4f4f8").pack(pady=5)
        var_pat = tk.StringVar(); ent = tk.Entry(sel, textvariable=var_pat, width=40); ent.pack(pady=4); ent.focus_set()
        
        frame_lista = tk.Frame(sel); frame_lista.pack(expand=True, fill="both", padx=10, pady=10)
        sc = Scrollbar(frame_lista); sc.pack(side="right", fill="y")
        lst = Listbox(frame_lista, selectmode=SINGLE, yscrollcommand=sc.set, width=50, height=12)
        lst.pack(side="left", fill="both", expand=True); sc.config(command=lst.yview)
        
        data = backend.obtener_productos_por_proveedor(id_prov)
        
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
        
        frame_boton = tk.Frame(sel, bg="#f4f4f8")
        frame_boton.pack(fill="x", pady=(0, 8))
        tk.Button(frame_boton, text="Seleccionar", command=tomar, bg="#4CAF50", fg="white", width=15).pack() 
        
        sel.grab_set(); sel.transient(win)

    def agregar_al_carrito(producto: dict):
        # --- ¡CORRECCIÓN! ---
        # Cambiado de askinteger a askfloat para permitir decimales (Kg)
        es_pesable = producto.get('es_pesable', False)
        
        prompt_cantidad = f"¿Qué cantidad (unid/Kg) de '{producto.get('nombre')}'?"
        if not es_pesable:
            prompt_cantidad = f"¿Cuántas unidades de '{producto.get('nombre')}'?"

        cantidad = simpledialog.askfloat("Cantidad", prompt_cantidad,
                                           parent=win, minvalue=0.001)
        
        if not cantidad or cantidad <= 0:
            return
            
        # Si no es pesable, forzamos a entero
        if not es_pesable:
            if cantidad != int(cantidad):
                 messagebox.showwarning("Cantidad Inválida", "Este producto no es pesable. Ingrese solo unidades enteras.", parent=win)
                 return
            cantidad = int(cantidad)
        # --- FIN CORRECCIÓN ---

        precio_costo = simpledialog.askfloat("Precio de Costo", f"Ingrese el PRECIO DE COSTO por unidad:",
                                             parent=win, minvalue=0.01)
        if precio_costo is None or precio_costo <= 0: 
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
            
            # Formatear cantidad
            cant_str = item['cantidad']
            if isinstance(cant_str, float) and cant_str != int(cant_str):
                cant_str = f"{cant_str:.3f}"
            
            tree.insert("", tk.END, values=[
                item['id_producto'],
                item['nombre'],
                cant_str, # <-- Muestra decimal si es necesario
                f"$ {item['precio_costo']:.2f}",
                f"$ {subtotal:.2f}"
            ])
            
    def quitar_del_carrito():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Atención", "Seleccione un producto de la lista para quitar.", parent=win)
            return
            
        # --- ¡CORRECCIÓN! Búsqueda más robusta por ID y Cantidad ---
        item_values = tree.item(selected_item[0], "values")
        if not item_values: return 
        
        item_id = int(item_values[0])
        item_cant_str = str(item_values[2])
        
        # Intentar encontrar el item exacto (por si el mismo ID está dos veces)
        item_a_quitar = None
        for item in carrito:
            # Comparamos el ID y también la cantidad (convertida a string)
            cant_str = str(item['cantidad'])
            if isinstance(item['cantidad'], float) and item['cantidad'] != int(item['cantidad']):
                cant_str = f"{item['cantidad']:.3f}"
                
            if item['id_producto'] == item_id and cant_str == item_cant_str:
                item_a_quitar = item
                break
        
        if item_a_quitar:
            carrito.remove(item_a_quitar)
        
        tree.delete(selected_item[0])
        refrescar_carrito() # Refresca el total

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