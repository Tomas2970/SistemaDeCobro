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
    win.title("Editar Cliente" if id_cliente_a_editar else "Nuevo Cliente")
    win.geometry("450x500")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # --- VALIDACIONES EN TIEMPO REAL (KEY PRESS) ---
    
    def check_dni(t):
        # DNI: máximo 8 dígitos
        if len(t) > 8: return False
        return t.isdigit() or t == ""
    
    def check_cuit(t):
        # CUIT: máximo 11 dígitos
        if len(t) > 11: return False
        return t.isdigit() or t == ""
    
    def check_telefono(t):
        # Teléfono: máximo 20 dígitos
        if len(t) > 20: return False
        return t.isdigit() or t == ""

    vc_dni = (win.register(check_dni), '%P')
    vc_cuit = (win.register(check_cuit), '%P')
    vc_tel = (win.register(check_telefono), '%P')

    # Variables
    var_nombre = tk.StringVar()
    var_dni = tk.StringVar()
    var_cuit = tk.StringVar()
    var_tel = tk.StringVar()
    var_email = tk.StringVar()
    var_dir = tk.StringVar()
    var_limite = tk.StringVar(value="50000.00")

    if id_cliente_a_editar:
        cli = backend.obtener_cliente_para_editar(id_cliente_a_editar)
        if cli:
            # 🔥 CORRECCIÓN: Usamos or '' para convertir None a string vacía en todos los campos
            var_nombre.set(cli.get('nombre', '') or '')
            var_dni.set(cli.get('dni', '') or '')
            var_cuit.set(cli.get('cuit', '') or '')
            var_tel.set(cli.get('telefono', '') or '')
            var_email.set(cli.get('email', '') or '')
            var_dir.set(cli.get('direccion', '') or '')
            var_limite.set(str(cli.get('limite_credito', '50000.00')) or '0.00')

    frm = tk.Frame(win, bg="#f4f4f8", padx=20, pady=20)
    frm.pack(fill="both", expand=True)

    def row(lbl, var, r, vcmd=None):
        tk.Label(frm, text=lbl, bg="#f4f4f8", anchor="w").grid(row=r, column=0, sticky="ew", pady=5)
        e = tk.Entry(frm, textvariable=var, validate="key", validatecommand=vcmd) if vcmd else tk.Entry(frm, textvariable=var)
        e.grid(row=r, column=1, sticky="ew", pady=5)
        return e

    # DNI y CUIT separados con validaciones
    e_nom = row("Nombre (*):", var_nombre, 0)
    e_dni = row("DNI (*):", var_dni, 1, vc_dni)
    e_cuit = row("CUIT/CUIL:", var_cuit, 2, vc_cuit)
    row("Teléfono:", var_tel, 3, vc_tel)
    row("Email:", var_email, 4)
    row("Dirección:", var_dir, 5)
    row("Límite Crédito ($):", var_limite, 6)

    frm.columnconfigure(1, weight=1)

    def guardar():
        nom = var_nombre.get().strip()
        dni = var_dni.get().strip()
        cuit = var_cuit.get().strip()
        tel = var_tel.get().strip()
        
        # VALIDACIÓN DE OBLIGATORIEDAD y LONGITUD ESTRICTA
        if not nom: return messagebox.showwarning("Error", "Nombre obligatorio", parent=win)
        if not dni: return messagebox.showwarning("Error", "DNI obligatorio", parent=win)
        
        if len(dni) not in [7, 8]: return messagebox.showwarning("Error", "DNI debe tener 7 u 8 dígitos.", parent=win)
        if cuit and len(cuit) != 11: return messagebox.showwarning("Error", "CUIT debe tener 11 dígitos.", parent=win)
        
        try: limite = float(var_limite.get())
        except: limite = 0.0

        try:
            if id_cliente_a_editar:
                ok = backend.actualizar_cliente(id_cliente_a_editar, nom, dni, cuit, var_dir.get(), tel, var_email.get(), limite)
                msg = "Cliente actualizado"
            else:
                ok = backend.crear_cliente(nom, dni, cuit, var_dir.get(), tel, var_email.get(), limite)
                msg = "Cliente creado"
                
            if ok:
                messagebox.showinfo("Éxito", msg, parent=win)
                win.destroy() 
            else:
                messagebox.showerror("Error", "No se pudo guardar.", parent=win)
        
        except ValueError as ve:
            msg = str(ve)
            if "DNI_DUPLICADO" in msg: messagebox.showerror("Error", f"El DNI {dni} ya existe.", parent=win)
            elif "EMAIL_DUPLICADO" in msg: messagebox.showerror("Error", "El Email ya existe.", parent=win)
            else: messagebox.showerror("Error de Validación", msg, parent=win)

        except Exception as e:
            error_msg = str(e)
            if "1062" in error_msg and ("dni" in error_msg.lower() or "email" in error_msg.lower() or "cuit" in error_msg.lower()):
                 messagebox.showerror("Error de Duplicado", "DNI, CUIT o Email duplicado detectado.", parent=win)
            else:
                messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado:\n{e}", parent=win)

    btn_frame = tk.Frame(win, bg="#f4f4f8", pady=20)
    btn_frame.pack(fill="x")
    # 🔥 BOTONES UNIFICADOS
    tk.Button(btn_frame, text="Guardar", command=guardar, 
              bg="#16a34a", fg="white", font=("Segoe UI", 10, "bold"), 
              relief="flat", padx=15, pady=7, cursor="hand2", width=15).pack(side="left", padx=20)
    tk.Button(btn_frame, text="Cancelar", command=win.destroy, 
              bg="#f44336", fg="white", font=("Segoe UI", 10), 
              relief="flat", padx=15, pady=7, cursor="hand2", width=15).pack(side="right", padx=20)

    e_nom.focus_set()
    configurar_navegacion_ventana(win)
    return win