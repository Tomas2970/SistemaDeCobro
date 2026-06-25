# app/frontend/interfaz_auditoria.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog
import customtkinter as ctk
import json
import csv
from datetime import datetime, timedelta
from typing import Optional

from app.frontend import custom_dialogs as messagebox
from app.frontend.theme_config import get_color, preparar_ventana, centrar_y_mostrar_ventana, aplicar_tema_ventana, configurar_estilo_treeview
from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
from app.frontend.componentes_ui import SelectorFecha

MAPEO_ACCIONES = {
    "CREAR_USUARIO": "➕ Usuario creado",
    "DESACTIVAR_USUARIO": "❌ Usuario desactivado",
    "REACTIVAR_USUARIO": "♻️ Usuario reactivado",
    "RESETEAR_PASSWORD": "🔑 Contraseña restablecida",
    "MODIFICAR_USUARIO": "✏️ Usuario modificado",
    "CREAR_PRODUCTO": "➕ Producto creado",
    "MODIFICAR_PRODUCTO": "✏️ Producto modificado",
    "DESACTIVAR_PRODUCTO": "❌ Producto desactivado",
    "AJUSTE_STOCK_MANUAL": "📦 Ajuste de stock",
    "CREAR_CLIENTE": "➕ Cliente creado",
    "MODIFICAR_LIMITE_CREDITO_CLIENTE": "💳 Límite de crédito modificado",
    "DESACTIVAR_CLIENTE": "❌ Cliente desactivado",
    "REACTIVAR_CLIENTE": "♻️ Cliente reactivado",
    "CREAR_PROVEEDOR": "➕ Proveedor creado",
    "DESACTIVAR_PROVEEDOR": "❌ Proveedor desactivado",
    "REACTIVAR_PROVEEDOR": "♻️ Proveedor reactivado",
    "CIERRE_CAJA_SUPERVISOR": "🔒 Cierre forzado de caja",
    "CIERRE_CAJA": "🔒 Cierre de caja",
    "EXPORTAR_HISTORIAL": "📤 Exportación de historial",
}

INV_MAPEO_ACCIONES = {v: k for k, v in MAPEO_ACCIONES.items()}

class InterfazAuditoria:
    def __init__(self, parent, backend, usuario_actual: dict):
        self.parent = parent
        self.backend = backend
        self.usuario_actual = usuario_actual
        
        # Colores
        self.col_bg = get_color("bg_root")
        self.col_card = get_color("bg_surface")
        self.col_text = get_color("text_primary")
        self.col_border = "#2d3748"
        
        self.win = ctk.CTkToplevel(parent)
        preparar_ventana(self.win)
        self.win.title("Bitácora del Sistema")
        self.win.geometry("1200x750")
        self.win.minsize(1050, 650)
        
        configurar_estilo_treeview()
        
        self.pag_size = 50
        self.pag_aud = 0
        self.total_aud = 0
        
        self.crear_widgets()
        self.cargar_filtros()
        self.cargar_datos()
        
        configurar_navegacion_ventana(self.win)
        self.win.transient(parent)
        centrar_y_mostrar_ventana(self.win)
        self.win.grab_set()

    def crear_widgets(self):
        # Título
        ctk.CTkLabel(self.win, text="🔒 Bitácora de Auditoría Administrativa", font=("Segoe UI", 20, "bold"), text_color=self.col_text).pack(pady=(20, 10))
        
        # --- FILTROS ---
        frame_filtros = ctk.CTkFrame(self.win, fg_color=self.col_card, corner_radius=10, border_color=self.col_border, border_width=1)
        frame_filtros.pack(fill="x", padx=20, pady=10)
        
        # Primera fila de filtros
        row1 = ctk.CTkFrame(frame_filtros, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(row1, text="Usuario:", font=("Segoe UI", 12)).pack(side="left", padx=(10, 5))
        self.combo_usuario = ctk.CTkOptionMenu(row1, width=150, font=("Segoe UI", 12))
        self.combo_usuario.pack(side="left", padx=5)
        
        ctk.CTkLabel(row1, text="Acción:", font=("Segoe UI", 12)).pack(side="left", padx=(20, 5))
        self.combo_accion = ctk.CTkOptionMenu(row1, width=250, font=("Segoe UI", 12))
        self.combo_accion.pack(side="left", padx=5)
        
        ctk.CTkLabel(row1, text="Desde:", font=("Segoe UI", 12)).pack(side="left", padx=(20, 5))
        self.entry_desde = SelectorFecha(row1)
        self.entry_desde.pack(side="left", padx=5)
        
        ctk.CTkLabel(row1, text="Hasta:", font=("Segoe UI", 12)).pack(side="left", padx=(20, 5))
        self.entry_hasta = SelectorFecha(row1)
        self.entry_hasta.pack(side="left", padx=5)
        
        # Segunda fila de botones
        row2 = ctk.CTkFrame(frame_filtros, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(5, 10))
        
        # Atajos de fecha
        ctk.CTkButton(row2, text="Hoy", command=self.atajo_hoy, width=80, fg_color="#4b5563", hover_color="#374151").pack(side="left", padx=(10, 5))
        ctk.CTkButton(row2, text="Últimos 7 días", command=self.atajo_7dias, width=120, fg_color="#4b5563", hover_color="#374151").pack(side="left", padx=5)
        ctk.CTkButton(row2, text="Este mes", command=self.atajo_mes, width=100, fg_color="#4b5563", hover_color="#374151").pack(side="left", padx=5)
        
        # Acciones de filtrado y exportación
        self.btn_exportar = ctk.CTkButton(row2, text="📄 Exportar CSV", command=self.exportar_csv, width=130, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 12, "bold"))
        self.btn_exportar.pack(side="right", padx=(10, 10))
        
        self.btn_limpiar = ctk.CTkButton(row2, text="🧹 Limpiar", command=self.limpiar_filtros, width=100, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 12))
        self.btn_limpiar.pack(side="right", padx=5)
        
        self.btn_filtrar = ctk.CTkButton(row2, text="🔍 Aplicar Filtros", command=self.cargar_datos, width=140, fg_color="#3b82f6", hover_color="#2563eb", font=("Segoe UI", 12, "bold"))
        self.btn_filtrar.pack(side="right", padx=5)
        
        # --- TABLA ---
        frame_tabla = ctk.CTkFrame(self.win, fg_color=self.col_card, corner_radius=10, border_color=self.col_border, border_width=1)
        frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        cols = ("Fecha", "Usuario", "Acción", "Entidad", "Resumen")
        self.tree = ttk.Treeview(frame_tabla, columns=cols, show="headings", style="Modern.Treeview")
        
        self.tree.heading("Fecha", text="Fecha")
        self.tree.column("Fecha", width=140, anchor="center")
        
        self.tree.heading("Usuario", text="Usuario")
        self.tree.column("Usuario", width=150)
        
        self.tree.heading("Acción", text="Acción")
        self.tree.column("Acción", width=250)
        
        self.tree.heading("Entidad", text="Entidad")
        self.tree.column("Entidad", width=150, anchor="center")
        
        self.tree.heading("Resumen", text="Resumen")
        self.tree.column("Resumen", width=350)
        
        # Configurar colores de tags para temas claros (o ajustables). CustomTkinter + ttk treeview a veces necesita colores base.
        self.tree.tag_configure("tag_create", background="#e6f4ea", foreground="#000000")
        self.tree.tag_configure("tag_update", background="#e8f0fe", foreground="#000000")
        self.tree.tag_configure("tag_delete", background="#fce8e6", foreground="#000000")
        self.tree.tag_configure("tag_sensitive", background="#fef0d9", foreground="#000000")
        
        self.tree.bind("<Double-1>", self.mostrar_detalle_evento)
        
        ys = ctk.CTkScrollbar(frame_tabla, command=self.tree.yview)
        ys.pack(side="right", fill="y", padx=2, pady=5)
        self.tree.configure(yscrollcommand=ys.set)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Estructura para guardar datos crudos asociados al row id
        self.datos_crudos_tree = {}
        
        # --- PAGINACION ---
        frm_pag_aud = ctk.CTkFrame(self.win, fg_color="transparent")
        frm_pag_aud.pack(fill="x", padx=20, pady=(0, 10))
        
        btn_prev_aud = ctk.CTkButton(frm_pag_aud, text="Anterior", width=80, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), command=self._prev_page_aud)
        btn_prev_aud.pack(side="left", padx=5)
        
        self.lbl_pag_aud = ctk.CTkLabel(frm_pag_aud, text="Página 1", font=("Segoe UI", 12))
        self.lbl_pag_aud.pack(side="left", padx=10)
        
        btn_next_aud = ctk.CTkButton(frm_pag_aud, text="Siguiente", width=80, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), command=self._next_page_aud)
        btn_next_aud.pack(side="left", padx=5)

        # --- BOTONES INFERIORES ---
        frame_btns = ctk.CTkFrame(self.win, fg_color="transparent")
        frame_btns.pack(fill="x", padx=20, pady=(0, 20))
        
        self.btn_cerrar = ctk.CTkButton(frame_btns, text="Cerrar", command=self.win.destroy, fg_color="#4b5563", hover_color="#374151", width=120, font=("Segoe UI", 13, "bold"))
        self.btn_cerrar.pack(side="right")
        
    def atajo_hoy(self):
        hoy = datetime.now()
        self._set_selector_fecha(self.entry_desde, hoy)
        self._set_selector_fecha(self.entry_hasta, hoy)

    def atajo_7dias(self):
        hoy = datetime.now()
        hace_7 = hoy - timedelta(days=7)
        self._set_selector_fecha(self.entry_desde, hace_7)
        self._set_selector_fecha(self.entry_hasta, hoy)

    def atajo_mes(self):
        hoy = datetime.now()
        primero = hoy.replace(day=1)
        self._set_selector_fecha(self.entry_desde, primero)
        self._set_selector_fecha(self.entry_hasta, hoy)
        
    def _set_selector_fecha(self, selector, fecha):
        if hasattr(selector.entrada, 'set_date'):
            selector.entrada.set_date(fecha)
        else:
            selector.entrada.delete(0, tk.END)
            selector.entrada.insert(0, fecha.strftime("%d/%m/%Y"))
        
    def cargar_filtros(self):
        try:
            # Cargar Usuarios
            usuarios = self.backend.obtener_usuarios_con_rol()
            nombres = ["Todos"] + [u['nombre'] for u in usuarios]
            self.combo_usuario.configure(values=nombres)
            self.combo_usuario.set("Todos")
            
            # Mapeo id_usuario para buscar
            self.map_usuarios = {u['nombre']: u['id_usuario'] for u in usuarios}
            
            # Cargar Acciones (amigables)
            acciones_amigables = ["Todas"] + list(MAPEO_ACCIONES.values())
            self.combo_accion.configure(values=acciones_amigables)
            self.combo_accion.set("Todas")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando filtros: {e}", parent=self.win)
            
    def limpiar_filtros(self):
        self.combo_usuario.set("Todos")
        self.combo_accion.set("Todas")
        if hasattr(self.entry_desde.entrada, 'set_date'):
            # tkcalendar's DateEntry doesn't have an empty state easily, so we set to today
            self._set_selector_fecha(self.entry_desde, datetime.now())
            self._set_selector_fecha(self.entry_hasta, datetime.now())
        else:
            self.entry_desde.entrada.delete(0, tk.END)
            self.entry_hasta.entrada.delete(0, tk.END)
        self.cargar_datos()
        
    def procesar_resumen(self, accion: str, ant: str, nue: str) -> str:
        if not nue and not ant: return "Sin detalles"
        
        try:
            d_ant = json.loads(ant) if ant else {}
            d_nue = json.loads(nue) if nue else {}
            
            if accion == "MODIFICAR_LIMITE_CREDITO_CLIENTE":
                o = d_ant.get('limite_credito', 0)
                n = d_nue.get('limite_credito', 0)
                return f"Límite: ${o:,.2f} → ${n:,.2f}"
            
            if accion == "MODIFICAR_PRODUCTO":
                o = d_ant.get('precio_venta', '')
                n = d_nue.get('precio_venta', '')
                if str(o) != str(n):
                    return f"Precio: ${o} → ${n}"
                return "Datos de producto modificados"
                
            if accion == "AJUSTE_STOCK_MANUAL":
                cant_ant = d_ant.get('cantidad', 0)
                cant_nue = d_nue.get('cantidad', 0)
                diff = cant_nue - cant_ant
                signo = "+" if diff > 0 else ""
                return f"Stock: {cant_ant} → {cant_nue} ({signo}{diff})"
                
            if accion == "CREAR_USUARIO":
                return f"Rol asignado: #{d_nue.get('id_rol', '?')}"
                
            if accion == "RESETEAR_PASSWORD":
                return "Contraseña restablecida"
                
            if accion == "MODIFICAR_USUARIO":
                rol_o = d_ant.get('id_rol')
                rol_n = d_nue.get('id_rol')
                if rol_o != rol_n:
                    return f"Rol: {rol_o} → {rol_n}"
                return "Datos de usuario modificados"

            if accion in ("CIERRE_CAJA", "CIERRE_CAJA_SUPERVISOR"):
                if 'diferencia' in d_nue and 'contado' in d_nue:
                    return f"Diferencia: ${d_nue['diferencia']:,.2f} | Contado: ${d_nue['contado']:,.2f}"
                if 'cerrado_por' in d_nue:
                    return f"Cerrado por #{d_nue['cerrado_por']} - Motivo: {d_nue.get('motivo', '')}"
                
            # Fallback a conteo de campos modificados
            cambios = 0
            for k, v in d_nue.items():
                if k in d_ant and d_ant[k] != v:
                    cambios += 1
                elif k not in d_ant:
                    cambios += 1
            if cambios > 0:
                return f"Se modificaron {cambios} campos."
                
            # Si no detectamos cambios, intentamos mostrar algo
            keys = list(d_nue.keys())
            if keys:
                return f"Actualizado: {', '.join(keys)}"
            
            return "Modificación registrada"
        except:
            return "Datos complejos"

    def determinar_tag_accion(self, accion: str) -> str:
        if accion.startswith("CREAR"): return "tag_create"
        if accion.startswith("DESACTIVAR"): return "tag_delete"
        if accion.startswith("CIERRE") or "LIMITE" in accion: return "tag_sensitive"
        return "tag_update" # Por defecto azul para modificaciones/reactivaciones/ajustes

    def validar_y_convertir_fecha(self, fecha_str: str) -> Optional[str]:
        if not fecha_str.strip():
            return None
        try:
            dt = datetime.strptime(fecha_str.strip(), "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Formato de fecha inválido: {fecha_str}. Use dd/mm/aaaa.")

    def cargar_datos(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.datos_crudos_tree.clear()
            
        usr_sel = self.combo_usuario.get()
        acc_sel = self.combo_accion.get()
        desde_str = self.entry_desde.get_date_str()
        hasta_str = self.entry_hasta.get_date_str()
        
        id_user = self.map_usuarios.get(usr_sel) if usr_sel != "Todos" else None
        
        # Mapear accion amigable a tecnica
        accion_tecnica = None
        if acc_sel != "Todas":
            accion_tecnica = INV_MAPEO_ACCIONES.get(acc_sel, acc_sel)
            
        try:
            fecha_desde = self.validar_y_convertir_fecha(desde_str)
            fecha_hasta = self.validar_y_convertir_fecha(hasta_str)
            
            if fecha_desde and fecha_hasta:
                if fecha_desde > fecha_hasta:
                    messagebox.showwarning("Fechas Inválidas", "La fecha 'Desde' no puede ser mayor que 'Hasta'.", parent=self.win)
                    return
        except ValueError as ve:
            messagebox.showwarning("Error de Formato", str(ve), parent=self.win)
            return
            
        try:
            limit = self.pag_size
            offset = self.pag_aud * self.pag_size
            self.total_aud = self.backend.contar_bitacora_acciones(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, id_usuario=id_user, accion=accion_tecnica)
            registros = self.backend.obtener_bitacora_acciones(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, id_usuario=id_user, accion=accion_tecnica, limit=limit, offset=offset)
            
            for r in registros:
                fecha = str(r.get('fecha'))[:16] # "2024-01-01 15:30"
                usr = r.get('usuario_nombre') or 'Sistema'
                acc = r.get('accion') or 'Desconocida'
                tabla = r.get('tabla_afectada') or ''
                id_reg = r.get('id_registro') or ''
                entidad = f"{tabla} #{id_reg}" if id_reg else tabla
                
                acc_amigable = MAPEO_ACCIONES.get(acc, acc)
                resumen = self.procesar_resumen(acc, r.get('datos_anteriores'), r.get('datos_nuevos'))
                
                resumen_corto = resumen
                if len(resumen) > 60:
                    resumen_corto = resumen[:57] + "..."
                
                tag = self.determinar_tag_accion(acc)
                
                item_id = self.tree.insert("", tk.END, values=(fecha, usr, acc_amigable, entidad, resumen_corto), tags=(tag,))
                
                # Guardamos los datos crudos para el doble clic
                self.datos_crudos_tree[item_id] = {
                    "fecha": fecha,
                    "usuario": usr,
                    "accion": acc_amigable,
                    "entidad": entidad,
                    "datos_anteriores": r.get('datos_anteriores'),
                    "datos_nuevos": r.get('datos_nuevos')
                }
                
            if hasattr(self, 'lbl_pag_aud'):
                tot_pages = max(1, (self.total_aud + self.pag_size - 1) // self.pag_size)
                self.lbl_pag_aud.configure(text=f"Página {self.pag_aud + 1} de {tot_pages} ({self.total_aud} registros)")
                
        except Exception as e:
            logger.error(f"Error cargar_datos auditoria: {e}")
            messagebox.showerror("Error", f"Ocurrió un error al cargar datos:\n{e}", parent=self.win)

    def _prev_page_aud(self):
        if self.pag_aud > 0:
            self.pag_aud -= 1
            self.cargar_datos()
            
    def _next_page_aud(self):
        tot_pages = max(1, (self.total_aud + self.pag_size - 1) // self.pag_size)
        if self.pag_aud < tot_pages - 1:
            self.pag_aud += 1
            self.cargar_datos()

    def mostrar_detalle_evento(self, event):
        item_id = self.tree.focus()
        if not item_id: return
        
        datos = self.datos_crudos_tree.get(item_id)
        if not datos: return
        
        modal = ctk.CTkToplevel(self.win)
        preparar_ventana(modal)
        modal.title("Detalle del Evento")
        modal.geometry("500x500")
        modal.transient(self.win)
        centrar_y_mostrar_ventana(modal)
        modal.grab_set()
        
        ctk.CTkLabel(modal, text="🔍 Detalle Completo", font=("Segoe UI", 18, "bold"), text_color=self.col_text).pack(pady=10)
        
        frame_info = ctk.CTkFrame(modal, fg_color="transparent")
        frame_info.pack(fill="x", padx=20, pady=5)
        
        def add_info_row(parent, label, value):
            r = ctk.CTkFrame(parent, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=label, font=("Segoe UI", 12, "bold"), width=80, anchor="w", text_color=self.col_text).pack(side="left")
            ctk.CTkLabel(r, text=value, font=("Segoe UI", 12), anchor="w", justify="left", text_color=self.col_text).pack(side="left", fill="x", expand=True)

        add_info_row(frame_info, "Evento:", datos["accion"])
        add_info_row(frame_info, "Usuario:", datos["usuario"])
        add_info_row(frame_info, "Fecha:", datos["fecha"])
        add_info_row(frame_info, "Entidad:", datos["entidad"])
        
        ctk.CTkLabel(modal, text="Cambios realizados:", font=("Segoe UI", 14, "bold"), anchor="w", text_color=self.col_text).pack(fill="x", padx=20, pady=(15, 5))
        
        txt_cambios = ctk.CTkTextbox(modal, font=("Consolas", 12), fg_color=self.col_card, text_color=self.col_text, border_color=self.col_border, border_width=1)
        txt_cambios.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Formatear cambios
        try:
            d_ant = json.loads(datos["datos_anteriores"]) if datos["datos_anteriores"] else {}
            d_nue = json.loads(datos["datos_nuevos"]) if datos["datos_nuevos"] else {}
            
            lineas = []
            todas_claves = set(list(d_ant.keys()) + list(d_nue.keys()))
            
            if not todas_claves:
                lineas.append("No hay detalles adicionales.")
            else:
                map_id_to_user = {v: k for k, v in getattr(self, 'map_usuarios', {}).items()}
                map_id_to_rol = {1: 'Administrador', 2: 'Vendedor', 3: 'Supervisor'}
                
                nombres_amigables = {
                    "cerrado_por": "Cerrado por",
                    "id_usuario": "Usuario",
                    "abierto_por": "Abierto por",
                    "autorizado_por": "Autorizado por",
                    "motivo": "Motivo",
                    "estado": "Estado",
                    "monto": "Monto",
                    "fecha_apertura": "Fecha de apertura",
                    "fecha_cierre": "Fecha de cierre",
                    "id_rol": "Rol",
                    "id_producto": "Producto",
                    "id_categoria": "Categoría",
                    "limite_credito": "Límite de crédito",
                    "precio_venta": "Precio de venta",
                    "precio_compra": "Precio de compra",
                    "stock_minimo": "Stock mínimo",
                    "codigo_barras": "Código de barras",
                    "descripcion": "Descripción"
                }

                def resolver_valor(clave, valor):
                    if valor is None:
                        return valor
                    
                    if clave in ("cerrado_por", "id_usuario", "abierto_por", "autorizado_por"):
                        try:
                            return map_id_to_user.get(int(valor), valor)
                        except (ValueError, TypeError):
                            pass
                    
                    if clave in ("id_rol", "rol_id"):
                        try:
                            return map_id_to_rol.get(int(valor), valor)
                        except (ValueError, TypeError):
                            pass
                    
                    if clave in ("id_producto", "producto_id"):
                        try:
                            p = self.backend.buscar_producto_por_id(int(valor))
                            if p and p.get("nombre"):
                                return p["nombre"]
                        except Exception:
                            pass
                            
                    if clave in ("id_categoria", "categoria_id"):
                        try:
                            c = self.backend.obtener_categoria_por_id(int(valor))
                            if c and c.get("nombre"):
                                return c["nombre"]
                        except Exception:
                            pass
                    
                    return valor

                for k in sorted(todas_claves):
                    v_ant = d_ant.get(k)
                    v_nue = d_nue.get(k)
                    
                    v_ant_res = resolver_valor(k, v_ant)
                    v_nue_res = resolver_valor(k, v_nue)
                    
                    k_amigable = nombres_amigables.get(k, k.replace('_', ' ').capitalize())
                    
                    if v_ant_res != v_nue_res:
                        es_tecnico = k.startswith("id_") and k not in nombres_amigables
                        es_sin_valor_ant = (k not in d_ant) or (v_ant_res is None or str(v_ant_res).strip() == "")
                        es_sin_valor_nue = (k not in d_nue) or (v_nue_res is None or str(v_nue_res).strip() == "")
                        
                        if es_sin_valor_ant and es_tecnico:
                            continue
                            
                        str_ant = "—" if es_sin_valor_ant else str(v_ant_res)
                        str_nue = "—" if es_sin_valor_nue else str(v_nue_res)
                        
                        if str_ant != str_nue:
                            lineas.append(f"{k_amigable}:\n{str_ant} → {str_nue}\n")
            
            txt_cambios.insert("1.0", "\n".join(lineas))
        except Exception as e:
            txt_cambios.insert("1.0", f"Error procesando JSON: {e}\n\nDatos Ant:\n{datos['datos_anteriores']}\n\nDatos Nue:\n{datos['datos_nuevos']}")
            
        txt_cambios.configure(state="disabled")
        
        ctk.CTkButton(modal, text="Cerrar", command=modal.destroy, fg_color="#4b5563", hover_color="#374151", width=100).pack(pady=15)

    def exportar_csv(self):
        usr_sel = self.combo_usuario.get()
        acc_sel = self.combo_accion.get()
        desde_str = self.entry_desde.get_date_str()
        hasta_str = self.entry_hasta.get_date_str()
        
        id_user = self.map_usuarios.get(usr_sel) if usr_sel != "Todos" else None
        accion_tecnica = None
        if acc_sel != "Todas":
            accion_tecnica = INV_MAPEO_ACCIONES.get(acc_sel, acc_sel)
            
        try:
            fecha_desde = self.validar_y_convertir_fecha(desde_str)
            fecha_hasta = self.validar_y_convertir_fecha(hasta_str)
        except ValueError as ve:
            messagebox.showwarning("Error de Formato", str(ve), parent=self.win)
            return

        filepath = filedialog.asksaveasfilename(
            parent=self.win,
            title="Exportar CSV Completo",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"auditoria_completa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not filepath: return
        
        def _do_export():
            try:
                registros = self.backend.obtener_bitacora_acciones(
                    fecha_desde=fecha_desde, 
                    fecha_hasta=fecha_hasta, 
                    id_usuario=id_user, 
                    accion=accion_tecnica,
                    limit=100000, # Maximos registros exportables de un golpe
                    offset=0
                )
                
                if not registros:
                    if self.win.winfo_exists():
                        self.win.after(0, lambda: messagebox.showinfo("Exportar", "No hay datos para exportar con los filtros actuales.", parent=self.win))
                    return

                with open(filepath, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Fecha", "Usuario", "Acción", "Entidad", "Resumen"])
                    
                    for r in registros:
                        fecha = str(r.get('fecha'))[:16]
                        usr = r.get('usuario_nombre') or 'Sistema'
                        acc = r.get('accion') or 'Desconocida'
                        tabla = r.get('tabla_afectada') or ''
                        id_reg = r.get('id_registro') or ''
                        entidad = f"{tabla} #{id_reg}" if id_reg else tabla
                        acc_amigable = MAPEO_ACCIONES.get(acc, acc)
                        resumen = self.procesar_resumen(acc, r.get('datos_anteriores'), r.get('datos_nuevos'))
                        writer.writerow([fecha, usr, acc_amigable, entidad, resumen])
                        
                if self.win.winfo_exists():
                    self.win.after(0, lambda: messagebox.showinfo("Éxito", "Exportación completada correctamente.", parent=self.win))
            except Exception as e:
                if self.win.winfo_exists():
                    self.win.after(0, lambda: messagebox.showerror("Error", f"Ocurrió un error al exportar:\n{e}", parent=self.win))

        import threading
        threading.Thread(target=_do_export, daemon=True).start()

def ui_auditoria(parent, backend, usuario_actual):
    InterfazAuditoria(parent, backend, usuario_actual)
