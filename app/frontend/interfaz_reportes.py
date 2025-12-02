# app/frontend/interfaz_reportes.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
import logging

try:
    from app.frontend.componentes_ui import EntryDecimal, SelectorFecha
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
    from app.database.permisos import tiene_permiso
    from app.frontend.interfaz_historiales import Historiales
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
    import app.impresora as impresora
except ImportError:
    impresora = None

logger = logging.getLogger(__name__)

def _fmt(v): return f"$ {float(v):,.2f}"

def ui_reportes(parent: tk.Misc, backend, usuario: dict, modo_vista: str = 'caja'):
    """
    modo_vista: 'caja' para Control de Caja, 'reportes' para Reportes de Ventas
    """
    win = tk.Toplevel(parent)
    win.config(bg="#f4f4f8")
    
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

# =================================================================
# LÓGICA DE CONTROL DE CAJA
# =================================================================
def _construir_panel_caja(win, backend, usuario):
    body = tk.Frame(win, bg="#f4f4f8", padx=20, pady=20)
    body.pack(fill="both", expand=True)

    session_actual = None
    puede_gestionar = tiene_permiso(usuario, 'abrir_caja')
    
    pnl_cerrada = tk.Frame(body, bg="#f4f4f8")
    pnl_abierta = tk.Frame(body, bg="#f4f4f8")

    # UI CAJA CERRADA
    tk.Label(pnl_cerrada, text="🔒 TU CAJA ESTÁ CERRADA", font=("Segoe UI", 24, "bold"), 
             fg="#757575", bg="#f4f4f8").pack(pady=40)
    ent_monto = None
    
    # --- Funciones internas de Caja ---
    def actualizar_dashboard():
        if not session_actual: return
        data = backend.obtener_resumen_cierre(session_actual['id_session'])
        if not data: return
        lbls_val['inicial'].config(text=_fmt(data['monto_inicial']))
        lbls_val['ingresos'].config(text=_fmt(data['total_ingresos']))
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
                ent_monto.delete(0, tk.END); ent_monto.insert(0, "0.00")

    if puede_gestionar:
        fr_ini = tk.Frame(pnl_cerrada, bg="white", padx=30, pady=30, relief="solid", bd=1)
        fr_ini.pack()
        tk.Label(fr_ini, text="Monto Inicial en Caja:", font=("Segoe UI", 12), bg="white").pack()
        ent_monto = EntryDecimal(fr_ini, font=("Segoe UI", 16), width=15, justify="center")
        ent_monto.insert(0, "0.00")
        ent_monto.pack(pady=10)
        
        def abrir_caja():
            try:
                texto_monto = ent_monto.get()
                monto = float(texto_monto) if texto_monto else 0.0
                if monto <= 0:
                    messagebox.showwarning("Atención", "El monto de apertura debe ser mayor a $0.")
                    return
                backend.abrir_caja_session(usuario['id_usuario'], monto)
                messagebox.showinfo("Éxito", "Tu caja ha sido abierta correctamente.")
                verificar_estado()
            except ValueError: messagebox.showwarning("Error", "Monto inválido.")
            except Exception as e: messagebox.showerror("Error", f"Error al abrir caja:\n{e}")

        ent_monto.bind("<Return>", lambda e: abrir_caja())
        tk.Button(fr_ini, text="ABRIR MI TURNO", bg="#2e9e44", fg="white", 
                  font=("bold", 12), command=abrir_caja, width=20).pack(pady=10)
    else:
        tk.Label(pnl_cerrada, text="⚠️ No tienes permisos para abrir caja", font=("Segoe UI", 14), fg="#ef4444", bg="#f4f4f8").pack(pady=20)

    # UI CAJA ABIERTA
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
        
        d = tk.Toplevel(win)
        d.title("Arqueo de Caja")
        d.geometry("400x500")
        tk.Label(d, text="Resumen de Tu Turno", font=("bold", 14)).pack(pady=10)
        tk.Label(d, text=f"Efectivo Esperado: {_fmt(esperado)}", font=("Segoe UI", 16), fg="blue").pack(pady=10)
        tk.Label(d, text="Ingrese Efectivo Contado (Real):").pack()
        e_real = EntryDecimal(d, font=("Segoe UI", 14), justify="center")
        e_real.pack(pady=5); e_real.focus_set()
        lbl_dif = tk.Label(d, text="Diferencia: $ 0.00", font=("bold", 12)); lbl_dif.pack(pady=10)
        tk.Label(d, text="Observaciones:").pack()
        txt_obs = tk.Text(d, height=4, width=40); txt_obs.pack()
        
        def calc_diff(e=None):
            try:
                real = float(e_real.get() or 0)
                dif = real - esperado
                col = "green" if abs(dif) < 0.01 else "red"
                lbl_dif.config(text=f"Diferencia: {_fmt(dif)}", fg=col)
            except: pass
        e_real.bind("<KeyRelease>", calc_diff)
        
        def confirmar():
            try:
                real = float(e_real.get())
                dif = real - esperado
                obs = txt_obs.get("1.0", tk.END).strip()
                if abs(dif) > 0.01 and len(obs) < 5:
                    messagebox.showwarning("Atención", "Debe justificar la diferencia.")
                    return
                if messagebox.askyesno("Confirmar", "¿Cerrar tu caja definitivamente?"):
                    backend.cerrar_caja_session(session_actual['id_session'], usuario['id_usuario'], esperado, real, dif, obs)
                    if impresora:
                        dt = data.copy(); dt.update({'efectivo_contado': real, 'diferencia': dif, 'observaciones': obs})
                        impresora.imprimir_cierre_caja(dt, [], usuario['nombre'])
                    messagebox.showinfo("Listo", "Caja cerrada.")
                    d.destroy(); verificar_estado()
            except ValueError: messagebox.showerror("Error", "Monto inválido")

        tk.Button(d, text="FINALIZAR CIERRE", command=confirmar, bg="#2e9e44", fg="white", font=("bold", 12)).pack(pady=20)
        configurar_navegacion_ventana(d)

    if tiene_permiso(usuario, 'movimientos_caja_manuales'):
        def modal_movimiento(tipo):
            top = tk.Toplevel(win); top.title(f"Registrar {tipo.upper()}")
            top.geometry("350x300")
            tk.Label(top, text="Monto:").pack(pady=5)
            e_m = EntryDecimal(top); e_m.pack(); e_m.focus_set()
            tk.Label(top, text="Motivo:").pack(pady=5)
            motivos = ["gasto_vario", "retiro_caja", "pago_proveedor"] if tipo == 'egreso' else ["ajuste_positivo"]
            cb_mot = ttk.Combobox(top, values=motivos, state="readonly"); cb_mot.pack(); cb_mot.current(0)
            tk.Label(top, text="Descripción:").pack(pady=5)
            e_d = tk.Entry(top, width=30); e_d.pack()
            def save():
                try:
                    m = float(e_m.get())
                    if m <= 0: raise ValueError
                    backend.registrar_movimiento_manual(session_actual['id_session'], tipo, m, cb_mot.get(), e_d.get(), usuario['id_usuario'])
                    top.destroy(); actualizar_dashboard(); messagebox.showinfo("Éxito", "Registrado")
                except: messagebox.showerror("Error", "Datos inválidos")
            tk.Button(top, text="Guardar", command=save, bg="#2e9e44", fg="white").pack(pady=20)
            configurar_navegacion_ventana(top)

        tk.Button(fr_ops, text="➖ GASTO/RETIRO", bg="#ef4444", fg="white", font=("bold", 10), command=lambda: modal_movimiento('egreso')).pack(side="left", padx=20)
        tk.Button(fr_ops, text="➕ AJUSTE (+)", bg="#22c55e", fg="white", font=("bold", 10), command=lambda: modal_movimiento('ingreso')).pack(side="left")
    
    if puede_gestionar:
        tk.Button(fr_ops, text="🔒 CERRAR CAJA", bg="#1f2937", fg="white", font=("bold", 11), command=iniciar_cierre).pack(side="right", padx=20)
    
    def imprimir_resumen():
        if impresora:
            impresora.imprimir_resumen_diario(backend.obtener_resumen_diario())
            messagebox.showinfo("Éxito", "Impreso")
        else: messagebox.showwarning("Error", "Sin impresora")
    tk.Button(fr_ops, text="🖨️ Resumen Día", bg="#f59e0b", fg="white", font=("bold", 10), command=imprimir_resumen).pack(side="right", padx=5)

    verificar_estado()

# =================================================================
# LÓGICA DE REPORTES (PANEL AISLADO)
# =================================================================
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
        elif seleccion == "Semana Pasada":
            fin_semana = hoy - timedelta(days=hoy.weekday() + 1)
            f_ini = fin_semana - timedelta(days=6); f_fin = fin_semana
        elif seleccion == "Este Mes":
            f_ini = hoy.replace(day=1); f_fin = hoy
        elif seleccion == "Mes Pasado":
            primero = hoy.replace(day=1); ultimo_mes = primero - timedelta(days=1)
            f_ini = ultimo_mes.replace(day=1); f_fin = ultimo_mes
        if f_ini:
            # Borrar antes de insertar para evitar duplicados
            entry_desde.delete(0, tk.END); entry_desde.insert(0, f_ini.strftime("%d/%m/%Y"))
            entry_hasta.delete(0, tk.END); entry_hasta.insert(0, f_fin.strftime("%d/%m/%Y"))

    # Ventas por Vendedor
    frm_vend = ttk.LabelFrame(body, text="📈 Ventas por Vendedor", padding=10)
    frm_vend.pack(fill="both", expand=True, pady=(0, 10))
    frm_f1 = tk.Frame(frm_vend); frm_f1.pack(fill="x", pady=5)
    
    cb_rango_v = ttk.Combobox(frm_f1, values=["Personalizado", "Hoy", "Ayer", "Esta Semana", "Mes Pasado"], state="readonly", width=12)
    cb_rango_v.current(0); cb_rango_v.pack(side="left", padx=5)
    
    fd_v = SelectorFecha(frm_f1); fd_v.pack(side="left", padx=5)
    fd_v.widget_entrada.delete(0, tk.END); fd_v.widget_entrada.insert(0, date.today().replace(day=1).strftime("%d/%m/%Y"))
    
    fh_v = SelectorFecha(frm_f1); fh_v.pack(side="left", padx=5)
    fh_v.widget_entrada.delete(0, tk.END); fh_v.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
    
    cb_rango_v.bind("<<ComboboxSelected>>", lambda e: aplicar_filtro_rapido(e, cb_rango_v, fd_v.widget_entrada, fh_v.widget_entrada))
    
    vendedores = backend.obtener_vendedores()
    v_ids = [None] + [v['id_usuario'] for v in vendedores]
    v_names = ["(Todos)"] + [v['nombre'] for v in vendedores]
    cb_vend = ttk.Combobox(frm_f1, values=v_names, state="readonly"); cb_vend.current(0); cb_vend.pack(side="left", padx=5)
    
    tree_v = ttk.Treeview(frm_vend, columns=("Vend", "Ventas", "Monto"), show="headings", height=5)
    tree_v.pack(fill="both", expand=True)
    tree_v.heading("Vend", text="Vendedor"); tree_v.heading("Ventas", text="Cant."); tree_v.heading("Monto", text="Total")
    
    def buscar_vend():
        for i in tree_v.get_children(): tree_v.delete(i)
        data = backend.reporte_ventas_por_vendedor(fd_v.get_date_sql(), fh_v.get_date_sql(), v_ids[cb_vend.current()])
        for r in data: tree_v.insert("", "end", values=(r['vendedor'], r['total_ventas'], _fmt(r['monto_total'])))
    
    tk.Button(frm_f1, text="Generar", command=buscar_vend, bg="#2563eb", fg="white").pack(side="left", padx=10)

    # Ventas Diarias
    frm_dia = ttk.LabelFrame(body, text="📅 Ventas Diarias", padding=10)
    frm_dia.pack(fill="both", expand=True)
    frm_f2 = tk.Frame(frm_dia); frm_f2.pack(fill="x", pady=5)
    
    cb_rango_d = ttk.Combobox(frm_f2, values=["Personalizado", "Hoy", "Esta Semana", "Este Mes"], state="readonly", width=12)
    cb_rango_d.current(0); cb_rango_d.pack(side="left", padx=5)
    
    fd_d = SelectorFecha(frm_f2); fd_d.pack(side="left", padx=5)
    fd_d.widget_entrada.delete(0, tk.END); fd_d.widget_entrada.insert(0, date.today().replace(day=1).strftime("%d/%m/%Y"))
    
    fh_d = SelectorFecha(frm_f2); fh_d.pack(side="left", padx=5)
    fh_d.widget_entrada.delete(0, tk.END); fh_d.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
    
    cb_rango_d.bind("<<ComboboxSelected>>", lambda e: aplicar_filtro_rapido(e, cb_rango_d, fd_d.widget_entrada, fh_d.widget_entrada))
    
    tree_d = ttk.Treeview(frm_dia, columns=("Fecha", "Ventas", "Monto"), show="headings", height=5)
    tree_d.pack(fill="both", expand=True)
    tree_d.heading("Fecha", text="Fecha"); tree_d.heading("Ventas", text="Cant."); tree_d.heading("Monto", text="Total")
    
    def buscar_dia():
        for i in tree_d.get_children(): tree_d.delete(i)
        data = backend.obtener_ventas_diarias(fd_d.get_date_sql(), fh_d.get_date_sql())
        for r in data: 
            # --- CORRECCIÓN AQUÍ: Usamos 'r' en lugar de 'row' ---
            f_str = datetime.strptime(str(r['fecha']), "%Y-%m-%d").strftime("%d/%m/%Y")
            tree_d.insert("", "end", values=(f_str, r['total_ventas'], _fmt(r['monto_total'])))
    
    tk.Button(frm_f2, text="Generar", command=buscar_dia, bg="#2563eb", fg="white").pack(side="left", padx=10)

    # Integración con Historiales (Doble Click)
    def ir_historial(e, tree, es_vendedor=True):
        sel = tree.selection()
        if not sel or not Historiales: return
        val = tree.item(sel[0])['values'][0]
        try:
            if es_vendedor:
                uid = next(v['id_usuario'] for v in vendedores if v['nombre'] == val)
                Historiales(win, backend, usuario, filtro_vendedor_id=uid,
                            filtro_fecha_desde_default=fd_v.widget_entrada.get(),
                            filtro_fecha_hasta_default=fh_v.widget_entrada.get())
            else:
                Historiales(win, backend, usuario, filtro_fecha=val) 
        except: pass

    tree_v.bind("<Double-1>", lambda e: ir_historial(e, tree_v, True))
    tree_d.bind("<Double-1>", lambda e: ir_historial(e, tree_d, False))