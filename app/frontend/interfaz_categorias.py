# app/frontend/interfaz_categorias.py
# 🎨 ACTUALIZADO: Estilo de botones unificado
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from typing import Any
import logging

try:
    from app.frontend.componentes_ui import EntryDecimal
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    EntryDecimal = None  # Se resolverá al importar ctk dentro de __init__
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

try:
    from app.database.permisos import tiene_permiso
except ImportError:
    def tiene_permiso(usuario, accion): return True

try:
    from app.frontend.theme_config import preparar_ventana, centrar_y_mostrar_ventana
except ImportError:
    def preparar_ventana(w): pass
    def centrar_y_mostrar_ventana(w): pass

logger = logging.getLogger(__name__)

def _fmt_porcentaje(val: Any) -> str:
    try: return f"{float(val):.2f} %"
    except: return "0.00 %"

class UIManageCategorias:
    def __init__(self, parent: tk.Misc, backend, usuario: dict):
        self.backend = backend
        self.usuario = usuario
        self.can_manage = tiene_permiso(self.usuario, 'gestionar_categorias')
        self.ventana_edicion_abierta = False
        
        import customtkinter as ctk
        from app.frontend.theme_config import get_color, configurar_estilo_treeview
        
        # 🔥 CARGA DE ESTILOS Y COLORES
        configurar_estilo_treeview()
        self.col_bg = get_color("bg_root")
        self.col_card = get_color("bg_surface")
        self.col_text = get_color("text_primary")
        self.col_input_bg = "#374151"
        self.col_input_fg = "#ffffff"
        self.col_border = "#2d3748"

        self.win = ctk.CTkToplevel(parent)
        preparar_ventana(self.win)
        self.win.title("🏷️ Gestión de Categorías")
        self.win.geometry("800x650")
        self.win.resizable(True, True)
        self.win.minsize(700, 500)

        self.var_mostrar_inactivas = tk.BooleanVar(value=False)
        self.categorias_cache = {}

        self._crear_widgets()
        self.cargar_categorias()
        
        configurar_navegacion_ventana(self.win, confirmar_cierre=False)
        centrar_y_mostrar_ventana(self.win)
        self.win.grab_set()
        self.win.after(100, lambda: self.tree.focus_set())

    def _crear_widgets(self):
        import customtkinter as ctk
        # 🔥 HEADER
        frm_header = ctk.CTkFrame(self.win, fg_color=self.col_card, corner_radius=10, border_color=self.col_border, border_width=1)
        frm_header.pack(fill=tk.X, padx=20, pady=(20, 5))
        
        ctk.CTkLabel(frm_header, text="Listado de Categorías", font=("Segoe UI", 15, "bold"), text_color=self.col_text).pack(side=tk.LEFT, padx=20, pady=15)
        
        # Filtro de inactivas
        chk_inactivas = ctk.CTkCheckBox(frm_header, text="Mostrar inactivas", variable=self.var_mostrar_inactivas, command=self.cargar_categorias, font=("Segoe UI", 12))
        chk_inactivas.pack(side=tk.RIGHT, padx=20, pady=15)

        # 🔥 TABLA MODERNA
        frm_tabla = ctk.CTkFrame(self.win, fg_color=self.col_card, corner_radius=10, border_color=self.col_border, border_width=1)
        frm_tabla.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        cols = ("ID", "Nombre", "Margen (%)", "Pesable")
        self.tree = ttk.Treeview(frm_tabla, columns=cols, show="headings", height=6, style="Modern.Treeview")

        vsb = ctk.CTkScrollbar(frm_tabla, command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Margen (%)", text="Margen Sugerido")
        self.tree.heading("Pesable", text="¿Es Pesable?")
        
        self.tree.column("ID", width=0, minwidth=0, stretch=False)
        self.tree.column("Nombre", width=300)
        self.tree.column("Margen (%)", width=180, anchor="center")
        self.tree.column("Pesable", width=120, anchor="center")

        # Configuración de etiqueta visual para filas inactivas (texto atenuado / gris)
        self.tree.tag_configure('inactiva', foreground='#888888')
        
        # 🔥 BOTONES ESTILO NUEVO
        frame_btns = ctk.CTkFrame(self.win, fg_color="transparent")
        frame_btns.pack(pady=(5, 30), fill="x", padx=20)
 
        self.btn_nueva = ctk.CTkButton(frame_btns, text="➕ Nueva", command=lambda: self._abrir_editor(None), fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 13, "bold"), width=110, height=45)
        self.btn_nueva.pack(side=tk.LEFT, padx=(5, 5))
        
        self.btn_editar = ctk.CTkButton(frame_btns, text="✎ Editar", command=self._editar_seleccionado, fg_color="#3b82f6", hover_color="#2563eb", font=("Segoe UI", 13, "bold"), width=100, height=45)
        self.btn_editar.pack(side=tk.LEFT, padx=5)

        self.btn_eliminar = ctk.CTkButton(frame_btns, text="❌ Desactivar", command=self._eliminar_seleccionado, fg_color="#ef4444", hover_color="#dc2626", font=("Segoe UI", 13, "bold"), width=120, height=45)
        self.btn_eliminar.pack(side=tk.LEFT, padx=5)

        self.btn_reactivar = ctk.CTkButton(frame_btns, text="🔄 Reactivar", command=self._reactivar_seleccionado, fg_color="#f59e0b", hover_color="#d97706", font=("Segoe UI", 13, "bold"), width=110, height=45)
        self.btn_reactivar.pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(frame_btns, text="Cerrar", command=self.win.destroy, fg_color="#4b5563", hover_color="#374151", font=("Segoe UI", 13, "bold"), width=90, height=45).pack(side=tk.RIGHT, padx=5)

        if not self.can_manage:
            # Disable buttons if user doesn't have permission
            for child in frame_btns.winfo_children():
                if isinstance(child, ctk.CTkButton) and child.cget("text") != "Cerrar":
                    child.configure(state="disabled", fg_color="#6b7280", hover_color="#6b7280")
        else:
            self.tree.bind("<Double-1>", lambda e: self._editar_seleccionado())
            
            def on_select(event):
                sel = self.tree.selection()
                if not sel:
                    self.btn_eliminar.configure(state="disabled", fg_color="#6b7280", hover_color="#6b7280")
                    self.btn_reactivar.configure(state="disabled", fg_color="#6b7280", hover_color="#6b7280")
                    self.btn_editar.configure(state="disabled", fg_color="#6b7280", hover_color="#6b7280")
                    return
                
                if not hasattr(self, 'categorias_cache') or not self.categorias_cache:
                    return
                
                id_cat = int(sel[0])
                cat_data = self.categorias_cache.get(id_cat)
                if not cat_data: return
                
                self.btn_editar.configure(state="normal", fg_color="#3b82f6", hover_color="#2563eb")
                if cat_data.get('activa', True):
                    self.btn_eliminar.configure(state="normal", fg_color="#ef4444", hover_color="#dc2626")
                    self.btn_reactivar.configure(state="disabled", fg_color="#6b7280", hover_color="#6b7280")
                else:
                    self.btn_eliminar.configure(state="disabled", fg_color="#6b7280", hover_color="#6b7280")
                    self.btn_reactivar.configure(state="normal", fg_color="#f59e0b", hover_color="#d97706")

            self.tree.bind("<<TreeviewSelect>>", on_select)

    def cargar_categorias(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if self.can_manage:
            self.btn_eliminar.configure(state="disabled", fg_color="#6b7280", hover_color="#6b7280")
            self.btn_reactivar.configure(state="disabled", fg_color="#6b7280", hover_color="#6b7280")
            self.btn_editar.configure(state="disabled", fg_color="#6b7280", hover_color="#6b7280")
        try:
            categorias = self.backend.obtener_categorias(self.var_mostrar_inactivas.get())
            self.categorias_cache = {c['id_categoria']: c for c in categorias}
            
            for cat in categorias:
                pesable_txt = "SI" if cat.get('es_pesable_default') else "NO"
                activa = cat.get('activa', True)
                nombre_visual = cat['nombre'] if activa else f"{cat['nombre']} [INACTIVA]"
                tag = () if activa else ('inactiva',)
                
                self.tree.insert("", tk.END, iid=cat['id_categoria'], 
                                 values=(
                                     cat['id_categoria'],
                                     nombre_visual,
                                     _fmt_porcentaje(cat.get('margen_ganancia')),
                                     pesable_txt
                                 ), tags=tag)
        except Exception as e:
            from app.frontend.manejador_errores import ManejadorErroresUI
            ManejadorErroresUI.manejar_error(e, parent=self.win, contexto="categorías")

    def _editar_seleccionado(self):
        if not self.can_manage: return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Categoría Requerida", "Por favor, selecciona una categoría de la lista para poder editarla.", parent=self.win)
            return
        
        id_cat = int(sel[0])
        cat_data = self.categorias_cache.get(id_cat)
        
        if cat_data:
            self._abrir_editor(cat_data)

    def _eliminar_seleccionado(self):
        if not self.can_manage: return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Categoría Requerida", "Por favor, selecciona una categoría de la lista para poder desactivarla.", parent=self.win)
            return
        
        id_cat = int(sel[0])
        cat_data = self.categorias_cache.get(id_cat)
        if not cat_data: return
        
        nombre = cat_data['nombre']
        
        confirmar = messagebox.askyesno(
            "Confirmar Desactivación",
            f"¿Estás seguro de que deseas desactivar la categoría '{nombre}'?\n\nLos productos e historiales existentes no se verán afectados, pero no podrás asignar esta categoría a nuevos productos.",
            parent=self.win
        )
        if not confirmar: return
        
        try:
            exito = self.backend.eliminar_categoria(id_cat, id_usuario=self.usuario.get('id_usuario'))
            if exito:
                messagebox.showinfo("Éxito", f"Categoría '{nombre}' desactivada correctamente.", parent=self.win)
                self.cargar_categorias()
            else:
                from app.frontend.manejador_errores import ManejadorErroresUI
                ManejadorErroresUI.manejar_error(Exception("No se pudo desactivar la categoría. Asegúrate de que no tenga productos asociados."), parent=self.win, contexto=nombre)
        except Exception as e:
            from app.frontend.manejador_errores import ManejadorErroresUI
            ManejadorErroresUI.manejar_error(e, parent=self.win, contexto=nombre)

    def _reactivar_seleccionado(self):
        if not self.can_manage: return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Categoría Requerida", "Por favor, selecciona una categoría de la lista para poder reactivarla.", parent=self.win)
            return
        
        id_cat = int(sel[0])
        cat_data = self.categorias_cache.get(id_cat)
        if not cat_data: return
        
        nombre = cat_data['nombre']
        
        confirmar = messagebox.askyesno(
            "Confirmar Reactivación",
            f"¿Estás seguro de que deseas reactivar la categoría '{nombre}'?",
            parent=self.win
        )
        if not confirmar: return
        
        try:
            exito = self.backend.reactivar_categoria(id_cat, id_usuario=self.usuario.get('id_usuario'))
            if exito:
                messagebox.showinfo("Éxito", f"Categoría '{nombre}' reactivada correctamente.", parent=self.win)
                self.cargar_categorias()
            else:
                from app.frontend.manejador_errores import ManejadorErroresUI
                ManejadorErroresUI.manejar_error(Exception("No se pudo reactivar la categoría."), parent=self.win, contexto=nombre)
        except Exception as e:
            from app.frontend.manejador_errores import ManejadorErroresUI
            ManejadorErroresUI.manejar_error(e, parent=self.win, contexto=nombre)

    def _abrir_editor(self, categoria: dict | None = None):
        if self.ventana_edicion_abierta: return
        self.ventana_edicion_abierta = True
        
        import customtkinter as ctk
        pop = ctk.CTkToplevel(self.win)
        preparar_ventana(pop)
        pop.title("Editar Categoría" if categoria else "Nueva Categoría")
        pop.geometry("450x450")
        pop.resizable(False, False)
 
        def on_close():
            self.ventana_edicion_abierta = False
            pop.destroy()
        pop.protocol("WM_DELETE_WINDOW", on_close)
        
        # 🔥 FORMULARIO MODERNO
        frm = ctk.CTkFrame(pop, fg_color=self.col_card, corner_radius=10, border_color=self.col_border, border_width=1)
        frm.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        ctk.CTkLabel(frm, text="Nombre de Categoría:", font=("Segoe UI", 13, "bold"), text_color=self.col_text).pack(pady=(20, 5), padx=20, anchor="w")
        ent_nom = ctk.CTkEntry(frm, font=("Segoe UI", 12), height=40)
        ent_nom.pack(fill="x", padx=20)
        if categoria: ent_nom.insert(0, categoria['nombre'])
        
        ctk.CTkLabel(frm, text="Margen de Ganancia Sugerido (%):", font=("Segoe UI", 13, "bold"), text_color=self.col_text).pack(pady=(20, 5), padx=20, anchor="w")
        ent_mar = EntryDecimal(frm, font=("Segoe UI", 12), justify="center", width=150, height=40)
        ent_mar.pack(padx=20, anchor="w")
        val_margen = str(categoria['margen_ganancia']) if categoria else "30.00"
        ent_mar.insert(0, val_margen)
 
        var_pesable = tk.BooleanVar(value=False)
        if categoria:
            var_pesable.set(bool(categoria.get('es_pesable_default', False)))
            
        chk = ctk.CTkCheckBox(frm, text="Productos son pesables (Kg) por defecto", variable=var_pesable, font=("Segoe UI", 12), checkbox_width=22, checkbox_height=22)
        chk.pack(pady=25, padx=20, anchor="w")
 
        def guardar():
            nom = ent_nom.get().strip()
            try: mar = float(ent_mar.get())
            except: 
                messagebox.showwarning("Margen Inválido", "Por favor, ingresa un valor numérico decimal válido para el margen de ganancia.", parent=pop)
                return
            if not nom:
                messagebox.showwarning("Nombre Requerido", "El campo Nombre de Categoría es obligatorio.", parent=pop)
                return
            if mar < 0:
                messagebox.showwarning("Margen Inválido", "El margen de ganancia sugerido no puede ser menor a cero.", parent=pop)
                return
                
            try:
                exito = False
                if categoria:
                    exito = self.backend.actualizar_categoria(categoria['id_categoria'], nom, mar, var_pesable.get())
                    if exito:
                        messagebox.showinfo("Éxito", f"Categoría '{nom}' actualizada correctamente.", parent=pop)
                else:
                    exito = self.backend.crear_categoria(nom, mar, var_pesable.get())
                    if exito:
                        messagebox.showinfo("Éxito", f"Categoría '{nom}' creada correctamente.", parent=pop)
                
                if exito:
                    self.cargar_categorias()
                    on_close()
                else:
                    from app.frontend.manejador_errores import ManejadorErroresUI
                    ManejadorErroresUI.manejar_error(Exception("No se pudo guardar la categoría en la base de datos."), parent=pop, contexto=nom)
 
            except Exception as e:
                from app.frontend.manejador_errores import ManejadorErroresUI
                ManejadorErroresUI.manejar_error(e, parent=pop, contexto=nom)
 
        # 🔥 BOTÓN GUARDAR
        ctk.CTkButton(frm, text="✓ Guardar Categoría", command=guardar, fg_color="#10b981", hover_color="#059669", font=("Segoe UI", 15, "bold"), height=50).pack(pady=10, fill="x", padx=20)
        
        configurar_navegacion_ventana(pop)
        pop.transient(self.win)
        centrar_y_mostrar_ventana(pop)
        pop.grab_set()
        ent_nom.focus_set()
        self.win.wait_window(pop)

def ui_categorias(parent: tk.Misc, backend, usuario: dict):
    UIManageCategorias(parent, backend, usuario)