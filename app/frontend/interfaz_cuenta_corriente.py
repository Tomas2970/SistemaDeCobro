# app/frontend/interfaz_cuenta_corriente.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from typing import Optional, Any
import logging

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

# 🔥 ENTRY QUE SOLO ACEPTA NÚMEROS Y UN PUNTO DECIMAL
class EntryDecimal(tk.Entry):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        vcmd = (self.register(self._validar), '%P')
        self.config(validate='key', validatecommand=vcmd)
    
    def _validar(self, nuevo_valor: str) -> bool:
        if nuevo_valor == "": return True
        if len(nuevo_valor) > 15: return False
        try:
            if nuevo_valor.replace(',', '.') == ".": return True
            float(nuevo_valor.replace(',', '.'))
            return True
        except ValueError: return False

logger = logging.getLogger(__name__)

class CuentaCorriente:
    def __init__(self, parent: tk.Misc, backend, usuario: dict):
        self.backend = backend
        self.usuario = usuario
        self.win = tk.Toplevel(parent)
        self.win.title("Gestión de Cuentas Corrientes")
        self.win.geometry("1200x650")
        self.win.config(bg="#f4f4f8")
        self.win.resizable(False, False)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Modern.Treeview", background="#ffffff", foreground="#1f2937", rowheight=32, fieldbackground="#ffffff", borderwidth=0, font=('Segoe UI', 10))
        style.configure("Modern.Treeview.Heading", background="#f3f4f6", foreground="#374151", relief="flat", font=('Segoe UI', 10, 'bold'))

        self.clientes_cache = []
        self.crear_widgets()
        self.cargar_deudores()
        
        configurar_navegacion_ventana(self.win)
        self.win.grab_set()

    def _fmt_mon(self, val: Any) -> str:
        try: return f"$ {float(val):,.2f}"
        except: return "$ 0.00"

    def crear_widgets(self):
        frm_header = tk.Frame(self.win, bg="#f4f4f8", pady=15, padx=20)
        frm_header.pack(fill=tk.X)

        tk.Label(frm_header, text="🔎 Buscar:", bg="#f4f4f8", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(5,10))
        self.var_busqueda_ppal = tk.StringVar()
        entry_busqueda = tk.Entry(frm_header, textvariable=self.var_busqueda_ppal, width=35, font=("Segoe UI", 10))
        entry_busqueda.pack(side=tk.LEFT)
        self.var_busqueda_ppal.trace_add("write", self.filtrar_lista_principal)
        
        tk.Label(frm_header, text="💡 Doble click para registrar pago", bg="#f4f4f8", fg="#6b7280", font=("Segoe UI", 9, "italic")).pack(side=tk.RIGHT, padx=20)
        
        frm_lista = tk.Frame(self.win, bg="#f4f4f8", padx=20)
        frm_lista.pack(fill=tk.BOTH, expand=True, pady=10)

        # 🔥 COLUMNAS CORREGIDAS: Se quitó CUIT
        cols = ("ID Cliente", "Nombre", "DNI", "Teléfono", "Email", "Saldo Actual", "Límite Crédito")
        self.tree_deudores = ttk.Treeview(frm_lista, columns=cols, show="headings", height=15, style="Modern.Treeview")
        self.tree_deudores.pack(side="left", fill="both", expand=True)

        ys = ttk.Scrollbar(frm_lista, orient="vertical", command=self.tree_deudores.yview)
        ys.pack(side="right", fill="y")
        self.tree_deudores.configure(yscrollcommand=ys.set)

        for col in cols: self.tree_deudores.heading(col, text=col)
        self.tree_deudores.column("ID Cliente", width=0, minwidth=0, stretch=False)
        self.tree_deudores.column("Nombre", width=200)
        self.tree_deudores.column("DNI", width=90, anchor="center")
        self.tree_deudores.column("Teléfono", width=100, anchor="center")
        self.tree_deudores.column("Email", width=180)
        self.tree_deudores.column("Saldo Actual", width=140, anchor="e")
        self.tree_deudores.column("Límite Crédito", width=130, anchor="e")
        
        self.tree_deudores.tag_configure("deuda", foreground="#dc2626")
        self.tree_deudores.tag_configure("favor", foreground="#16a34a")
        self.tree_deudores.bind("<Double-1>", self.on_doble_click)
        
        frame_botones = tk.Frame(self.win, bg="#f4f4f8", pady=15)
        frame_botones.pack(fill="x", padx=20)
        
        tk.Button(frame_botones, text="Cerrar", command=self.win.destroy, bg="#64748b", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=10, cursor="hand2").pack(side=tk.RIGHT)

    def on_doble_click(self, event):
        sel = self.tree_deudores.selection()
        if not sel: return
        item = self.tree_deudores.item(sel[0], "values")
        self.abrir_ventana_pago(int(item[0]))

    def cargar_deudores(self):
        try:
            data = self.backend.listar_clientes_con_saldos(incluir_inactivos=False)
            def prioridad_saldo(c):
                s = float(c.get('saldo', 0.0))
                if s < -0.01: return 0
                if s > 0.01: return 1
                return 2
            self.clientes_cache = sorted(data, key=prioridad_saldo)
            self.filtrar_lista_principal()
        except Exception as e:
            logger.error(f"Error cargando deudores: {e}")

    def filtrar_lista_principal(self, *args):
        q = self.var_busqueda_ppal.get().lower().strip()
        for i in self.tree_deudores.get_children(): self.tree_deudores.delete(i)

        for d in self.clientes_cache:
            txt_busqueda = f"{d.get('nombre','')} {d.get('dni','')} {d.get('id_cliente','')}".lower()
            if not q or q in txt_busqueda:
                saldo = float(d.get('saldo', 0.0))
                tag = "deuda" if saldo < -0.01 else "cero"
                # Mostrar en positivo con etiqueta clara
                if saldo < -0.01:
                    saldo_txt = f"$ {abs(saldo):,.2f}"
                else:
                    saldo_txt = "Sin deuda"

                # 🔥 VALORES INSERTADOS: Se quitó el dato de CUIT
                self.tree_deudores.insert("", tk.END, values=[
                    d.get('id_cliente'), d.get('nombre'), d.get('dni') or "-",
                    d.get('telefono') or "", d.get('email') or "",
                    saldo_txt, self._fmt_mon(d.get('limite_credito', 0.0))
                ], tags=(tag,))

    def abrir_ventana_pago(self, id_cliente):
        self.win_pago = Toplevel(self.win)
        self.win_pago.title("Registrar Pago")
        self.win_pago.geometry("500x460")
        self.win_pago.config(bg="#f4f4f8")
        self.win_pago.resizable(False, False)
        self.win_pago.transient(self.win)
        self.win_pago.grab_set()

        cliente = next((c for c in self.clientes_cache if c['id_cliente'] == id_cliente), None)
        if not cliente: return self.win_pago.destroy()

        self.backend.crear_cuenta_corriente_si_no_existe(id_cliente)
        self.cuenta_seleccionada = self.backend.obtener_cuenta_por_cliente(id_cliente)
        self.saldo_actual_cache = float(self.cuenta_seleccionada.get('saldo', 0.0))

        frame = tk.Frame(self.win_pago, bg="#ffffff", padx=30, pady=30)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.columnconfigure(0, weight=0, minsize=120)
        frame.columnconfigure(1, weight=1)
        
        tk.Label(frame, text="Registrar Pago de Cliente", bg="#ffffff", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")

        tk.Label(frame, text="Cliente:", bg="#ffffff", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="e", pady=5)
        tk.Label(frame, text=cliente['nombre'], bg="#ffffff", font=("Segoe UI", 11)).grid(row=1, column=1, sticky="w", padx=10)

        ttk.Separator(frame, orient="horizontal").grid(row=2, column=0, columnspan=2, sticky="ew", pady=15)

        tk.Label(frame, text="Monto ($):", bg="#ffffff", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="e", pady=10)
        frm_monto = tk.Frame(frame, bg="#ffffff")
        frm_monto.grid(row=3, column=1, sticky="w", padx=10)
        self.entry_monto = EntryDecimal(frm_monto, width=18, font=("Segoe UI", 11), justify="right")
        self.entry_monto.pack(side=tk.LEFT)
        self._deuda_maxima = abs(self.saldo_actual_cache) if self.saldo_actual_cache < -0.01 else 0.0

        self.entry_monto.bind("<KeyRelease>", self.calcular_saldo_proyectado)
        self.entry_monto.focus_set()

        tk.Label(frame, text="Método:", bg="#ffffff", font=("Segoe UI", 10, "bold")).grid(row=4, column=0, sticky="e", pady=10)
        self.cb_metodo = ttk.Combobox(frame, state="readonly", values=["efectivo", "transferencia", "tarjeta_debito"], width=16, font=("Segoe UI", 10))
        self.cb_metodo.grid(row=4, column=1, sticky="w", padx=10)
        self.cb_metodo.current(0)

        # Cuadro inferior: arranca mostrando la deuda, se actualiza al escribir
        frame_res = tk.Frame(frame, bg="#f8fafc", relief="solid", bd=1)
        frame_res.grid(row=5, column=0, columnspan=2, sticky="ew", pady=20)
        tk.Label(frame_res, text="Deuda del cliente:", bg="#f8fafc", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=15, pady=10)
        if self._deuda_maxima > 0:
            texto_inicial = f"Debe: $ {self._deuda_maxima:,.2f}"
            color_inicial = "#dc2626"
        else:
            texto_inicial = "Sin deuda"
            color_inicial = "#6b7280"
        self.lbl_resultado = tk.Label(frame_res, text=texto_inicial, bg="#f8fafc",
                                      font=("Segoe UI", 11, "bold"), fg=color_inicial,
                                      wraplength=280, anchor="w")
        self.lbl_resultado.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        btn_frm = tk.Frame(frame, bg="#ffffff")
        btn_frm.grid(row=7, column=0, columnspan=2, pady=(10, 0))
        
        tk.Button(btn_frm, text="💾 GUARDAR PAGO", command=self.confirmar_pago, bg="#16a34a", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=8, cursor="hand2").pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frm, text="CANCELAR", command=self.win_pago.destroy, bg="#64748b", fg="white", font=("Segoe UI", 10), relief="flat", padx=15, pady=8, cursor="hand2").pack(side=tk.LEFT)

        configurar_navegacion_ventana(self.win_pago)

    # 🔥 FUNCIÓN CORREGIDA: Mensaje genérico cuando la caja está cerrada
    def confirmar_pago(self):
        try:
            monto_raw = self.entry_monto.get().strip()
            if not monto_raw:
                messagebox.showwarning("Atención", "Ingrese un monto.", parent=self.win_pago)
                return
            monto = float(monto_raw.replace(",", "."))
            
            if monto <= 0:
                messagebox.showwarning("Atención", "El monto debe ser mayor a 0.", parent=self.win_pago)
                return
            if monto > self._deuda_maxima + 0.01:
                messagebox.showwarning(
                    "Monto excede la deuda",
                    f"La deuda es de $ {self._deuda_maxima:,.2f}. No puede ingresar un monto mayor.",
                    parent=self.win_pago
                )
                self.entry_monto.delete(0, tk.END)
                self.entry_monto.insert(0, f"{self._deuda_maxima:.2f}")
                return

            uid = self.usuario['id_usuario']
            id_cuenta = self.cuenta_seleccionada.get('id_cuenta')
            
            resultado = self.backend.registrar_pago_cuenta_corriente(id_cuenta, monto, self.cb_metodo.get(), uid)
            if resultado:
                messagebox.showinfo("Éxito", "Pago registrado correctamente.", parent=self.win_pago)
                self.win_pago.destroy()
                self.cargar_deudores()
            else:
                messagebox.showerror("Error", "No se pudo registrar el pago. Revisá que la caja esté abierta.", parent=self.win_pago)
                
        except ValueError as ve:
            if "CAJA_CERRADA" in str(ve):
                messagebox.showerror("Caja Cerrada", "No se puede procesar el pago porque la caja está cerrada.", parent=self.win_pago)
            else:
                messagebox.showerror("Error", f"Monto inválido: {ve}", parent=self.win_pago)
        except Exception as e:
            messagebox.showerror("Error Crítico", f"No se pudo procesar el pago: {e}", parent=self.win_pago)

    def calcular_saldo_proyectado(self, event=None):
        try: pago = float(self.entry_monto.get().replace(",", ".") or 0)
        except: pago = 0.0
        # Sin nada escrito: mostrar deuda original
        if pago <= 0:
            if self._deuda_maxima > 0:
                self.lbl_resultado.config(text=f"Debe: $ {self._deuda_maxima:,.2f}", fg="#dc2626")
            else:
                self.lbl_resultado.config(text="Sin deuda", fg="#6b7280")
            return
        if pago > self._deuda_maxima + 0.01:
            txt = f"⚠ Excede la deuda (máx $ {self._deuda_maxima:,.2f})"
            col = "#f59e0b"
        else:
            restante = self._deuda_maxima - pago
            if restante > 0.01:
                txt = f"Quedará debiendo: $ {restante:,.2f}"
                col = "#dc2626"
            else:
                txt = "Deuda cancelada ✓"
                col = "#059669"
        self.lbl_resultado.config(text=txt, fg=col)

def ui_cuenta_corriente(parent: tk.Misc, backend, usuario: dict):
    CuentaCorriente(parent, backend, usuario)