import re

filepath = r"d:\Documentos\GitHub\SistemaDeCobro\app\frontend\interfaz_forma_pago.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

init_start = content.find("    def __init__(self, parent, total_venta, cliente_seleccionado, callback):")
init_end = content.find("    def _crear_widgets(self):")

nuevo_init = """    def __init__(self, parent, total_venta, cliente_seleccionado, callback):
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
        self.ventana.title("Método de Pago")
        self.ventana.resizable(False, False)
        self.ventana.transient(parent)
        self.ventana.grab_set()
        self.col_bg = "#f3f4f6" if ctk.get_appearance_mode()=="Light" else "#111827"
        self.col_card = "#ffffff" if ctk.get_appearance_mode()=="Light" else "#1f2937"
        self.ventana.configure(fg_color=self.col_bg)

        self._crear_widgets()

        self.ventana.update_idletasks()
        req_w = 600
        req_h = 650
        sw = self.ventana.winfo_screenwidth()
        sh = self.ventana.winfo_screenheight()
        x = (sw - req_w) // 2
        y = (sh - req_h) // 2
        self.ventana.geometry(f"{req_w}x{req_h}+{x}+{y}")
        
        configurar_navegacion_ventana(self.ventana)
        self.ventana.after(50, lambda: self.entry_paga.focus_set())
        self.ventana.wait_window()

"""

widgets_start = content.find("    def _crear_widgets(self):")
widgets_end = content.find("    def _cambio_metodo(self):")

nuevo_widgets = """    def _crear_widgets(self):
        import customtkinter as ctk
        col_border = "#e5e7eb" if ctk.get_appearance_mode()=="Light" else "#374151"
        font_title = ("Segoe UI", 16, "bold")
        font_normal = ("Segoe UI", 15)

        main_frame = ctk.CTkFrame(self.ventana, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        ctk.CTkLabel(main_frame, text="Confirmación de Pago", font=("Segoe UI", 22, "bold"), text_color="#1f2937" if ctk.get_appearance_mode()=="Light" else "white").pack(pady=(0, 20))

        frame_total = ctk.CTkFrame(main_frame, fg_color=self.col_card, corner_radius=15, border_color=col_border, border_width=1)
        frame_total.pack(fill="x", pady=(0, 25))
        
        ctk.CTkLabel(frame_total, text="TOTAL A PAGAR", font=("Segoe UI", 15, "bold"), text_color="#6b7280").pack(pady=(20, 5))
        ctk.CTkLabel(frame_total, text=f"$ {self.total_venta:,.2f}", font=("Segoe UI", 48, "bold"), text_color="#10b981").pack(pady=(0, 25))

        frame_metodo = ctk.CTkFrame(main_frame, fg_color=self.col_card, corner_radius=15, border_color=col_border, border_width=1)
        frame_metodo.pack(fill="x", pady=(0, 25))
        
        ctk.CTkLabel(frame_metodo, text="Seleccione el método:", font=font_title, text_color="#1f2937" if ctk.get_appearance_mode()=="Light" else "white").pack(anchor="w", padx=20, pady=(15, 10))

        self.metodo_var = tk.StringVar(value="efectivo")
        metodos = [
            ("💵 Efectivo", "efectivo"),
            ("💳 Tarjeta Débito/Crédito", "tarjeta"),
            ("🏦 Transferencia", "transferencia"),
        ]
        
        for texto, valor in metodos:
            ctk.CTkRadioButton(frame_metodo, text=texto, variable=self.metodo_var, value=valor, command=self._cambio_metodo, font=font_normal, fg_color="#3b82f6", text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white").pack(anchor="w", padx=30, pady=10)

        self.rb_cc = ctk.CTkRadioButton(frame_metodo, text="📋 Cuenta Corriente", variable=self.metodo_var, value="cuenta_corriente", command=self._cambio_metodo, font=font_normal, fg_color="#3b82f6", text_color="#374151" if ctk.get_appearance_mode()=="Light" else "white")
        self.rb_cc.pack(anchor="w", padx=30, pady=(10, 20))
        
        if not self.cliente_seleccionado:
            self.rb_cc.configure(state="disabled", text="📋 Cuenta Corriente (Debe elegir un cliente)", text_color="#9ca3af")

        self.frame_efectivo = ctk.CTkFrame(main_frame, fg_color=self.col_card, corner_radius=15, border_color=col_border, border_width=1)
        self.frame_efectivo.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(self.frame_efectivo, text="Paga con:", font=font_title, text_color="#1f2937" if ctk.get_appearance_mode()=="Light" else "white").grid(row=0, column=0, padx=(20, 10), pady=(20, 10), sticky="w")
        
        def validar_float(texto):
            if texto == "": return True
            import re
            if not re.match(r'^[0-9]*\.?[0-9]*$', texto): return False
            try:
                tope = self._sugerir_pago(self.total_venta)
                if float(texto) > tope: return False
            except: pass
            return True

        vcmd = (self.ventana.register(validar_float), '%P')
        
        frm_paga_border = ctk.CTkFrame(self.frame_efectivo, fg_color="#f3f4f6", height=50, width=180, corner_radius=6)
        frm_paga_border.grid(row=0, column=1, padx=10, pady=(20, 10), sticky="w")
        frm_paga_border.pack_propagate(False)
        self.entry_paga = tk.Entry(frm_paga_border, font=("Segoe UI", 18, "bold"), validate="key", validatecommand=vcmd, bd=0, bg="#f3f4f6", justify="center")
        self.entry_paga.pack(expand=True, fill="both", padx=5, pady=2)
        
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

        ctk.CTkLabel(self.frame_efectivo, text="Vuelto:", font=font_title, text_color="#1f2937" if ctk.get_appearance_mode()=="Light" else "white").grid(row=1, column=0, padx=(20, 10), pady=(10, 20), sticky="w")
        self.label_vuelto = ctk.CTkLabel(self.frame_efectivo, text="$ 0.00", font=("Segoe UI", 24, "bold"), text_color="#3b82f6")
        self.label_vuelto.grid(row=1, column=1, padx=10, pady=(10, 20), sticky="w")

        frame_botones = ctk.CTkFrame(main_frame, fg_color="transparent")
        frame_botones.pack(fill="x", side="bottom")
        
        ctk.CTkButton(frame_botones, text="Cancelar", command=self._cancelar, fg_color="#ef4444", hover_color="#dc2626", font=font_title, width=150, height=55).pack(side="left")
        ctk.CTkButton(frame_botones, text="✓ Confirmar Pago", command=self._confirmar, fg_color="#10b981", hover_color="#059669", font=font_title, width=220, height=55).pack(side="right")

        self._cambio_metodo()

"""

if init_start != -1 and widgets_start != -1:
    content_nuevo = content[:init_start] + nuevo_init + content[init_end:widgets_start] + nuevo_widgets + content[widgets_end:]
    content_nuevo = content_nuevo.replace("self.label_vuelto.config(text=", "self.label_vuelto.configure(text=")
    content_nuevo = content_nuevo.replace("fg=", "text_color=")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content_nuevo)
    print("INTERFAZ PAGO PARCHEADA")
else:
    print("FALLO: No se encontraron los bloques")
