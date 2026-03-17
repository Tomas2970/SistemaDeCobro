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
    EntryDecimal = ttk.Entry
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

try:
    from app.database.permisos import tiene_permiso
except ImportError:
    def tiene_permiso(usuario, accion): return True

logger = logging.getLogger(__name__)

def _fmt_porcentaje(val: Any) -> str:
    try: return f"{float(val):.2f} %"
    except: return "0.00 %"

class UIManageCategorias:
    def __init__(self, parent: tk.Misc, backend, usuario: dict):
        self.backend = backend
        self.usuario = usuario
        self.can_manage = tiene_permiso(self.usuario, 'gestionar_categorias')
        
        self.win = Toplevel(parent)
        self.win.title("🏷️ Gestión de Categorías")
        self.win.geometry("750x550")
        self.win.config(bg="#f4f4f8")
        self.win.resizable(False, False)
        self.win.grab_set()
        
        self.ventana_edicion_abierta = False

        # 🔥 ESTILOS MODERNOS
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

        self._crear_widgets()
        self.cargar_categorias()
        
        configurar_navegacion_ventana(self.win, confirmar_cierre=True)
        self.win.after(100, lambda: self.tree.focus_set())

    def _crear_widgets(self):
        # 🔥 HEADER
        frm_header = tk.Frame(self.win, bg="#ffffff", pady=15)
        frm_header.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(
            frm_header,
            text="Listado de Categorías",
            font=("Segoe UI", 14, "bold"),
            bg="#ffffff",
            fg="#1f2937"
        ).pack()

        # 🔥 TABLA MODERNA
        frm_tabla = tk.Frame(self.win, bg="#f4f4f8", padx=10, pady=10)
        frm_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("ID", "Nombre", "Margen (%)", "Pesable")
        self.tree = ttk.Treeview(frm_tabla, columns=cols, show="headings", style="Modern.Treeview")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(frm_tabla, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Margen (%)", text="Margen Sugerido")
        self.tree.heading("Pesable", text="¿Es Pesable?")
        
        self.tree.column("ID", width=0, minwidth=0, stretch=False)
        self.tree.column("Nombre", width=280)
        self.tree.column("Margen (%)", width=120, anchor="e")
        self.tree.column("Pesable", width=100, anchor="center")

        # 🔥 BOTONES ESTILO NUEVO
        frame_btns = tk.Frame(self.win, bg="#f4f4f8")
        frame_btns.pack(pady=15)

        btn_nueva = tk.Button(
            frame_btns, 
            text="+ Nueva Categoría", 
            command=lambda: self._abrir_editor(None),
            bg="#10b981",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground="#059669",
            activeforeground="white",
            width=18
        )
        btn_nueva.pack(side=tk.LEFT, padx=10)
        
        btn_editar = tk.Button(
            frame_btns, 
            text="✎ Editar", 
            command=self._editar_seleccionado,
            bg="#3b82f6",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground="#2563eb",
            activeforeground="white",
            width=15
        )
        btn_editar.pack(side=tk.LEFT, padx=10)
        
        btn_eliminar = tk.Button(
            frame_btns, 
            text="× Eliminar", 
            command=self._eliminar_seleccionado,
            bg="#ef4444",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground="#dc2626",
            activeforeground="white",
            width=15
        )
        btn_eliminar.pack(side=tk.LEFT, padx=10)

        tk.Button(
            frame_btns,
            text="Cerrar",
            command=self.win.destroy,
            bg="#64748b",
            fg="white",
            font=("Segoe UI", 10),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=10)

        if not self.can_manage:
            btn_nueva.config(state=tk.DISABLED, bg="#d1d5db", cursor="arrow")
            btn_editar.config(state=tk.DISABLED, bg="#d1d5db", cursor="arrow")
            btn_eliminar.config(state=tk.DISABLED, bg="#d1d5db", cursor="arrow")
        else:
            self.tree.bind("<Double-1>", lambda e: self._editar_seleccionado())

    def cargar_categorias(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            categorias = self.backend.obtener_categorias()
            self.categorias_cache = {c['id_categoria']: c for c in categorias}
            
            for cat in categorias:
                pesable_txt = "SI" if cat.get('es_pesable_default') else "NO"
                
                self.tree.insert("", tk.END, iid=cat['id_categoria'], 
                                 values=(
                                     cat['id_categoria'],
                                     cat['nombre'],
                                     _fmt_porcentaje(cat.get('margen_ganancia')),
                                     pesable_txt
                                 ))
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando categorías: {e}", parent=self.win)

    def _editar_seleccionado(self):
        if not self.can_manage: return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una categoría.", parent=self.win)
            return
        
        id_cat = int(sel[0])
        cat_data = self.categorias_cache.get(id_cat)
        
        if cat_data:
            self._abrir_editor(cat_data)

    def _eliminar_seleccionado(self):
        if not self.can_manage: return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una categoría.", parent=self.win)
            return
        
        id_cat = int(sel[0])
        cat_data = self.categorias_cache.get(id_cat)
        if not cat_data: return
        
        nombre = cat_data.get('nombre', '')
        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar la categoría '{nombre}'?\n\nEsta acción no se puede deshacer.",
            parent=self.win
        )
        if not confirmar: return
        
        try:
            exito = self.backend.eliminar_categoria(id_cat)
            if exito:
                messagebox.showinfo("Éxito", f"Categoría '{nombre}' eliminada.", parent=self.win)
                self.cargar_categorias()
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo eliminar la categoría.\nProbablemente tiene productos asociados.",
                    parent=self.win
                )
        except Exception as e:
            if "foreign key" in str(e).lower() or "1451" in str(e):
                messagebox.showerror(
                    "No se puede eliminar",
                    f"La categoría '{nombre}' tiene productos asociados.\nReasigná los productos antes de eliminarla.",
                    parent=self.win
                )
            else:
                messagebox.showerror("Error", f"Error al eliminar: {e}", parent=self.win)

    def _abrir_editor(self, categoria: dict | None = None):
        if self.ventana_edicion_abierta: return
        self.ventana_edicion_abierta = True
        
        pop = Toplevel(self.win)
        pop.title("Editar Categoría" if categoria else "Nueva Categoría")
        pop.geometry("400x350")
        pop.config(bg="#f4f4f8")
        pop.resizable(False, False)

        def on_close():
            self.ventana_edicion_abierta = False
            pop.destroy()
        pop.protocol("WM_DELETE_WINDOW", on_close)
        
        # 🔥 FORMULARIO MODERNO
        frm = tk.Frame(pop, bg="#ffffff", padx=25, pady=25)
        frm.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(frm, text="Nombre:", bg="#ffffff", font=("Segoe UI", 10)).pack(pady=(10, 5), anchor="w")
        ent_nom = tk.Entry(frm, width=35, font=("Segoe UI", 10))
        ent_nom.pack(fill=tk.X)
        if categoria: ent_nom.insert(0, categoria['nombre'])
        
        tk.Label(frm, text="Margen de Ganancia (%):", bg="#ffffff", font=("Segoe UI", 10)).pack(pady=(15, 5), anchor="w")
        ent_mar = EntryDecimal(frm, width=15)
        ent_mar.pack(anchor="w")
        val_margen = str(categoria['margen_ganancia']) if categoria else "30.00"
        ent_mar.insert(0, val_margen)

        var_pesable = tk.BooleanVar(value=False)
        if categoria:
            var_pesable.set(bool(categoria.get('es_pesable_default', False)))
            
        chk = tk.Checkbutton(
            frm, 
            text="Productos son pesables (Kg)", 
            variable=var_pesable, 
            bg="#ffffff",
            font=("Segoe UI", 10)
        )
        chk.pack(pady=15, anchor="w")

        def guardar():
            nom = ent_nom.get().strip()
            try: mar = float(ent_mar.get())
            except: 
                messagebox.showerror("Error", "Margen inválido", parent=pop); return
            if not nom:
                messagebox.showerror("Error", "Nombre obligatorio", parent=pop); return
            if mar < 0:
                messagebox.showerror("Error", "Margen negativo no permitido.", parent=pop); return
                
            try:
                exito = False
                if categoria:
                    exito = self.backend.actualizar_categoria(categoria['id_categoria'], nom, mar, var_pesable.get())
                    if exito:
                        messagebox.showinfo("Éxito", "Categoría actualizada.", parent=pop)
                else:
                    exito = self.backend.crear_categoria(nom, mar, var_pesable.get())
                    if exito:
                        messagebox.showinfo("Éxito", "Categoría creada.", parent=pop)
                
                if exito:
                    self.cargar_categorias()
                    on_close()
                else:
                    messagebox.showerror("Error", "No se pudo guardar en la base de datos.", parent=pop)

            except Exception as e:
                messagebox.showerror("Error", f"Excepción al guardar: {e}", parent=pop)

        # 🔥 BOTÓN GUARDAR
        tk.Button(
            frm, 
            text="✓ Guardar", 
            command=guardar,
            bg="#10b981",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=25,
            pady=10,
            cursor="hand2",
            activebackground="#059669"
        ).pack(pady=20)
        
        configurar_navegacion_ventana(pop)
        pop.transient(self.win)
        pop.grab_set()
        ent_nom.focus_set()
        self.win.wait_window(pop)

def ui_categorias(parent: tk.Misc, backend, usuario: dict):
    UIManageCategorias(parent, backend, usuario)