# app/frontend/interfaz_forma_pago.py
# 🎨 ACTUALIZADO: Estilo de botones unificado
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Optional
import re

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False):
        pass

class VentanaPago:
    """Ventana para seleccionar forma de pago y calcular vuelto"""

    def __init__(self, parent, total_venta, cliente_seleccionado, callback):
        self.total_venta = round(float(total_venta), 2)
        # Máximo razonable: un solo billete de 0k cubre cualquier compra hasta 0k.
        import math
        def _sugerir_pago(total):
            for b in [100, 200, 500, 1000, 2000, 10000, 20000]:
                if b >= total:
                    return b
            return math.ceil(total / 20000) * 20000
        self._sugerir_pago = _sugerir_pago
        self.cliente_seleccionado = cliente_seleccionado
        self.callback = callback
        self.resultado = None

        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Método de Pago")
        self.ventana.resizable(False, False)
        self.ventana.transient(parent)
        self.ventana.grab_set()
        self.ventana.config(bg="#f4f4f8")

        self._crear_widgets()

        self.ventana.update_idletasks()
        req_w = max(500, self.ventana.winfo_reqwidth() + 20)
        req_h = max(520, self.ventana.winfo_reqheight() + 20)
        sw = self.ventana.winfo_screenwidth()
        sh = self.ventana.winfo_screenheight()
        x = (sw - req_w) // 2
        y = (sh - req_h) // 2
        self.ventana.geometry(f"{req_w}x{req_h}+{x}+{y}")
        
        configurar_navegacion_ventana(self.ventana)
        self.ventana.after(50, lambda: self.entry_paga.focus_set())
        self.ventana.wait_window()

    def _crear_widgets(self):
        """Crear todos los widgets de la ventana"""
        main_frame = tk.Frame(self.ventana, bg="#f4f4f8", padx=25, pady=25)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 🔥 TÍTULO MODERNO
        titulo = tk.Label(
            main_frame,
            text="Método de Pago",
            font=("Segoe UI", 16, "bold"),
            bg="#f4f4f8",
            fg="#1f2937"
        )
        titulo.pack(pady=(0, 25))

        # 🔥 FRAME TOTAL (BLANCO CON SOMBRA SUTIL)
        frame_total = tk.Frame(main_frame, bg="#ffffff", relief="flat", bd=0)
        frame_total.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            frame_total,
            text="TOTAL A PAGAR",
            font=("Segoe UI", 11),
            bg="#ffffff",
            fg="#6b7280"
        ).pack(pady=(15, 5))

        total_label = tk.Label(
            frame_total,
            text=f"$ {self.total_venta:,.2f}",
            font=("Segoe UI", 28, "bold"),
            bg="#ffffff",
            fg="#059669"
        )
        total_label.pack(pady=(0, 15))

        # 🔥 MÉTODOS DE PAGO (FRAME BLANCO)
        frame_metodo = tk.Frame(main_frame, bg="#ffffff", relief="flat", bd=0, padx=20, pady=15)
        frame_metodo.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            frame_metodo,
            text="Seleccione el método:",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            fg="#1f2937"
        ).pack(anchor=tk.W, pady=(0, 10))

        self.metodo_var = tk.StringVar(value="efectivo")

        metodos = [
            ("💵 Efectivo", "efectivo"),
            ("💳 Tarjeta Débito/Crédito", "tarjeta"),
            ("🏦 Transferencia", "transferencia"),
        ]
        
        for texto, valor in metodos:
            rb = tk.Radiobutton(
                frame_metodo, 
                text=texto,
                variable=self.metodo_var, 
                value=valor,
                command=self._cambio_metodo,
                bg="#ffffff",
                fg="#374151",
                font=("Segoe UI", 10),
                activebackground="#ffffff",
                activeforeground="#1f2937",
                selectcolor="#ffffff",
                cursor="hand2"
            )
            rb.pack(anchor=tk.W, pady=3)

        rb_cc = tk.Radiobutton(
            frame_metodo,
            text="📋 Cuenta Corriente",
            variable=self.metodo_var,
            value="cuenta_corriente",
            command=self._cambio_metodo,
            bg="#ffffff",
            fg="#374151",
            font=("Segoe UI", 10),
            activebackground="#ffffff",
            activeforeground="#1f2937",
            selectcolor="#ffffff",
            cursor="hand2"
        )
        rb_cc.pack(anchor=tk.W, pady=3)
        
        if not self.cliente_seleccionado:
            rb_cc.config(state="disabled", text="📋 Cuenta Corriente (Debe elegir un cliente)", fg="#9ca3af")

        # 🔥 FRAME EFECTIVO (BLANCO)
        self.frame_efectivo = tk.Frame(main_frame, bg="#ffffff", relief="flat", bd=0, padx=20, pady=15)
        self.frame_efectivo.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            self.frame_efectivo,
            text="Detalles del pago en efectivo:",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1f2937"
        ).pack(anchor=tk.W, pady=(0, 10))

        frame_paga = tk.Frame(self.frame_efectivo, bg="#ffffff")
        frame_paga.pack(fill=tk.X, pady=8)
        
        tk.Label(
            frame_paga, 
            text="Paga con:", 
            width=12,
            bg="#ffffff",
            fg="#374151",
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)
        
        def validar_float(texto):
            if texto == "": return True
            if not re.match(r'^[0-9]*\.?[0-9]*$', texto): return False
            try:
                tope = self._sugerir_pago(self.total_venta)
                if float(texto) > tope: return False
            except: pass
            return True

        vcmd = (self.ventana.register(validar_float), '%P')
        
        self.entry_paga = tk.Entry(
            frame_paga, 
            font=("Segoe UI", 13), 
            width=15, 
            validate="key", 
            validatecommand=vcmd,
            relief="solid",
            bd=1,
            bg="#ffffff"
        )
        self.entry_paga.pack(side=tk.LEFT, padx=8)
        def _on_key_paga(event=None):
            self._calcular_vuelto()
            # Aplicar tope DESPUÉS de escribir, no mientras
            try:
                val = float(self.entry_paga.get().replace(",", "."))
                tope = self._sugerir_pago(self.total_venta)
                if val > tope:
                    self.entry_paga.delete(0, tk.END)
                    self.entry_paga.insert(0, str(tope))
                    self._calcular_vuelto()
            except: pass

        self.entry_paga.bind("<KeyRelease>", _on_key_paga)
        self.entry_paga.bind("<Return>", lambda e: self._confirmar())

        frame_vuelto = tk.Frame(self.frame_efectivo, bg="#ffffff")
        frame_vuelto.pack(fill=tk.X, pady=8)
        
        tk.Label(
            frame_vuelto, 
            text="Vuelto:", 
            width=12,
            bg="#ffffff",
            fg="#374151",
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)
        
        self.label_vuelto = tk.Label(
            frame_vuelto, 
            text="$ 0.00", 
            font=("Segoe UI", 16, "bold"), 
            bg="#ffffff",
            fg="#3b82f6"
        )
        self.label_vuelto.pack(side=tk.LEFT, padx=8)

        # 🔥 BOTONES ESTILO NUEVO
        frame_botones = tk.Frame(main_frame, bg="#f4f4f8")
        frame_botones.pack(fill=tk.X, pady=(15, 0))
        
        btn_cancelar = tk.Button(
            frame_botones, 
            text="Cancelar", 
            command=self._cancelar,
            bg="#6b7280",
            fg="white",
            font=("Segoe UI", 10),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground="#4b5563",
            activeforeground="white"
        )
        btn_cancelar.pack(side=tk.RIGHT, padx=5)
        
        btn_confirmar = tk.Button(
            frame_botones, 
            text="✓ Confirmar Pago", 
            command=self._confirmar,
            bg="#10b981",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            padx=25,
            pady=10,
            cursor="hand2",
            activebackground="#059669",
            activeforeground="white"
        )
        btn_confirmar.pack(side=tk.RIGHT, padx=5)

        self._cambio_metodo()

    def _cambio_metodo(self):
        if self.metodo_var.get() == "efectivo":
            self.frame_efectivo.pack(fill=tk.X, pady=(0, 20))
            self.entry_paga.delete(0, tk.END)
            sugerido = self._sugerir_pago(self.total_venta)
            self.entry_paga.insert(0, str(sugerido))
            self.entry_paga.select_range(0, tk.END)
            self.entry_paga.focus_set()
            self._calcular_vuelto()
        else:
            self.frame_efectivo.pack_forget()

    def _calcular_vuelto(self, event=None):
        try:
            monto_str = self.entry_paga.get().strip().replace(",", ".")
            if not monto_str:
                self.label_vuelto.config(text="$ 0.00", fg="#3b82f6")
                return
            
            monto_pagado = float(monto_str)
            diferencia = round(monto_pagado - self.total_venta, 2)
            
            if diferencia < 0:
                self.label_vuelto.config(text=f"$ {abs(diferencia):,.2f} (FALTA)", fg="#ef4444")
            else:
                self.label_vuelto.config(text=f"$ {diferencia:,.2f}", fg="#10b981")
                
        except ValueError:
            self.label_vuelto.config(text="$ 0.00", fg="#3b82f6")

    def _confirmar(self):
        tipo_pago = self.metodo_var.get()
        if tipo_pago == "efectivo":
            try:
                monto_pagado = float(self.entry_paga.get().strip().replace(",", "."))
                
                if round(monto_pagado, 2) < round(self.total_venta, 2):
                    messagebox.showerror(
                        "Error",
                        f"El monto pagado (${monto_pagado:,.2f}) es menor al total (${self.total_venta:,.2f})",
                        parent=self.ventana
                    )
                    return
                
                vuelto = round(monto_pagado - self.total_venta, 2)
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