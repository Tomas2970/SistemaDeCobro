# app/frontend/interfaz_ajuste_stock.py
"""
Módulo de Ajuste Manual de Inventario.

Proporciona el diálogo `UIAjusteStock` que permite a usuarios con rol
Admin o Supervisor corregir el stock de un producto con motivo obligatorio.

Flujo:
    1. Se abre desde UIInventario al seleccionar un producto y pulsar "Ajustar Stock".
    2. El usuario indica el nuevo stock y elige un motivo predefinido.
    3. Si el motivo es "Otro", debe ingresar una descripción adicional.
    4. Tras una confirmación explícita, se aplica el ajuste y se registran:
       - Una fila en AuditoriaAcciones (acción: AJUSTE_STOCK_MANUAL, con motivo en datos_nuevos).
       - Una fila en AuditoriaInventario (tipo_movimiento='ajuste_manual', observaciones=motivo).
"""
from __future__ import annotations
import tkinter as tk
from typing import Callable, Optional
import logging

from app.frontend import custom_dialogs as messagebox

try:
    from app.frontend.theme_config import preparar_ventana, centrar_y_mostrar_ventana
except ImportError:
    def preparar_ventana(w): pass
    def centrar_y_mostrar_ventana(w): pass

try:
    from app.frontend.custom_dialogs import mostrar_toast_centrado
except ImportError:
    def mostrar_toast_centrado(parent, mensaje, **kwargs):
        messagebox.showinfo("Notificación", mensaje, parent=parent)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Motivos predefinidos
# ---------------------------------------------------------------------------
MOTIVOS_AJUSTE = [
    "Merma / Vencimiento",
    "Rotura o daño físico",
    "Diferencia de conteo físico",
    "Corrección de error de carga",
    "Robo o pérdida no identificada",
    "Inventario inicial / apertura",
    "Consumo interno / muestra",
    "Otro",
]

_MOTIVO_OTRO = "Otro"


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------
class UIAjusteStock:
    """
    Diálogo modal para ajustar el stock de un producto.

    Args:
        parent:            Ventana padre (CTkToplevel o CTkFrame raíz).
        backend:           Instancia de BackendAdapter.
        usuario:           Dict con datos del usuario autenticado.
        producto:          Dict con al menos: id_producto, nombre, stock, es_pesable.
        callback_on_save:  Función a llamar cuando el ajuste se aplicó exitosamente
                           (típicamente UIInventario.cargar_todo).
    """

    def __init__(
        self,
        parent: tk.Misc,
        backend,
        usuario: dict,
        producto: dict,
        callback_on_save: Optional[Callable] = None,
    ):
        import customtkinter as ctk

        self.backend = backend
        self.usuario = usuario
        self.producto = producto
        self.callback_on_save = callback_on_save
        self._id_prod = int(producto["id_producto"])
        self._es_pesable = bool(producto.get("es_pesable", False))
        self._stock_actual = float(producto.get("stock", 0.0))
        self._nombre = producto.get("nombre", "—")

        # ── Ventana ──────────────────────────────────────────────────────────
        self.win = ctk.CTkToplevel(parent)
        preparar_ventana(self.win)
        self.win.title("📝 Ajuste Manual de Stock")
        self.win.geometry("520x520")
        self.win.resizable(False, False)

        # Colores
        mode = ctk.get_appearance_mode()
        col_card   = "#ffffff" if mode == "Light" else "#1f2937"
        col_border = "#e5e7eb" if mode == "Light" else "#374151"
        col_text   = "#111827" if mode == "Light" else "#f9fafb"
        col_sub    = "#6b7280"
        col_input  = "#f9fafb" if mode == "Light" else "#374151"

        font_title  = ("Segoe UI", 16, "bold")
        font_label  = ("Segoe UI", 13, "bold")
        font_normal = ("Segoe UI", 13)
        font_small  = ("Segoe UI", 11)

        # ── Header ───────────────────────────────────────────────────────────
        frm_header = ctk.CTkFrame(self.win, fg_color="#4f46e5", corner_radius=0)
        frm_header.pack(fill="x")
        ctk.CTkLabel(
            frm_header,
            text="📦 Ajuste Manual de Inventario",
            font=("Segoe UI", 17, "bold"),
            text_color="white",
        ).pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(
            frm_header,
            text="Solo Administradores y Supervisores pueden realizar esta operación.",
            font=font_small,
            text_color="#c7d2fe",
        ).pack(anchor="w", padx=20, pady=(0, 14))

        # ── Cuerpo ───────────────────────────────────────────────────────────
        frm_body = ctk.CTkFrame(self.win, fg_color=col_card, corner_radius=0)
        frm_body.pack(fill="both", expand=True, padx=0)

        # — Producto (solo lectura) —
        frm_prod = ctk.CTkFrame(frm_body, fg_color=col_input, corner_radius=8)
        frm_prod.pack(fill="x", padx=20, pady=(18, 10))
        ctk.CTkLabel(frm_prod, text="Producto", font=font_small, text_color=col_sub).pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkLabel(frm_prod, text=self._nombre, font=font_label, text_color=col_text, wraplength=440, justify="left").pack(anchor="w", padx=12, pady=(2, 8))

        # — Stocks lado a lado —
        frm_stocks = ctk.CTkFrame(frm_body, fg_color="transparent")
        frm_stocks.pack(fill="x", padx=20, pady=4)
        frm_stocks.grid_columnconfigure(0, weight=1)
        frm_stocks.grid_columnconfigure(1, weight=1)

        frm_actual = ctk.CTkFrame(frm_stocks, fg_color=col_input, corner_radius=8)
        frm_actual.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(frm_actual, text="Stock actual", font=font_small, text_color=col_sub).pack(anchor="w", padx=12, pady=(8, 0))
        stock_fmt = self._fmt_stock(self._stock_actual)
        self._lbl_stock_actual = ctk.CTkLabel(
            frm_actual,
            text=f"{stock_fmt} {'kg' if self._es_pesable else 'un'}",
            font=("Segoe UI", 22, "bold"),
            text_color="#4f46e5",
        )
        self._lbl_stock_actual.pack(anchor="w", padx=12, pady=(2, 8))

        frm_nuevo = ctk.CTkFrame(frm_stocks, fg_color=col_input, corner_radius=8)
        frm_nuevo.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(frm_nuevo, text="Nuevo stock *", font=font_small, text_color=col_sub).pack(anchor="w", padx=12, pady=(8, 0))

        def _validar_decimal(val: str) -> bool:
            from app.frontend.validaciones_ui import ValidadoresTeclado
            return len(val) <= 12 and ValidadoresTeclado.decimal(val)

        vc = (self.win.register(_validar_decimal), "%P")
        self.var_nuevo_stock = tk.StringVar(value=stock_fmt)
        self.ent_nuevo_stock = ctk.CTkEntry(
            frm_nuevo,
            textvariable=self.var_nuevo_stock,
            font=("Segoe UI", 18, "bold"),
            height=38,
            justify="left",
            validate="key",
            validatecommand=vc,
            fg_color="transparent",
            border_width=0,
            text_color="#10b981",
        )
        self.ent_nuevo_stock.pack(anchor="w", padx=10, pady=(2, 8), fill="x")
        self.var_nuevo_stock.trace_add("write", self._actualizar_delta)

        # Delta indicador
        self._lbl_delta = ctk.CTkLabel(frm_body, text="", font=font_small, text_color=col_sub)
        self._lbl_delta.pack(anchor="w", padx=20, pady=(0, 4))

        # — Separador —
        ctk.CTkFrame(frm_body, fg_color=col_border, height=1, corner_radius=0).pack(fill="x", padx=20, pady=8)

        # — Motivo —
        ctk.CTkLabel(frm_body, text="Motivo del ajuste *", font=font_label, text_color=col_text, anchor="w").pack(fill="x", padx=20, pady=(0, 4))
        self.var_motivo = tk.StringVar(value=MOTIVOS_AJUSTE[0])
        self.cb_motivo = ctk.CTkOptionMenu(
            frm_body,
            values=MOTIVOS_AJUSTE,
            variable=self.var_motivo,
            font=font_normal,
            height=38,
            command=self._on_motivo_cambio,
        )
        self.cb_motivo.pack(fill="x", padx=20)

        # — Descripción adicional (visible solo si motivo = "Otro") —
        self.frm_otro = ctk.CTkFrame(frm_body, fg_color="transparent")
        ctk.CTkLabel(self.frm_otro, text="Descripción adicional *", font=font_label, text_color=col_text, anchor="w").pack(fill="x")
        self.var_descripcion = tk.StringVar()
        self.ent_descripcion = ctk.CTkEntry(
            self.frm_otro,
            textvariable=self.var_descripcion,
            font=font_normal,
            height=36,
            placeholder_text="Describa brevemente el motivo…",
        )
        self.ent_descripcion.pack(fill="x", pady=(4, 0))

        # ── Footer con botones ───────────────────────────────────────────────
        frm_footer = ctk.CTkFrame(self.win, fg_color=col_card, corner_radius=0)
        frm_footer.pack(fill="x", side="bottom", padx=20, pady=16)

        ctk.CTkButton(
            frm_footer,
            text="Cancelar",
            fg_color="#6b7280",
            hover_color="#4b5563",
            font=font_label,
            width=130,
            height=44,
            command=self.win.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            frm_footer,
            text="✅ Confirmar Ajuste",
            fg_color="#4f46e5",
            hover_color="#4338ca",
            font=font_label,
            width=190,
            height=44,
            command=self._confirmar,
        ).pack(side="right")

        # ── Inicialización ───────────────────────────────────────────────────
        self._on_motivo_cambio(MOTIVOS_AJUSTE[0])
        self._actualizar_delta()
        centrar_y_mostrar_ventana(self.win)
        self.win.grab_set()
        self.win.after(100, lambda: self.ent_nuevo_stock.focus_set())
        self.ent_nuevo_stock.select_range(0, "end")

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _fmt_stock(self, valor: float) -> str:
        if self._es_pesable:
            return f"{valor:.3f}"
        return str(int(valor))

    def _actualizar_delta(self, *_):
        """Actualiza el indicador de diferencia (+/-) en tiempo real."""
        try:
            nuevo = float(self.var_nuevo_stock.get() or 0)
            diff = nuevo - self._stock_actual
            unidad = "kg" if self._es_pesable else "un"
            if diff > 0:
                texto = f"  ↑  +{diff:,.3f} {unidad} respecto al stock actual"
                color = "#10b981"
            elif diff < 0:
                texto = f"  ↓  {diff:,.3f} {unidad} respecto al stock actual"
                color = "#ef4444"
            else:
                texto = "  Sin cambio respecto al stock actual"
                color = "#6b7280"
            self._lbl_delta.configure(text=texto, text_color=color)
        except ValueError:
            self._lbl_delta.configure(text="", text_color="#6b7280")

    def _on_motivo_cambio(self, valor: str):
        """Muestra u oculta el campo de descripción adicional según el motivo."""
        if valor == _MOTIVO_OTRO:
            self.frm_otro.pack(fill="x", padx=20, pady=(8, 0))
            self.win.after(50, lambda: self.ent_descripcion.focus_set())
        else:
            self.frm_otro.pack_forget()

    # ── Lógica de confirmación ────────────────────────────────────────────────

    def _confirmar(self):
        """Valida los datos y aplica el ajuste previo a una confirmación del usuario."""
        # 1. Validar nuevo stock
        try:
            nuevo_stock = float(self.var_nuevo_stock.get())
        except ValueError:
            messagebox.showwarning("Campo requerido", "Ingrese un valor numérico válido para el nuevo stock.", parent=self.win)
            self.ent_nuevo_stock.focus_set()
            return

        if nuevo_stock < 0:
            messagebox.showwarning("Valor inválido", "El stock no puede ser negativo.", parent=self.win)
            return

        # 2. Validar motivo
        motivo_elegido = self.var_motivo.get()
        if motivo_elegido == _MOTIVO_OTRO:
            descripcion = self.var_descripcion.get().strip()
            if not descripcion:
                messagebox.showwarning("Campo requerido", "Si elige 'Otro', debe ingresar una descripción.", parent=self.win)
                self.ent_descripcion.focus_set()
                return
            motivo_final = f"Otro — {descripcion}"
        else:
            motivo_final = motivo_elegido

        # 3. Sin cambio real
        if nuevo_stock == self._stock_actual:
            messagebox.showinfo("Sin cambio", "El nuevo stock es igual al stock actual. No se realizó ningún ajuste.", parent=self.win)
            return

        # 4. Confirmación explícita
        unidad = "kg" if self._es_pesable else "un"
        diff = nuevo_stock - self._stock_actual
        signo = "+" if diff > 0 else ""
        msg = (
            f"¿Confirmar el ajuste de stock?\n\n"
            f"Producto :       {self._nombre}\n"
            f"Stock anterior : {self._fmt_stock(self._stock_actual)} {unidad}\n"
            f"Stock nuevo :    {self._fmt_stock(nuevo_stock)} {unidad}  ({signo}{diff:.3f})\n"
            f"Motivo :         {motivo_final}"
        )
        if not messagebox.mostrar_confirmacion("Confirmar ajuste", msg, parent=self.win):
            return

        # 5. Aplicar
        try:
            ok = self.backend.actualizar_inventario_absoluto(
                id_producto=self._id_prod,
                stock_abs=nuevo_stock,
                stock_minimo=None,          # No se modifica el mínimo desde aquí
                id_usuario=self.usuario.get("id_usuario"),
                motivo=motivo_final,
            )
            if ok:
                mostrar_toast_centrado(
                    self.win,
                    f"✅ Stock de '{self._nombre}' ajustado correctamente.",
                )
                logger.info(
                    f"Ajuste manual: producto={self._id_prod} | "
                    f"{self._stock_actual} → {nuevo_stock} | motivo='{motivo_final}' | "
                    f"usuario={self.usuario.get('nombre')}"
                )
                if self.callback_on_save:
                    self.callback_on_save()
                self.win.destroy()
            else:
                messagebox.showerror("Error", "No se pudo aplicar el ajuste. Intente nuevamente.", parent=self.win)
        except Exception as e:
            logger.error(f"Error en ajuste manual de stock: {e}")
            messagebox.showerror("Error inesperado", str(e), parent=self.win)


# ---------------------------------------------------------------------------
# Función pública de entrada
# ---------------------------------------------------------------------------

def ui_ajuste_stock(
    parent: tk.Misc,
    backend,
    usuario: dict,
    producto: dict,
    callback_on_save: Optional[Callable] = None,
) -> None:
    """
    Abre el diálogo de ajuste manual de stock.

    Args:
        parent:            Ventana padre.
        backend:           Instancia de BackendAdapter.
        usuario:           Dict del usuario autenticado.
        producto:          Dict del producto seleccionado (id_producto, nombre, stock, es_pesable).
        callback_on_save:  Función a llamar tras el ajuste exitoso.
    """
    UIAjusteStock(parent, backend, usuario, producto, callback_on_save)
