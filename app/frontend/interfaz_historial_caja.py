# app/frontend/interfaz_historial_caja.py
"""
Historial de Movimientos de Caja
Muestra todos los movimientos manuales y automáticos registrados en caja_movimiento
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import logging

try:
    from app.frontend.componentes_ui import SelectorFecha
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
    from app.database.permisos import tiene_permiso
except ImportError:
    class SelectorFecha(tk.Frame):
        def __init__(self, master, **kw):
            super().__init__(master, **kw)
            self.widget_entrada = tk.Entry(self)
            self.widget_entrada.pack()
        def get_date_sql(self): return None
    def configurar_navegacion_ventana(win): pass
    def tiene_permiso(u, a): return True

logger = logging.getLogger(__name__)

def _fmt(v): 
    """Formatea montos con símbolo de pesos"""
    return f"$ {float(v):,.2f}"

def ui_historial_caja(parent: tk.Misc, backend, usuario: dict):
    """
    Ventana principal del historial de movimientos de caja
    """
    # Validar permiso
    if not tiene_permiso(usuario, 'ver_historial_movimientos'):
        messagebox.showwarning(
            "Acceso Denegado",
            "No tienes permisos para ver el historial de movimientos de caja.",
            parent=parent
        )
        return
    
    win = tk.Toplevel(parent)
    win.title("📋 Historial de Movimientos de Caja")
    win.geometry("1200x700")
    win.config(bg="#f4f4f8")
    
    # Header
    frm_header = tk.Frame(win, bg="#2563eb", pady=15)
    frm_header.pack(fill="x")
    tk.Label(frm_header, text="HISTORIAL DE MOVIMIENTOS DE CAJA", 
             font=("Segoe UI", 16, "bold"), fg="white", bg="#2563eb").pack()
    
    # Body
    body = tk.Frame(win, bg="#f4f4f8", padx=20, pady=20)
    body.pack(fill="both", expand=True)
    
    # =================================================================
    # FILTROS
    # =================================================================
    frm_filtros = ttk.LabelFrame(body, text="🔍 Filtros", padding=15)
    frm_filtros.pack(fill="x", pady=(0, 15))
    
    # Fila 1: Fechas
    frm_fechas = tk.Frame(frm_filtros, bg="white")
    frm_fechas.pack(fill="x", pady=5)
    
    tk.Label(frm_fechas, text="Desde:", font=("Segoe UI", 10, "bold"), bg="white").grid(row=0, column=0, padx=5)
    fecha_desde = SelectorFecha(frm_fechas)
    fecha_desde.grid(row=0, column=1, padx=5)
    fecha_desde.widget_entrada.delete(0, tk.END)
    fecha_desde.widget_entrada.insert(0, date.today().replace(day=1).strftime("%d/%m/%Y"))
    
    tk.Label(frm_fechas, text="Hasta:", font=("Segoe UI", 10, "bold"), bg="white").grid(row=0, column=2, padx=5)
    fecha_hasta = SelectorFecha(frm_fechas)
    fecha_hasta.grid(row=0, column=3, padx=5)
    fecha_hasta.widget_entrada.delete(0, tk.END)
    fecha_hasta.widget_entrada.insert(0, date.today().strftime("%d/%m/%Y"))
    
    # Fila 2: Tipo y Motivo
    frm_tipo = tk.Frame(frm_filtros, bg="white")
    frm_tipo.pack(fill="x", pady=5)
    
    tk.Label(frm_tipo, text="Tipo:", font=("Segoe UI", 10, "bold"), bg="white").grid(row=0, column=0, padx=5)
    cb_tipo = ttk.Combobox(frm_tipo, values=["(Todos)", "Ingreso", "Egreso"], state="readonly", width=15)
    cb_tipo.current(0)
    cb_tipo.grid(row=0, column=1, padx=5)
    
    tk.Label(frm_tipo, text="Motivo:", font=("Segoe UI", 10, "bold"), bg="white").grid(row=0, column=2, padx=5)
    motivos = [
        "(Todos)",
        "apertura_caja",
        "venta_efectivo",
        "pago_cuenta_corriente_efectivo",
        "pago_proveedor",
        "gasto_vario",
        "retiro_caja",
        "devolucion_efectivo",
        "ajuste_positivo",
        "ajuste_negativo",
        "otro"
    ]
    cb_motivo = ttk.Combobox(frm_tipo, values=motivos, state="readonly", width=25)
    cb_motivo.current(0)
    cb_motivo.grid(row=0, column=3, padx=5)
    
    # Fila 3: Usuario (solo si es Admin/Supervisor)
    frm_usuario = tk.Frame(frm_filtros, bg="white")
    frm_usuario.pack(fill="x", pady=5)
    
    usuarios_list = []
    cb_usuario = None
    
    if tiene_permiso(usuario, 'ver_caja_todos'):
        tk.Label(frm_usuario, text="Usuario:", font=("Segoe UI", 10, "bold"), bg="white").grid(row=0, column=0, padx=5)
        
        # Obtener lista de usuarios
        try:
            usuarios_list = backend.obtener_usuarios_con_rol()
            nombres_usuarios = ["(Todos)"] + [u['nombre'] for u in usuarios_list]
        except:
            nombres_usuarios = ["(Todos)"]
        
        cb_usuario = ttk.Combobox(frm_usuario, values=nombres_usuarios, state="readonly", width=20)
        cb_usuario.current(0)
        cb_usuario.grid(row=0, column=1, padx=5)
    
    # Botón Buscar
    def buscar():
        cargar_movimientos()
    
    tk.Button(frm_filtros, text="🔎 BUSCAR", command=buscar, 
              bg="#2563eb", fg="white", font=("Segoe UI", 11, "bold"), 
              width=15).pack(pady=10)
    
    # =================================================================
    # TABLA DE MOVIMIENTOS
    # =================================================================
    frm_tabla = ttk.LabelFrame(body, text="📊 Movimientos Registrados", padding=10)
    frm_tabla.pack(fill="both", expand=True)
    
    # Scrollbar
    scroll_y = ttk.Scrollbar(frm_tabla)
    scroll_y.pack(side="right", fill="y")
    
    # Treeview
    columnas = ("ID", "Fecha", "Usuario", "Tipo", "Motivo", "Monto", "Medio", "Descripción")
    tree = ttk.Treeview(frm_tabla, columns=columnas, show="headings", 
                        yscrollcommand=scroll_y.set, height=15)
    tree.pack(fill="both", expand=True)
    scroll_y.config(command=tree.yview)
    
    # Configurar columnas
    tree.heading("ID", text="ID Mov.")
    tree.heading("Fecha", text="Fecha/Hora")
    tree.heading("Usuario", text="Usuario")
    tree.heading("Tipo", text="Tipo")
    tree.heading("Motivo", text="Motivo")
    tree.heading("Monto", text="Monto")
    tree.heading("Medio", text="Medio")
    tree.heading("Descripción", text="Descripción")
    
    tree.column("ID", width=60, anchor="center")
    tree.column("Fecha", width=140, anchor="center")
    tree.column("Usuario", width=120)
    tree.column("Tipo", width=80, anchor="center")
    tree.column("Motivo", width=180)
    tree.column("Monto", width=100, anchor="e")
    tree.column("Medio", width=100, anchor="center")
    tree.column("Descripción", width=300)
    
    # Colores alternados
    tree.tag_configure('ingreso', background='#d1fae5')  # Verde claro
    tree.tag_configure('egreso', background='#fee2e2')   # Rojo claro
    
    # =================================================================
    # CARGAR DATOS
    # =================================================================
    def cargar_movimientos():
        """Carga los movimientos de caja según filtros"""
        # Limpiar tabla
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            # Obtener filtros
            desde = fecha_desde.get_date_sql()
            hasta = fecha_hasta.get_date_sql()
            
            tipo_sel = cb_tipo.get()
            tipo_filtro = None if tipo_sel == "(Todos)" else tipo_sel.lower()
            
            motivo_sel = cb_motivo.get()
            motivo_filtro = None if motivo_sel == "(Todos)" else motivo_sel
            
            usuario_filtro = None
            if cb_usuario and tiene_permiso(usuario, 'ver_caja_todos'):
                idx = cb_usuario.current()
                if idx > 0:  # No es "(Todos)"
                    usuario_filtro = usuarios_list[idx - 1]['id_usuario']
            
            # Llamar al backend
            movimientos = backend.obtener_historial_movimientos_caja(
                fecha_desde=desde,
                fecha_hasta=hasta,
                tipo=tipo_filtro,
                motivo=motivo_filtro,
                id_usuario=usuario_filtro
            )
            
            # Totales
            total_ingresos = 0.0
            total_egresos = 0.0
            
            # Llenar tabla
            for mov in movimientos:
                tipo_mov = mov['tipo']
                monto = float(mov['monto'])
                
                # Calcular totales
                if tipo_mov == 'ingreso':
                    total_ingresos += monto
                    tag = 'ingreso'
                    tipo_texto = "➕ INGRESO"
                else:
                    total_egresos += monto
                    tag = 'egreso'
                    tipo_texto = "➖ EGRESO"
                
                valores = (
                    mov['id_movimiento'],
                    mov['fecha_hora'],
                    mov['usuario_nombre'] or f"ID {mov['id_usuario']}",
                    tipo_texto,
                    mov['motivo'].replace('_', ' ').title(),
                    _fmt(monto),
                    mov['medio'].title(),
                    mov['descripcion'] or '-'
                )
                
                tree.insert("", tk.END, values=valores, tags=(tag,))
            
            # Mostrar resumen
            lbl_resumen.config(
                text=f"Total Ingresos: {_fmt(total_ingresos)} | "
                     f"Total Egresos: {_fmt(total_egresos)} | "
                     f"Diferencia: {_fmt(total_ingresos - total_egresos)}"
            )
            
        except Exception as e:
            logger.error(f"Error cargando movimientos: {e}")
            messagebox.showerror("Error", f"No se pudieron cargar los movimientos:\n{e}")
    
    # =================================================================
    # FOOTER CON RESUMEN
    # =================================================================
    frm_footer = tk.Frame(body, bg="#e0f2fe", pady=10, relief="solid", bd=1)
    frm_footer.pack(fill="x", pady=(10, 0))
    
    lbl_resumen = tk.Label(frm_footer, text="Total Ingresos: $ 0.00 | Total Egresos: $ 0.00 | Diferencia: $ 0.00",
                           font=("Segoe UI", 12, "bold"), bg="#e0f2fe", fg="#1e40af")
    lbl_resumen.pack()
    
    # =================================================================
    # REDIRECCION A HISTORIALES (Doble clic)
    # =================================================================
    def redirigir_a_historial(event):
        """Redirige al historial correspondiente según el motivo"""
        sel = tree.selection()
        if not sel:
            return
        
        # Obtener datos del movimiento
        item_id = tree.index(sel[0])
        movimiento = None
        
        try:
            # Obtener el movimiento original de la lista cargada
            desde = fecha_desde.get_date_sql()
            hasta = fecha_hasta.get_date_sql()
            
            tipo_sel = cb_tipo.get()
            tipo_filtro = None if tipo_sel == "(Todos)" else tipo_sel.lower()
            
            motivo_sel = cb_motivo.get()
            motivo_filtro = None if motivo_sel == "(Todos)" else motivo_sel
            
            usuario_filtro = None
            if cb_usuario and tiene_permiso(usuario, 'ver_caja_todos'):
                idx = cb_usuario.current()
                if idx > 0:
                    usuario_filtro = usuarios_list[idx - 1]['id_usuario']
            
            movimientos = backend.obtener_historial_movimientos_caja(
                fecha_desde=desde,
                fecha_hasta=hasta,
                tipo=tipo_filtro,
                motivo=motivo_filtro,
                id_usuario=usuario_filtro
            )
            
            if item_id < len(movimientos):
                movimiento = movimientos[item_id]
        except Exception as e:
            logger.error(f"Error obteniendo movimiento: {e}")
            return
        
        if not movimiento:
            return
        
        motivo = movimiento['motivo']
        id_venta = movimiento.get('id_venta')
        id_compra = movimiento.get('id_compra')
        id_cliente = movimiento.get('id_cliente')
        
        # Importar módulo de historiales
        try:
            from app.frontend.interfaz_historiales import Historiales
        except ImportError:
            messagebox.showinfo("No disponible", "Módulo de historiales no integrado.", parent=win)
            return
        
        # Redirigir según el tipo de movimiento
        if motivo == 'venta_efectivo' and id_venta:
            # Abrir historial de ventas filtrado por esta venta
            Historiales(win, backend, usuario, tab_inicial=0, filtro_venta_id=id_venta)
            
        elif motivo == 'pago_proveedor' and id_compra:
            # Abrir historial de compras filtrado por esta compra
            Historiales(win, backend, usuario, tab_inicial=1, filtro_compra_id=id_compra)
            
        elif motivo == 'pago_cuenta_corriente_efectivo' and id_cliente:
            # Abrir historial de pagos filtrado por este cliente
            Historiales(win, backend, usuario, tab_inicial=2, filtro_cliente_id=id_cliente)
            
        else:
            # Para movimientos manuales, mostrar detalle
            valores = tree.item(sel[0])['values']
            detalle = f"""
📋 DETALLE DEL MOVIMIENTO MANUAL

ID: {valores[0]}
Fecha/Hora: {valores[1]}
Usuario: {valores[2]}
Tipo: {valores[3]}
Motivo: {valores[4]}
Monto: {valores[5]}
Medio de Pago: {valores[6]}

Descripción:
{valores[7]}

ℹ️ Este es un movimiento manual.
No tiene transacción asociada.
            """
            messagebox.showinfo("Detalle de Movimiento", detalle.strip(), parent=win)
    
    tree.bind("<Double-1>", redirigir_a_historial)
    
    # =================================================================
    # BOTÓN EXPORTAR (Futuro)
    # =================================================================
    # frm_acciones = tk.Frame(body, bg="#f4f4f8")
    # frm_acciones.pack(fill="x", pady=(10, 0))
    # 
    # tk.Button(frm_acciones, text="📄 Exportar a Excel", 
    #           bg="#16a34a", fg="white", font=("bold", 10),
    #           command=lambda: messagebox.showinfo("Próximamente", "Función en desarrollo")).pack(side="right")
    
    # Init
    configurar_navegacion_ventana(win)
    cargar_movimientos()  # Carga inicial
    
    win.grab_set()