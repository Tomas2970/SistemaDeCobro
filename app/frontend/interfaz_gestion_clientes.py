# app/frontend/interfaz_gestion_clientes.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from app.frontend import custom_dialogs as messagebox
from app.frontend.interfaz_crear_cliente import ui_crear_cliente
from app.frontend.autorizacion import solicitar_autorizacion_supervisor

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

try:
    from app.frontend.theme_config import get_color, aplicar_tema_ventana, configurar_estilo_treeview, preparar_ventana, centrar_y_mostrar_ventana
except ImportError:
    def get_color(k): return "#000000"
    def aplicar_tema_ventana(w): pass
    def configurar_estilo_treeview(): pass
    def preparar_ventana(w): pass
    def centrar_y_mostrar_ventana(w): pass

import customtkinter as ctk

def _fmt_mon(val):
    try: return f"$ {float(val):,.2f}"
    except: return "$ 0.00"
def ui_gestion_clientes(parent: tk.Misc, backend, usuario_actual: dict = None):
    win = ctk.CTkToplevel(parent)
    preparar_ventana(win)
    win.title("Gestión de Clientes")
    win.geometry("1280x650")
    win.resizable(True, True)
    win.minsize(950, 550)

    configurar_estilo_treeview()

    # --- BARRA DE BÚSQUEDA ---
    frame_busqueda = ctk.CTkFrame(win, fg_color="transparent")
    frame_busqueda.pack(pady=(20,0), padx=25, fill="x")
    
    ctk.CTkLabel(frame_busqueda, text="🔎 Buscar Cliente:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary")).pack(side="left")
    var_busqueda = tk.StringVar()
    entry_busqueda = ctk.CTkEntry(frame_busqueda, textvariable=var_busqueda, width=350, height=40, font=("Segoe UI", 13), placeholder_text="Nombre o DNI...")
    entry_busqueda.pack(side="left", padx=20)

    # --- FRAME DE BOTONES (Empacado al fondo primero para evitar que se achique) ---
    frame_botones = ctk.CTkFrame(win, fg_color="transparent")
    frame_botones.pack(side=tk.BOTTOM, pady=(0, 20), fill="x", padx=25)

    frame_lista_cont = ctk.CTkFrame(win, fg_color=get_color("bg_surface"), corner_radius=10, border_width=1, border_color=get_color("border_color"))
    frame_lista_cont.pack(pady=15, padx=25, fill="both", expand=True)

    # 🔥 COLUMNAS ACTUALIZADAS: Se eliminó CUIT/CUIL
    cols = ["ID", "Nombre", "DNI", "Teléfono", "Email", "Dirección", "Saldo", "Límite Crédito", "Activo"]

    tree = ttk.Treeview(frame_lista_cont, columns=cols, show="headings", height=8, style="Modern.Treeview")
    
    ys = ctk.CTkScrollbar(frame_lista_cont, command=tree.yview)
    ys.pack(side="right", fill="y", padx=(0, 5), pady=5)
    tree.configure(yscrollcommand=ys.set)
    tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    
    for c in cols: tree.heading(c, text=c)
    
    tree.column("ID", width=0, stretch=False)
    tree.configure(displaycolumns=[c for c in cols if c != "ID"])
    tree.column("Nombre", width=160, minwidth=140, stretch=True)
    tree.column("DNI", width=90, minwidth=85, stretch=False)
    tree.column("Teléfono", width=100, minwidth=95, stretch=False)
    tree.column("Email", width=160, minwidth=145, stretch=True)
    tree.column("Dirección", width=150, minwidth=130, stretch=True) 
    tree.column("Saldo", width=130, minwidth=120, stretch=False)
    tree.column("Límite Crédito", width=130, minwidth=120, stretch=False)
    tree.column("Activo", width=80, minwidth=75, stretch=False)

    tree.tag_configure("deuda", foreground="#f87171") # Rojo claro (más legible en oscuro)
    tree.tag_configure("favor", foreground="#10b981") 
    tree.tag_configure("cero", foreground="#6b7280" if ctk.get_appearance_mode() == "Light" else "#9ca3af")

    var_mostrar_inactivos = tk.BooleanVar(value=False)
    todos_clientes = []

    def cargar_datos():
        nonlocal todos_clientes
        if not win.winfo_exists():
            return
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
        if not win.winfo_exists():
            return
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

    def _ejecutar_crear_cliente():
        top = ui_crear_cliente(win, backend, callback_on_save=cargar_datos)
        if isinstance(top, tk.Toplevel):
            win.wait_window(top)
            cargar_datos()
        else:
            win.after(1000, cargar_datos)

    def accion_nuevo():
        if usuario_actual.get('id_rol') in (1, 3):  # Admin o Supervisor → acceso directo
            _ejecutar_crear_cliente()
        else:  # Vendedor → pedir credenciales de administrador
            def on_autorizado(usr_autorizado):
                _ejecutar_crear_cliente()
            solicitar_autorizacion_supervisor(win, backend, usuario_actual, on_autorizado)

    def _ejecutar_editar_cliente():
        sel = tree.selection()
        if not sel: 
            messagebox.showwarning("Atención", "Seleccione un cliente para editar.", parent=win)
            return
        item = tree.item(sel[0], "values")
        
        top = ui_crear_cliente(win, backend, id_cliente_a_editar=int(item[0]), callback_on_save=cargar_datos)
        if isinstance(top, tk.Toplevel):
            win.wait_window(top)
            cargar_datos()

    def abrir_editar():
        sel = tree.selection()
        if not sel: 
            messagebox.showwarning("Atención", "Seleccione un cliente para editar.", parent=win)
            return

        if usuario_actual.get('id_rol') in (1, 3):  # Admin o Supervisor → acceso directo
            _ejecutar_editar_cliente()
        else:  # Vendedor → pedir credenciales de administrador
            def on_autorizado(usr_autorizado):
                _ejecutar_editar_cliente()
            solicitar_autorizacion_supervisor(win, backend, usuario_actual, on_autorizado)
    
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

    def limpiar_filtros():
        var_busqueda.set('')
        if var_mostrar_inactivos.get():
            var_mostrar_inactivos.set(False)
            btn_activar.pack_forget()
        cargar_datos()

    ctk.CTkButton(
        frame_filtros, text="🧹 Limpiar", command=limpiar_filtros,
        fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 11, "bold"),
        width=100, height=35
    ).pack(side=tk.LEFT, padx=10)

    ctk.CTkButton(
        frame_botones, text="Cerrar", command=win.destroy, 
        fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), 
        font=("Segoe UI", 12, "bold"), width=120, height=45
    ).pack(side=tk.RIGHT)

    cargar_datos()
    entry_busqueda.focus_set()
    configurar_navegacion_ventana(win)
    win.grab_set()
    centrar_y_mostrar_ventana(win)