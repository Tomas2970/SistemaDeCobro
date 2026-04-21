# app/frontend/interfaz_gestion_clientes.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from app.frontend.interfaz_crear_cliente import ui_crear_cliente

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

try:
    from app.frontend.theme_config import get_color, aplicar_tema_ventana, configurar_estilo_treeview
except ImportError:
    def get_color(k): return "#000000"
    def aplicar_tema_ventana(w): pass
    def configurar_estilo_treeview(): pass

import customtkinter as ctk

def _fmt_mon(val):
    try: return f"$ {float(val):,.2f}"
    except: return "$ 0.00"

def ui_gestion_clientes(parent: tk.Misc, backend, usuario_actual: dict = None):
    win = ctk.CTkToplevel(parent)
    win.title("Gestión de Clientes")
    win.geometry("1150x650")
    aplicar_tema_ventana(win)
    win.resizable(False, False)

    configurar_estilo_treeview()

    # --- BARRA DE BÚSQUEDA ---
    frame_busqueda = ctk.CTkFrame(win, fg_color="transparent")
    frame_busqueda.pack(pady=(20,0), padx=25, fill="x")
    
    ctk.CTkLabel(frame_busqueda, text="🔎 Buscar Cliente:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).pack(side="left")
    var_busqueda = tk.StringVar()
    entry_busqueda = ctk.CTkEntry(frame_busqueda, textvariable=var_busqueda, width=350, height=40, font=("Segoe UI", 13), placeholder_text="Nombre o DNI...")
    entry_busqueda.pack(side="left", padx=20)

    frame_lista_cont = ctk.CTkFrame(win, fg_color=get_color("bg_surface"), corner_radius=10, border_width=1, border_color=get_color("border_color"))
    frame_lista_cont.pack(pady=15, padx=25, fill="both", expand=True)

    # 🔥 COLUMNAS ACTUALIZADAS: Se eliminó CUIT/CUIL
    cols = ["ID", "Nombre", "DNI", "Teléfono", "Email", "Dirección", "Saldo (Deuda)", "Límite Crédito", "Activo"]

    tree = ttk.Treeview(frame_lista_cont, columns=cols, show="headings", height=8, style="Modern.Treeview")
    tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    
    ys = ttk.Scrollbar(frame_lista_cont, orient="vertical", command=tree.yview)
    ys.pack(side="right", fill="y", pady=5)
    tree.configure(yscrollcommand=ys.set)
    
    for c in cols: tree.heading(c, text=c)
    
    tree.column("ID", width=0, stretch=False)
    tree.configure(displaycolumns=[c for c in cols if c != "ID"])
    tree.column("Nombre", width=180)
    tree.column("DNI", width=100, anchor="center")
    tree.column("Teléfono", width=110)
    tree.column("Email", width=170)
    tree.column("Dirección", width=200) 
    tree.column("Saldo (Deuda)", width=120, anchor="e")
    tree.column("Límite Crédito", width=120, anchor="e")
    tree.column("Activo", width=80, anchor="center")

    tree.tag_configure("deuda", foreground="#f87171") # Rojo claro (más legible en oscuro)
    tree.tag_configure("favor", foreground="#4ade80") # Verde claro
    tree.tag_configure("cero", foreground="#f9fafb")  # Blanco/Gris muy claro (era negro)

    var_mostrar_inactivos = tk.BooleanVar(value=False)
    todos_clientes = []

    def cargar_datos():
        nonlocal todos_clientes
        try:
            incluir = var_mostrar_inactivos.get()
            todos_clientes = backend.listar_clientes_con_saldos(incluir_inactivos=incluir)
            
            def custom_sort(c):
                saldo = float(c.get('saldo', 0.0))
                if saldo < -0.01: return 0  
                if saldo > 0.01: return 1   
                return 2                    

            todos_clientes.sort(key=custom_sort)
            filtrar_lista()
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando: {e}", parent=win)

    def filtrar_lista(*args):
        query = var_busqueda.get().lower().strip()
        for i in tree.get_children(): tree.delete(i)
        
        for c in todos_clientes:
            nom = str(c.get('nombre','')).lower()
            dni = str(c.get('dni','')).lower()
            
            if query in nom or query in dni:
                saldo = float(c.get('saldo', 0.0))
                tag = "cero"
                if saldo < -0.01: tag = "deuda"
                elif saldo > 0.01: tag = "favor"
                
                saldo_vis = f"- $ {abs(saldo):,.2f}" if saldo < 0 else f"+ $ {saldo:,.2f}"
                if abs(saldo) < 0.01: saldo_vis = "$ 0.00"

                activo = "SI" if c.get('activo') else "NO"
                
                # 🔥 Se eliminó el mapeo de CUIT para coincidir con las columnas
                tree.insert("", tk.END, values=[
                    c.get('id_cliente'),
                    c.get('nombre'),
                    c.get('dni') or "-",
                    c.get('telefono') or "-",
                    c.get('email') or "-",
                    c.get('direccion') or "-", 
                    saldo_vis,
                    _fmt_mon(c.get('limite_credito')),
                    activo
                ], tags=(tag,))

    var_busqueda.trace_add("write", filtrar_lista)

    def accion_nuevo():
        top = ui_crear_cliente(win, backend)
        if isinstance(top, tk.Toplevel):
            win.wait_window(top)
            cargar_datos()
        else:
            win.after(1000, cargar_datos)

    def abrir_editar():
        rol_id = usuario_actual.get('id_rol')
        if rol_id not in [1, 3]: 
            messagebox.showwarning("Acceso Denegado", "⚠️ Solo Administradores y Supervisores pueden modificar clientes.", parent=win)
            return

        sel = tree.selection()
        if not sel: 
            messagebox.showwarning("Atención", "Seleccione un cliente para editar.", parent=win)
            return
        item = tree.item(sel[0], "values")
        
        top = ui_crear_cliente(win, backend, id_cliente_a_editar=int(item[0]))
        if isinstance(top, tk.Toplevel):
            win.wait_window(top)
            cargar_datos()
    
    def on_doble_click(event):
        abrir_editar()

    tree.bind("<Double-1>", on_doble_click)

    def desactivar():
        rol_id = usuario_actual.get('id_rol')
        if rol_id != 1:
            messagebox.showwarning("Acceso Denegado", "No tienes permisos para desactivar clientes.", parent=win)
            return

        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        if messagebox.askyesno("Confirmar", f"¿Desactivar a {item[1]}?", parent=win):
            backend.eliminar_cliente_logico(int(item[0]))
            cargar_datos()

    def activar_cliente():
        rol_id = usuario_actual.get('id_rol')
        if rol_id not in [1, 3]:
            messagebox.showwarning("Acceso Denegado", "No tienes permisos para activar clientes.", parent=win)
            return

        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        
        # Índice ajustado: Activo ahora es la columna 8 (índice 8)
        if item[8] == 'SI': 
             messagebox.showwarning("Atención", "El cliente ya está activo.", parent=win)
             return

        if messagebox.askyesno("Confirmar", f"¿Activar cliente {item[1]}?"):
            if backend.activar_cliente_logico(int(item[0])):
                messagebox.showinfo("Éxito", "Cliente activado.", parent=win)
                cargar_datos()
            else:
                messagebox.showerror("Error", "No se pudo activar.", parent=win)

    frame_botones = ctk.CTkFrame(win, fg_color="transparent")
    frame_botones.pack(pady=(0, 20), fill="x", padx=25)

    frame_acciones = ctk.CTkFrame(frame_botones, fg_color="transparent")
    frame_acciones.pack(side=tk.LEFT)

    ctk.CTkButton(
        frame_acciones, text="➕ Crear Cliente", command=accion_nuevo, 
        fg_color="#16a34a", hover_color="#15803d", font=("Segoe UI", 13, "bold"), 
        width=160, height=45
    ).pack(side=tk.LEFT, padx=5)
    
    ctk.CTkButton(
        frame_acciones, text="🗑️ Desactivar", command=desactivar, 
        fg_color="#dc2626", hover_color="#b91c1c", font=("Segoe UI", 12, "bold"), 
        width=130, height=45
    ).pack(side=tk.LEFT, padx=5)

    btn_activar = ctk.CTkButton(
        frame_acciones, text="✅ Activar", command=activar_cliente, 
        fg_color="#0ea5e9", hover_color="#0284c7", font=("Segoe UI", 12, "bold"), 
        width=120, height=45
    )

    def toggle_mostrar_inactivos():
        cargar_datos()
        if var_mostrar_inactivos.get():
            btn_activar.pack(side=tk.LEFT, padx=5)
        else:
            btn_activar.pack_forget()

    frame_filtros = ctk.CTkFrame(frame_botones, fg_color="transparent")
    frame_filtros.pack(side=tk.LEFT, padx=30)

    ctk.CTkCheckBox(
        frame_filtros, text="Ver Inactivos", variable=var_mostrar_inactivos, 
        font=("Segoe UI", 11), command=toggle_mostrar_inactivos,
        fg_color=get_color("accent_primary"), hover_color=get_color("accent_hover")
    ).pack(side=tk.LEFT)

    ctk.CTkButton(
        frame_botones, text="Cerrar", command=win.destroy, 
        fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), 
        font=("Segoe UI", 12, "bold"), width=120, height=45
    ).pack(side=tk.RIGHT)

    cargar_datos()
    entry_busqueda.focus_set()
    configurar_navegacion_ventana(win)
    win.grab_set()