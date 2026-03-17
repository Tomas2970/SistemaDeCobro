# app/frontend/interfaz_reportes.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Listbox, SINGLE
from datetime import date, datetime, timedelta
import logging
from typing import Any

try:
    from frontend.componentes_ui import EntryDecimal, SelectorFecha
    from frontend.navegacion_teclado_comun import configurar_navegacion_ventana
    from database.permisos import tiene_permiso
    from frontend.interfaz_historiales import Historiales
except ImportError:
    class EntryDecimal(tk.Entry): pass
    class SelectorFecha(tk.Frame):
        def __init__(self, master, **kw):
            super().__init__(master, **kw)
            self.widget_entrada = tk.Entry(self)
            self.widget_entrada.pack()
        def get_date_sql(self): return None
    def configurar_navegacion_ventana(win): pass
    def tiene_permiso(u, a): return True
    Historiales = None

try:
    import impresora as impresora
except ImportError:
    impresora = None

logger = logging.getLogger(__name__)

def _fmt(v): return f"$ {float(v):,.2f}"

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
    win = tk.Toplevel(parent)
    win.config(bg="#f4f4f8")
    
    style = ttk.Style()
    style.theme_use('clam')

    style.configure("Modern.Treeview",
                    background="#ffffff",
                    foreground="#1f2937",
                    rowheight=32,
                    fieldbackground="#ffffff",
                    borderwidth=0,
                    font=('Segoe UI', 10))

    style.configure("Modern.Treeview.Heading",
                    background="#f3f4f6",
                    foreground="#374151",
                    relief="flat",
                    borderwidth=1,
                    font=('Segoe UI', 10, 'bold'))

    style.map("Modern.Treeview.Heading",
              background=[('active', '#e5e7eb')])

    win.var_vendedor_sel = {"id": None, "nombre": "(Todos)"}
    win.vendedores_full_list = backend.obtener_vendedores() 

    if modo_vista == 'caja':
        win.title("📦 Control de Caja")
        win.geometry("900x650")
        _construir_panel_caja(win, backend, usuario)
    else:
        win.title("📊 Reportes de Ventas")
        win.geometry("1150x700")
        _construir_panel_reportes(win, backend, usuario)

    configurar_navegacion_ventana(win)
    win.grab_set()

def _crear_selector_entidad_reportes(win: tk.Toplevel, tipo: str, var_seleccion: dict, lista_datos: list):
    popup = Toplevel(win)
    popup.title(f"Seleccionar {tipo}")
    popup.geometry("500x450")
    popup.config(bg="#f4f4f8")
    
    configurar_navegacion_ventana(popup)

    tk.Label(popup, text=f"Buscar {tipo} (ID/Nombre):", bg="#f4f4f8", font=("Segoe UI", 10)).pack(pady=(10,5))
    var_pat = tk.StringVar()
    ent = tk.Entry(popup, textvariable=var_pat, width=40, font=("Segoe UI", 10))
    ent.pack(pady=5, padx=15, fill=tk.X)
    
    frame_list = tk.Frame(popup)
    frame_list.pack(expand=True, fill="both", padx=15, pady=5)
    sc = tk.Scrollbar(frame_list)
    sc.pack(side="right", fill="y")
    
    cols = ("ID", "Nombre")
    tree_sel = ttk.Treeview(frame_list, columns=cols, show="headings", style="Modern.Treeview", height=12)
    tree_sel.pack(side="left", fill="both", expand=True)
    sc.config(command=tree_sel.yview)
    tree_sel.configure(yscrollcommand=sc.set)
    
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
             win.lbl_vend_sel.config(text=win.var_vendedor_sel['nombre'])

    tree_sel.bind("<Double-1>", tomar)
    tree_sel.bind("<Return>", tomar)

    btn_frm = tk.Frame(popup, bg="#f4f4f8")
    btn_frm.pack(pady=10)
    
    btn_sel = tk.Button(btn_frm, text="✓ Seleccionar", command=tomar, 
                       bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"),
                       relief="flat", padx=20, pady=8, cursor="hand2",
                       activebackground="#059669")
    btn_sel.pack(side="left", padx=5)
    
    btn_canc = tk.Button(btn_frm, text="Cancelar", command=popup.destroy,
                        bg="#6b7280", fg="white", font=("Segoe UI", 10),
                        relief="flat", padx=15, pady=8, cursor="hand2",
                        activebackground="#4b5563")
    btn_canc.pack(side="left", padx=5)
    
    popup.after(100, lambda: ent.focus_set())
    popup.grab_set()
    popup.transient(win)
    win.wait_window(popup)

# --- PANEL DE CAJA ---
def _construir_panel_caja(win, backend, usuario):
    body = tk.Frame(win, bg="#f4f4f8", padx=20, pady=20)
    body.pack(fill="both", expand=True)

    session_actual = None
    puede_gestionar = tiene_permiso(usuario, 'abrir_caja')
    
    pnl_cerrada = tk.Frame(body, bg="#f4f4f8")
    pnl_abierta = tk.Frame(body, bg="#f4f4f8")

    def actualizar_dashboard():
        if not session_actual: return
        data = backend.obtener_resumen_cierre(session_actual['id_session'])
        if not data: return
        lbls_val['inicial'].config(text=_fmt(data['monto_inicial']))
        medios = data.get('medios_pago', {})
        total_ingresos_todos = (data['total_ingresos']
                                + medios.get('tarjetas', 0.0)
                                + medios.get('transferencias', 0.0)
                                + medios.get('cuenta_corriente', 0.0))
        lbls_val['ingresos'].config(text=_fmt(total_ingresos_todos))
        lbls_val['egresos'].config(text=_fmt(data['total_egresos']))
        lbls_val['esperado'].config(text=_fmt(data['efectivo_esperado']))
        lbl_status.config(text=f"✅ Caja Abierta | Apertura: {data['fecha_apertura']} por {usuario['nombre']}")

    def verificar_estado():
        nonlocal session_actual
        session_actual = backend.obtener_session_abierta(id_usuario=usuario['id_usuario'])
        pnl_cerrada.pack_forget(); pnl_abierta.pack_forget()
        if session_actual:
            pnl_abierta.pack(fill="both", expand=True)
            actualizar_dashboard()
        else:
            pnl_cerrada.pack(fill="both", expand=True)
            if puede_gestionar and ent_monto:
                ent_monto.delete(0, tk.END)
                ent_monto.insert(0, PLACEHOLDER)
                ent_monto.config(foreground=PLACEHOLDER_COLOR)

    if puede_gestionar:
        fr_ini = tk.Frame(pnl_cerrada, bg="white", padx=30, pady=30, relief="solid", bd=1)
        fr_ini.pack()
        tk.Label(fr_ini, text="Monto Inicial en Caja:", font=("Segoe UI", 12), bg="white").pack()
        def _val_apertura(t):
            if t == "" or t == PLACEHOLDER: return True
            import re
            if not re.match(r'^\d*\.?\d*$', t): return False
            partes = t.split('.')
            return len(partes[0]) <= 10
        vc_ap = (fr_ini.register(_val_apertura), '%P')
        ent_monto = tk.Entry(fr_ini, font=("Segoe UI", 16), width=15, justify="center",
                             validate="key", validatecommand=vc_ap)
        ent_monto.pack(pady=10)

        # Placeholder behavior
        PLACEHOLDER = "Ej: 1000.00"
        PLACEHOLDER_COLOR = "#000000"
        NORMAL_COLOR = "#1f2937"

        def on_focus_in(e):
            if ent_monto.get() == PLACEHOLDER:
                ent_monto.delete(0, tk.END)
                ent_monto.config(foreground=NORMAL_COLOR)

        def on_focus_out(e):
            if not ent_monto.get().strip():
                ent_monto.insert(0, PLACEHOLDER)
                ent_monto.config(foreground=PLACEHOLDER_COLOR)

        ent_monto.insert(0, PLACEHOLDER)
        ent_monto.config(foreground=PLACEHOLDER_COLOR)
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
                    messagebox.showwarning("Atención", "El monto de apertura debe ser mayor a $0.")
                    return
                backend.abrir_caja_session(usuario['id_usuario'], monto)
                messagebox.showinfo("Éxito", "Tu caja ha sido abierta correctamente.")
                verificar_estado()
            except ValueError: messagebox.showwarning("Error", "Monto inválido.")
            except Exception as e: messagebox.showerror("Error", f"Error al abrir caja:\n{e}")

        ent_monto.bind("<Return>", lambda e: abrir_caja())
        tk.Button(fr_ini, text="ABRIR MI TURNO", command=abrir_caja, bg="#10b981", fg="white", 
                 font=("Segoe UI", 12, "bold"), relief="flat", padx=25, pady=12, cursor="hand2", 
                 activebackground="#059669", width=20).pack(pady=10)
    else:
        tk.Label(pnl_cerrada, text="⚠️ No tienes permisos para abrir caja", font=("Segoe UI", 14), fg="#ef4444", bg="#f4f4f8").pack(pady=20)

    fr_head = tk.Frame(pnl_abierta, bg="#e0f2fe", pady=15, relief="solid", bd=1)
    fr_head.pack(fill="x")
    lbl_status = tk.Label(fr_head, text="...", bg="#e0f2fe", font=("Segoe UI", 10))
    lbl_status.pack()
    fr_totales = tk.Frame(fr_head, bg="#e0f2fe")
    fr_totales.pack(pady=10)
    
    lbls_val = {}
    def mk_ind(parent, txt, col=0, color="black"):
        f = tk.Frame(parent, bg="#e0f2fe"); f.grid(row=0, column=col, padx=20)
        tk.Label(f, text=txt, bg="#e0f2fe", fg="#666").pack()
        l = tk.Label(f, text="$ -", bg="#e0f2fe", font=("Segoe UI", 14, "bold"), fg=color)
        l.pack()
        return l

    lbls_val['inicial'] = mk_ind(fr_totales, "Inicial", 0)
    lbls_val['ingresos'] = mk_ind(fr_totales, "(+) Ingresos", 1, "green")
    lbls_val['egresos'] = mk_ind(fr_totales, "(-) Egresos", 2, "red")
    lbls_val['esperado'] = mk_ind(fr_totales, "= Efectivo Esperado", 3, "blue")

    fr_ops = tk.Frame(pnl_abierta, bg="#f4f4f8", pady=20)
    fr_ops.pack(fill="x")

    def iniciar_cierre():
        if not puede_gestionar: return
        
        data = backend.obtener_resumen_cierre(session_actual['id_session'])
        esperado = data['efectivo_esperado']
        medios_pago = data.get('medios_pago', {'tarjetas': 0.0, 'transferencias': 0.0, 'cuenta_corriente': 0.0})
        # Total recaudado = solo lo que entró en el turno, sin el saldo inicial
        # efectivo_esperado = monto_inicial + ingresos - egresos, entonces:
        ingresos_efectivo = data.get('total_ingresos', 0.0)
        # Total recaudado = lo que ENTRÓ en el turno (sin el inicial, sin restar egresos no-efectivo)
        total_general = ingresos_efectivo + medios_pago.get('tarjetas', 0.0) + medios_pago.get('transferencias', 0.0) + medios_pago.get('cuenta_corriente', 0.0)
        
        d = tk.Toplevel(win)
        d.title("📋 Cierre de Caja Completo")
        d.geometry("560x720")
        d.config(bg="#f4f4f8")
        
        fr_header = tk.Frame(d, bg="#3b82f6", pady=10)
        fr_header.pack(fill="x")
        tk.Label(fr_header, text="RESUMEN DE CIERRE DE CAJA", font=("Segoe UI", 15, "bold"), 
                 fg="white", bg="#3b82f6").pack()
        
        fr_main = tk.Frame(d, bg="#f4f4f8", padx=20, pady=10)
        fr_main.pack(fill="both", expand=True)
        
        fr_efectivo = tk.Frame(fr_main, bg="white", relief="solid", bd=1, padx=20, pady=10)
        fr_efectivo.pack(fill="x", pady=(0, 8))
        
        tk.Label(fr_efectivo, text="💰 ARQUEO DE EFECTIVO", font=("Segoe UI", 12, "bold"), 
                 bg="white", fg="#1f2937").pack(anchor="w")
        tk.Frame(fr_efectivo, bg="#e5e7eb", height=1).pack(fill="x", pady=5)
        
        tk.Label(fr_efectivo, text=f"Efectivo Esperado: {_fmt(esperado)}", font=("Segoe UI", 12, "bold"), 
                 bg="white", fg="#3b82f6").pack(anchor="w", pady=5)
        
        tk.Label(fr_efectivo, text="Ingrese Efectivo Contado (Real):", font=("Segoe UI", 10), bg="white").pack(anchor="w")
        def _val_real(t):
            if t == "": return True
            import re
            if not re.match(r'^\d*\.?\d*$', t): return False
            partes = t.split('.')
            return len(partes[0]) <= 10
        vc_real = (d.register(_val_real), '%P')
        e_real = tk.Entry(fr_efectivo, font=("Segoe UI", 14), justify="center", width=20,
                          validate="key", validatecommand=vc_real)
        e_real.pack(pady=5)
        e_real.focus_set()
        
        lbl_dif = tk.Label(fr_efectivo, text="Diferencia: $ 0.00", font=("Segoe UI", 11, "bold"), bg="white")
        lbl_dif.pack(pady=5)
        
        fr_medios = tk.Frame(fr_main, bg="white", relief="solid", bd=1, padx=20, pady=10)
        fr_medios.pack(fill="x", pady=(0, 8))
        
        def crear_linea_medio(parent, icono, texto, monto, color="#059669"):
            fr = tk.Frame(parent, bg="white")
            fr.pack(fill="x", pady=2)
            tk.Label(fr, text=f"{icono} {texto}:", font=("Segoe UI", 9), bg="white", width=28, anchor="w").pack(side="left")
            tk.Label(fr, text=_fmt(monto), font=("Segoe UI", 9, "bold"), bg="white", fg=color).pack(side="right")

        tar_ing = medios_pago.get('tarjetas', 0)
        tra_ing = medios_pago.get('transferencias', 0)
        cc_ing  = medios_pago.get('cuenta_corriente', 0)
        tra_egr = data.get('total_egresos_transferencia', 0.0)
        tar_egr = data.get('total_egresos_tarjeta', 0.0)

        # --- INGRESOS NO EFECTIVO ---
        tk.Label(fr_medios, text="📥 INGRESOS (No Efectivo)", font=("Segoe UI", 11, "bold"), bg="white", fg="#1f2937").pack(anchor="w", pady=(0,4))
        crear_linea_medio(fr_medios, "💳", "Tarjetas", tar_ing)
        crear_linea_medio(fr_medios, "🏦", "Transferencias", tra_ing)
        crear_linea_medio(fr_medios, "📋", "Cuenta Corriente", cc_ing)

        # --- EGRESOS NO EFECTIVO (solo si hubo) ---
        if tra_egr > 0 or tar_egr > 0:
            tk.Frame(fr_medios, bg="#e5e7eb", height=1).pack(fill="x", pady=6)
            tk.Label(fr_medios, text="📤 EGRESOS (No Efectivo)", font=("Segoe UI", 11, "bold"), bg="white", fg="#1f2937").pack(anchor="w", pady=(0,4))
            if tar_egr > 0:
                crear_linea_medio(fr_medios, "💳", "Tarjetas (pagos)", tar_egr, "#dc2626")
            if tra_egr > 0:
                crear_linea_medio(fr_medios, "🏦", "Transferencias (pagos)", tra_egr, "#dc2626")
        
        fr_total = tk.Frame(fr_main, bg="#e0f2fe", relief="solid", bd=1, padx=20, pady=10)
        fr_total.pack(fill="x", pady=(0, 8))
        tk.Label(fr_total, text="📈 TOTAL RECAUDADO", font=("Segoe UI", 11, "bold"), bg="#e0f2fe").pack()
        tk.Label(fr_total, text=_fmt(total_general), font=("Segoe UI", 16, "bold"), bg="#e0f2fe", fg="#0369a1").pack()
        
        tk.Label(fr_main, text="Observaciones:", font=("Segoe UI", 10), bg="#f4f4f8").pack(anchor="w")
        txt_obs = tk.Text(fr_main, height=2, width=50, font=("Segoe UI", 9), relief="solid", bd=1)
        txt_obs.pack(pady=5, fill="x")
        
        def calc_diff(e=None):
            try:
                real = float(e_real.get() or 0)
                dif = real - esperado
                col = "#059669" if abs(dif) < 0.01 else "#dc2626"
                lbl_dif.config(text=f"Diferencia: {'' if dif < 0 else '+'}{_fmt(dif)}", fg=col)
            except: pass
        
        e_real.bind("<KeyRelease>", calc_diff)
        
        def confirmar():
            try:
                real = float(e_real.get())
                dif = real - esperado
                obs = txt_obs.get("1.0", tk.END).strip()
                if abs(dif) > 0.01 and len(obs) < 5:
                    messagebox.showwarning("Atención", "Justifique la diferencia.", parent=d)
                    return
                if messagebox.askyesno("Confirmar", "¿Cerrar caja definitivamente?", parent=d):
                    backend.cerrar_caja_session(session_actual['id_session'], usuario['id_usuario'], esperado, real, dif, obs)
                    if impresora:
                        dt = data.copy(); dt.update({'efectivo_contado': real, 'diferencia': dif, 'observaciones': obs, 'medios_pago': medios_pago, 'total_general': total_general})
                        impresora.imprimir_cierre_caja(dt, [], usuario['nombre'])
                    messagebox.showinfo("Listo", "Caja cerrada.", parent=d)
                    d.destroy(); verificar_estado()
            except ValueError: messagebox.showerror("Error", "Monto inválido", parent=d)
        
        fr_botones = tk.Frame(fr_main, bg="#f4f4f8")
        fr_botones.pack(pady=10)
        
        tk.Button(fr_botones, text="✓ Confirmar Cierre", command=confirmar, bg="#10b981", fg="white", 
                 font=("Segoe UI", 11, "bold"), relief="flat", padx=20, pady=8, cursor="hand2").pack(side="left", padx=5)
        
        tk.Button(fr_botones, text="Cancelar", command=d.destroy, bg="#6b7280", fg="white", 
                 font=("Segoe UI", 11), relief="flat", padx=20, pady=8, cursor="hand2").pack(side="left", padx=5)
        
        configurar_navegacion_ventana(d); d.grab_set()

    if tiene_permiso(usuario, 'movimientos_caja_manuales'):
        def modal_movimiento(tipo):
            top = tk.Toplevel(win)
            top.title(f"Registrar {tipo.upper()}")
            top.geometry("400x380")
            top.config(bg="#f4f4f8")
            
            tk.Label(top, text="Monto:", bg="#f4f4f8", font=("Segoe UI", 10)).pack(pady=(15,5))
            e_m = EntryDecimal(top, font=("Segoe UI", 12), width=20); e_m.pack(pady=5); e_m.focus_set()
            
            tk.Label(top, text="Motivo:", bg="#f4f4f8", font=("Segoe UI", 10)).pack(pady=(10,5))
            motivos_dict = {"Gasto Vario": "gasto_vario", "Retiro/Ajuste": "retiro_caja", "Pago a Proveedor": "pago_proveedor", "Reembolso a Cliente": "devolucion_efectivo"} if tipo == 'egreso' else {"Ajuste Positivo": "ajuste_positivo"}
            cb_mot = ttk.Combobox(top, values=list(motivos_dict.keys()), state="readonly", width=25); cb_mot.pack(pady=5); cb_mot.current(0)
            
            tk.Label(top, text="Observaciones:", bg="#f4f4f8", font=("Segoe UI", 10)).pack(pady=(10,5))
            txt_obs_mov = tk.Text(top, height=4, width=35, font=("Segoe UI", 9)); txt_obs_mov.pack(pady=5, padx=15)
            
            def save():
                try:
                    m = float(e_m.get())
                    if m <= 0: raise ValueError
                    if tipo == 'egreso':
                        data_c = backend.obtener_resumen_cierre(session_actual['id_session'])
                        if m > data_c.get('efectivo_esperado', 0.0):
                            messagebox.showerror("Saldo Insuficiente", "No hay suficiente efectivo.", parent=top)
                            return
                    backend.registrar_movimiento_manual(session_actual['id_session'], tipo, m, motivos_dict[cb_mot.get()], txt_obs_mov.get("1.0", tk.END).strip(), usuario['id_usuario'])
                    top.destroy(); actualizar_dashboard(); messagebox.showinfo("Éxito", "Registrado.")
                except ValueError: messagebox.showerror("Error", "Monto inválido")
            
            tk.Button(top, text="💾 Guardar", command=save, bg="#10b981", fg="white", font=("Segoe UI", 11, "bold"), 
                     relief="flat", padx=20, pady=10, cursor="hand2").pack(pady=20)
            configurar_navegacion_ventana(top); top.grab_set()

        tk.Button(fr_ops, text="➖ GASTO/RETIRO", command=lambda: modal_movimiento('egreso'), bg="#ef4444", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8, cursor="hand2").pack(side="left", padx=20)
        tk.Button(fr_ops, text="➕ AJUSTE (+)", command=lambda: modal_movimiento('ingreso'), bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8, cursor="hand2").pack(side="left")
    
    if puede_gestionar:
        tk.Button(fr_ops, text="🔒 CERRAR CAJA", command=iniciar_cierre, bg="#1f2937", fg="white", font=("Segoe UI", 11, "bold"), relief="flat", padx=20, pady=10, cursor="hand2").pack(side="right", padx=20)
    
    # --- TREEVIEW DE MOVIMIENTOS DEL TURNO ---
    fr_mov_header = tk.Frame(pnl_abierta, bg="#f4f4f8", pady=5)
    fr_mov_header.pack(fill="x", padx=10)
    tk.Label(fr_mov_header, text="📋 Movimientos del día:", bg="#f4f4f8",
             font=("Segoe UI", 10, "bold")).pack(side="left")
    btn_refrescar = tk.Button(fr_mov_header, text="🔄 Actualizar", bg="#3b82f6", fg="white",
                              font=("Segoe UI", 9), relief="flat", padx=10, pady=4, cursor="hand2")
    btn_refrescar.pack(side="right", padx=5)

    cols_mov = ("Hora", "Tipo", "Motivo", "Monto", "Descripción")
    tree_mov = ttk.Treeview(pnl_abierta, columns=cols_mov, show="headings", height=8,
                            style="Modern.Treeview" if hasattr(ttk.Style(), "layout") else "Treeview")
    tree_mov.pack(fill="both", expand=True, padx=10, pady=(0, 5))

    sc_mov = ttk.Scrollbar(pnl_abierta, orient="vertical", command=tree_mov.yview)
    tree_mov.configure(yscrollcommand=sc_mov.set)

    tree_mov.heading("Hora", text="Hora")
    tree_mov.heading("Tipo", text="Tipo")
    tree_mov.heading("Motivo", text="Motivo")
    tree_mov.heading("Monto", text="Monto")
    tree_mov.heading("Descripción", text="Descripción")
    tree_mov.column("Hora", width=90, anchor="center")
    tree_mov.column("Tipo", width=90, anchor="center")
    tree_mov.column("Motivo", width=160, anchor="center")
    tree_mov.column("Monto", width=100, anchor="e")
    tree_mov.column("Descripción", width=300)

    tree_mov.tag_configure("ingreso", background="#d1fae5")
    tree_mov.tag_configure("egreso", background="#fee2e2")

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
        from datetime import date as _date
        hoy = _date.today().strftime("%Y-%m-%d")
        movs = backend.obtener_historial_movimientos_caja(
            fecha_desde=hoy, fecha_hasta=hoy, tipo=None, motivo=None, id_usuario=None
        )
        for m in movs:
            motivo_raw = m.get("motivo", "")
            if motivo_raw == "apertura_caja": continue
            try:
                hora = m["fecha_hora"].strftime("%H:%M:%S") if hasattr(m["fecha_hora"], "strftime") else str(m["fecha_hora"])[-8:]
            except: hora = ""
            tipo = "➕ Ingreso" if m.get("tipo") == "ingreso" else "➖ Egreso"
            motivo_lbl = MAPEO_MOTIVOS.get(motivo_raw, motivo_raw)
            monto = f"$ {float(m.get('monto', 0)):,.2f}"
            desc = m.get("descripcion") or ""
            tag = "ingreso" if m.get("tipo") == "ingreso" else "egreso"
            tree_mov.insert("", "end", values=(hora, tipo, motivo_lbl, monto, desc), tags=(tag,))

    btn_refrescar.config(command=cargar_movimientos)

    # Sobreescribir actualizar_dashboard para que también refresque movimientos
    _orig_actualizar = actualizar_dashboard
    def actualizar_dashboard():
        _orig_actualizar()
        cargar_movimientos()

    verificar_estado()

# --- PANEL DE REPORTES ---
def _construir_panel_reportes(win, backend, usuario):
    body = tk.Frame(win, bg="#f4f4f8", padx=10, pady=10)
    body.pack(fill="both", expand=True)

    def aplicar_filtro_rapido(event, combo, entry_desde, entry_hasta):
        seleccion = combo.get()
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

    frm_vend = ttk.LabelFrame(body, text="📈 Ventas por Vendedor", padding=10)
    frm_vend.pack(fill="both", expand=True, pady=(0, 10))
    frm_f1 = tk.Frame(frm_vend); frm_f1.pack(fill="x", pady=5)
    
    cb_rango_v = ttk.Combobox(frm_f1, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Mes Pasado"], state="readonly", width=12); cb_rango_v.current(0); cb_rango_v.pack(side="left", padx=5)
    
    # 🔥 CORRECCIÓN: Limpieza antes de insertar fecha para evitar duplicidad
    fd_v = SelectorFecha(frm_f1); fd_v.pack(side="left", padx=5)
    fd_v.widget_entrada.delete(0, tk.END)
    fd_v.widget_entrada.insert(0, date.today().replace(day=1).strftime("%d/%m/%Y"))
    
    fh_v = SelectorFecha(frm_f1); fh_v.pack(side="left", padx=5)
    fh_v.widget_entrada.delete(0, tk.END)
    fh_v.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
    
    cb_rango_v.bind("<<ComboboxSelected>>", lambda e: aplicar_filtro_rapido(e, cb_rango_v, fd_v.widget_entrada, fh_v.widget_entrada))
    
    tk.Label(frm_f1, text="Vendedor:", bg="#f4f4f8").pack(side="left", padx=(10, 5))
    win.lbl_vend_sel = tk.Label(frm_f1, text=win.var_vendedor_sel['nombre'], bg="#f4f4f8"); win.lbl_vend_sel.pack(side="left", padx=5)
    
    tk.Button(frm_f1, text="Buscar Vendedor", command=lambda: _crear_selector_entidad_reportes(win, "Vendedor", win.var_vendedor_sel, win.vendedores_full_list), bg="#3b82f6", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5).pack(side="left", padx=5)
    
    tree_v = ttk.Treeview(frm_vend, columns=("Vend", "Ventas", "Monto"), show="headings", height=5, style="Modern.Treeview"); tree_v.pack(fill="both", expand=True)
    tree_v.heading("Vend", text="Vendedor"); tree_v.heading("Ventas", text="Cant."); tree_v.heading("Monto", text="Total")
    
    def buscar_vend():
        for i in tree_v.get_children(): tree_v.delete(i)
        data = backend.reporte_ventas_por_vendedor(fd_v.get_date_sql(), fh_v.get_date_sql(), win.var_vendedor_sel['id'])
        for r in data: tree_v.insert("", "end", values=(r['vendedor'], r['total_ventas'], _fmt(r['monto_total'])))
    
    tk.Button(frm_f1, text="Generar", command=buscar_vend, bg="#3b82f6", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5).pack(side="left", padx=5)

    # DOBLE CLICK en ventas por vendedor -> abre historial con datos pre-cargados
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

    frm_dia = ttk.LabelFrame(body, text="Ventas Diarias", padding=10)
    frm_dia.pack(fill="both", expand=True)
    frm_f2 = tk.Frame(frm_dia); frm_f2.pack(fill="x", pady=5)

    # Filtros rapidos de fecha para ventas diarias
    cb_rango_d = ttk.Combobox(frm_f2, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Mes Pasado"], state="readonly", width=12)
    cb_rango_d.current(0); cb_rango_d.pack(side="left", padx=5)

    fd_d = SelectorFecha(frm_f2); fd_d.pack(side="left", padx=5)
    fd_d.widget_entrada.delete(0, tk.END)
    fd_d.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
    
    fh_d = SelectorFecha(frm_f2); fh_d.pack(side="left", padx=5)
    fh_d.widget_entrada.delete(0, tk.END)
    fh_d.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))

    cb_rango_d.bind("<<ComboboxSelected>>", lambda e: aplicar_filtro_rapido(e, cb_rango_d, fd_d.widget_entrada, fh_d.widget_entrada))
    
    tree_d = ttk.Treeview(frm_dia, columns=("Fecha", "Ventas", "Monto"), show="headings", height=5, style="Modern.Treeview"); tree_d.pack(fill="both", expand=True)
    tree_d.heading("Fecha", text="Fecha"); tree_d.heading("Ventas", text="Cant."); tree_d.heading("Monto", text="Total")
    
    def buscar_dia():
        for i in tree_d.get_children(): tree_d.delete(i)
        data = backend.obtener_ventas_diarias(fd_d.get_date_sql(), fh_d.get_date_sql())
        for r in data: 
            f_str = datetime.strptime(str(r['fecha']), "%Y-%m-%d").strftime("%d/%m/%Y")
            tree_d.insert("", "end", values=(f_str, r['total_ventas'], _fmt(r['monto_total'])))
    
    tk.Button(frm_f2, text="Generar", command=buscar_dia, bg="#3b82f6", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5).pack(side="left", padx=5)

    # DOBLE CLICK en ventas diarias -> abre historial con fecha pre-cargada
    def on_doble_click_dia(event):
        sel = tree_d.selection()
        if not sel: return
        vals = tree_d.item(sel[0], "values")
        if not vals: return
        fecha_ui = vals[0]  # formato dd/mm/YYYY
        if Historiales:
            Historiales(
                win, backend, usuario,
                tab_inicial=0,
                filtro_fecha=fecha_ui,
                filtro_fecha_desde_default=fecha_ui,
                filtro_fecha_hasta_default=fecha_ui
            )
    tree_d.bind("<Double-1>", on_doble_click_dia)
    # Boton imprimir reporte diario eliminado: ver historial con doble click para el detalle del dia

    # Boton cerrar al pie del panel reportes
    frm_footer = tk.Frame(body, bg="#f4f4f8", pady=10)
    frm_footer.pack(fill="x")
    tk.Button(frm_footer, text="Cerrar", command=win.destroy,
              bg="#64748b", fg="white", font=("Segoe UI", 10),
              relief="flat", padx=20, pady=6, cursor="hand2").pack(side=tk.RIGHT)