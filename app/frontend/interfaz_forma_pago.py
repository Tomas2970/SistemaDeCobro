# app/frontend/interfaz_forma_pago.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

class FormaPagoPopup:
    def __init__(self, parent: tk.Misc, total: float, cliente_seleccionado: bool):
        self.parent = parent
        self.total = total
        self.cliente_seleccionado = cliente_seleccionado
        self.resultado: Optional[str] = None # Aquí guardaremos la forma de pago
        
        self.win = tk.Toplevel(parent)
        self.win.title("Forma de Pago")
        self.win.config(bg="#f4f4f8")
        self.win.resizable(False, False)
        
        self.crear_widgets()
        
        self.win.grab_set()
        self.win.transient(parent)
        self.win.wait_window() # Detiene la ejecución hasta que esta ventana se cierre

    def crear_widgets(self):
        frame = tk.Frame(self.win, bg="#f4f4f8", padx=30, pady=20)
        frame.pack()

        tk.Label(frame, text="Total a Pagar:", bg="#f4f4f8", font=("Segoe UI", 12)).pack(pady=(0, 5))
        tk.Label(frame, text=f"$ {self.total:,.2f}", bg="#f4f4f8", font=("Segoe UI", 22, "bold"), fg="#16a34a").pack(pady=(0, 20))

        tk.Label(frame, text="Seleccione el método de pago:", bg="#f4f4f8", font=("Segoe UI", 10)).pack(pady=(10, 5))
        
        # --- Botones de Pago ---
        btn_efectivo = tk.Button(frame, text="Efectivo", command=lambda: self.seleccionar("efectivo"), 
                                 width=20, height=2, bg="#607D8B", fg="white", font=("Segoe UI", 10, "bold"))
        btn_efectivo.pack(pady=5)
        
        btn_tarjeta = tk.Button(frame, text="Tarjeta (Débito/Crédito)", command=lambda: self.seleccionar("tarjeta"), 
                                width=20, height=2, bg="#607D8B", fg="white", font=("Segoe UI", 10, "bold"))
        btn_tarjeta.pack(pady=5)
        
        btn_transferencia = tk.Button(frame, text="Transferencia", command=lambda: self.seleccionar("transferencia"), 
                                      width=20, height=2, bg="#607D8B", fg="white", font=("Segoe UI", 10, "bold"))
        btn_transferencia.pack(pady=5)

        # El botón de Cuenta Corriente solo aparece si hay un cliente seleccionado
        if self.cliente_seleccionado:
            ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=15)
            
            btn_cc = tk.Button(frame, text="Usar Cuenta Corriente", command=lambda: self.seleccionar("cuenta_corriente"), 
                               width=20, height=2, bg="#2563eb", fg="white", font=("Segoe UI", 10, "bold"))
            btn_cc.pack(pady=5)
        
        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=15)
        
        btn_cancelar = tk.Button(frame, text="Cancelar Venta", command=self.cancelar, 
                                 width=20, height=2, bg="#f44336", fg="white", font=("Segoe UI", 10, "bold"))
        btn_cancelar.pack(pady=5)

    def seleccionar(self, metodo: str):
        self.resultado = metodo
        self.win.destroy()

    def cancelar(self):
        self.resultado = None # Si es None, la venta se cancela
        self.win.destroy()

    def obtener_resultado(self) -> Optional[str]:
        return self.resultado

# Función wrapper para llamarla fácilmente
def pedir_forma_pago(parent: tk.Misc, total: float, cliente_seleccionado: bool) -> Optional[str]:
    popup = FormaPagoPopup(parent, total, cliente_seleccionado)
    return popup.obtener_resultado()