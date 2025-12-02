# app/frontend/interfaz_crear_cliente.py
import tkinter as tk
from tkinter import messagebox, Toplevel
import re

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

def ui_crear_cliente(parent, backend, id_cliente_a_editar=None):
    win = Toplevel(parent)
    titulo = "Editar Cliente" if id_cliente_a_editar else "Nuevo Cliente"
    win.title(titulo)
    win.geometry("450x480")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # Variables
    var_nombre = tk.StringVar()
    var_dni = tk.StringVar()
    var_tel = tk.StringVar()
    var_email = tk.StringVar()
    var_dir = tk.StringVar()
    var_limite = tk.StringVar(value="50000.00")

    if id_cliente_a_editar:
        cli = backend.obtener_cliente_para_editar(id_cliente_a_editar)
        if cli:
            var_nombre.set(cli.get('nombre', ''))
            var_dni.set(cli.get('dni', ''))
            var_tel.set(cli.get('telefono', ''))
            var_email.set(cli.get('email', ''))
            var_dir.set(cli.get('direccion', ''))
            var_limite.set(str(cli.get('limite_credito', '50000.00')))

    frm = tk.Frame(win, bg="#f4f4f8", padx=20, pady=20)
    frm.pack(fill="both", expand=True)

    def row(lbl, var, r):
        tk.Label(frm, text=lbl, bg="#f4f4f8", anchor="w").grid(row=r, column=0, sticky="ew", pady=5)
        e = tk.Entry(frm, textvariable=var)
        e.grid(row=r, column=1, sticky="ew", pady=5)
        return e

    e_nom = row("Nombre (*):", var_nombre, 0)
    row("DNI/CUIT(*):", var_dni, 1)
    row("Teléfono:", var_tel, 2)
    row("Email:", var_email, 3)
    row("Dirección:", var_dir, 4)
    row("Límite Crédito ($):", var_limite, 5)

    frm.columnconfigure(1, weight=1)

    def guardar():
        nom = var_nombre.get().strip()
        dni = var_dni.get().strip()
        tel = var_tel.get().strip()
        
        # 1. Validar Nombre (No debe tener números)
        if not nom:
            messagebox.showwarning("Error", "El nombre es obligatorio", parent=win)
            return
        if any(char.isdigit() for char in nom):
            messagebox.showwarning("Error", "El nombre no puede contener números.", parent=win)
            return

        # 2. Validar DNI
        if dni:
            if not dni.isdigit():
                messagebox.showwarning("Error", "El DNI/CUIT debe contener solo números.", parent=win)
                return
            if len(dni) not in [7, 8, 11]:
                messagebox.showwarning("Error", "El DNI debe tener 7, 8 u 11 dígitos.", parent=win)
                return

        # 3. Validar Teléfono (Estricto: Solo números, espacios, - +)
        # Si contiene cualquier letra (a-z) lanza error
        if tel:
            if re.search(r'[a-zA-Z]', tel):
                messagebox.showwarning("Error", "El teléfono NO puede contener letras.", parent=win)
                return
            # Opcional: Validar que tenga al menos algunos números
            if not any(char.isdigit() for char in tel):
                 messagebox.showwarning("Error", "El teléfono debe tener números.", parent=win)
                 return

        try:
            limite = float(var_limite.get())
        except:
            limite = 0.0

        try:
            if id_cliente_a_editar:
                ok = backend.actualizar_cliente(id_cliente_a_editar, nom, dni, var_dir.get(), tel, var_email.get(), limite)
                msg = "Cliente actualizado"
            else:
                ok = backend.crear_cliente(nom, dni, var_dir.get(), tel, var_email.get(), limite)
                msg = "Cliente creado"
                
            if ok:
                messagebox.showinfo("Éxito", msg, parent=win)
                win.destroy() 
            else:
                messagebox.showerror("Error", "No se pudo guardar (¿DNI duplicado?)", parent=win)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {e}", parent=win)

    btn_frame = tk.Frame(win, bg="#f4f4f8", pady=20)
    btn_frame.pack(fill="x")
    tk.Button(btn_frame, text="Guardar", bg="#4CAF50", fg="white", command=guardar, width=15).pack(side="left", padx=20)
    tk.Button(btn_frame, text="Cancelar", bg="#f44336", fg="white", command=win.destroy, width=15).pack(side="right", padx=20)

    e_nom.focus_set()
    configurar_navegacion_ventana(win)
    return win