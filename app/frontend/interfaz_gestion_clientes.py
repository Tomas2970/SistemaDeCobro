# app/frontend/interfaz_gestion_clientes.py
import tkinter as tk
from tkinter import ttk, messagebox
# ¡Asegúrate de que importa el archivo correcto!
from app.frontend.interfaz_crear_cliente import ui_crear_cliente 

def ui_gestion_clientes(parent: tk.Misc, backend, usuario: dict):
    win = tk.Toplevel(parent)
    win.title("Gestión de Clientes")
    win.geometry("1100x500") 
    win.config(bg="#f4f4f8")
    win.resizable(False, False)
    
    frame_lista = tk.Frame(win, bg="#f4f4f8")
    frame_lista.pack(pady=20, padx=20, fill="both", expand=True)

    cols = ("ID", "Nombre", "DNI", "Teléfono", "Email", "Activo", "Saldo (Deuda)", "Límite Crédito")
    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", height=15)
    tree.pack(side="left", fill="both", expand=True)
    
    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    ys.pack(side="right", fill="y")
    tree.configure(yscrollcommand=ys.set)
    
    for c in cols: tree.heading(c, text=c)
    
    tree.column("ID", width=40, anchor="center")
    tree.column("Nombre", width=200)
    tree.column("DNI", width=90, anchor="center")
    tree.column("Teléfono", width=110)
    tree.column("Email", width=180)
    tree.column("Activo", width=50, anchor="center")
    tree.column("Saldo (Deuda)", width=110, anchor="e")
    tree.column("Límite Crédito", width=110, anchor="e")
    
    # --- ¡NUEVO! Checkbox para filtrar activos ---
    var_mostrar_inactivos = tk.BooleanVar(value=False)
    # --- FIN NUEVO ---

    # --- Cargar Datos ---
    def cargar_datos():
        for i in tree.get_children():
            tree.delete(i)
        
        try:
            # --- ¡MODIFICACIÓN! Usa el checkbox ---
            incluir_inactivos = var_mostrar_inactivos.get()
            clientes = backend.listar_clientes_con_saldos(incluir_inactivos=incluir_inactivos)
            # --- FIN MODIFICACIÓN ---
            
            for c in clientes:
                estado = "SI" if c.get('activo') else "NO"
                
                try:
                    saldo_val = float(c.get('saldo'))
                    saldo_str = f"$ {saldo_val:,.2f}"
                except (TypeError, ValueError):
                    saldo_str = "(N/A)"
                    
                try:
                    limite_val = float(c.get('limite_credito'))
                    limite_str = f"$ {limite_val:,.2f}"
                except (TypeError, ValueError):
                    limite_str = "(N/A)"
                
                tree.insert("", tk.END, values=[
                    c.get('id_cliente', ''),
                    c.get('nombre', ''),
                    c.get('dni', ''),
                    c.get('telefono', ''),
                    c.get('email', ''),
                    estado,
                    saldo_str,
                    limite_str
                ])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los clientes:\n{e}", parent=win)

    # --- Botones de Acción ---
    frame_botones = tk.Frame(win, bg="#f4f4f8")
    frame_botones.pack(pady=10, fill="x")

    def abrir_crear_cliente():
        # Llama a la ventana emergente (en modo CREAR)
        ui_crear_cliente(win, backend, usuario, id_cliente_a_editar=None)
        cargar_datos() 

    # --- ¡ESTA ES LA FUNCIÓN CORREGIDA! ---
    def abrir_editar_cliente():
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un cliente de la lista para editar.", parent=win)
            return
            
        item = tree.item(seleccion[0], "values")
        id_cli = item[0]
        
        # Llama a la ventana 'crear_cliente' pero en modo EDICIÓN
        ui_crear_cliente(win, backend, usuario, id_cliente_a_editar=int(id_cli))
        
        cargar_datos() # Recarga al cerrar
    # --- ¡FIN DE LA CORRECCIÓN! ---

    def desactivar_cliente():
        seleccion = tree.selection()
        # ... (código de desactivar sin cambios) ...
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un cliente de la lista.", parent=win)
            return
            
        item = tree.item(seleccion[0], "values")
        id_cli = item[0]
        nombre_cli = item[1]
        
        if not messagebox.askyesno("Confirmar", f"¿Está seguro de que desea DESACTIVAR a '{nombre_cli}' (ID: {id_cli})?\n\nNo podrá seleccionarlo para futuras ventas.", parent=win):
            return
            
        try:
            if backend.eliminar_cliente_logico(int(id_cli)):
                messagebox.showinfo("Éxito", "Cliente desactivado.", parent=win)
                cargar_datos()
            else:
                messagebox.showerror("Error", "No se pudo desactivar el cliente.", parent=win)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}", parent=win)
    
    tk.Button(frame_botones, text="↻ Recargar Lista", command=cargar_datos, bg="#03A9F4", fg="white", width=15).pack(side=tk.LEFT, padx=(20, 10))
    tk.Button(frame_botones, text="+ Crear Cliente", command=abrir_crear_cliente, bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=10)
    
    # Este botón ahora llama a 'abrir_editar_cliente'
    tk.Button(frame_botones, text="✎ Editar Seleccionado", command=abrir_editar_cliente, bg="#FFC107", fg="black", width=18).pack(side=tk.LEFT, padx=10)
    
    tk.Button(frame_botones, text="Desactivar Seleccionado", command=desactivar_cliente, bg="#f44336", fg="white", width=20).pack(side=tk.LEFT, padx=10)
    
    # --- ¡NUEVO CHECKBOX! ---
    chk_inactivos = tk.Checkbutton(
        frame_botones, 
        text="Mostrar clientes desactivados", 
        variable=var_mostrar_inactivos, 
        onvalue=True, 
        offvalue=False,
        bg="#f4f4f8",
        command=cargar_datos # Recarga la lista al cambiar
    )
    chk_inactivos.pack(side=tk.LEFT, padx=20)
    # --- FIN NUEVO CHECKBOX ---
    
    tk.Button(frame_botones, text="Cerrar", command=win.destroy, bg="#607D8B", fg="white", width=15).pack(side=tk.RIGHT, padx=20)

    # Carga inicial
    cargar_datos()
    win.grab_set()
    win.transient(parent)