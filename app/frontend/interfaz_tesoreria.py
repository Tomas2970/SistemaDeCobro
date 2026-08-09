import customtkinter as ctk
import tkinter as tk
import logging
from app.frontend.theme_config import get_color, configurar_estilo_treeview
from app.frontend import custom_dialogs as messagebox
from tkinter import ttk

logger = logging.getLogger(__name__)

class InterfazTesoreria:
    def __init__(self, parent, backend, usuario):
        self.parent = parent
        self.backend = backend
        self.usuario = usuario
        self.win = ctk.CTkToplevel(parent)
        self.win.title("🏦 Tesorería - Gestión de Fondos")
        self.win.geometry("900x600")
        self.win.grab_set()
        
        # Color fondo
        self.bg_color = get_color("bg_surface") if ctk.get_appearance_mode() == "Light" else "#111827"
        self.win.configure(fg_color=self.bg_color)

        self.crear_interfaz()
        self.actualizar_estado()

    def crear_interfaz(self):
        # Título
        header = ctk.CTkFrame(self.win, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header, text="🏦 Tesorería Central", font=("Segoe UI", 24, "bold")).pack(side="left")

        # Contenedor principal
        main_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Panel Izquierdo: Estado de la Tesorería
        estado_frame = ctk.CTkFrame(main_frame, fg_color=get_color("bg_surface"), corner_radius=15, border_width=1, border_color="#d1d5db" if ctk.get_appearance_mode() == "Light" else "#475569")
        estado_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(estado_frame, text="📊 Estado Actual", font=("Segoe UI", 18, "bold")).pack(pady=(20, 10))
        
        self.lbl_estado = ctk.CTkLabel(estado_frame, text="Buscando...", font=("Segoe UI", 16))
        self.lbl_estado.pack(pady=5)

        self.lbl_saldo = ctk.CTkLabel(estado_frame, text="$0.00", font=("Segoe UI", 36, "bold"), text_color="#10b981")
        self.lbl_saldo.pack(pady=(10, 20))

        self.btn_abrir = ctk.CTkButton(estado_frame, text="✅ Abrir Tesorería", font=("Segoe UI", 14, "bold"), fg_color="#10b981", hover_color="#059669", height=45, command=self.abrir_tesoreria)
        self.btn_abrir.pack(fill="x", padx=40, pady=10)

        self.btn_cerrar = ctk.CTkButton(estado_frame, text="⛔ Cerrar Tesorería", font=("Segoe UI", 14, "bold"), fg_color="#ef4444", hover_color="#dc2626", height=45, command=self.cerrar_tesoreria)
        self.btn_cerrar.pack(fill="x", padx=40, pady=10)

        # Panel Derecho: Aportes e Ingresos
        acciones_frame = ctk.CTkFrame(main_frame, fg_color=get_color("bg_surface"), corner_radius=15, border_width=1, border_color="#d1d5db" if ctk.get_appearance_mode() == "Light" else "#475569")
        acciones_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(acciones_frame, text="💸 Movimientos Extraordinarios", font=("Segoe UI", 18, "bold")).pack(pady=(20, 10))
        
        form_frame = ctk.CTkFrame(acciones_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=10)

        ctk.CTkLabel(form_frame, text="Monto ($):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 2))
        self.var_monto = tk.StringVar()
        ctk.CTkEntry(form_frame, textvariable=self.var_monto, font=("Segoe UI", 14), height=35).pack(fill="x")

        ctk.CTkLabel(form_frame, text="Motivo:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(15, 2))
        self.var_motivo = tk.StringVar(value="aporte_capital")
        motivos = ["aporte_capital", "ingreso_bancario_a_caja"]
        self.combo_motivo = ctk.CTkComboBox(form_frame, variable=self.var_motivo, values=motivos, state="readonly", font=("Segoe UI", 14), height=35)
        self.combo_motivo.pack(fill="x")

        ctk.CTkLabel(form_frame, text="Descripción:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(15, 2))
        self.var_desc = tk.StringVar()
        ctk.CTkEntry(form_frame, textvariable=self.var_desc, font=("Segoe UI", 14), height=35).pack(fill="x")

        self.btn_registrar = ctk.CTkButton(acciones_frame, text="➕ Registrar Ingreso", font=("Segoe UI", 14, "bold"), fg_color="#3b82f6", hover_color="#2563eb", height=45, command=self.registrar_ingreso)
        self.btn_registrar.pack(fill="x", padx=40, pady=(0, 30))

    def actualizar_estado(self):
        try:
            tesoreria = self.backend.obtener_tesoreria_activa()
            if tesoreria:
                self.id_session = tesoreria['id_session']
                self.lbl_estado.configure(text="✅ Abierta (Día en curso)", text_color="#10b981")
                
                # Obtener saldo de la tesorería (monto apertura + ingresos efectivo - egresos efectivo)
                # Reutilizamos lógica de resumen o iteramos sobre sesiones
                sesiones = self.backend.obtener_sesiones_abiertas_con_totales()
                saldo = 0.0
                for s in sesiones:
                    if s.get('id_session') == self.id_session:
                        saldo = float(s.get('monto_acumulado', 0.0))
                        break
                
                self.lbl_saldo.configure(text=f"${saldo:,.2f}")
                self.btn_abrir.configure(state="disabled")
                self.btn_cerrar.configure(state="normal")
                self.btn_registrar.configure(state="normal")
            else:
                self.id_session = None
                self.lbl_estado.configure(text="⛔ Cerrada", text_color="#ef4444")
                self.lbl_saldo.configure(text="$0.00")
                self.btn_abrir.configure(state="normal")
                self.btn_cerrar.configure(state="disabled")
                self.btn_registrar.configure(state="disabled")
        except Exception as e:
            logger.error(f"Error actualizando estado tesorería: {e}")
            self.lbl_estado.configure(text="Error de conexión")

    def abrir_tesoreria(self):
        monto_str = messagebox.mostrar_entrada("Abrir Tesorería", "Ingrese el monto inicial (Ej: 0):", parent=self.win)
        if monto_str is None: return
        from app.frontend.validaciones_ui import ValidadorFormulario
        ok, msg = ValidadorFormulario.validar_campos({
            'Monto inicial': (monto_str, 'monto', True)
        })
        if not ok:
            messagebox.mostrar_error("Error", msg, parent=self.win)
            return
        monto = float(monto_str)

        try:
            if self.backend.abrir_caja_session(self.usuario['id_usuario'], monto, tipo_caja='administrativa'):
                messagebox.mostrar_exito("Éxito", "Tesorería abierta correctamente.", parent=self.win)
                self.actualizar_estado()
            else:
                messagebox.mostrar_error("Error", "No se pudo abrir la tesorería.", parent=self.win)
        except ValueError as e:
            messagebox.mostrar_error("Error", str(e), parent=self.win)

    def cerrar_tesoreria(self):
        if not messagebox.mostrar_confirmacion("Cerrar Tesorería", "¿Seguro que deseas cerrar la Tesorería de hoy?", parent=self.win):
            return
            
        try:
            if hasattr(self.backend, "cerrar_caja_por_supervisor"):
                if self.backend.cerrar_caja_por_supervisor(self.id_session, self.usuario['id_usuario'], "Cierre Manual de Tesorería"):
                    messagebox.mostrar_exito("Éxito", "Tesorería cerrada correctamente.", parent=self.win)
                    self.actualizar_estado()
                else:
                    messagebox.mostrar_error("Error", "No se pudo cerrar la tesorería.", parent=self.win)
            else:
                messagebox.mostrar_error("Error", "El backend no tiene implementado el cierre forzado.", parent=self.win)
        except Exception as e:
            messagebox.mostrar_error("Error", f"Error al cerrar: {e}", parent=self.win)

    def registrar_ingreso(self):
        monto_str = self.var_monto.get().strip()
        from app.frontend.validaciones_ui import ValidadorFormulario
        ok, msg = ValidadorFormulario.validar_campos({
            'Monto a ingresar': (monto_str, 'monto', True)
        })
        if not ok:
            messagebox.mostrar_error("Error", msg, parent=self.win)
            return
        
        monto = float(monto_str)
        if monto <= 0:
            messagebox.mostrar_error("Error", "El monto debe ser mayor a 0.", parent=self.win)
            return
            
        motivo = self.var_motivo.get()
        desc = self.var_desc.get().strip()
        if not desc:
            messagebox.mostrar_error("Error", "La descripción es obligatoria.", parent=self.win)
            return

        try:
            if self.backend.registrar_movimiento_manual(self.id_session, 'ingreso', monto, motivo, desc, self.usuario['id_usuario']):
                messagebox.mostrar_exito("Éxito", "Ingreso registrado correctamente.", parent=self.win)
                self.var_monto.set("")
                self.var_desc.set("")
                self.actualizar_estado()
            else:
                messagebox.mostrar_error("Error", "No se pudo registrar el ingreso.", parent=self.win)
        except Exception as e:
            messagebox.mostrar_error("Error", str(e), parent=self.win)

def ui_tesoreria(parent, backend, usuario):
    InterfazTesoreria(parent, backend, usuario)
