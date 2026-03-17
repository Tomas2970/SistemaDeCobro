# app/frontend/interfaz_crear_usuario.py
# 🎯 ACTUALIZADO: Estética moderna unificada
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Any
import logging 

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

logger = logging.getLogger(__name__)

class CrearEditarUsuario:
    def __init__(self, parent: tk.Misc, backend, usuario_existente: Optional[dict] = None, callback_on_save: Optional[callable] = None):
        self.parent = parent
        self.backend = backend
        self.usuario_existente = usuario_existente
        self.callback_on_save = callback_on_save
        
        self.win = tk.Toplevel(parent)
        self.win.config(bg="#f4f4f8")
        self.win.geometry("500x450")  # Tamaño fijo
        self.win.resizable(False, False)

        self.roles_map: dict[str, int] = {}
        
        self.crear_widgets()
        self.cargar_datos_iniciales()
        
        configurar_navegacion_ventana(self.win)
        
        self.win.after(50, lambda: self.entry_nombre.focus_set())
        self.win.grab_set()
        self.win.transient(parent)

    def crear_widgets(self):
        # Título
        titulo = "Editar Usuario" if self.usuario_existente else "Crear Nuevo Usuario"
        self.win.title(titulo)
        
        tk.Label(
            self.win, 
            text=titulo, 
            bg="#f4f4f8", 
            font=("Segoe UI", 14, "bold"), 
            fg="#1f2937"
        ).pack(pady=(20, 10))

        frame = tk.Frame(self.win, bg="#f4f4f8")
        frame.pack(padx=30, pady=10, fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        # Validación: Límite 20 chars
        def check_user(t): return len(t) <= 20
        vc_user = (self.win.register(check_user), '%P')

        row = 0
        
        # CAMPO NOMBRE
        tk.Label(
            frame, 
            text="👤 Nombre (*):", 
            bg="#f4f4f8", 
            font=("Segoe UI", 10)
        ).grid(row=row, column=0, sticky="e", pady=8, padx=(0, 10))
        
        self.var_nombre = tk.StringVar()
        self.entry_nombre = tk.Entry(
            frame, 
            textvariable=self.var_nombre, 
            width=30, 
            font=("Segoe UI", 10),
            validate="key", 
            validatecommand=vc_user
        )
        self.entry_nombre.grid(row=row, column=1, sticky="ew", pady=8)
        row += 1

        # CAMPO ROL
        tk.Label(
            frame, 
            text="🎭 Rol (*):", 
            bg="#f4f4f8", 
            font=("Segoe UI", 10)
        ).grid(row=row, column=0, sticky="e", pady=8, padx=(0, 10))
        
        self.combo_rol = ttk.Combobox(
            frame, 
            state="readonly", 
            width=28, 
            font=("Segoe UI", 10)
        )
        self.combo_rol.grid(row=row, column=1, sticky="ew", pady=8)
        row += 1
        
        if self.usuario_existente:
            # MODO EDICIÓN: Botón resetear contraseña
            self.btn_reset_pass = tk.Button(
                frame, 
                text="🔑 Resetear Contraseña", 
                command=self.resetear_password, 
                bg="#f59e0b", 
                fg="white", 
                font=("Segoe UI", 9, "bold"),
                relief="flat", 
                padx=15, 
                pady=8,
                cursor="hand2"
            )
            self.btn_reset_pass.grid(row=row, column=1, sticky="w", pady=10)
            row += 1
        
        else:
            # MODO CREACIÓN: Campos de contraseña
            tk.Label(
                frame, 
                text="🔒 Contraseña (*):", 
                bg="#f4f4f8", 
                font=("Segoe UI", 10)
            ).grid(row=row, column=0, sticky="e", pady=8, padx=(0, 10))
            
            self.var_pass1 = tk.StringVar()
            self.entry_pass1 = tk.Entry(
                frame, 
                textvariable=self.var_pass1, 
                width=30, 
                show="*", 
                font=("Segoe UI", 10),
                validate="key", 
                validatecommand=vc_user
            )
            self.entry_pass1.grid(row=row, column=1, sticky="ew", pady=8)
            row += 1
            
            tk.Label(
                frame, 
                text="🔒 Confirmar (*):", 
                bg="#f4f4f8", 
                font=("Segoe UI", 10)
            ).grid(row=row, column=0, sticky="e", pady=8, padx=(0, 10))
            
            self.var_pass2 = tk.StringVar()
            self.entry_pass2 = tk.Entry(
                frame, 
                textvariable=self.var_pass2, 
                width=30, 
                show="*", 
                font=("Segoe UI", 10),
                validate="key", 
                validatecommand=vc_user
            )
            self.entry_pass2.grid(row=row, column=1, sticky="ew", pady=8)
            row += 1

            self.var_mostrar = tk.BooleanVar(value=False)
            self.chk_mostrar = tk.Checkbutton(
                frame, 
                text="Mostrar contraseña", 
                variable=self.var_mostrar, 
                command=self.toggle_password, 
                bg="#f4f4f8",
                font=("Segoe UI", 9)
            )
            self.chk_mostrar.grid(row=row, column=1, sticky="w", pady=5)
            row += 1

        # FRAME BOTONES
        btn_frame = tk.Frame(self.win, bg="#f4f4f8")
        btn_frame.pack(pady=20)
        
        texto_guardar = "💾 Actualizar Usuario" if self.usuario_existente else "💾 Crear Usuario"
        
        self.btn_guardar = tk.Button(
            btn_frame, 
            text=texto_guardar, 
            command=self.guardar, 
            bg="#16a34a", 
            fg="white", 
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            width=20
        )
        self.btn_guardar.pack(side=tk.LEFT, padx=10)
        
        self.btn_cancelar = tk.Button(
            btn_frame, 
            text="Cancelar", 
            command=self.win.destroy, 
            bg="#6b7280", 
            fg="white", 
            font=("Segoe UI", 10),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            width=15
        )
        self.btn_cancelar.pack(side=tk.LEFT, padx=10)

    def toggle_password(self):
        show_char = "" if self.var_mostrar.get() else "*"
        if hasattr(self, 'entry_pass1'): self.entry_pass1.config(show=show_char)
        if hasattr(self, 'entry_pass2'): self.entry_pass2.config(show=show_char)

    def cargar_datos_iniciales(self):
        try:
            roles = self.backend.obtener_roles()
            self.roles_map = {r.get('nombre'): r.get('id_rol') for r in roles}
            self.combo_rol["values"] = list(self.roles_map.keys())
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los roles: {e}", parent=self.win)
            self.win.destroy()
            return
            
        if self.usuario_existente:
            self.var_nombre.set(self.usuario_existente.get('nombre', ''))
            rol_nombre_actual = self.usuario_existente.get('rol_nombre', '')
            if rol_nombre_actual in self.roles_map:
                self.combo_rol.set(rol_nombre_actual)
        else:
            if self.combo_rol["values"]: 
                self.combo_rol.current(0)

    def guardar(self):
        nombre = self.var_nombre.get().strip()
        rol_nombre = self.combo_rol.get()
        
        if not nombre or not rol_nombre:
            messagebox.showwarning("Campos vacíos", "Nombre y Rol son obligatorios.", parent=self.win)
            return
            
        id_rol = self.roles_map.get(rol_nombre)
        
        try:
            if self.usuario_existente:
                id_usuario = self.usuario_existente.get('id_usuario')
                
                ok_rol_nombre = self.backend.actualizar_rol_usuario(
                    id_usuario, 
                    id_rol, 
                    nuevo_nombre=nombre
                )
                
                if ok_rol_nombre:
                    messagebox.showinfo("Éxito", f"Usuario '{nombre}' actualizado.", parent=self.win)
                    if self.callback_on_save: 
                        self.callback_on_save()
                    self.win.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo actualizar el usuario.", parent=self.win)
            else:
                pass1 = self.var_pass1.get()
                pass2 = self.var_pass2.get()
                
                if not pass1 or not pass2:
                    messagebox.showwarning("Campos vacíos", "La contraseña es obligatoria.", parent=self.win)
                    return
                if pass1 != pass2:
                    messagebox.showwarning("Error", "Las contraseñas no coinciden.", parent=self.win)
                    return
                
                nuevo_id = self.backend.crear_usuario(nombre, pass1, id_rol)
                if nuevo_id:
                    messagebox.showinfo("Éxito", f"Usuario '{nombre}' creado.", parent=self.win)
                    if self.callback_on_save: 
                        self.callback_on_save()
                    self.win.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo crear (¿Nombre duplicado?).", parent=self.win)

        except ValueError as ve:
            if "NOMBRE_DUPLICADO" in str(ve):
                messagebox.showerror(
                    "Error de Duplicado", 
                    f"El nombre de usuario '{nombre}' ya existe.", 
                    parent=self.win
                )
            else:
                messagebox.showerror("Error", f"Error de Validación:\n{ve}", parent=self.win)
        
        except Exception as e:
            logger.exception("Error al guardar usuario")
            messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado:\n{e}", parent=self.win)

    def resetear_password(self):
        if not self.usuario_existente: return
        id_usuario = self.usuario_existente.get('id_usuario')
        nombre = self.usuario_existente.get('nombre')
        
        nueva_pass = simpledialog.askstring(
            "Resetear Contraseña", 
            f"Ingrese la NUEVA contraseña para '{nombre}':", 
            parent=self.win, 
            show="*"
        )
        if not nueva_pass: return
        
        try:
            ok = self.backend.resetear_password_usuario(id_usuario, nueva_pass)
            if ok: 
                messagebox.showinfo("Éxito", "Contraseña actualizada.", parent=self.win)
            else: 
                messagebox.showerror("Error", "No se pudo actualizar.", parent=self.win)
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}", parent=self.win)

def ui_crear_usuario(parent: tk.Misc, backend, id_usuario_a_editar=None, callback_on_save=None):
    usuario_existente = None
    if id_usuario_a_editar:
        users = backend.obtener_usuarios_con_rol()
        usuario_existente = next((u for u in users if u['id_usuario'] == id_usuario_a_editar), None)
    
    CrearEditarUsuario(parent, backend, usuario_existente, callback_on_save=callback_on_save)