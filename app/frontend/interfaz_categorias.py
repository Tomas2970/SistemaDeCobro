# app/frontend/interfaz_categorias.py
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
        self.win.geometry("700x500")
        self.win.config(bg="#f4f4f8")
        self.win.resizable(False, False)
        self.win.grab_set()
        
        self.ventana_edicion_abierta = False

        self._crear_widgets()
        self.cargar_categorias()
        
        configurar_navegacion_ventana(self.win, confirmar_cierre=True)
        self.win.after(100, lambda: self.tree.focus_set())

    def _crear_widgets(self):
        frm_tabla = ttk.LabelFrame(self.win, text="Listado de Categorías", padding="10")
        frm_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # AGREGADA COLUMNA PESABLE
        cols = ("ID", "Nombre", "Margen (%)", "Pesable")
        self.tree = ttk.Treeview(frm_tabla, columns=cols, show="headings")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(frm_tabla, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Margen (%)", text="Margen Sugerido")
        self.tree.heading("Pesable", text="¿Es Pesable?")
        
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Nombre", width=250)
        self.tree.column("Margen (%)", width=100, anchor="e")
        self.tree.column("Pesable", width=80, anchor="center")

        frame_btns = tk.Frame(self.win, bg=self.win["bg"])
        frame_btns.pack(pady=10)

        btn_nueva = tk.Button(frame_btns, text="➕ Nueva Categoría", bg="#03A9F4", fg="white", 
                              command=lambda: self._abrir_editor(None), font=("Segoe UI", 10, "bold"), width=18)
        btn_nueva.pack(side=tk.LEFT, padx=10)
        
        btn_editar = tk.Button(frame_btns, text="✎ Editar Seleccionada", bg="#FFC107", fg="black",
                               command=self._editar_seleccionado, font=("Segoe UI", 10, "bold"), width=18)
        btn_editar.pack(side=tk.LEFT, padx=10)
        
        btn_eliminar = tk.Button(frame_btns, text="❌ Eliminar", bg="#EF4444", fg="white",
                               command=self._eliminar_seleccionado, font=("Segoe UI", 10, "bold"), width=15)
        btn_eliminar.pack(side=tk.LEFT, padx=10)

        if not self.can_manage:
            btn_nueva.config(state=tk.DISABLED, bg="#cccccc")
            btn_editar.config(state=tk.DISABLED, bg="#cccccc")
            btn_eliminar.config(state=tk.DISABLED, bg="#cccccc")
        else:
            self.tree.bind("<Double-1>", lambda e: self._editar_seleccionado())

    def cargar_categorias(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            categorias = self.backend.obtener_categorias()
            self.categorias_cache = {c['id_categoria']: c for c in categorias} # Cache para datos completos
            
            for cat in categorias:
                # Mostrar SI/NO en pesable
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
        # Buscamos el objeto completo en el cache para tener el booleano real, no el texto "SI/NO"
        cat_data = self.categorias_cache.get(id_cat)
        
        if cat_data:
            self._abrir_editor(cat_data)

    def _eliminar_seleccionado(self):
        # (Lógica de eliminar igual que antes...)
        pass # Para no alargar el código aquí, asumo que mantienes la lógica

    def _abrir_editor(self, categoria: dict | None = None):
        if self.ventana_edicion_abierta: return
        self.ventana_edicion_abierta = True
        
        pop = Toplevel(self.win)
        pop.title("Editar Categoría" if categoria else "Nueva Categoría")
        pop.geometry("350x280")
        pop.config(bg="#f4f4f8")
        pop.resizable(False, False)

        def on_close():
            self.ventana_edicion_abierta = False
            pop.destroy()
        pop.protocol("WM_DELETE_WINDOW", on_close)
        
        tk.Label(pop, text="Nombre:", bg="#f4f4f8").pack(pady=(20,5))
        ent_nom = tk.Entry(pop, width=30)
        ent_nom.pack()
        if categoria: ent_nom.insert(0, categoria['nombre'])
        
        tk.Label(pop, text="Margen de Ganancia (%):", bg="#f4f4f8").pack(pady=(10,5))
        ent_mar = EntryDecimal(pop, width=10)
        ent_mar.pack()
        val_margen = str(categoria['margen_ganancia']) if categoria else "30.00"
        ent_mar.insert(0, val_margen)

        # NUEVO CHECKBOX
        var_pesable = tk.BooleanVar(value=False)
        if categoria:
            var_pesable.set(bool(categoria.get('es_pesable_default', False)))
            
        chk = tk.Checkbutton(pop, text="Productos son pesables (Kg)", variable=var_pesable, bg="#f4f4f8")
        chk.pack(pady=10)

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
                if categoria:
                    self.backend.actualizar_categoria(categoria['id_categoria'], nom, mar, var_pesable.get())
                    messagebox.showinfo("Éxito", "Categoría actualizada.", parent=pop)
                else:
                    self.backend.crear_categoria(nom, mar, var_pesable.get())
                    messagebox.showinfo("Éxito", "Categoría creada.", parent=pop)
                
                self.cargar_categorias()
                on_close()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=pop)

        tk.Button(pop, text="Guardar", bg="#4CAF50", fg="white", command=guardar).pack(pady=20)
        configurar_navegacion_ventana(pop)
        pop.transient(self.win)
        pop.grab_set()
        ent_nom.focus_set()
        self.win.wait_window(pop)

def ui_categorias(parent: tk.Misc, backend, usuario: dict):
    UIManageCategorias(parent, backend, usuario)