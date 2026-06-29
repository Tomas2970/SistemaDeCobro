# app/frontend/interfaz_reportes.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, Toplevel, Listbox, SINGLE
from app.frontend import custom_dialogs as messagebox
from app.frontend.custom_dialogs import mostrar_exito, mostrar_confirmacion, mostrar_info
from datetime import date, datetime, timedelta
import logging
from typing import Any
import customtkinter as ctk

try:
    from app.frontend.componentes_ui import EntryDecimal, SelectorFecha
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
    from app.database.permisos import tiene_permiso
    from app.frontend.interfaz_historiales import Historiales
    from app.frontend.theme_config import configurar_estilo_treeview, get_color, preparar_ventana, centrar_y_mostrar_ventana
    from app.frontend.autorizacion import solicitar_autorizacion_supervisor
except ImportError:
    class EntryDecimal(ctk.CTkEntry): pass
    class SelectorFecha(ctk.CTkFrame):
        def __init__(self, master, **kw):
            super().__init__(master, fg_color="transparent", **kw)
            self.widget_entrada = ctk.CTkEntry(self)
            self.widget_entrada.pack()
        def get_date_sql(self): return None
    def configurar_navegacion_ventana(win): pass
    def tiene_permiso(u, a): return True
    def configurar_estilo_treeview(): pass
    def get_color(c): return "#ffffff"
    def preparar_ventana(w): pass
    def centrar_y_mostrar_ventana(w): pass
    def solicitar_autorizacion_supervisor(p, b, u, c=None): pass
    Historiales = None

try:
    from app import impresora as impresora
except ImportError:
    try:
        import impresora as impresora
    except ImportError:
        impresora = None

logger = logging.getLogger(__name__)

def _fmt(v):
    try:
        return f"$ {float(v or 0):,.2f}"
    except (TypeError, ValueError):
        return "$ 0.00"

def _darken_color(hex_color):
    colors = {
        "#3b82f6": "#2563eb",
        "#10b981": "#059669",
        "#16a34a": "#059669",
        "#03A9F4": "#0288d1",
        "#ef4444": "#dc2626",
        "#f59e0b": "#d97706",
        "#6b7280": "#4b5563"
    }
    return colors.get(hex_color, hex_color)

def ui_reportes(parent: tk.Misc, backend, usuario: dict, modo_vista: str = 'caja'):
    win = ctk.CTkToplevel(parent)
    
    preparar_ventana(win)
    configurar_estilo_treeview()
    
    col_bg = get_color("bg_root")
    col_card = get_color("bg_surface")
    col_text = get_color("text_primary")
    col_input_bg = "#374151"
    col_input_fg = "#ffffff"

    win.configure(fg_color=col_bg)
    win.col_bg = col_bg
    win.col_card = col_card
    win.col_text = col_text
    win.col_input_bg = col_input_bg
    win.col_input_fg = col_input_fg
    win.col_border = "#2d3748"  # Definido para evitar crash en paneles internos

    win.var_vendedor_sel = {"id": None, "nombre": "(Todos)"}
    win.vendedores_full_list = backend.obtener_vendedores() 

    if modo_vista == 'caja':
        if usuario.get('id_rol') == 1:
            win.title("👑 Panel de Control - Administración")
            win.geometry("1100x700")
            _construir_panel_admin_caja(win, backend, usuario)
        else:
            win.title("📦 Control de Caja")
            win.geometry("900x650")
            _construir_panel_caja(win, backend, usuario)
    else:
        win.title("📊 Reportes de Ventas")
        win.geometry("1150x700")
        _construir_panel_reportes(win, backend, usuario)

    configurar_navegacion_ventana(win)
    centrar_y_mostrar_ventana(win)
    win.grab_set()

def _crear_selector_entidad_reportes(win: tk.Toplevel, tipo: str, var_seleccion: dict, lista_datos: list):
    popup = ctk.CTkToplevel(win)
    preparar_ventana(popup)
    popup.title(f"Seleccionar {tipo}")
    popup.geometry("500x480")
    
    configurar_navegacion_ventana(popup)

    var_pat = tk.StringVar()
    ctk.CTkLabel(popup, text=f"Buscar {tipo} (ID/Nombre):", font=("Segoe UI", 12, "bold"), text_color=win.col_text).pack(pady=(15,5), padx=15, anchor="w")
    ent = ctk.CTkEntry(popup, textvariable=var_pat, font=("Segoe UI", 13), height=40, placeholder_text="Buscar por ID o Nombre...")
    ent.pack(fill="x", padx=15, pady=5)
    
    frame_list = ctk.CTkFrame(popup, fg_color=win.col_card, corner_radius=10, border_color=win.col_border, border_width=1)
    frame_list.pack(expand=True, fill="both", padx=15, pady=10)
    
    cols = ("ID", "Nombre")
    tree_sel = ttk.Treeview(frame_list, columns=cols, show="headings", style="Modern.Treeview", height=12)
    
    sc = ctk.CTkScrollbar(frame_list, command=tree_sel.yview)
    sc.pack(side="right", fill="y", padx=(0, 5), pady=5)
    tree_sel.configure(yscrollcommand=sc.set)
    tree_sel.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    
    tree_sel.column("ID", width=60, anchor="center")
    tree_sel.column("Nombre", width=350, anchor="w")
    tree_sel.heading("ID", text="ID")
    tree_sel.heading("Nombre", text="Nombre")
    
    tree_sel.insert("", "end", iid="opt_all", values=["-", "(Todos)"])

    def render(filas):
        for i in tree_sel.get_children(): 
            if i != "opt_all": tree_sel.delete(i)
        for c in filas:
            id_val = c.get('id_usuario')
            nombre_val = c.get('nombre')
            tree_sel.insert("", "end", values=[id_val, nombre_val])

    render(lista_datos)
    
    def filtrar(*_):
        q = var_pat.get().strip().lower()
        if not q:
            render(lista_datos)
            return
        filas_filtradas = [d for d in lista_datos 
                           if str(d.get('id_usuario', '')).startswith(q) or q in d.get('nombre', '').lower()]
        render(filas_filtradas)

    var_pat.trace_add("write", filtrar)

    def tomar(event=None): 
        sel_id = tree_sel.focus()
        if not sel_id: return 
        if sel_id == "opt_all":
            var_seleccion["id"] = None
            var_seleccion["nombre"] = "(Todos)"
        else:
            vals = tree_sel.item(sel_id, "values")
            if not vals: return
            try: id_val = int(vals[0])
            except: id_val = None
            var_seleccion["id"] = id_val
            var_seleccion["nombre"] = vals[1]
        popup.destroy()
        if hasattr(win, 'lbl_vend_sel'):
             win.lbl_vend_sel.configure(text=win.var_vendedor_sel['nombre'])

    tree_sel.bind("<Double-1>", tomar)
    tree_sel.bind("<Return>", tomar)

    btn_frm = ctk.CTkFrame(popup, fg_color="transparent")
    btn_frm.pack(fill="x", side="bottom", padx=15, pady=(5, 15))
    
    ctk.CTkButton(btn_frm, text="Cancelar", command=popup.destroy, fg_color="#ef4444", hover_color="#dc2626", font=("Segoe UI", 13, "bold"), width=150, height=45).pack(side="left", padx=10)
    ctk.CTkButton(btn_frm, text="✓ Seleccionar", command=tomar, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 14, "bold"), width=180, height=45).pack(side="right", padx=10)
    popup.after(100, lambda: ent.focus_set())
    centrar_y_mostrar_ventana(popup)
    popup.grab_set()
    popup.transient(win)
    win.wait_window(popup)

# --- PANEL DE CAJA ---
def _construir_panel_caja(win, backend, usuario):
    body = ctk.CTkFrame(win, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=20, pady=20)

    session_actual = None
    puede_gestionar = tiene_permiso(usuario, 'abrir_caja')
    ent_monto = None  # Se define en el bloque puede_gestionar
    
    pnl_cerrada = ctk.CTkFrame(body, fg_color="transparent")
    pnl_abierta = ctk.CTkFrame(body, fg_color="transparent")

    # 🔒 CIERRE CIEGO: Determinar si el usuario es vendedor
    es_vendedor = usuario.get('id_rol') == 2

    def actualizar_dashboard():
        if not session_actual: return
        data = backend.obtener_resumen_cierre(session_actual['id_session'])
        if not data: return
        
        if es_vendedor:
            # 🔒 CIERRE CIEGO: Vendedor no ve montos en el dashboard
            lbls_val['inicial'].configure(text="$ ***")
            lbls_val['ingresos'].configure(text="$ ***")
            lbls_val['egresos'].configure(text="$ ***")
            lbls_val['esperado'].configure(text="$ ***")
        else:
            lbls_val['inicial'].configure(text=_fmt(data['monto_inicial']))
            
            # 🔥 CORRECCIÓN: Los ingresos principales reflejan LIQUIDEZ (Efectivo + Tarjetas + Transf)
            # pero EXCLUYEN Cuenta Corriente por ser deuda no cobrada.
            medios = data.get('medios_pago', {})
            total_liquid = (data['total_ingresos'] 
                            + medios.get('tarjetas', 0.0) 
                            + medios.get('transferencias', 0.0))
            lbls_val['ingresos'].configure(text=_fmt(total_liquid))
            
            lbls_val['egresos'].configure(text=_fmt(data['total_egresos']))
            lbls_val['esperado'].configure(text=_fmt(data['efectivo_esperado']))
        
        # 🔥 Dinámico: usa el nombre que viene del backend
        fecha_ap_str = str(data.get('fecha_apertura', ''))
        try:
            from datetime import datetime
            fecha_ap_fmt = datetime.strptime(fecha_ap_str, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            fecha_ap_fmt = fecha_ap_str
            
        lbl_status.configure(text=f"✅ Caja Abierta | Apertura: {fecha_ap_fmt} por {data['usuario_apertura']}")

    def verificar_estado():
        nonlocal session_actual
        # Se obtiene solo la sesión del usuario actual
        session_actual = backend.obtener_session_abierta(usuario['id_usuario'])
        pnl_cerrada.pack_forget(); pnl_abierta.pack_forget()
        if session_actual:
            pnl_abierta.pack(fill="both", expand=True)
            actualizar_dashboard()
        else:
            pnl_cerrada.pack(fill="both", expand=True)
            if puede_gestionar and ent_monto:
                ent_monto.delete(0, tk.END)
                ent_monto.insert(0, PLACEHOLDER)
                ent_monto.configure(text_color=PLACEHOLDER_COLOR)

    if puede_gestionar:
        fr_ini = ctk.CTkFrame(pnl_cerrada, fg_color=win.col_card, corner_radius=15, border_color=win.col_border, border_width=1)
        fr_ini.pack(pady=40, padx=40)
        
        ctk.CTkLabel(fr_ini, text="Monto Inicial en Caja ($):", font=("Segoe UI", 16, "bold"), text_color=win.col_text).pack(pady=(30, 10), padx=40)
        
        def _val_apertura(t):
            if t == "" or t == PLACEHOLDER: return True
            import re
            if not re.match(r'^\d*\.?\d*$', t): return False
            partes = t.split('.')
            return len(partes[0]) <= 10
            
        vc_ap = (fr_ini.register(_val_apertura), '%P')
        
        ent_monto = ctk.CTkEntry(fr_ini, font=("Segoe UI", 20, "bold"), justify="center", height=50, width=250)
        ent_monto.configure(validate="key", validatecommand=vc_ap)
        ent_monto.pack(pady=10)

        PLACEHOLDER = "1000.00"
        PLACEHOLDER_COLOR = "#9ca3af"
        NORMAL_COLOR = win.col_input_fg

        def on_focus_in(e):
            if ent_monto.get() == PLACEHOLDER:
                ent_monto.delete(0, tk.END)
                ent_monto.configure(text_color=NORMAL_COLOR)

        def on_focus_out(e):
            if not ent_monto.get().strip():
                ent_monto.insert(0, PLACEHOLDER)
                ent_monto.configure(text_color=PLACEHOLDER_COLOR)

        ent_monto.insert(0, PLACEHOLDER)
        ent_monto.configure(text_color=PLACEHOLDER_COLOR)
        ent_monto.bind("<FocusIn>", on_focus_in)
        ent_monto.bind("<FocusOut>", on_focus_out)
        
        def abrir_caja():
            try:
                texto_monto = ent_monto.get().strip()
                if texto_monto == PLACEHOLDER or not texto_monto:
                    monto = 0.0
                else:
                    monto = float(texto_monto)
                if monto <= 0:
                    messagebox.showwarning("Atención", "El monto de apertura debe ser mayor a 0.\n(Si no tienes cambio, ingresa un monto mínimo como 0.01)", parent=win)
                    return
                backend.abrir_caja_session(usuario['id_usuario'], monto)
                mostrar_exito("✅ Caja Abierta", "Tu caja ha sido abierta correctamente.", parent=win)
                verificar_estado()
            except ValueError: messagebox.showwarning("Error", "Monto inválido.", parent=win)
            except Exception as e: messagebox.showerror("Error", f"Error al abrir caja:\n{e}", parent=win)

        ent_monto.bind("<Return>", lambda e: abrir_caja())
        ctk.CTkButton(fr_ini, text="✓ ABRIR MI TURNO", command=abrir_caja, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 16, "bold"), height=50, width=250).pack(pady=(10, 30))
    else:
        ctk.CTkLabel(pnl_cerrada, text="⚠️ No tienes permisos para abrir caja", font=("Segoe UI", 16, "bold"), text_color="#ef4444").pack(pady=40)

    # CABECERA DE CAJA ABIERTA
    fr_head = ctk.CTkFrame(pnl_abierta, fg_color="#e0f2fe" if ctk.get_appearance_mode()=="Light" else "#1e3a8a", corner_radius=10, border_color="#bae6fd" if ctk.get_appearance_mode()=="Light" else "#1d4ed8", border_width=1)
    fr_head.pack(fill="x", pady=(0, 20))
    
    lbl_status = ctk.CTkLabel(fr_head, text="...", font=("Segoe UI", 12, "bold"), text_color="#0369a1" if ctk.get_appearance_mode()=="Light" else "#bfdbfe")
    lbl_status.pack(pady=(15, 5))
    
    fr_totales = ctk.CTkFrame(fr_head, fg_color="transparent")
    fr_totales.pack(pady=(5, 15))
    
    lbls_val = {}
    def mk_ind(parent, txt, col=0, color="#1f2937", dark_color="#f9fafb"):
        f = ctk.CTkFrame(parent, fg_color="transparent"); f.grid(row=0, column=col, padx=20)
        ctk.CTkLabel(f, text=txt, text_color="#4b5563" if ctk.get_appearance_mode()=="Light" else "#9ca3af", font=("Segoe UI", 11, "bold")).pack()
        c = color if ctk.get_appearance_mode()=="Light" else dark_color
        l = ctk.CTkLabel(f, text="$ -", font=("Segoe UI", 18, "bold"), text_color=c)
        l.pack()
        return l

    lbls_val['inicial'] = mk_ind(fr_totales, "Inicial", 0)
    lbls_val['ingresos'] = mk_ind(fr_totales, "(+) Ingresos", 1, "#16a34a", "#34d399")
    lbls_val['egresos'] = mk_ind(fr_totales, "(-) Egresos", 2, "#dc2626", "#f87171")
    lbls_val['esperado'] = mk_ind(fr_totales, "= Efectivo Esperado", 3, "#2563eb", "#60a5fa")

    fr_ops = ctk.CTkFrame(pnl_abierta, fg_color="transparent")
    fr_ops.pack(fill="x", pady=10)

    def iniciar_cierre():
        if not puede_gestionar: return
        
        # Variables que se llenarán dinámicamente
        data = {}
        esperado = 0.0
        medios_pago = {}
        ingresos_efectivo = 0.0
        total_general = 0.0
        
        d = ctk.CTkToplevel(win)
        d.title("📋 Cierre de Caja Completo")
        d.geometry("580x600")
        d.resizable(True, True)
        d.configure(fg_color=win.col_bg)
        
        fr_header = ctk.CTkFrame(d, fg_color="#3b82f6", corner_radius=0)
        fr_header.pack(fill="x")
        # 🔒 CIERRE CIEGO: Título diferente para vendedor
        titulo_cierre = "CIERRE DE CAJA - CONTEO DE EFECTIVO" if es_vendedor else "RESUMEN DE CIERRE DE CAJA"
        ctk.CTkLabel(fr_header, text=titulo_cierre, font=("Segoe UI", 16, "bold"), text_color="white").pack(pady=8)
        
        # Botones y observaciones anclados al fondo de la ventana (fuera del scroll)
        fr_botones_bottom = ctk.CTkFrame(d, fg_color="transparent")
        fr_botones_bottom.pack(side="bottom", fill="x", pady=(5, 15), padx=15)
        
        fr_obs = ctk.CTkFrame(d, fg_color="transparent")
        fr_obs.pack(side="bottom", fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(fr_obs, text="Observaciones (opcional):", font=("Segoe UI", 11), text_color=win.col_text).pack(anchor="w", padx=5)
        txt_obs = ctk.CTkTextbox(fr_obs, height=60, font=("Segoe UI", 11))
        txt_obs.pack(fill="x", pady=(2, 5))
        
        # 🔥 Área scrolleable ahora solo contiene los números
        fr_main = ctk.CTkScrollableFrame(d, fg_color="transparent")
        fr_main.pack(fill="both", expand=True, padx=15, pady=5)
        
        fr_efectivo = ctk.CTkFrame(fr_main, fg_color=win.col_card, corner_radius=10, border_color=win.col_border, border_width=1)
        fr_efectivo.pack(fill="x", pady=(0, 5), ipadx=5, ipady=5)

        # Desglose de efectivo - COMPACTO
        lbls_arqueo = {}
        def crear_item_arqueo(key, txt, color=None):
            f = ctk.CTkFrame(fr_efectivo, fg_color="transparent")
            f.pack(fill="x", padx=15, pady=0) # Sin pady
            ctk.CTkLabel(f, text=txt, font=("Segoe UI", 10), text_color=win.col_text).pack(side="left")
            lbl = ctk.CTkLabel(f, text="$ 0.00", font=("Segoe UI", 10, "bold"), text_color=color or win.col_text)
            lbl.pack(side="right")
            lbls_arqueo[key] = lbl

        # 🔒 CIERRE CIEGO: Frames que se ocultan/muestran según rol
        # Contenedor para la info financiera sensible (desglose + medios + total)
        fr_info_sensible = ctk.CTkFrame(fr_main, fg_color="transparent")
        
        lbl_esperado = None
        if not es_vendedor:
            # Admin/Supervisor: Mostrar todo el desglose normalmente
            crear_item_arqueo("inicial", "Saldo Inicial:")
            crear_item_arqueo("ingresos", "(+) Ingresos (Efectivo):", "#10b981")
            crear_item_arqueo("egresos", "(-) Egresos (Efectivo):", "#ef4444")
            
            lbl_esperado = ctk.CTkLabel(fr_efectivo, text="Efectivo Esperado: $ 0.00", font=("Segoe UI", 12, "bold"), text_color="#3b82f6")
            lbl_esperado.pack(anchor="w", padx=10, pady=1)
        else:
            # 🔒 Vendedor: Solo mensaje de instrucción, sin desglose
            ctk.CTkLabel(fr_efectivo, text="🔒 Cierre Ciego", font=("Segoe UI", 14, "bold"), text_color="#f59e0b").pack(anchor="w", padx=15, pady=(5, 2))
            ctk.CTkLabel(fr_efectivo, text="Cuente el efectivo en caja e ingrese el total.", font=("Segoe UI", 11), text_color="#9ca3af").pack(anchor="w", padx=15, pady=(0, 5))
        
        ctk.CTkLabel(fr_efectivo, text="Ingrese Efectivo Contado (Real):", font=("Segoe UI", 11), text_color=win.col_text).pack(anchor="w", padx=10, pady=(2, 0))
        def _val_real(t):
            if t == "": return True
            import re
            if not re.match(r'^\d*\.?\d*$', t): return False
            partes = t.split('.')
            return len(partes[0]) <= 10
        vc_real = (d.register(_val_real), '%P')
        
        e_real = ctk.CTkEntry(fr_efectivo, font=("Segoe UI", 16, "bold"), justify="center", height=45, width=250)
        e_real.configure(validate="key", validatecommand=vc_real)
        e_real.pack(pady=10)
        e_real.focus_set()
        
        lbl_dif = ctk.CTkLabel(fr_efectivo, text="Diferencia: $ 0.00", font=("Segoe UI", 12, "bold"), text_color="#059669")
        # 🔒 CIERRE CIEGO: Vendedor no ve la diferencia en tiempo real
        if not es_vendedor:
            lbl_dif.pack(pady=(0, 5))
        
        # --- Sección de medios de pago y total (dentro de fr_info_sensible) ---
        fr_medios = ctk.CTkFrame(fr_info_sensible, fg_color=win.col_card, corner_radius=10, border_color=win.col_border, border_width=1)
        fr_medios.pack(fill="x", pady=(0, 2), ipadx=5, ipady=2)
        
        lbls_medios = {}
        def crear_linea_medio(key, parent, icono, texto, color="#10b981"):
            fr = ctk.CTkFrame(parent, fg_color="transparent")
            fr.pack(fill="x", pady=0, padx=10)
            ctk.CTkLabel(fr, text=f"{icono} {texto}:", font=("Segoe UI", 11), text_color=win.col_text, width=200, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(fr, text="$ 0.00", font=("Segoe UI", 12, "bold"), text_color=color)
            lbl.pack(side="right")
            lbls_medios[key] = lbl

        ctk.CTkLabel(fr_medios, text="📥 INGRESOS (No Efectivo)", font=("Segoe UI", 12, "bold"), text_color=win.col_text).pack(anchor="w", padx=10, pady=(2, 2))
        crear_linea_medio("tar_ing", fr_medios, "💳", "Tarjetas")
        crear_linea_medio("tra_ing", fr_medios, "🏦", "Transferencias")
        crear_linea_medio("cc_ing", fr_medios, "📋", "Crédito (A Cobrar C.C.)", "#f59e0b")

        ctk.CTkLabel(fr_medios, text="----------------------------------------------------------------", text_color=win.col_border).pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(fr_medios, text="📤 EGRESOS (No Efectivo)", font=("Segoe UI", 12, "bold"), text_color=win.col_text).pack(anchor="w", padx=10, pady=2)
        crear_linea_medio("tar_egr", fr_medios, "💳", "Tarjetas (pagos)", "#ef4444")
        crear_linea_medio("tra_egr", fr_medios, "🏦", "Transferencias (pagos)", "#ef4444")
        
        fr_total = ctk.CTkFrame(fr_info_sensible, fg_color="#e0f2fe" if ctk.get_appearance_mode()=="Light" else "#1e3a8a", corner_radius=10, border_color="#bae6fd" if ctk.get_appearance_mode()=="Light" else "#1d4ed8", border_width=1)
        fr_total.pack(fill="x", pady=(0, 5), ipadx=5, ipady=5)
        ctk.CTkLabel(fr_total, text="📈 TOTAL RECAUDADO", font=("Segoe UI", 11, "bold"), text_color="#0369a1" if ctk.get_appearance_mode()=="Light" else "#bfdbfe").pack(pady=(2, 0))
        lbl_total_general = ctk.CTkLabel(fr_total, text="$ 0.00", font=("Segoe UI", 18, "bold"), text_color="#0284c7" if ctk.get_appearance_mode()=="Light" else "#e0f2fe")
        lbl_total_general.pack(pady=(0, 2))
        
        # 🔒 CIERRE CIEGO: Controlar visibilidad de la info sensible
        if not es_vendedor:
            # Admin/Supervisor: mostrar todo
            fr_info_sensible.pack(fill="x", pady=0)
        else:
            # Vendedor: Ocultar info sensible, mostrar botón para revelar con autorización
            fr_btn_revelar = ctk.CTkFrame(fr_main, fg_color="transparent")
            fr_btn_revelar.pack(fill="x", pady=10)
            
            def revelar_info(usr_autorizado):
                """Callback cuando el admin autoriza ver los totales."""
                fr_btn_revelar.pack_forget()
                fr_info_sensible.pack(fill="x", pady=0)
                # También revelar el desglose de efectivo y diferencia
                lbl_dif.pack(pady=(0, 5))
            
            ctk.CTkButton(
                fr_btn_revelar, text="👁️ Ver Totales (Requiere Autorización)", 
                fg_color="#6b7280", hover_color="#4b5563",
                font=("Segoe UI", 12, "bold"), height=40, width=320,
                command=lambda: solicitar_autorizacion_supervisor(d, backend, usuario, revelar_info)
            ).pack(pady=5)
        
        def calc_diff(e=None):
            try:
                real = float(e_real.get() or 0)
                dif = real - esperado
                col = "#10b981" if abs(dif) < 0.01 else "#ef4444"
                lbl_dif.configure(text=f"Diferencia: {'' if dif < 0 else '+'}{_fmt(dif)}", text_color=col)
            except: pass
        
        def forzar_calculo_totales():
            nonlocal data, esperado, medios_pago, ingresos_efectivo, total_general
            data = backend.obtener_resumen_cierre(session_actual['id_session'])
            esperado = data.get('efectivo_esperado', 0.0)
            medios_pago = data.get('medios_pago', {'tarjetas': 0.0, 'transferencias': 0.0, 'cuenta_corriente': 0.0})
            ingresos_efectivo = data.get('total_ingresos', 0.0)
            total_general = ingresos_efectivo + medios_pago.get('tarjetas', 0.0) + medios_pago.get('transferencias', 0.0)
            
            if not es_vendedor:
                lbls_arqueo["inicial"].configure(text=_fmt(data.get('monto_inicial', 0.0)))
                lbls_arqueo["ingresos"].configure(text=_fmt(ingresos_efectivo))
                lbls_arqueo["egresos"].configure(text=_fmt(data.get('total_egresos', 0.0)))
                if lbl_esperado:
                    lbl_esperado.configure(text=f"Efectivo Esperado: {_fmt(esperado)}")
            
            lbls_medios["tar_ing"].configure(text=_fmt(medios_pago.get('tarjetas', 0.0)))
            lbls_medios["tra_ing"].configure(text=_fmt(medios_pago.get('transferencias', 0.0)))
            lbls_medios["cc_ing"].configure(text=_fmt(medios_pago.get('cuenta_corriente', 0.0)))
            lbls_medios["tar_egr"].configure(text=_fmt(data.get('total_egresos_tarjeta', 0.0)))
            lbls_medios["tra_egr"].configure(text=_fmt(data.get('total_egresos_transferencia', 0.0)))
            
            lbl_total_general.configure(text=_fmt(total_general))
            calc_diff()

        e_real.bind("<KeyRelease>", calc_diff)
        d.after(100, forzar_calculo_totales)
        
        def confirmar():
            try:
                real = float(e_real.get())
                dif = real - esperado
                obs = txt_obs.get("1.0", tk.END).strip()
                # 🔒 CIERRE CIEGO: Solo exigimos justificar diferencia si NO es vendedor.
                # Si es vendedor, aceptamos el número en silencio para no darle pistas.
                if not es_vendedor and abs(dif) > 0.01 and len(obs) < 5:
                    messagebox.showwarning("Atención", "Por favor justifique la diferencia de caja en 'Observaciones'.", parent=d)
                    return
                if mostrar_confirmacion("Confirmar Cierre", "¿Cerrar caja definitivamente?", parent=d):
                    backend.cerrar_caja_session(session_actual['id_session'], usuario['id_usuario'], esperado, real, dif, obs)
                    if impresora:
                        dt = data.copy(); dt.update({'efectivo_contado': real, 'diferencia': dif, 'observaciones': obs, 'medios_pago': medios_pago, 'total_general': total_general})
                        impresora.imprimir_cierre_caja(dt, [], usuario['nombre'])
                    mostrar_exito("✅ Caja Cerrada", "Caja cerrada correctamente.", parent=d)
                    try:
                        d.destroy()
                        # Solo destruir ventana actual de reportes, evitar quit() que cuelga la app
                        win.destroy()
                    except: pass
            except ValueError: messagebox.showerror("Error", "Monto real inválido", parent=d)
        
        ctk.CTkButton(fr_botones_bottom, text="Cancelar", command=d.destroy, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 13, "bold"), width=120, height=40).pack(side="left", padx=10)
        ctk.CTkButton(fr_botones_bottom, text="✓ CONFIRMAR CIERRE", command=confirmar, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 13, "bold"), width=180, height=40).pack(side="right", padx=10)

        configurar_navegacion_ventana(d); d.grab_set()

    def iniciar_transferencia_tesoreria():
        def on_autorizado(admin_dict):
            top = ctk.CTkToplevel(win)
            top.title("Transferir a Tesorería")
            top.geometry("450x420")
            top.configure(fg_color=win.col_bg)
            
            ctk.CTkLabel(top, text="Monto a transferir ($):", font=("Segoe UI", 13, "bold"), text_color=win.col_text).pack(pady=(20,5))
            e_m = ctk.CTkEntry(top, font=("Segoe UI", 16, "bold"), justify="center", width=200, height=45, fg_color=win.col_input_bg, text_color=win.col_input_fg)
            e_m.pack(pady=5)
            e_m.focus_set()
            
            ctk.CTkLabel(top, text="Observaciones (Obligatorio):", font=("Segoe UI", 13, "bold"), text_color=win.col_text).pack(pady=(15,5))
            txt_obs = ctk.CTkTextbox(top, height=80, font=("Segoe UI", 12))
            txt_obs.pack(fill="x", padx=40, pady=5)
            
            def save():
                try:
                    m = float(e_m.get())
                    if m <= 0: raise ValueError
                    data_c = backend.obtener_resumen_cierre(session_actual['id_session'])
                    if m > data_c.get('efectivo_esperado', 0.0):
                        messagebox.showerror("Saldo Insuficiente", "No hay suficiente efectivo en la caja para realizar esta transferencia.", parent=top)
                        return
                    
                    obs_usuario = txt_obs.get("1.0", tk.END).strip()
                    if not obs_usuario:
                        messagebox.showerror("Campo Obligatorio", "La observación es obligatoria para registrar la transferencia.", parent=top)
                        return
                        
                    # Obtener o crear tesorería automáticamente
                    if hasattr(backend, "obtener_o_crear_tesoreria_hoy"):
                        tesoreria = backend.obtener_o_crear_tesoreria_hoy(admin_dict['id_usuario'])
                    else:
                        tesoreria = getattr(backend, "obtener_tesoreria_activa", lambda: None)()
                        
                    if not tesoreria:
                        messagebox.showerror("Error", "No se pudo obtener ni crear la sesión de Tesorería.", parent=top)
                        return
                        
                    desc_final = f"[Autorizado por: {admin_dict['nombre']}] - {obs_usuario}"
                        
                    # Transferir de Caja a Tesorería
                    if getattr(backend, "transferir_entre_cajas", None):
                        exito = backend.transferir_entre_cajas(
                            origen=session_actual['id_session'],
                            destino=tesoreria['id_session'],
                            monto=m,
                            id_usuario=usuario['id_usuario'],
                            motivo_salida='transferencia_tesoreria_salida',
                            motivo_entrada='transferencia_tesoreria_entrada',
                            obs=desc_final,
                            id_autorizador=admin_dict['id_usuario']
                        )
                        if exito:
                            top.destroy()
                            actualizar_dashboard()
                            messagebox.showinfo("Éxito", "Efectivo transferido a Tesorería exitosamente.", parent=win)
                        else:
                            messagebox.showerror("Error", "Ocurrió un error en la transferencia.", parent=top)
                    else:
                        messagebox.showerror("Error", "La función de transferencia no está implementada.", parent=top)
                except ValueError: 
                    messagebox.showerror("Error", "Monto inválido", parent=top)
            
            btn_frm = ctk.CTkFrame(top, fg_color="transparent")
            btn_frm.pack(fill="x", side="bottom", padx=20, pady=(0, 20))
            ctk.CTkButton(btn_frm, text="Cancelar", command=top.destroy, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 14, "bold"), width=120, height=45).pack(side="left", padx=10)
            ctk.CTkButton(btn_frm, text="🏦 TRANSFERIR", command=save, fg_color="#059669", hover_color="#047857", font=("Segoe UI", 15, "bold"), width=160, height=45).pack(side="right", padx=10)

            configurar_navegacion_ventana(top)
            top.grab_set()

        solicitar_autorizacion_supervisor(win, backend, usuario, on_autorizado, roles_permitidos=(1, 3), motivo="Autorización para Transferir a Tesorería")

    ctk.CTkButton(fr_ops, text="🏦 TRANSFERIR A TESORERÍA", command=iniciar_transferencia_tesoreria, fg_color="#059669", hover_color="#047857", font=("Segoe UI", 13, "bold"), height=40).pack(side="left", padx=10)

    if tiene_permiso(usuario, 'movimientos_caja_manuales'):
        def modal_movimiento(tipo):
            top = ctk.CTkToplevel(win)
            top.title(f"Registrar {tipo.upper()}")
            top.geometry("450x450")
            top.configure(fg_color=win.col_bg)
            
            ctk.CTkLabel(top, text="Monto a registrar ($):", font=("Segoe UI", 13, "bold"), text_color=win.col_text).pack(pady=(20,5))
            
            e_m = ctk.CTkEntry(top, font=("Segoe UI", 16, "bold"), justify="center", width=200, height=45, fg_color=win.col_input_bg, text_color=win.col_input_fg)
            e_m.pack(pady=5)
            e_m.focus_set()
            
            ctk.CTkLabel(top, text="Motivo:", font=("Segoe UI", 13, "bold"), text_color=win.col_text).pack(pady=(15,5))
            motivos_dict = {"Gasto Vario": "gasto_vario", "Retiro/Ajuste": "retiro_caja", "Pago a Proveedor": "pago_proveedor", "Reembolso a Cliente": "devolucion_efectivo"} if tipo == 'egreso' else {"Ajuste Positivo": "ajuste_positivo"}
            
            cb_mot = ctk.CTkOptionMenu(top, values=list(motivos_dict.keys()), font=("Segoe UI", 14), width=250, height=40, fg_color=win.col_input_bg, text_color=win.col_input_fg, button_color="#4b5563")
            cb_mot.pack(pady=5)
            cb_mot.set(list(motivos_dict.keys())[0])
            
            ctk.CTkLabel(top, text="Observaciones (Obligatorio para retiros):", font=("Segoe UI", 13, "bold"), text_color=win.col_text).pack(pady=(15,5))
            
            txt_obs_mov = ctk.CTkTextbox(top, height=80, font=("Segoe UI", 12))
            txt_obs_mov.pack(fill="x", padx=40, pady=5)
            
            def save():
                try:
                    m = float(e_m.get())
                    if m <= 0: raise ValueError
                    motivo_seleccionado = cb_mot.get()
                    motivo_key = motivos_dict[motivo_seleccionado]
                    
                    if tipo == 'egreso':
                        data_c = backend.obtener_resumen_cierre(session_actual['id_session'])
                        if m > data_c.get('efectivo_esperado', 0.0):
                            messagebox.showerror("Saldo Insuficiente", "No hay suficiente efectivo en la caja para realizar este egreso.", parent=top)
                            return
                        
                        if motivo_key == 'retiro_caja' and not txt_obs_mov.get("1.0", tk.END).strip():
                            messagebox.showerror("Campo Obligatorio", "La observación es obligatoria para registrar un retiro de dinero.", parent=top)
                            return

                    backend.registrar_movimiento_manual(session_actual['id_session'], tipo, m, motivo_key, txt_obs_mov.get("1.0", tk.END).strip(), usuario['id_usuario'])
                    top.destroy(); actualizar_dashboard(); messagebox.showinfo("Éxito", "Movimiento registrado exitosamente.", parent=win)
                except ValueError: messagebox.showerror("Error", "Monto inválido", parent=top)
            
            btn_frm = ctk.CTkFrame(top, fg_color="transparent")
            btn_frm.pack(fill="x", side="bottom", padx=20, pady=(0, 20))
            ctk.CTkButton(btn_frm, text="Cancelar", command=top.destroy, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 14, "bold"), width=120, height=45).pack(side="left", padx=10)
            ctk.CTkButton(btn_frm, text="💾 GUARDAR", command=save, fg_color="#10b981" if tipo == 'ingreso' else "#ef4444", hover_color="#059669" if tipo == 'ingreso' else "#dc2626", font=("Segoe UI", 15, "bold"), width=160, height=45).pack(side="right", padx=10)

            configurar_navegacion_ventana(top); top.grab_set()

        ctk.CTkButton(fr_ops, text="➖ GASTO/RETIRO", command=lambda: modal_movimiento('egreso'), fg_color="#f59e0b", hover_color="#d97706", font=("Segoe UI", 13, "bold"), height=40).pack(side="left", padx=10)
        ctk.CTkButton(fr_ops, text="➕ AJUSTE (+)", command=lambda: modal_movimiento('ingreso'), fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 13, "bold"), height=40).pack(side="left")
    
    if puede_gestionar:
        ctk.CTkButton(fr_ops, text="🔒 CERRAR CAJA", command=iniciar_cierre, fg_color="#dc2626", hover_color="#b91c1c", font=("Segoe UI", 15, "bold"), height=48, width=200).pack(side="right", padx=10)
    
    # --- TREEVIEW DE MOVIMIENTOS DEL TURNO ---
    fr_mov_header = ctk.CTkFrame(pnl_abierta, fg_color="transparent")
    fr_mov_header.pack(fill="x", pady=(10, 5))
    ctk.CTkLabel(fr_mov_header, text="📋 Movimientos del turno:", font=("Segoe UI", 14, "bold"), text_color=win.col_text).pack(side="left")
    
    btn_refrescar = ctk.CTkButton(fr_mov_header, text="🔄 Actualizar", fg_color="#3b82f6", hover_color="#2563eb", font=("Segoe UI", 12, "bold"), width=120, height=35)
    btn_refrescar.pack(side="right")

    frm_tree = ctk.CTkFrame(pnl_abierta, fg_color=win.col_card, corner_radius=10, border_color=win.col_border, border_width=1)
    frm_tree.pack(fill="both", expand=True)

    from app.frontend.theme_config import configurar_estilo_treeview
    configurar_estilo_treeview()
    cols_mov = ("Fecha/Hora", "Tipo", "Motivo", "Monto", "Descripción")
    tree_mov = ttk.Treeview(frm_tree, columns=cols_mov, show="headings", height=8, style="Modern.Treeview")
    
    sc_mov = ctk.CTkScrollbar(frm_tree, command=tree_mov.yview)
    sc_mov.pack(side="right", fill="y", padx=(0, 5), pady=5)
    tree_mov.configure(yscrollcommand=sc_mov.set)
    tree_mov.pack(side="left", fill="both", expand=True, padx=5, pady=5)

    for col in cols_mov: tree_mov.heading(col, text=col)
    tree_mov.column("Fecha/Hora", width=130, anchor="center")
    tree_mov.column("Tipo", width=120, anchor="center")
    tree_mov.column("Motivo", width=220, anchor="center")
    tree_mov.column("Monto", width=130, anchor="e")
    tree_mov.column("Descripción", width=350)

    # Note: the colors might look weird on dark mode if we keep bg light, let's adapt them.
    tree_mov.tag_configure("ingreso", foreground="#16a34a" if ctk.get_appearance_mode()=="Light" else "#34d399")
    tree_mov.tag_configure("egreso", foreground="#dc2626" if ctk.get_appearance_mode()=="Light" else "#f87171")

    MAPEO_MOTIVOS = {
        'venta_efectivo': 'Venta efectivo', 'venta_tarjeta': 'Venta tarjeta',
        'venta_transferencia': 'Venta transf.', 'venta_cuenta_corriente': 'Venta cta. cte.',
        'cobro_cuenta_corriente': 'Cobro cta. cte.', 'pago_proveedor': 'Pago proveedor',
        'gasto_vario': 'Gasto varios', 'retiro_caja': 'Retiro', 'ajuste_positivo': 'Ajuste (+)',
        'devolucion_efectivo': 'Devolución', 'apertura_caja': 'Apertura',
    }

    def cargar_movimientos():
        for i in tree_mov.get_children(): tree_mov.delete(i)
        if not session_actual: return
        movs = backend.obtener_historial_movimientos_caja(
            fecha_desde=None, fecha_hasta=None, tipo=None, motivo=None, 
            id_usuario=usuario['id_usuario'], id_session=session_actual['id_session']
        )
        for m in movs:
            motivo_raw = m.get("motivo", "")
            if motivo_raw == "apertura_caja": continue
            try:
                if hasattr(m["fecha_hora"], "strftime"):
                    hora = m["fecha_hora"].strftime("%d/%m %H:%M")
                else:
                    hora_str = str(m["fecha_hora"])
                    if len(hora_str) >= 16:
                        hora = hora_str[8:10] + "/" + hora_str[5:7] + " " + hora_str[11:16]
                    else:
                        hora = hora_str
            except: hora = ""
            tipo = "➕ Ingreso" if m.get("tipo") == "ingreso" else "➖ Egreso"
            motivo_lbl = MAPEO_MOTIVOS.get(motivo_raw, motivo_raw)
            # 🔒 CIERRE CIEGO: Vendedor no ve montos en movimientos
            monto = "$ ***" if es_vendedor else _fmt(m.get('monto'))
            desc = m.get("descripcion") or ""
            tag = "ingreso" if m.get("tipo") == "ingreso" else "egreso"
            tree_mov.insert("", "end", values=(hora, tipo, motivo_lbl, monto, desc), tags=(tag,))

    btn_refrescar.configure(command=cargar_movimientos)

    _orig_actualizar = actualizar_dashboard
    def actualizar_dashboard():
        _orig_actualizar()
        cargar_movimientos()

    verificar_estado()

# --- PANEL DE REPORTES ---
def _construir_panel_reportes(win, backend, usuario):
    body = ctk.CTkFrame(win, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=20, pady=(10, 5))

    # Configurar grid layout en body para garantizar un reparto 50/50 exacto de altura
    body.grid_rowconfigure(0, weight=1)
    body.grid_rowconfigure(1, weight=1)
    body.grid_rowconfigure(2, weight=0)
    body.grid_columnconfigure(0, weight=1)

    def aplicar_filtro_rapido(nuevo_val, cb_obj, entry_desde, entry_hasta):
        seleccion = nuevo_val
        hoy = date.today()
        f_ini, f_fin = None, None
        if seleccion == "Hoy": f_ini, f_fin = hoy, hoy
        elif seleccion == "Ayer": f_ini = f_fin = hoy - timedelta(days=1)
        elif seleccion == "Esta Semana": f_ini = hoy - timedelta(days=hoy.weekday()); f_fin = hoy
        elif seleccion == "Mes Pasado":
            primero = hoy.replace(day=1); ultimo_mes = primero - timedelta(days=1)
            f_ini = ultimo_mes.replace(day=1); f_fin = ultimo_mes
        if f_ini:
            entry_desde.delete(0, tk.END); entry_desde.insert(0, f_ini.strftime("%d/%m/%Y"))
            entry_hasta.delete(0, tk.END); entry_hasta.insert(0, f_fin.strftime("%d/%m/%Y"))

    # ====== VENTAS POR VENDEDOR ======
    frm_vend = ctk.CTkFrame(body, fg_color=win.col_card, corner_radius=10, border_color=win.col_border, border_width=1)
    frm_vend.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
    
    frm_vend_header = ctk.CTkFrame(frm_vend, fg_color="transparent")
    frm_vend_header.pack(fill="x", padx=15, pady=(8, 2))
    ctk.CTkLabel(frm_vend_header, text="📈 Ventas por Vendedor", font=("Segoe UI", 15, "bold"), text_color=win.col_text).pack(side="left")

    frm_f1 = ctk.CTkFrame(frm_vend, fg_color="transparent")
    frm_f1.pack(fill="x", padx=15, pady=2)
    
    ctk.CTkLabel(frm_f1, text="Rango:", font=("Segoe UI", 12), text_color=win.col_text).pack(side="left", padx=(0,5))
    
    cb_rango_v = ctk.CTkOptionMenu(frm_f1, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Mes Pasado"], font=("Segoe UI", 12), width=130, fg_color=win.col_input_bg, text_color=win.col_input_fg, button_color="#4b5563")
    cb_rango_v.set("Personalizado")
    cb_rango_v.pack(side="left", padx=(0,15))
    
    ctk.CTkLabel(frm_f1, text="Desde:", font=("Segoe UI", 12), text_color=win.col_text).pack(side="left", padx=(0,5))
    fd_v = SelectorFecha(frm_f1)
    fd_v.pack(side="left", padx=(0,15))
    fd_v.widget_entrada.delete(0, tk.END)
    fd_v.widget_entrada.insert(0, date.today().replace(day=1).strftime("%d/%m/%Y"))
    
    ctk.CTkLabel(frm_f1, text="Hasta:", font=("Segoe UI", 12), text_color=win.col_text).pack(side="left", padx=(0,5))
    fh_v = SelectorFecha(frm_f1)
    fh_v.pack(side="left", padx=(0,15))
    fh_v.widget_entrada.delete(0, tk.END)
    fh_v.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))

    cb_rango_v.configure(command=lambda val: aplicar_filtro_rapido(val, cb_rango_v, fd_v.widget_entrada, fh_v.widget_entrada))
    
    ctk.CTkLabel(frm_f1, text="Vendedor:", font=("Segoe UI", 12, "bold"), text_color=win.col_text).pack(side="left", padx=(10, 5))
    
    frm_vend_sel_cont = ctk.CTkFrame(frm_f1, fg_color="transparent")
    frm_vend_sel_cont.pack(side="left", padx=(0, 15))
    
    win.lbl_vend_sel = ctk.CTkLabel(frm_vend_sel_cont, text=win.var_vendedor_sel['nombre'], font=("Segoe UI", 12), text_color="#6b7280" if ctk.get_appearance_mode()=="Light" else "#9ca3af")
    win.lbl_vend_sel.pack(side="left", padx=(0, 5))
    
    btn_vend = ctk.CTkButton(frm_vend_sel_cont, text="🔍", width=30, height=28, fg_color="#3b82f6", 
                            command=lambda: _crear_selector_entidad_reportes(win, "Vendedor", win.var_vendedor_sel, win.vendedores_full_list))
    btn_vend.pack(side="left")
    
    def limpiar_filtros_vend():
        from datetime import date
        cb_rango_v.set("Personalizado")
        fd_v.widget_entrada.delete(0, tk.END)
        fd_v.widget_entrada.insert(0, date.today().replace(day=1).strftime("%d/%m/%Y"))
        fh_v.widget_entrada.delete(0, tk.END)
        fh_v.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        win.var_vendedor_sel.update({"id": None, "nombre": "(Todos)"})
        if hasattr(win, 'lbl_vend_sel'):
            win.lbl_vend_sel.configure(text="(Todos)")
        for i in tree_v.get_children(): tree_v.delete(i)

    ctk.CTkButton(frm_f1, text="Generar Reporte", command=lambda: buscar_vend(), fg_color="#3b82f6", hover_color="#2563eb", font=("Segoe UI", 12, "bold"), width=120, height=35).pack(side="right")
    ctk.CTkButton(frm_f1, text="🧹 Limpiar", command=limpiar_filtros_vend, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 12, "bold"), width=100, height=35).pack(side="right", padx=(0, 5))
    
    frm_tree_1 = ctk.CTkFrame(frm_vend, fg_color="transparent")
    frm_tree_1.pack(fill="both", expand=True, padx=15, pady=(2, 8))

    tree_v = ttk.Treeview(frm_tree_1, columns=("Vend", "Ventas", "Monto"), show="headings", height=6, style="Modern.Treeview")
    
    sc_v = ctk.CTkScrollbar(frm_tree_1, command=tree_v.yview)
    sc_v.pack(side="right", fill="y", padx=(0, 5), pady=5)
    tree_v.configure(yscrollcommand=sc_v.set)
    tree_v.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    
    tree_v.column("Vend", width=400)
    tree_v.column("Ventas", width=150, anchor="center")
    tree_v.column("Monto", width=250, anchor="e")
    tree_v.heading("Vend", text="Vendedor"); tree_v.heading("Ventas", text="Cant."); tree_v.heading("Monto", text="Total Facturado")
    
    def buscar_vend():
        for i in tree_v.get_children(): tree_v.delete(i)
        try:
            d_sql = datetime.strptime(fd_v.get_date_str() or fd_v.widget_entrada.get(), "%d/%m/%Y").strftime("%Y-%m-%d") if fd_v.get_date_str() else datetime.strptime(fd_v.widget_entrada.get(), "%d/%m/%Y").strftime("%Y-%m-%d")
            h_sql = datetime.strptime(fh_v.get_date_str() or fh_v.widget_entrada.get(), "%d/%m/%Y").strftime("%Y-%m-%d") if fh_v.get_date_str() else datetime.strptime(fh_v.widget_entrada.get(), "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            d_sql = fd_v.get_date_sql() or datetime.today().strftime("%Y-%m-%d")
            h_sql = fh_v.get_date_sql() or datetime.today().strftime("%Y-%m-%d")
            
        try:
            data = backend.reporte_ventas_por_vendedor(d_sql, h_sql, win.var_vendedor_sel['id'])
            for r in data: tree_v.insert("", "end", values=(r['vendedor'], r['total_ventas'], _fmt(r['monto_total'])))
        except Exception as e:
            pass

    def on_doble_click_vend(event):
        sel = tree_v.selection()
        if not sel: return
        vals = tree_v.item(sel[0], "values")
        if not vals: return
        vendedor_nombre = vals[0]
        id_vend = None
        for v in win.vendedores_full_list:
            if v.get('nombre') == vendedor_nombre:
                id_vend = v.get('id_usuario')
                break
        desde_ui = fd_v.widget_entrada.get()
        hasta_ui = fh_v.widget_entrada.get()
        if Historiales:
            Historiales(
                win, backend, usuario,
                tab_inicial=0,
                filtro_fecha_desde_default=desde_ui,
                filtro_fecha_hasta_default=hasta_ui,
                filtro_vendedor_id=id_vend
            )
    tree_v.bind("<Double-1>", on_doble_click_vend)


    # ====== VENTAS DIARIAS ======
    frm_dia = ctk.CTkFrame(body, fg_color=win.col_card, corner_radius=10, border_color=win.col_border, border_width=1)
    frm_dia.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
    
    frm_dia_header = ctk.CTkFrame(frm_dia, fg_color="transparent")
    frm_dia_header.pack(fill="x", padx=15, pady=(8, 2))
    ctk.CTkLabel(frm_dia_header, text="📅 Ventas Diarias", font=("Segoe UI", 15, "bold"), text_color=win.col_text).pack(side="left")

    frm_f2 = ctk.CTkFrame(frm_dia, fg_color="transparent")
    frm_f2.pack(fill="x", padx=15, pady=2)
    
    ctk.CTkLabel(frm_f2, text="Rango:", font=("Segoe UI", 12), text_color=win.col_text).pack(side="left", padx=(0,5))
    
    cb_rango_d = ctk.CTkOptionMenu(frm_f2, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Mes Pasado"], font=("Segoe UI", 12), width=130, fg_color=win.col_input_bg, text_color=win.col_input_fg, button_color="#4b5563")
    cb_rango_d.set("Mes Pasado")
    cb_rango_d.pack(side="left", padx=(0,15))

    ctk.CTkLabel(frm_f2, text="Desde:", font=("Segoe UI", 12), text_color=win.col_text).pack(side="left", padx=(0,5))
    fd_d = SelectorFecha(frm_f2)
    fd_d.pack(side="left", padx=(0,15))
    fd_d.widget_entrada.delete(0, tk.END)
    fd_d.widget_entrada.insert(0, date.today().replace(day=1).strftime("%d/%m/%Y"))
    
    ctk.CTkLabel(frm_f2, text="Hasta:", font=("Segoe UI", 12), text_color=win.col_text).pack(side="left", padx=(0,5))
    fh_d = SelectorFecha(frm_f2)
    fh_d.pack(side="left", padx=(0,15))
    fh_d.widget_entrada.delete(0, tk.END)
    fh_d.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))

    cb_rango_d.configure(command=lambda val: aplicar_filtro_rapido(val, cb_rango_d, fd_d.widget_entrada, fh_d.widget_entrada))
    
    def limpiar_filtros_dia():
        from datetime import date
        cb_rango_d.set("Mes Pasado")
        fd_d.widget_entrada.delete(0, tk.END)
        fd_d.widget_entrada.insert(0, date.today().replace(day=1).strftime("%d/%m/%Y"))
        fh_d.widget_entrada.delete(0, tk.END)
        fh_d.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        for i in tree_d.get_children(): tree_d.delete(i)

    ctk.CTkButton(frm_f2, text="Generar Reporte", command=lambda: buscar_dia(), fg_color="#3b82f6", hover_color="#2563eb", font=("Segoe UI", 12, "bold"), width=120, height=35).pack(side="right")
    ctk.CTkButton(frm_f2, text="🧹 Limpiar", command=limpiar_filtros_dia, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 12, "bold"), width=100, height=35).pack(side="right", padx=(0, 5))
    
    frm_tree_2 = ctk.CTkFrame(frm_dia, fg_color="transparent")
    frm_tree_2.pack(fill="both", expand=True, padx=15, pady=(2, 8))

    tree_d = ttk.Treeview(frm_tree_2, columns=("Fecha", "Ventas", "Monto"), show="headings", height=6, style="Modern.Treeview")
    
    sc_d = ctk.CTkScrollbar(frm_tree_2, command=tree_d.yview)
    sc_d.pack(side="right", fill="y", padx=(0, 5), pady=5)
    tree_d.configure(yscrollcommand=sc_d.set)
    tree_d.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    tree_d.heading("Fecha", text="Fecha"); tree_d.heading("Ventas", text="Cant."); tree_d.heading("Monto", text="Total Diario")
    tree_d.column("Fecha", width=150, anchor="center")
    tree_d.column("Ventas", width=150, anchor="center")
    tree_d.column("Monto", width=250, anchor="e")
    
    def buscar_dia():
        for i in tree_d.get_children(): tree_d.delete(i)
        try:
            d_sql = datetime.strptime(fd_d.get_date_str() or fd_d.widget_entrada.get(), "%d/%m/%Y").strftime("%Y-%m-%d") if fd_d.get_date_str() else datetime.strptime(fd_d.widget_entrada.get(), "%d/%m/%Y").strftime("%Y-%m-%d")
            h_sql = datetime.strptime(fh_d.get_date_str() or fh_d.widget_entrada.get(), "%d/%m/%Y").strftime("%Y-%m-%d") if fh_d.get_date_str() else datetime.strptime(fh_d.widget_entrada.get(), "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            d_sql = fd_d.get_date_sql() or datetime.today().strftime("%Y-%m-%d")
            h_sql = fh_d.get_date_sql() or datetime.today().strftime("%Y-%m-%d")
            
        try:
            data = backend.obtener_ventas_diarias(d_sql, h_sql)
            for r in data: 
                f_str = datetime.strptime(str(r['fecha']), "%Y-%m-%d").strftime("%d/%m/%Y")
                tree_d.insert("", "end", values=(f_str, r['total_ventas'], _fmt(r['monto_total'])))
        except Exception as e: pass
    
    def on_doble_click_dia(event):
        sel = tree_d.selection()
        if not sel: return
        vals = tree_d.item(sel[0], "values")
        if not vals: return
        fecha_ui = vals[0]
        if Historiales:
            Historiales(
                win, backend, usuario,
                tab_inicial=0,
                filtro_fecha=fecha_ui,
                filtro_fecha_desde_default=fecha_ui,
                filtro_fecha_hasta_default=fecha_ui
            )
    tree_d.bind("<Double-1>", on_doble_click_dia)

    frm_footer = ctk.CTkFrame(body, fg_color="transparent")
    frm_footer.grid(row=2, column=0, sticky="ew", pady=(5, 0))
    ctk.CTkButton(frm_footer, text="Cerrar", command=win.destroy, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 14, "bold"), width=150, height=45).pack(side="right")

def _construir_panel_admin_caja(win, backend, usuario):
    body = ctk.CTkFrame(win, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=20, pady=20)
    
    # --- HEADER ---
    fr_head = ctk.CTkFrame(body, fg_color="transparent")
    fr_head.pack(fill="x", pady=(0, 15))
    ctk.CTkLabel(fr_head, text="📈 Dashboard del Día", font=("Segoe UI", 24, "bold"), text_color=win.col_text).pack(side="left")
    
    lbl_last_update = ctk.CTkLabel(fr_head, text="Actualizando...", font=("Segoe UI", 12), text_color="#6b7280")
    lbl_last_update.pack(side="right")
    
    # --- TOP ROW (Métricas y Top Productos) ---
    fr_top = ctk.CTkFrame(body, fg_color="transparent")
    fr_top.pack(fill="x", pady=10)
    
    fr_metricas = ctk.CTkFrame(fr_top, fg_color="transparent")
    fr_metricas.pack(side="left", fill="both", expand=True, padx=(0, 10))
    
    # Card: Dinero Total Ingresado
    fr_total = ctk.CTkFrame(fr_metricas, fg_color="#10b981", corner_radius=15)
    fr_total.pack(fill="x", pady=(0, 10), ipady=15)
    ctk.CTkLabel(fr_total, text="💰 Total Facturado (Hoy)", font=("Segoe UI", 14, "bold"), text_color="white").pack(pady=(10, 0))
    lbl_total_ingresado = ctk.CTkLabel(fr_total, text="$ 0.00", font=("Segoe UI", 32, "bold"), text_color="white")
    lbl_total_ingresado.pack(pady=(5, 10))
    
    # Card: Ventas por Vendedor (Treeview)
    fr_vend = ctk.CTkFrame(fr_metricas, fg_color=win.col_card, corner_radius=10, border_color=win.col_border, border_width=1)
    fr_vend.pack(fill="both", expand=True)
    ctk.CTkLabel(fr_vend, text="👥 Ventas por Vendedor", font=("Segoe UI", 14, "bold"), text_color=win.col_text).pack(pady=(10, 5))
    
    tree_vendedores = ttk.Treeview(fr_vend, columns=("Vendedor", "Cant", "Monto"), show="headings", height=4)
    tree_vendedores.heading("Vendedor", text="Vendedor")
    tree_vendedores.heading("Cant", text="Cant.")
    tree_vendedores.heading("Monto", text="Monto")
    tree_vendedores.column("Vendedor", width=120)
    tree_vendedores.column("Cant", width=60, anchor="center")
    tree_vendedores.column("Monto", width=100, anchor="e")
    tree_vendedores.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Card: Productos Más Vendidos
    fr_top_prod = ctk.CTkFrame(fr_top, fg_color=win.col_card, corner_radius=10, border_color=win.col_border, border_width=1, width=350)
    fr_top_prod.pack(side="right", fill="both")
    fr_top_prod.pack_propagate(False)
    ctk.CTkLabel(fr_top_prod, text="🔥 Top Productos del Día", font=("Segoe UI", 14, "bold"), text_color=win.col_text).pack(pady=(10, 5))
    
    tree_top_prod = ttk.Treeview(fr_top_prod, columns=("Prod", "Cant"), show="headings", height=7)
    tree_top_prod.heading("Prod", text="Producto")
    tree_top_prod.heading("Cant", text="Vendidos")
    tree_top_prod.column("Prod", width=200)
    tree_top_prod.column("Cant", width=80, anchor="center")
    tree_top_prod.pack(fill="both", expand=True, padx=10, pady=10)
    
    # --- MIDDLE ROW (Cajas Activas) ---
    ctk.CTkLabel(body, text="📦 Cajas Activas en este momento", font=("Segoe UI", 16, "bold"), text_color=win.col_text).pack(anchor="w", pady=(15, 5))
    
    fr_cajas_container = ctk.CTkScrollableFrame(body, fg_color="transparent", height=200, orientation="horizontal")
    fr_cajas_container.pack(fill="both", expand=True)
    
    # --- BOTTOM ROW (Botones de Historial) ---
    fr_botones = ctk.CTkFrame(body, fg_color="transparent")
    fr_botones.pack(fill="x", pady=(15, 0))
    
    def abrir_historial_cajas():
        parent_win = win.master
        try:
            win.destroy()
        except Exception:
            pass
        if Historiales:
            Historiales(parent=parent_win, backend=backend, usuario=usuario, tab_inicial=3)
            
    ctk.CTkButton(fr_botones, text="📜 Historial de Cajas Cerradas / Retiros", command=abrir_historial_cajas, fg_color="#3b82f6", hover_color="#2563eb", font=("Segoe UI", 14, "bold"), height=45).pack(side="left", padx=(0, 10))
    
    def render_caja_activa(parent, caja):
        card = ctk.CTkFrame(parent, fg_color=win.col_card, corner_radius=10, border_color="#3b82f6", border_width=2)
        card.pack(side="left", padx=10, pady=10, fill="y")
        
        ctk.CTkLabel(card, text=f"👤 {caja['vendedor']}", font=("Segoe UI", 16, "bold"), text_color=win.col_text).pack(pady=(15, 5), padx=20)
        try:
            texto_ap = caja['fecha_apertura'].strftime('%d/%m/%Y %H:%M:%S') if hasattr(caja['fecha_apertura'], 'strftime') else datetime.strptime(str(caja['fecha_apertura']), "%Y-%m-%d %H:%M:%S").strftime('%d/%m/%Y %H:%M:%S')
        except:
            texto_ap = str(caja['fecha_apertura'])
        ctk.CTkLabel(card, text=f"Apertura: {texto_ap}", font=("Segoe UI", 12), text_color="#6b7280").pack()
        
        ctk.CTkLabel(card, text=_fmt(caja['monto_acumulado']), font=("Segoe UI", 22, "bold"), text_color="#10b981").pack(pady=(10, 0))
        ctk.CTkLabel(card, text="Monto Acumulado (Efvo)", font=("Segoe UI", 11), text_color="#9ca3af").pack()
        
        ctk.CTkLabel(card, text=f"{caja['cantidad_ventas']} ventas (Efvo) hoy", font=("Segoe UI", 12, "bold"), text_color=win.col_text).pack(pady=(10, 15))
        
        def ver_detalle():
            d = ctk.CTkToplevel(win)
            d.title(f"Detalle de Caja - {caja['vendedor']}")
            d.geometry("500x550")
            d.configure(fg_color=win.col_bg)
            
            res = backend.obtener_resumen_cierre(caja['id_session'])
            fr_header = ctk.CTkFrame(d, fg_color="#3b82f6", corner_radius=0)
            fr_header.pack(fill="x")
            ctk.CTkLabel(fr_header, text=f"CAJA ACTIVA - {caja['vendedor']}", font=("Segoe UI", 16, "bold"), text_color="white").pack(pady=8)
            
            fr_main = ctk.CTkScrollableFrame(d, fg_color="transparent")
            fr_main.pack(fill="both", expand=True, padx=15, pady=10)
            
            def add_row(parent, label, val, color=None):
                f = ctk.CTkFrame(parent, fg_color="transparent")
                f.pack(fill="x", pady=2)
                ctk.CTkLabel(f, text=label, font=("Segoe UI", 12), text_color=win.col_text).pack(side="left")
                ctk.CTkLabel(f, text=_fmt(val), font=("Segoe UI", 12, "bold"), text_color=color or win.col_text).pack(side="right")

            fr_efectivo = ctk.CTkFrame(fr_main, fg_color=win.col_card, corner_radius=10, border_color=win.col_border, border_width=1)
            fr_efectivo.pack(fill="x", pady=5, ipadx=10, ipady=10)
            add_row(fr_efectivo, "Saldo Inicial:", res.get('monto_inicial', 0))
            add_row(fr_efectivo, "(+) Ingresos Efectivo:", res.get('total_ingresos', 0), "#10b981")
            add_row(fr_efectivo, "(-) Egresos Efectivo:", res.get('total_egresos', 0), "#ef4444")
            ctk.CTkLabel(fr_efectivo, text=f"Efectivo Esperado: {_fmt(res.get('efectivo_esperado', 0))}", font=("Segoe UI", 14, "bold"), text_color="#3b82f6").pack(anchor="w", pady=(10,0))
            
            fr_medios = ctk.CTkFrame(fr_main, fg_color=win.col_card, corner_radius=10, border_color=win.col_border, border_width=1)
            fr_medios.pack(fill="x", pady=5, ipadx=10, ipady=10)
            ctk.CTkLabel(fr_medios, text="Otros Medios", font=("Segoe UI", 13, "bold"), text_color=win.col_text).pack(anchor="w", pady=(0, 5))
            medios = res.get('medios_pago', {})
            add_row(fr_medios, "Tarjetas:", medios.get('tarjetas', 0))
            add_row(fr_medios, "Transferencias:", medios.get('transferencias', 0))
            add_row(fr_medios, "Cuenta Corriente:", medios.get('cuenta_corriente', 0))
            
            ctk.CTkButton(d, text="Cerrar Detalle", command=d.destroy, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 14, "bold"), height=40).pack(pady=15)
            
            configurar_navegacion_ventana(d)
            d.grab_set()
            
        ctk.CTkButton(card, text="👁️ Ver Detalle", command=ver_detalle, fg_color="#6366f1", hover_color="#4f46e5", font=("Segoe UI", 12, "bold"), height=30).pack(pady=(0, 15), padx=20)
    
    def refresh_dashboard():
        if not win.winfo_exists(): return
        
        try:
            hoy = date.today().strftime("%Y-%m-%d")
            resumen_dia = backend.obtener_resumen_diario(hoy)
            monto_dia = resumen_dia.get('monto_total', 0.0)
            lbl_total_ingresado.configure(text=_fmt(monto_dia))
            
            for i in tree_vendedores.get_children(): tree_vendedores.delete(i)
            for v in resumen_dia.get('ventas_por_vendedor', []):
                tree_vendedores.insert("", "end", values=(v['vendedor'], v['cantidad_ventas'], _fmt(v['monto_total'])))
                
            top_prod = backend.obtener_productos_mas_vendidos(hoy, hoy, 7)
            for i in tree_top_prod.get_children(): tree_top_prod.delete(i)
            for p in top_prod:
                tree_top_prod.insert("", "end", values=(p['nombre'], int(p['cantidad_vendida'])))
                
            for widget in fr_cajas_container.winfo_children(): widget.destroy()
            cajas_activas = backend.obtener_sesiones_abiertas_con_totales()
            if not cajas_activas:
                ctk.CTkLabel(fr_cajas_container, text="No hay cajas abiertas en este momento.", font=("Segoe UI", 14), text_color="#6b7280").pack(pady=40)
            else:
                for c in cajas_activas:
                    render_caja_activa(fr_cajas_container, c)
                    
            lbl_last_update.configure(text=f"Actualizado: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            logger.error(f"Error actualizando dashboard admin: {e}")
            
        win.after(10000, refresh_dashboard)

    refresh_dashboard()
