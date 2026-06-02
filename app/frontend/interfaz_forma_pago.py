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

try:
    from app.frontend.theme_config import preparar_ventana
except ImportError:
    def preparar_ventana(w): pass

class VentanaPago:
    """Ventana para seleccionar forma de pago y calcular vuelto"""

    def __init__(self, parent, total_venta, cliente_seleccionado, callback):
        import customtkinter as ctk
        self.total_venta = round(float(total_venta), 2)
        import math
        def _sugerir_pago(total):
            for b in [100, 200, 500, 1000, 2000, 10000, 20000]:
                if b >= total: return b
            return math.ceil(total / 20000) * 20000
        self._sugerir_pago = _sugerir_pago
        self.cliente_seleccionado = cliente_seleccionado
        self.callback = callback
        self.resultado = None

        self.ventana = ctk.CTkToplevel(parent)
        preparar_ventana(self.ventana)
        self.ventana.title("Método de Pago")
        self.ventana.resizable(False, False)
        self.ventana.transient(parent)
        
        self.col_bg = "#f3f4f6" if ctk.get_appearance_mode()=="Light" else "#111827"
        self.col_card = "#ffffff" if ctk.get_appearance_mode()=="Light" else "#1f2937"
        self.col_input_bg = "#f9fafb" if ctk.get_appearance_mode() == "Light" else "#374151"
        self.col_input_fg = "#1f2937" if ctk.get_appearance_mode() == "Light" else "#f9fafb"
        
        self.ventana.configure(fg_color=self.col_bg)

        self._crear_widgets()

        self.ventana.update_idletasks()
        req_w = 580
        req_h = min(self.ventana.winfo_reqheight() + 40, 700) 
        sw = self.ventana.winfo_screenwidth()
        sh = self.ventana.winfo_screenheight()
        x = (sw - req_w) // 2
        y = (sh - req_h) // 2
        
        if req_h >= sh - 50:
            self.ventana.resizable(True, True)
        
        self.ventana.geometry(f"{req_w}x{req_h}+{x}+{y}")
        self.ventana.deiconify()
        self.ventana.grab_set()
        
        configurar_navegacion_ventana(self.ventana)
        self.ventana.after(50, lambda: self.entry_paga.focus_set())
        self.ventana.wait_window()

    def _crear_widgets(self):
        import customtkinter as ctk
        col_border = "#e5e7eb" if ctk.get_appearance_mode()=="Light" else "#374151"
        font_title = ("Segoe UI", 16, "bold")
        font_normal = ("Segoe UI", 15)

        main_frame = ctk.CTkFrame(self.ventana, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(main_frame, text="Confirmación de Pago", font=("Segoe UI", 20, "bold"), text_color="#1f2937" if ctk.get_appearance_mode()=="Light" else "white").pack(pady=(0, 10))

        frame_total = ctk.CTkFrame(main_frame, fg_color=self.col_card, corner_radius=10, border_color=col_border, border_width=1)
        frame_total.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(frame_total, text="TOTAL A PAGAR", font=("Segoe UI", 14, "bold"), text_color="#6b7280").pack(pady=(10, 2))
        ctk.CTkLabel(frame_total, text=f"$ {self.total_venta:,.2f}", font=("Segoe UI", 42, "bold"), text_color="#10b981").pack(pady=(0, 10))

        frame_metodo = ctk.CTkFrame(main_frame, fg_color=self.col_card, corner_radius=10, border_color=col_border, border_width=1)
        frame_metodo.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(frame_metodo, text="Seleccione el método:", font=font_title, text_color="#1f2937" if ctk.get_appearance_mode()=="Light" else "white").pack(anchor="w", padx=20, pady=(15, 10))

        self.metodo_var = tk.StringVar(value="efectivo")
        metodos = [
            ("💵 Efectivo", "efectivo"),
            ("💳 Tarjeta Débito/Crédito", "tarjeta"),
            ("🏦 Transferencia", "transferencia"),
        ]
        
        for texto, valor in metodos:
            ctk.CTkRadioButton(frame_metodo, text=texto, variable=self.metodo_var, value=valor, command=self._cambio_metodo, font=font_normal, fg_color="#3b82f6", text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white").pack(anchor="w", padx=25, pady=6)

        self.rb_cc = ctk.CTkRadioButton(frame_metodo, text="📋 Cuenta Corriente", variable=self.metodo_var, value="cuenta_corriente", command=self._cambio_metodo, font=font_normal, fg_color="#3b82f6", text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white")
        self.rb_cc.pack(anchor="w", padx=25, pady=(6, 15))
        
        if not self.cliente_seleccionado:
            self.rb_cc.configure(state="disabled", text="📋 Cuenta Corriente (Debe elegir un cliente)", text_color="#9ca3af")

        self.frame_efectivo = ctk.CTkFrame(main_frame, fg_color=self.col_card, corner_radius=10, border_color=col_border, border_width=1)
        # No se empaqueta todavía, _cambio_metodo lo hace.

        ctk.CTkLabel(self.frame_efectivo, text="Paga con:", font=font_title, text_color="#1f2937" if ctk.get_appearance_mode()=="Light" else "white").grid(row=0, column=0, padx=(15, 5), pady=(15, 5), sticky="w")
        
        def validar_float(texto):
            if texto == "": return True
            import re
            if not re.match(r'^[0-9]*\.?[0-9]*$', texto): return False
            return True

        self.entry_paga = ctk.CTkEntry(self.frame_efectivo, font=("Segoe UI", 18, "bold"), width=180, height=50, justify="center")
        self.entry_paga.grid(row=0, column=1, padx=10, pady=(20, 10), sticky="w")
        
        def _on_key_paga(event=None):
            self._calcular_vuelto()
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

        ctk.CTkLabel(self.frame_efectivo, text="Vuelto:", font=font_title, text_color="#1f2937" if ctk.get_appearance_mode()=="Light" else "white").grid(row=1, column=0, padx=(15, 5), pady=(5, 15), sticky="w")
        self.label_vuelto = ctk.CTkLabel(self.frame_efectivo, text="$ 0.00", font=("Segoe UI", 20, "bold"), text_color="#3b82f6")
        self.label_vuelto.grid(row=1, column=1, padx=5, pady=(5, 15), sticky="w")

        self.frame_botones = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.frame_botones.pack(fill="x", side="bottom", pady=(5, 10))
        
        ctk.CTkButton(self.frame_botones, text="Cancelar", command=self._cancelar, fg_color="#ef4444", hover_color="#dc2626", font=font_title, width=130, height=45).pack(side="left")
        ctk.CTkButton(self.frame_botones, text="✓ Confirmar Pago", command=self._confirmar, fg_color="#10b981", hover_color="#059669", font=font_title, width=180, height=45).pack(side="right")

        self._cambio_metodo()

    def _cambio_metodo(self):
        if self.metodo_var.get() == "efectivo":
            self.frame_efectivo.pack(fill="x", pady=(0, 10), before=self.frame_botones if hasattr(self, 'frame_botones') else None)
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
                self.label_vuelto.configure(text="$ 0.00", text_color="#3b82f6")
                return
            
            monto_pagado = float(monto_str)
            diferencia = round(monto_pagado - self.total_venta, 2)
            
            if diferencia < 0:
                self.label_vuelto.configure(text=f"$ {abs(diferencia):,.2f} (FALTA)", text_color="#ef4444")
            else:
                self.label_vuelto.configure(text=f"$ {diferencia:,.2f}", text_color="#10b981")
                
        except ValueError:
            self.label_vuelto.configure(text="$ 0.00", text_color="#3b82f6")

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