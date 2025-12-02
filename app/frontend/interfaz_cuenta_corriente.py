# app/frontend/interfaz_cuenta_corriente.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Toplevel
from typing import Optional, Any
import logging

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

logger = logging.getLogger(__name__)

class CuentaCorriente:
    def __init__(self, parent: tk.Misc, backend, usuario: dict):
        self.backend = backend
        self.usuario = usuario
        self.win = tk.Toplevel(parent)
        self.win.title("🏦 Gestión de Cuentas Corrientes")
        self.win.geometry("900x600")
        self.win.config(bg="#f4f4f8")
        self.win.resizable(False, False)

        self.crear_widgets()
        self.cargar_deudores()
        
        configurar_navegacion_ventana(self.win)
        self.win.grab_set()

    def _fmt_mon(self, val: Any) -> str:
        try: return f"$ {float(val):,.2f}"
        except: return "$ 0.00"

    def crear_widgets(self):
        # Frame superior más limpio (solo la instrucción)
        frm_acciones = tk.Frame(self.win, bg="#f4f4f8", pady=15)
        frm_acciones.pack(fill=tk.X)

        tk.Label(frm_acciones, text="💡 Doble Click en un cliente para registrar pago", 
                 bg="#f4f4f8", fg="#555", font=("Segoe UI", 10, "italic")).pack(side=tk.LEFT, padx=20)
        
        # (Botón recargar eliminado por redundante)

        frm_lista = tk.LabelFrame(self.win, text="Estado de Cuentas", bg="#f4f4f8", padx=10, pady=10)
        frm_lista.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        cols = ("ID Cliente", "Nombre", "Teléfono", "Email", "Saldo Actual", "Límite Crédito")
        self.tree_deudores = ttk.Treeview(frm_lista, columns=cols, show="headings", height=18)
        self.tree_deudores.pack(side="left", fill="both", expand=True)

        ys = ttk.Scrollbar(frm_lista, orient="vertical", command=self.tree_deudores.yview)
        ys.pack(side="right", fill="y")
        self.tree_deudores.configure(yscrollcommand=ys.set)

        for c in cols: self.tree_deudores.heading(c, text=c)
        
        self.tree_deudores.column("ID Cliente", width=70, anchor="center")
        self.tree_deudores.column("Nombre", width=200)
        self.tree_deudores.column("Teléfono", width=100)
        self.tree_deudores.column("Email", width=180)
        self.tree_deudores.column("Saldo Actual", width=120, anchor="e")
        self.tree_deudores.column("Límite Crédito", width=100, anchor="e")
        
        self.tree_deudores.tag_configure("deuda", foreground="#dc2626")
        self.tree_deudores.tag_configure("favor", foreground="#16a34a")
        self.tree_deudores.tag_configure("cero", foreground="black")

        self.tree_deudores.bind("<Double-1>", self.on_doble_click)

    def on_doble_click(self, event):
        sel = self.tree_deudores.selection()
        if not sel: return
        item = self.tree_deudores.item(sel[0], "values")
        # item[1] es el Nombre del cliente
        self.abrir_ventana_pago(cliente_preseleccionado=item[1])

    def cargar_deudores(self):
        for i in self.tree_deudores.get_children(): self.tree_deudores.delete(i)
        try:
            clientes = self.backend.listar_clientes_con_saldos(incluir_inactivos=False)
            clientes.sort(key=lambda x: float(x.get('saldo', 0.0)))

            for d in clientes:
                saldo = float(d.get('saldo', 0.0))
                limite = float(d.get('limite_credito', 0.0))
                
                if saldo < -0.01:
                    tag = "deuda"
                    saldo_txt = f"- $ {abs(saldo):,.2f}"
                elif saldo > 0.01:
                    tag = "favor"
                    saldo_txt = f"+ $ {saldo:,.2f}"
                else:
                    tag = "cero"
                    saldo_txt = "$ 0.00"

                self.tree_deudores.insert("", tk.END, values=[
                    d.get('id_cliente'), d.get('nombre'),
                    d.get('telefono') or "", d.get('email') or "",
                    saldo_txt, self._fmt_mon(limite)
                ], tags=(tag,))
                
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self.win)

    def abrir_ventana_pago(self, cliente_preseleccionado=None):
        self.win_pago = Toplevel(self.win)
        self.win_pago.title("Registrar Pago")
        self.win_pago.geometry("550x450")
        self.win_pago.config(bg="#f4f4f8")
        self.win_pago.transient(self.win)
        self.win_pago.grab_set()

        self.cliente_seleccionado = None
        self.cuenta_seleccionada = None
        self.saldo_actual_cache = 0.0

        frame = tk.Frame(self.win_pago, bg="#f4f4f8")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        tk.Label(frame, text="1. Seleccione Cliente:", bg="#f4f4f8", font=("bold")).grid(row=0, column=0, sticky="w")
        
        try:
            clis = self.backend.listar_clientes()
            self.clientes_map = {c.get('nombre'): c for c in clis}
            names = sorted(self.clientes_map.keys())
        except: names = []
            
        self.cb_clientes_pago = ttk.Combobox(frame, state="readonly", values=names, width=40)
        self.cb_clientes_pago.grid(row=1, column=0, columnspan=2, pady=5)
        self.cb_clientes_pago.bind("<<ComboboxSelected>>", self.cargar_info_cuenta)
        
        if cliente_preseleccionado and cliente_preseleccionado in names:
            self.cb_clientes_pago.set(cliente_preseleccionado)
            self.cargar_info_cuenta() 
        
        tk.Label(frame, text="Saldo Actual:", bg="#f4f4f8").grid(row=2, column=0, sticky="e")
        self.lbl_saldo = tk.Label(frame, text="-", bg="#f4f4f8", font=("bold"), fg="blue")
        self.lbl_saldo.grid(row=2, column=1, sticky="w")
        
        ttk.Separator(frame).grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        tk.Label(frame, text="2. Ingrese Pago:", bg="#f4f4f8", font=("bold")).grid(row=4, column=0, sticky="w")

        tk.Label(frame, text="Monto ($):", bg="#f4f4f8").grid(row=5, column=0, sticky="e")
        self.entry_monto = tk.Entry(frame, width=15)
        self.entry_monto.grid(row=5, column=1, sticky="w")
        self.entry_monto.bind("<KeyRelease>", self.calcular_saldo_proyectado)
        self.entry_monto.focus_set()

        tk.Label(frame, text="Método:", bg="#f4f4f8").grid(row=6, column=0, sticky="e")
        self.cb_metodo = ttk.Combobox(frame, state="readonly", values=["efectivo", "tarjeta_debito", "transferencia"], width=15)
        self.cb_metodo.grid(row=6, column=1, sticky="w")
        self.cb_metodo.current(0)
        
        tk.Label(frame, text="Resultado:", bg="#f4f4f8").grid(row=7, column=0, sticky="e", pady=10)
        self.lbl_resultado = tk.Label(frame, text="-", bg="#f4f4f8", font=("Arial", 11, "bold"))
        self.lbl_resultado.grid(row=7, column=1, sticky="w", pady=10)

        btn_frame = tk.Frame(frame, bg="#f4f4f8")
        btn_frame.grid(row=8, column=0, columnspan=2, pady=20)
        tk.Button(btn_frame, text="Confirmar Pago", command=self.confirmar_pago, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancelar", command=self.win_pago.destroy, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=10)

        configurar_navegacion_ventana(self.win_pago)

    def cargar_info_cuenta(self, event=None):
        nombre = self.cb_clientes_pago.get()
        self.cliente_seleccionado = self.clientes_map.get(nombre)
        if not self.cliente_seleccionado: return
        
        try:
            self.backend.crear_cuenta_corriente_si_no_existe(self.cliente_seleccionado['id_cliente'])
            cta = self.backend.obtener_cuenta_por_cliente(self.cliente_seleccionado['id_cliente'])
            self.cuenta_seleccionada = cta
            
            self.saldo_actual_cache = float(cta.get('saldo', 0.0))
            
            if self.saldo_actual_cache < 0:
                txt = f"- $ {abs(self.saldo_actual_cache):,.2f} (Deuda)"
                col = "#dc2626"
            else:
                txt = f"+ $ {self.saldo_actual_cache:,.2f} (A Favor)"
                col = "#16a34a"
                
            self.lbl_saldo.config(text=txt, fg=col)
            self.calcular_saldo_proyectado()
        except: pass

    def calcular_saldo_proyectado(self, event=None):
        if not self.cuenta_seleccionada: return
        try:
            pago = float(self.entry_monto.get() or 0)
        except: pago = 0.0
        
        nuevo_saldo = self.saldo_actual_cache + pago
        
        if nuevo_saldo >= 0:
            self.lbl_resultado.config(text=f"Saldo Final: + $ {nuevo_saldo:,.2f} (A Favor)", fg="green")
        else:
            self.lbl_resultado.config(text=f"Saldo Final: - $ {abs(nuevo_saldo):,.2f} (Deuda)", fg="red")

    def confirmar_pago(self):
        if not self.cliente_seleccionado: return
        try:
            monto = float(self.entry_monto.get())
            if monto <= 0: raise ValueError
        except:
            messagebox.showwarning("Error", "Monto inválido", parent=self.win_pago)
            return
            
        try:
            ok = self.backend.registrar_pago_cuenta_corriente(
                self.cuenta_seleccionada['id_cuenta'],
                monto, self.cb_metodo.get(), self.usuario['id_usuario']
            )
            if ok:
                messagebox.showinfo("Éxito", "Pago registrado.", parent=self.win_pago)
                self.win_pago.destroy()
                self.cargar_deudores() # Esto actualiza la lista automáticamente
            else: messagebox.showerror("Error", "Error al guardar", parent=self.win_pago)
        except Exception as e: messagebox.showerror("Error", str(e), parent=self.win_pago)

def ui_cuenta_corriente(parent: tk.Misc, backend, usuario: dict):
    CuentaCorriente(parent, backend, usuario)