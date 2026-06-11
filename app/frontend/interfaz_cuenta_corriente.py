# app/frontend/interfaz_cuenta_corriente.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from app.frontend import custom_dialogs as messagebox
from typing import Optional, Any
import logging
import customtkinter as ctk

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

try:
    from app.frontend.theme_config import configurar_estilo_treeview
except ImportError:
    def configurar_estilo_treeview(): pass

class EntryDecimal(ctk.CTkEntry):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        vcmd = (self.register(self._validar), '%P')
        self.configure(validate='key', validatecommand=vcmd)
    
    def _validar(self, nuevo_valor: str) -> bool:
        if nuevo_valor == "": return True
        if len(nuevo_valor) > 15: return False
        try:
            val = nuevo_valor.replace(',', '.')
            if val == "." or val == "-": return True
            float(val)
            return True
        except ValueError: return False

logger = logging.getLogger(__name__)

class CuentaCorriente:
    def __init__(self, parent: tk.Misc, backend, usuario: dict):
        self.backend = backend
        self.usuario = usuario
        self.win = ctk.CTkToplevel(parent)
        self.win.title("Gestión de Cuentas Corrientes")
        self.win.geometry("1200x650")
        
        self.col_bg = "#f3f4f6" if ctk.get_appearance_mode()=="Light" else "#111827"
        self.col_card = "#ffffff" if ctk.get_appearance_mode()=="Light" else "#1f2937"
        self.col_border = "#e5e7eb" if ctk.get_appearance_mode()=="Light" else "#374151"
        self.col_text = "#374151" if ctk.get_appearance_mode()=="Light" else "white"
        
        self.col_input_bg = "#f9fafb" if ctk.get_appearance_mode() == "Light" else "#374151"
        self.col_input_fg = "#1f2937" if ctk.get_appearance_mode() == "Light" else "#f9fafb"
        self.col_tree_bg = "#ffffff" if ctk.get_appearance_mode() == "Light" else "#1f2937"
        self.col_tree_fg = "#1f2937" if ctk.get_appearance_mode() == "Light" else "white"
        self.col_tree_head = "#f3f4f6" if ctk.get_appearance_mode() == "Light" else "#111827"
        
        self.win.configure(fg_color=self.col_bg)
        self.win.resizable(True, True)

        configurar_estilo_treeview()

        self.clientes_cache = []
        self.crear_widgets()
        self.cargar_deudores()
        
        configurar_navegacion_ventana(self.win)
        self.win.grab_set()

    def _fmt_mon(self, val: Any) -> str:
        try: return f"$ {float(val):,.2f}"
        except: return "$ 0.00"

    def crear_widgets(self):
        frm_header = ctk.CTkFrame(self.win, fg_color=self.col_card, corner_radius=10, border_color=self.col_border, border_width=1)
        frm_header.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(frm_header, text="🔎 Buscar:", font=("Segoe UI", 14, "bold"), text_color=self.col_text).pack(side="left", padx=(15,5), pady=15)
        self.var_busqueda_ppal = tk.StringVar()
        
        self.entry_busqueda = ctk.CTkEntry(frm_header, textvariable=self.var_busqueda_ppal, font=("Segoe UI", 13), width=350, height=40, placeholder_text="Nombre, DNI o ID...")
        self.entry_busqueda.pack(side="left", padx=15)
        
        def limpiar_filtros_cc():
            self.var_busqueda_ppal.set("")
            self.entry_busqueda.focus_set()
            
        ctk.CTkButton(frm_header, text="🧹 Limpiar", command=limpiar_filtros_cc, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 12, "bold"), width=100, height=35).pack(side="left", padx=(0, 15))
        
        self.var_busqueda_ppal.trace_add("write", self.filtrar_lista_principal)
        
        ctk.CTkLabel(frm_header, text="💡 Doble click sobre un cliente para registrar pago", font=("Segoe UI", 12, "italic"), text_color="#6b7280").pack(side="right", padx=20)
        
        frm_lista = ctk.CTkFrame(self.win, fg_color=self.col_card, corner_radius=10, border_color=self.col_border, border_width=1)
        frm_lista.pack(fill="both", expand=True, padx=15, pady=5)

        cols = ("ID Cliente", "Nombre", "DNI", "Teléfono", "Email", "Saldo Actual", "Límite Crédito")
        self.tree_deudores = ttk.Treeview(frm_lista, columns=cols, show="headings", height=15, style="Modern.Treeview")

        ys = ctk.CTkScrollbar(frm_lista, command=self.tree_deudores.yview)
        ys.pack(side="right", fill="y", padx=(0, 5), pady=5)
        self.tree_deudores.configure(yscrollcommand=ys.set)
        self.tree_deudores.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        for col in cols: self.tree_deudores.heading(col, text=col)
        self.tree_deudores.column("ID Cliente", width=0, minwidth=0, stretch=False)
        self.tree_deudores.column("Nombre", width=250)
        self.tree_deudores.column("DNI", width=120, anchor="center")
        self.tree_deudores.column("Teléfono", width=120, anchor="center")
        self.tree_deudores.column("Email", width=200)
        self.tree_deudores.column("Saldo Actual", width=150, anchor="e")
        self.tree_deudores.column("Límite Crédito", width=150, anchor="e")
        
        self.tree_deudores.tag_configure("deuda", foreground="#f87171")
        self.tree_deudores.tag_configure("favor", foreground="#10b981")
        self.tree_deudores.tag_configure("cero", foreground="#6b7280" if ctk.get_appearance_mode() == "Light" else "#9ca3af")
        self.tree_deudores.bind("<Double-1>", self.on_doble_click)
        
        frame_botones = ctk.CTkFrame(self.win, fg_color="transparent")
        frame_botones.pack(fill="x", side="bottom", padx=15, pady=(5, 15))
        
        ctk.CTkButton(frame_botones, text="Cerrar", command=self.win.destroy, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 14, "bold"), width=150, height=45).pack(side="right", padx=10)

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
                if saldo < -0.01:
                    saldo_txt = f"- $ {abs(saldo):,.2f}"
                else:
                    saldo_txt = "$ 0.00"

                self.tree_deudores.insert("", tk.END, values=[
                    d.get('id_cliente'), d.get('nombre'), d.get('dni') or "-",
                    d.get('telefono') or "", d.get('email') or "",
                    saldo_txt, self._fmt_mon(d.get('limite_credito', 0.0))
                ], tags=(tag,))

    def abrir_ventana_pago(self, id_cliente):
        self.win_pago = ctk.CTkToplevel(self.win)
        self.win_pago.title("Registrar Pago")
        self.win_pago.geometry("500x520")
        self.win_pago.configure(fg_color=self.col_bg)
        self.win_pago.resizable(False, False)
        self.win_pago.transient(self.win)
        self.win_pago.grab_set()

        cliente = next((c for c in self.clientes_cache if c['id_cliente'] == id_cliente), None)
        if not cliente: return self.win_pago.destroy()

        self.backend.crear_cuenta_corriente_si_no_existe(id_cliente)
        self.cuenta_seleccionada = self.backend.obtener_cuenta_por_cliente(id_cliente)
        self.saldo_actual_cache = float(self.cuenta_seleccionada.get('saldo', 0.0))

        frame = ctk.CTkFrame(self.win_pago, fg_color=self.col_card, corner_radius=10, border_color=self.col_border, border_width=1)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.columnconfigure(0, weight=0, minsize=140)
        frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(frame, text="Registrar Pago de Cliente", font=("Segoe UI", 18, "bold"), text_color=self.col_text).grid(row=0, column=0, columnspan=2, pady=(15, 20), padx=20, sticky="w")

        ctk.CTkLabel(frame, text="Cliente:", font=("Segoe UI", 13, "bold"), text_color=self.col_text).grid(row=1, column=0, sticky="e", pady=5, padx=10)
        ctk.CTkLabel(frame, text=cliente['nombre'], font=("Segoe UI", 14), text_color=self.col_text).grid(row=1, column=1, sticky="w", padx=10)

        ctk.CTkLabel(frame, text="----------------------------------------------------------------", text_color=self.col_border).grid(row=2, column=0, columnspan=2, sticky="ew", pady=15, padx=20)

        ctk.CTkLabel(frame, text="Monto a Pagar ($):", font=("Segoe UI", 13, "bold"), text_color=self.col_text).grid(row=3, column=0, sticky="e", pady=10, padx=10)
        
        self.entry_monto = EntryDecimal(frame, font=("Segoe UI", 15, "bold"), justify="right", width=180, height=45)
        self.entry_monto.grid(row=3, column=1, sticky="w", padx=10)
        
        self._deuda_maxima = abs(self.saldo_actual_cache) if self.saldo_actual_cache < -0.01 else 0.0

        self.entry_monto.bind("<KeyRelease>", self.calcular_saldo_proyectado)
        self.entry_monto.focus_set()

        ctk.CTkLabel(frame, text="Método:", font=("Segoe UI", 13, "bold"), text_color=self.col_text).grid(row=4, column=0, sticky="e", pady=15, padx=10)
        
        # Diccionario para mapear selecciones visuales a las claves de BD reales
        self.mapa_metodos = {
            "Efectivo": "efectivo",
            "Transferencia": "transferencia",
            "Tarjeta de Débito": "tarjeta_debito"
        }
        self.cb_metodo = ctk.CTkOptionMenu(frame, values=["Efectivo", "Transferencia", "Tarjeta de Débito"], font=("Segoe UI", 13), width=180, height=40, fg_color=self.col_input_bg, text_color=self.col_input_fg, button_color="#4b5563", button_hover_color="#374151")
        self.cb_metodo.grid(row=4, column=1, sticky="w", padx=10, pady=15)
        self.cb_metodo.set("Efectivo")

        frame_res = ctk.CTkFrame(frame, fg_color=self.col_input_bg, corner_radius=6)
        frame_res.grid(row=5, column=0, columnspan=2, sticky="ew", pady=20, padx=20)
        
        ctk.CTkLabel(frame_res, text="Deuda del cliente:", font=("Segoe UI", 13), text_color=self.col_text).pack(side="left", padx=15, pady=15)
        if self._deuda_maxima > 0:
            texto_inicial = f"- $ {self._deuda_maxima:,.2f}"
            color_inicial = "#ef4444"
        else:
            texto_inicial = "$ 0.00"
            color_inicial = "#6b7280"
        self.lbl_resultado = ctk.CTkLabel(frame_res, text=texto_inicial, font=("Segoe UI", 14, "bold"), text_color=color_inicial)
        self.lbl_resultado.pack(side="left", padx=5, fill="x", expand=True)

        btn_frm = ctk.CTkFrame(self.win_pago, fg_color="transparent")
        btn_frm.pack(fill="x", side="bottom", padx=20, pady=(0, 20))
        
        ctk.CTkButton(btn_frm, text="Cancelar", command=self.win_pago.destroy, fg_color="#ef4444", hover_color="#dc2626", font=("Segoe UI", 14, "bold"), width=150, height=45).pack(side="left", padx=10)
        ctk.CTkButton(btn_frm, text="💾 GUARDAR PAGO", command=self.confirmar_pago, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 15, "bold"), width=200, height=45).pack(side="right", padx=10)

        configurar_navegacion_ventana(self.win_pago)

    def confirmar_pago(self):
        try:
            monto_raw = self.entry_monto.get().strip()
            if not monto_raw:
                messagebox.showwarning("Monto Requerido", "Por favor, ingresa el monto del pago a registrar.", parent=self.win_pago)
                return
            try:
                monto = float(monto_raw.replace(",", "."))
            except ValueError:
                messagebox.showwarning("Monto Inválido", "El monto ingresado para el pago no es un número válido.", parent=self.win_pago)
                return
            
            if monto <= 0:
                messagebox.showwarning("Monto Inválido", "El monto ingresado para el pago debe ser mayor a cero.", parent=self.win_pago)
                return
            if monto > self._deuda_maxima + 0.01:
                messagebox.showwarning(
                    "Monto Excesivo",
                    f"El monto ingresado supera la deuda actual del cliente ($ {self._deuda_maxima:,.2f}). Por favor, ajusta el monto del pago.",
                    parent=self.win_pago
                )
                self.entry_monto.delete(0, tk.END)
                self.entry_monto.insert(0, f"{self._deuda_maxima:.2f}")
                return

            uid = self.usuario['id_usuario']
            id_cuenta = self.cuenta_seleccionada.get('id_cuenta')
            
            # Mapear el valor visual del OptionMenu al valor SQL
            metodo_sql = self.mapa_metodos.get(self.cb_metodo.get(), "efectivo")
            
            resultado = self.backend.registrar_pago_cuenta_corriente(id_cuenta, monto, metodo_sql, uid)
            if resultado:
                messagebox.showinfo("Éxito", "El pago de cuenta corriente fue registrado correctamente.", parent=self.win_pago)
                self.win_pago.destroy()
                self.cargar_deudores()
            else:
                from app.frontend.manejador_errores import ManejadorErroresUI
                ManejadorErroresUI.manejar_error(Exception("No se pudo registrar el pago. Asegúrate de que la caja de cobros esté abierta."), parent=self.win_pago, contexto="caja")
                
        except ValueError as ve:
            from app.frontend.manejador_errores import ManejadorErroresUI
            ManejadorErroresUI.manejar_error(ve, parent=self.win_pago, contexto="monto")
        except Exception as e:
            from app.frontend.manejador_errores import ManejadorErroresUI
            ManejadorErroresUI.manejar_error(e, parent=self.win_pago, contexto="pago")

    def calcular_saldo_proyectado(self, event=None):
        try: pago = float(self.entry_monto.get().replace(",", ".") or 0)
        except: pago = 0.0
        if pago <= 0:
            if self._deuda_maxima > 0:
                self.lbl_resultado.configure(text=f"- $ {self._deuda_maxima:,.2f}", text_color="#ef4444")
            else:
                self.lbl_resultado.configure(text="$ 0.00", text_color="#6b7280")
            return
        if pago > self._deuda_maxima + 0.01:
            txt = f"⚠ Excede la deuda (máx - $ {self._deuda_maxima:,.2f})"
            col = "#f59e0b"
        else:
            restante = self._deuda_maxima - pago
            if restante > 0.01:
                txt = f"Quedará: - $ {restante:,.2f}"
                col = "#ef4444"
            else:
                txt = "✓ Deuda cancelada ($ 0.00)"
                col = "#10b981"
        self.lbl_resultado.configure(text=txt, text_color=col)

def ui_cuenta_corriente(parent: tk.Misc, backend, usuario: dict):
    CuentaCorriente(parent, backend, usuario)