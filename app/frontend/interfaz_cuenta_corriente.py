# app/frontend/interfaz_cuenta_corriente.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Toplevel
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class CuentaCorriente:
    def __init__(self, parent: tk.Misc, backend, usuario: dict):
        self.backend = backend
        self.usuario = usuario # Guardamos el usuario para registrar quién cobra
        self.win = tk.Toplevel(parent)
        self.win.title("🏦 Gestión de Cuentas Corrientes")
        self.win.geometry("900x600")
        self.win.config(bg="#f4f4f8")
        self.win.resizable(False, False)

        self.crear_widgets()
        self.cargar_deudores()
        
        self.win.grab_set()

    def _fmt_mon(self, val: Any) -> str:
        try: return f"$ {float(val):,.2f}"
        except: return "$ 0.00"

    def crear_widgets(self):
        # --- Frame de Acciones ---
        frm_acciones = tk.Frame(self.win, bg="#f4f4f8", pady=15)
        frm_acciones.pack(fill=tk.X)

        tk.Button(frm_acciones, text="Registrar un Pago", 
                  command=self.abrir_ventana_pago, 
                  bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"), width=20, height=2).pack(side=tk.LEFT, padx=20)
        
        tk.Button(frm_acciones, text="↻ Recargar Lista de Deudores", 
                  command=self.cargar_deudores, 
                  bg="#03A9F4", fg="white", font=("Segoe UI", 10, "bold"), width=25, height=2).pack(side=tk.LEFT, padx=10)

        # --- Frame Maestro (Lista de Deudores) ---
        frm_lista = tk.LabelFrame(self.win, text="Clientes con Deuda (Saldo Negativo)", bg="#f4f4f8", padx=10, pady=10)
        frm_lista.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        cols = ("ID Cliente", "Nombre", "Teléfono", "Email", "Saldo Actual", "Límite Crédito")
        self.tree_deudores = ttk.Treeview(frm_lista, columns=cols, show="headings", height=18)
        self.tree_deudores.pack(side="left", fill="both", expand=True)

        ys = ttk.Scrollbar(frm_lista, orient="vertical", command=self.tree_deudores.yview)
        ys.pack(side="right", fill="y")
        self.tree_deudores.configure(yscrollcommand=ys.set)

        for c in cols: self.tree_deudores.heading(c, text=c)
        self.tree_deudores.column("ID Cliente", width=80, anchor="center")
        self.tree_deudores.column("Nombre", width=200)
        self.tree_deudores.column("Teléfono", width=120)
        self.tree_deudores.column("Email", width=200)
        self.tree_deudores.column("Saldo Actual", width=120, anchor="e")
        self.tree_deudores.column("Límite Crédito", width=120, anchor="e")
        
    def cargar_deudores(self):
        # Limpiar tabla
        for i in self.tree_deudores.get_children():
            self.tree_deudores.delete(i)
            
        try:
            deudores = self.backend.obtener_clientes_con_deuda()
            for d in deudores:
                saldo = self._fmt_mon(d.get('saldo'))
                limite = self._fmt_mon(d.get('limite_credito'))
                
                self.tree_deudores.insert("", tk.END, values=[
                    d.get('id_cliente'),
                    d.get('nombre'),
                    d.get('telefono') or "",
                    d.get('email') or "",
                    saldo,
                    limite
                ])
        except Exception as e:
            logger.exception("Error cargando deudores")
            messagebox.showerror("Error", f"No se pudieron cargar los deudores:\n{e}", parent=self.win)

    def abrir_ventana_pago(self):
        # --- Ventana emergente para registrar el pago ---
        self.win_pago = Toplevel(self.win)
        self.win_pago.title("Registrar Pago de Cliente")
        self.win_pago.geometry("500x400")
        self.win_pago.config(bg="#f4f4f8")
        self.win_pago.resizable(False, False)
        
        self.win_pago.grab_set()
        self.win_pago.transient(self.win)

        # --- Variables ---
        self.cliente_seleccionado: dict | None = None
        self.cuenta_seleccionada: dict | None = None
        
        # --- Widgets de la ventana de pago ---
        frame = tk.Frame(self.win_pago, bg="#f4f4f8")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        tk.Label(frame, text="1. Seleccione el Cliente:", bg="#f4f4f8", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", columnspan=2)
        
        try:
            clientes = self.backend.listar_clientes()
            self.clientes_map = {c.get('nombre'): c for c in clientes}
            nombres_clientes = ["Seleccione..."] + sorted(self.clientes_map.keys())
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar clientes:\n{e}", parent=self.win_pago)
            self.win_pago.destroy()
            return
            
        self.cb_clientes_pago = ttk.Combobox(frame, state="readonly", values=nombres_clientes, width=40)
        self.cb_clientes_pago.grid(row=1, column=0, columnspan=2, pady=10)
        self.cb_clientes_pago.current(0)
        self.cb_clientes_pago.bind("<<ComboboxSelected>>", self.cargar_info_cuenta)
        
        # --- Info de la cuenta ---
        tk.Label(frame, text="Saldo Actual:", bg="#f4f4f8").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.lbl_saldo = tk.Label(frame, text="-", bg="#f4f4f8", font=("Segoe UI", 12, "bold"), fg="blue")
        self.lbl_saldo.grid(row=2, column=1, sticky="w", padx=5)
        
        tk.Label(frame, text="Límite de Crédito:", bg="#f4f4f8").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.lbl_limite = tk.Label(frame, text="-", bg="#f4f4f8")
        self.lbl_limite.grid(row=3, column=1, sticky="w", padx=5)

        tk.Label(frame, text="Crédito Disponible:", bg="#f4f4f8").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.lbl_disponible = tk.Label(frame, text="-", bg="#f4f4f8")
        self.lbl_disponible.grid(row=4, column=1, sticky="w", padx=5)
        
        ttk.Separator(frame, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=15)

        # --- Formulario de Pago ---
        tk.Label(frame, text="2. Ingrese el Pago:", bg="#f4f4f8", font=("Segoe UI", 10, "bold")).grid(row=6, column=0, sticky="w", columnspan=2)

        tk.Label(frame, text="Monto a Pagar (*):", bg="#f4f4f8").grid(row=7, column=0, sticky="e", padx=5, pady=10)
        self.entry_monto = tk.Entry(frame, width=15)
        self.entry_monto.grid(row=7, column=1, sticky="w")
        
        tk.Label(frame, text="Método de Pago (*):", bg="#f4f4f8").grid(row=8, column=0, sticky="e", padx=5, pady=10)
        self.cb_metodo = ttk.Combobox(frame, state="readonly", values=["efectivo", "tarjeta_debito", "transferencia", "cheque"], width=15)
        self.cb_metodo.grid(row=8, column=1, sticky="w")
        self.cb_metodo.current(0)
        
        # --- Botones ---
        btn_frame = tk.Frame(frame, bg="#f4f4f8")
        btn_frame.grid(row=9, column=0, columnspan=2, pady=20)
        
        tk.Button(btn_frame, text="Confirmar Pago", command=self.confirmar_pago, bg="#4CAF50", fg="white", width=20).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancelar", command=self.win_pago.destroy, bg="#f44336", fg="white", width=15).pack(side=tk.LEFT, padx=10)

    def cargar_info_cuenta(self, event=None):
        # Resetea los labels
        self.lbl_saldo.config(text="-", fg="blue")
        self.lbl_limite.config(text="-")
        self.lbl_disponible.config(text="-")
        self.cliente_seleccionado = None
        self.cuenta_seleccionada = None

        nombre_cliente = self.cb_clientes_pago.get()
        if nombre_cliente == "Seleccione...":
            return
            
        self.cliente_seleccionado = self.clientes_map.get(nombre_cliente)
        if not self.cliente_seleccionado:
            return
            
        id_cliente = self.cliente_seleccionado.get('id_cliente')
        
        try:
            # --- Lógica Clave: Asegura que la CC exista ---
            self.backend.crear_cuenta_corriente_si_no_existe(id_cliente)
            
            # Ahora sí, obtiene la info de la cuenta
            cuenta = self.backend.obtener_cuenta_por_cliente(id_cliente)
            self.cuenta_seleccionada = cuenta
            
            if cuenta:
                saldo = cuenta.get('saldo', 0.0)
                limite = cuenta.get('limite_credito', 0.0)
                disponible = saldo + limite # Si saldo es -1000 y limite 5000, disponible es 4000
                
                self.lbl_saldo.config(text=self._fmt_mon(saldo), fg=("#ef4444" if saldo < 0 else "blue"))
                self.lbl_limite.config(text=self._fmt_mon(limite))
                self.lbl_disponible.config(text=self._fmt_mon(disponible))
            else:
                self.lbl_saldo.config(text="Error al cargar", fg="#ef4444")

        except Exception as e:
            logger.exception("Error cargando info de cuenta")
            messagebox.showerror("Error", f"No se pudo cargar la info de la cuenta:\n{e}", parent=self.win_pago)

    def confirmar_pago(self):
        # 1. Validar Cliente y Cuenta
        if not self.cliente_seleccionado or not self.cuenta_seleccionada:
            messagebox.showwarning("Faltan datos", "Debe seleccionar un cliente válido.", parent=self.win_pago)
            return
            
        id_cuenta = self.cuenta_seleccionada.get('id_cuenta')
        id_usuario = self.usuario.get('id_usuario')

        # 2. Validar Monto
        try:
            monto = float(self.entry_monto.get().strip())
            if monto <= 0:
                raise ValueError("El monto debe ser positivo")
        except Exception:
            messagebox.showwarning("Monto Inválido", "Ingrese un monto numérico positivo (ej: 1500.50).", parent=self.win_pago)
            return
            
        # 3. Validar Método
        metodo = self.cb_metodo.get()
        
        # 4. Enviar al Backend
        try:
            ok = self.backend.registrar_pago_cuenta_corriente(
                id_cuenta=id_cuenta,
                monto=monto,
                metodo=metodo,
                id_usuario=id_usuario
            )
            
            if ok:
                messagebox.showinfo("Éxito", "Pago registrado correctamente.", parent=self.win_pago)
                self.win_pago.destroy() # Cierra la ventana de pago
                self.cargar_deudores() # Recarga la lista de deudores en la ventana principal
            else:
                messagebox.showerror("Error", "No se pudo registrar el pago.", parent=self.win_pago)
                
        except Exception as e:
            logger.exception("Error al confirmar pago")
            messagebox.showerror("Error", f"Ocurrió un error al guardar:\n{e}", parent=self.win_pago)


# Wrapper para ser llamado desde el menú principal
def ui_cuenta_corriente(parent: tk.Misc, backend, usuario: dict):
    CuentaCorriente(parent, backend, usuario)