# app/frontend/interfaz_forma_pago.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Any, Optional

# ¡NUEVO! Importar navegación por teclado
try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    print("ADVERTENCIA: navegacion_teclado_comun.py no encontrado")
    def configurar_navegacion_ventana(win, confirmar_cierre=False):
        pass

class VentanaPago:
    """Ventana para seleccionar forma de pago y calcular vuelto"""

    def __init__(self, parent, total_venta, cliente_seleccionado, callback):
        """
        Args:
            parent: Ventana padre
            total_venta: Monto total de la venta
            cliente_seleccionado: (bool) True si hay un cliente
            callback: Función a llamar con (tipo_pago, monto_pagado, vuelto)
        """
        self.total_venta = total_venta
        self.cliente_seleccionado = cliente_seleccionado
        self.callback = callback
        self.resultado = None

        # Crear ventana modal
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Método de Pago")
        self.ventana.resizable(False, False)
        self.ventana.transient(parent)
        self.ventana.grab_set()

        self._crear_widgets()

        # --- TAMAÑO / CENTRADO DINÁMICO ---
        self.ventana.update_idletasks()
        req_w = max(450, self.ventana.winfo_reqwidth() + 20)
        req_h = max(460, self.ventana.winfo_reqheight() + 20)
        sw = self.ventana.winfo_screenwidth()
        sh = self.ventana.winfo_screenheight()
        x = (sw - req_w) // 2
        y = (sh - req_h) // 2
        self.ventana.geometry(f"{req_w}x{req_h}+{x}+{y}")
        
        # ¡NUEVO! Aplicar navegación por teclado
        configurar_navegacion_ventana(self.ventana)
        
        # ¡NUEVO! Foco inicial en el campo de pago
        self.ventana.after(50, lambda: self.entry_paga.focus_set())

        self.ventana.wait_window()

    def _crear_widgets(self):
        """Crear todos los widgets de la ventana"""
        main_frame = ttk.Frame(self.ventana, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        titulo = ttk.Label(
            main_frame,
            text="Seleccione Método de Pago",
            font=("Arial", 14, "bold")
        )
        titulo.pack(pady=(0, 20))

        frame_total = ttk.LabelFrame(main_frame, text="Total a Pagar", padding="10")
        frame_total.pack(fill=tk.X, pady=(0, 20))

        total_label = ttk.Label(
            frame_total,
            text=f"$ {self.total_venta:,.2f}",
            font=("Arial", 20, "bold"),
            foreground="green"
        )
        total_label.pack()

        frame_metodo = ttk.LabelFrame(main_frame, text="Método de Pago", padding="10")
        frame_metodo.pack(fill=tk.X, pady=(0, 15))

        self.metodo_var = tk.StringVar(value="efectivo")

        metodos = [
            ("Efectivo", "efectivo"),
            ("Tarjeta Débito/Crédito", "tarjeta"),
            ("Transferencia", "transferencia"),
        ]
        for texto, valor in metodos:
            ttk.Radiobutton(
                frame_metodo, text=texto,
                variable=self.metodo_var, value=valor,
                command=self._cambio_metodo
            ).pack(anchor=tk.W, pady=2)

        rb_cc = ttk.Radiobutton(
            frame_metodo,
            text="Cuenta Corriente",
            variable=self.metodo_var,
            value="cuenta_corriente",
            command=self._cambio_metodo
        )
        rb_cc.pack(anchor=tk.W, pady=2)
        if not self.cliente_seleccionado:
            rb_cc.config(state="disabled", text="Cuenta Corriente (Debe elegir un cliente)")

        self.frame_efectivo = ttk.LabelFrame(main_frame, text="Detalles del Pago", padding="10")
        self.frame_efectivo.pack(fill=tk.X, pady=(0, 18))

        frame_paga = ttk.Frame(self.frame_efectivo)
        frame_paga.pack(fill=tk.X, pady=6)
        ttk.Label(frame_paga, text="Paga con: $", width=12).pack(side=tk.LEFT)
        self.entry_paga = ttk.Entry(frame_paga, font=("Arial", 12), width=15)
        self.entry_paga.pack(side=tk.LEFT, padx=6)
        self.entry_paga.bind("<KeyRelease>", self._calcular_vuelto)
        self.entry_paga.bind("<Return>", lambda e: self._confirmar())

        frame_vuelto = ttk.Frame(self.frame_efectivo)
        frame_vuelto.pack(fill=tk.X, pady=6)
        ttk.Label(frame_vuelto, text="Vuelto:", width=12).pack(side=tk.LEFT)
        self.label_vuelto = ttk.Label(frame_vuelto, text="$ 0.00", font=("Arial", 14, "bold"), foreground="blue")
        self.label_vuelto.pack(side=tk.LEFT, padx=6)

        frame_botones = ttk.Frame(main_frame)
        frame_botones.pack(fill=tk.X, pady=(14, 0))
        
        btn_confirmar = ttk.Button(frame_botones, text="Confirmar Pago", command=self._confirmar)
        btn_confirmar.pack(side=tk.RIGHT, padx=6)
        
        btn_cancelar = ttk.Button(frame_botones, text="Cancelar", command=self._cancelar)
        btn_cancelar.pack(side=tk.RIGHT)

        self._cambio_metodo()

    def _cambio_metodo(self):
        if self.metodo_var.get() == "efectivo":
            self.frame_efectivo.pack(fill=tk.X, pady=(0, 18))
            self.entry_paga.delete(0, tk.END)
            self.entry_paga.insert(0, f"{self.total_venta:.2f}")
            self.entry_paga.select_range(0, tk.END)
            self.entry_paga.focus_set()
            self._calcular_vuelto()
        else:
            self.frame_efectivo.pack_forget()

    def _calcular_vuelto(self, event=None):
        try:
            monto_str = self.entry_paga.get().strip().replace(",", ".")
            if not monto_str:
                self.label_vuelto.config(text="$ 0.00", foreground="blue")
                return
            monto_pagado = float(monto_str)
            vuelto = monto_pagado - self.total_venta
            if vuelto < 0:
                self.label_vuelto.config(text=f"$ {abs(vuelto):,.2f} (FALTA)", foreground="red")
            else:
                self.label_vuelto.config(text=f"$ {vuelto:,.2f}", foreground="green")
        except ValueError:
            self.label_vuelto.config(text="$ 0.00", foreground="blue")

    def _confirmar(self):
        tipo_pago = self.metodo_var.get()
        if tipo_pago == "efectivo":
            try:
                monto_pagado = float(self.entry_paga.get().strip().replace(",", "."))
                if monto_pagado < self.total_venta:
                    messagebox.showerror(
                        "Error",
                        f"El monto pagado (${monto_pagado:.2f}) es menor al total (${self.total_venta:.2f})",
                        parent=self.ventana
                    )
                    return
                vuelto = monto_pagado - self.total_venta
                self.resultado = {'tipo_pago': tipo_pago, 'monto_pagado': monto_pagado, 'vuelto': vuelto}
            except ValueError:
                messagebox.showerror("Error", "Ingrese un monto válido", parent=self.ventana)
                return
        else:
            self.resultado = {'tipo_pago': tipo_pago, 'monto_pagado': self.total_venta, 'vuelto': 0.0}

        if self.callback:
            self.callback(self.resultado)
        self.ventana.destroy()

    def _cancelar(self):
        self.resultado = None
        self.ventana.destroy()

    def obtener_resultado(self):
        return self.resultado


def mostrar_ventana_pago(parent, total_venta, cliente_seleccionado):
    resultado = None
    def callback(res):
        nonlocal resultado
        resultado = res
    VentanaPago(parent, total_venta, cliente_seleccionado, callback)
    return resultado