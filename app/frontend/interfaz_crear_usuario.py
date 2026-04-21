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

import customtkinter as ctk
from app.frontend.theme_config import get_color, aplicar_tema_ventana

logger = logging.getLogger(__name__)

class CrearEditarUsuario:
    def __init__(self, parent: tk.Misc, backend, usuario_existente: Optional[dict] = None, callback_on_save: Optional[callable] = None):
        
        self.parent = parent
        self.backend = backend
        self.usuario_existente = usuario_existente
        self.callback_on_save = callback_on_save
        
        # 🔥 COLORES GLOBALES
        self.col_bg = get_color("bg_root")
        self.col_card = get_color("bg_surface")
        self.col_text = get_color("text_primary")
        self.col_input_bg = "#374151"
        self.col_input_fg = "#ffffff"
        self.col_border = "#2d3748"

        self.win = ctk.CTkToplevel(parent)
        self.win.configure(fg_color=self.col_bg)
        self.win.geometry("550x550") 
        self.win.resizable(False, False)
        aplicar_tema_ventana(self.win)

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
        
        ctk.CTkLabel(self.win, text=titulo, font=("Segoe UI", 18, "bold"), text_color=self.col_text).pack(pady=(25, 15))

        self.main_frame = ctk.CTkFrame(self.win, fg_color=self.col_card, corner_radius=12, border_color=self.col_border, border_width=1)
        self.main_frame.pack(padx=30, pady=10, fill="both", expand=True)
        self.main_frame.columnconfigure(1, weight=1)

        # Validación: Límite 20 chars
        def check_user(t): return len(t) <= 20
        vc_user = (self.win.register(check_user), '%P')

        row = 0
        
        # CAMPO NOMBRE
        ctk.CTkLabel(self.main_frame, text="👤 Nombre del Usuario:", font=("Segoe UI", 13, "bold"), text_color=self.col_text).grid(row=row, column=0, sticky="e", pady=15, padx=(20, 15))
        
        self.var_nombre = tk.StringVar()
        self.entry_nombre = ctk.CTkEntry(self.main_frame, textvariable=self.var_nombre, font=("Segoe UI", 12), height=40)
        self.entry_nombre.configure(validate="key", validatecommand=vc_user)
        self.entry_nombre.grid(row=row, column=1, sticky="ew", pady=15, padx=(0, 25))
        row += 1

        # CAMPO ROL
        ctk.CTkLabel(self.main_frame, text="🎭 Rol del Sistema:", font=("Segoe UI", 13, "bold"), text_color=self.col_text).grid(row=row, column=0, sticky="e", pady=15, padx=(20, 15))
        
        self.combo_rol = ctk.CTkOptionMenu(self.main_frame, width=200, height=40, dynamic_resizing=False, font=("Segoe UI", 13),
                                          fg_color=get_color("accent_primary"), button_color=get_color("accent_hover"))
        self.combo_rol.set("") # Valor inicial
        self.combo_rol.grid(row=row, column=1, sticky="w", pady=15)
        row += 1
        
        if self.usuario_existente:
            # MODO EDICIÓN: Botón resetear contraseña
            self.btn_reset_pass = ctk.CTkButton(self.main_frame, text="🔑 Resetear Contraseña", command=self.resetear_password_moderno, fg_color="#f59e0b", hover_color="#d97706", font=("Segoe UI", 12, "bold"), height=40)
            self.btn_reset_pass.grid(row=row, column=1, sticky="w", pady=15)
            row += 1
        
        else:
            # MODO CREACIÓN: Campos de contraseña
            ctk.CTkLabel(self.main_frame, text="🔒 Contraseña (*):", font=("Segoe UI", 13, "bold"), text_color=self.col_text).grid(row=row, column=0, sticky="e", pady=15, padx=(20, 15))
            
            self.var_pass1 = tk.StringVar()
            self.entry_pass1 = ctk.CTkEntry(self.main_frame, textvariable=self.var_pass1, show="*", font=("Segoe UI", 12), width=250, height=40)
            self.entry_pass1.grid(row=row, column=1, sticky="w", pady=15)
            row += 1
            
            ctk.CTkLabel(self.main_frame, text="🔒 Confirmar (*):", font=("Segoe UI", 13, "bold"), text_color=self.col_text).grid(row=row, column=0, sticky="e", pady=15, padx=(20, 15))
            
            self.var_pass2 = tk.StringVar()
            self.entry_pass2 = ctk.CTkEntry(self.main_frame, textvariable=self.var_pass2, show="*", font=("Segoe UI", 12), width=250, height=40)
            self.entry_pass2.grid(row=row, column=1, sticky="w", pady=15)
            row += 1

            self.var_mostrar = tk.BooleanVar(value=False)
            self.chk_mostrar = ctk.CTkCheckBox(self.main_frame, text="Mostrar contraseña", variable=self.var_mostrar, command=self.toggle_password, font=("Segoe UI", 11))
            self.chk_mostrar.grid(row=row, column=1, sticky="w", pady=5)
            row += 1

        # FRAME BOTONES
        btn_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_frame.pack(pady=25)
        
        texto_guardar = "💾 Actualizar" if self.usuario_existente else "💾 Crear Usuario"
        
        self.btn_guardar = ctk.CTkButton(btn_frame, text=texto_guardar, command=self.guardar, fg_color="#16a34a", hover_color="#15803d", font=("Segoe UI", 14, "bold"), width=180, height=45)
        self.btn_guardar.pack(side="left", padx=10)
        
        self.btn_cancelar = ctk.CTkButton(btn_frame, text="Cancelar", command=self.win.destroy, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 14), width=120, height=45)
        self.btn_cancelar.pack(side="left", padx=10)

    def toggle_password(self):
        show_char = "" if self.var_mostrar.get() else "*"
        if hasattr(self, 'entry_pass1'): self.entry_pass1.configure(show=show_char)
        if hasattr(self, 'entry_pass2'): self.entry_pass2.configure(show=show_char)

    def cargar_datos_iniciales(self):
        try:
            roles = self.backend.obtener_roles()
            self.roles_map = {r.get('nombre'): r.get('id_rol') for r in roles}
            rol_nombres = list(self.roles_map.keys())
            self.combo_rol.configure(values=rol_nombres)
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
            if rol_nombres: 
                self.combo_rol.set(rol_nombres[0])

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

    def resetear_password_moderno(self):
        if not self.usuario_existente: return
        id_usuario = self.usuario_existente.get('id_usuario')
        nombre = self.usuario_existente.get('nombre')
        
        popup = ctk.CTkToplevel(self.win)
        popup.title("🔒 Resetear Contraseña")
        popup.geometry("400x300")
        aplicar_tema_ventana(popup)
        popup.resizable(False, False)
        
        ctk.CTkLabel(popup, text=f"Nueva contraseña para:\n'{nombre}'", font=("Segoe UI", 14, "bold"), text_color=self.col_text).pack(pady=(20, 10))
        
        var_new_pass = tk.StringVar()
        entry_new_pass = ctk.CTkEntry(popup, textvariable=var_new_pass, show="*", font=("Segoe UI", 14), width=300, height=45)
        entry_new_pass.pack(pady=10)
        entry_new_pass.focus_set()
        
        def confirmar():
            p = var_new_pass.get().strip()
            if not p:
                messagebox.showwarning("Atención", "Ingrese una contraseña.", parent=popup)
                return
            try:
                if self.backend.resetear_password_usuario(id_usuario, p):
                    messagebox.showinfo("Éxito", "Contraseña actualizada.", parent=popup)
                    popup.destroy()
                else:
                    messagebox.showerror("Error", "Fallo al actualizar.", parent=popup)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=popup)

        frm_btn = ctk.CTkFrame(popup, fg_color="transparent")
        frm_btn.pack(pady=20)
        
        ctk.CTkButton(frm_btn, text="✓ Confirmar", command=confirmar, fg_color="#16a34a", hover_color="#15803d", font=("Segoe UI", 12, "bold"), height=40).pack(side="left", padx=10)
        ctk.CTkButton(frm_btn, text="Cancelar", command=popup.destroy, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 12), height=40).pack(side="left", padx=10)
        
        entry_new_pass.bind("<Return>", lambda e: confirmar())
        popup.grab_set()
        popup.transient(self.win)

def ui_crear_usuario(parent: tk.Misc, backend, id_usuario_a_editar=None, callback_on_save=None):
    usuario_existente = None
    if id_usuario_a_editar:
        users = backend.obtener_usuarios_con_rol()
        usuario_existente = next((u for u in users if u['id_usuario'] == id_usuario_a_editar), None)
    
    CrearEditarUsuario(parent, backend, usuario_existente, callback_on_save=callback_on_save)