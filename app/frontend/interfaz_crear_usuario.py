# app/frontend/interfaz_crear_usuario.py
# 🎯 ACTUALIZADO: Estética moderna unificada
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from app.frontend import custom_dialogs as messagebox
from typing import Optional, Any
import logging 

try:
    from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana
except ImportError:
    def configurar_navegacion_ventana(win, confirmar_cierre=False): pass

import customtkinter as ctk
from app.frontend.theme_config import get_color, aplicar_tema_ventana, preparar_ventana, centrar_y_mostrar_ventana

logger = logging.getLogger(__name__)

class CrearEditarUsuario:
    def __init__(self, parent: tk.Misc, backend, usuario_existente: Optional[dict] = None, usuario_actual: Optional[dict] = None, callback_on_save: Optional[callable] = None):
        
        self.parent = parent
        self.backend = backend
        self.usuario_existente = usuario_existente
        self.usuario_actual = usuario_actual
        self.callback_on_save = callback_on_save
        
        # 🔥 COLORES GLOBALES
        self.col_bg = get_color("bg_root")
        self.col_card = get_color("bg_surface")
        self.col_text = get_color("text_primary")
        self.col_input_bg = "#374151"
        self.col_input_fg = "#ffffff"
        self.col_border = "#2d3748"

        self.win = ctk.CTkToplevel(parent)
        preparar_ventana(self.win)
        self.win.geometry("550x550") 
        self.win.resizable(False, False)

        self.roles_map: dict[str, int] = {}
        
        self.crear_widgets()
        self.cargar_datos_iniciales()
        
        configurar_navegacion_ventana(self.win)
        self.win.transient(parent)
        centrar_y_mostrar_ventana(self.win)
        self.win.after(50, lambda: self.entry_nombre.focus_set())
        self.win.grab_set()

    def crear_widgets(self):
        # Título
        titulo = "Editar Usuario" if self.usuario_existente else "Crear Nuevo Usuario"
        self.win.title(titulo)
        
        ctk.CTkLabel(self.win, text=titulo, font=("Segoe UI", 18, "bold"), text_color=self.col_text).pack(pady=(25, 15))

        self.main_frame = ctk.CTkFrame(self.win, fg_color=self.col_card, corner_radius=12, border_color=self.col_border, border_width=1)
        self.main_frame.pack(padx=30, pady=10, fill="both", expand=True)
        self.main_frame.columnconfigure(1, weight=1)

        # Validación: Límite 20 chars y alfanumérico
        def check_user(t): 
            from app.frontend.validaciones_ui import ValidadoresTeclado
            return len(t) <= 20 and ValidadoresTeclado.letras_y_numeros(t)
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
        
        # CAMPO CODIGO BARRAS
        ctk.CTkLabel(self.main_frame, text="💳 Código de Barras / Tarjeta:", font=("Segoe UI", 13, "bold"), text_color=self.col_text).grid(row=row, column=0, sticky="e", pady=15, padx=(20, 15))
        
        self.var_codigo_barras = tk.StringVar()
        self.entry_codigo_barras = ctk.CTkEntry(self.main_frame, textvariable=self.var_codigo_barras, font=("Segoe UI", 12), width=250, height=40, placeholder_text="Escanee aquí...")
        self.entry_codigo_barras.grid(row=row, column=1, sticky="w", pady=15)
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
            from app.frontend.manejador_errores import ManejadorErroresUI
            ManejadorErroresUI.manejar_error(e, parent=self.win, contexto="roles")
            self.win.destroy()
            return
            
        if self.usuario_existente:
            self.var_nombre.set(self.usuario_existente.get('nombre', ''))
            self.var_codigo_barras.set(self.usuario_existente.get('codigo_barras') or '')
            rol_nombre_actual = self.usuario_existente.get('rol_nombre', '')
            if rol_nombre_actual in self.roles_map:
                self.combo_rol.set(rol_nombre_actual)
        else:
            if rol_nombres: 
                self.combo_rol.set(rol_nombres[0])

    def guardar(self):
        nombre = self.var_nombre.get().strip()
        rol_nombre = self.combo_rol.get()
        codigo_barras = self.var_codigo_barras.get().strip() or None
        
        from app.frontend.validaciones_ui import ValidadorFormulario
        ok, msg = ValidadorFormulario.validar_campos({'Nombre del Usuario': (nombre, 'nombre', True)})
        if not ok:
            messagebox.showwarning("Campo Inválido", msg, parent=self.win)
            return
            
        if not rol_nombre:
            messagebox.showwarning("Campos Obligatorios", "Por favor, selecciona el Rol del Sistema.", parent=self.win)
            return
            
        id_rol = self.roles_map.get(rol_nombre)
        
        try:
            if self.usuario_existente:
                id_usuario = self.usuario_existente.get('id_usuario')
                rol_actual_nombre = self.usuario_existente.get('rol_nombre')
                
                if rol_nombre != rol_actual_nombre:
                    msg = "Este usuario podría tener una sesión activa. Si cambiás su rol ahora, su sesión se invalidará y perderá cualquier operación en curso. ¿Querés continuar?"
                    if not messagebox.askyesno("Advertencia de Cambio de Rol", msg, parent=self.win):
                        return
                
                ok_rol_nombre = self.backend.actualizar_rol_usuario(
                    id_usuario, 
                    id_rol, 
                    nuevo_nombre=nombre,
                    codigo_barras=codigo_barras
                )
                
                if ok_rol_nombre:
                    messagebox.showinfo("Éxito", f"Usuario '{nombre}' actualizado correctamente.", parent=self.win)
                    if self.callback_on_save: 
                        self.callback_on_save()
                    self.win.destroy()
                else:
                    from app.frontend.manejador_errores import ManejadorErroresUI
                    ManejadorErroresUI.manejar_error(Exception("No se pudo actualizar la información del usuario en el sistema."), parent=self.win, contexto=nombre)
            else:
                pass1 = self.var_pass1.get()
                pass2 = self.var_pass2.get()
                
                if not pass1 or not pass2:
                    messagebox.showwarning("Contraseña Requerida", "Por favor, ingresa y confirma la contraseña para crear el usuario.", parent=self.win)
                    return
                if pass1 != pass2:
                    messagebox.showwarning("Contraseñas no Coincidentes", "Las contraseñas ingresadas no coinciden. Por favor, verifícalas.", parent=self.win)
                    return
                if len(pass1) < 6:
                    messagebox.showwarning("Contraseña Débil", "La contraseña debe tener al menos 6 caracteres.", parent=self.win)
                    return
                
                id_admin = self.usuario_actual.get('id_usuario') if self.usuario_actual else None
                nuevo_id = self.backend.crear_usuario(nombre, pass1, id_rol, codigo_barras=codigo_barras, id_usuario_admin=id_admin)
                if nuevo_id:
                    messagebox.showinfo("Éxito", f"Usuario '{nombre}' creado correctamente.", parent=self.win)
                    if self.callback_on_save: 
                        self.callback_on_save()
                    self.win.destroy()
                else:
                    from app.frontend.manejador_errores import ManejadorErroresUI
                    ManejadorErroresUI.manejar_error(Exception("No se pudo registrar el nuevo usuario en el sistema. Asegúrate de que el nombre no esté duplicado."), parent=self.win, contexto=nombre)

        except ValueError as ve:
            from app.frontend.manejador_errores import ManejadorErroresUI
            ManejadorErroresUI.manejar_error(ve, parent=self.win, contexto=nombre)
        
        except Exception as e:
            logger.exception("Error al guardar usuario")
            from app.frontend.manejador_errores import ManejadorErroresUI
            ManejadorErroresUI.manejar_error(e, parent=self.win, contexto=nombre)

    def resetear_password_moderno(self):
        if not self.usuario_existente: return
        id_usuario = self.usuario_existente.get('id_usuario')
        nombre = self.usuario_existente.get('nombre')
        
        popup = ctk.CTkToplevel(self.win)
        preparar_ventana(popup)
        popup.title("🔒 Resetear Contraseña")
        popup.geometry("400x300")
        popup.resizable(False, False)
        
        ctk.CTkLabel(popup, text=f"Nueva contraseña para:\n'{nombre}'", font=("Segoe UI", 14, "bold"), text_color=self.col_text).pack(pady=(20, 10))
        
        var_new_pass = tk.StringVar()
        entry_new_pass = ctk.CTkEntry(popup, textvariable=var_new_pass, show="*", font=("Segoe UI", 14), width=300, height=45)
        entry_new_pass.pack(pady=10)
        entry_new_pass.focus_set()
        
        def confirmar():
            p = var_new_pass.get().strip()
            if not p:
                messagebox.showwarning("Contraseña Requerida", "Por favor, ingresa una nueva contraseña para continuar.", parent=popup)
                return
            if len(p) < 6:
                messagebox.showwarning("Contraseña Débil", "La nueva contraseña debe tener al menos 6 caracteres.", parent=popup)
                return
            try:
                id_admin = self.usuario_actual.get('id_usuario') if self.usuario_actual else None
                if self.backend.resetear_password_usuario(id_usuario, p, id_usuario_admin=id_admin):
                    messagebox.showinfo("Éxito", "Contraseña restablecida correctamente.", parent=popup)
                    popup.destroy()
                else:
                    from app.frontend.manejador_errores import ManejadorErroresUI
                    ManejadorErroresUI.manejar_error(Exception("No se pudo restablecer la contraseña."), parent=popup)
            except Exception as e:
                from app.frontend.manejador_errores import ManejadorErroresUI
                ManejadorErroresUI.manejar_error(e, parent=popup)

        frm_btn = ctk.CTkFrame(popup, fg_color="transparent")
        frm_btn.pack(pady=20)
        
        ctk.CTkButton(frm_btn, text="✓ Confirmar", command=confirmar, fg_color="#16a34a", hover_color="#15803d", font=("Segoe UI", 12, "bold"), height=40).pack(side="left", padx=10)
        ctk.CTkButton(frm_btn, text="Cancelar", command=popup.destroy, fg_color="#6b7280", hover_color="#4b5563", font=("Segoe UI", 12), height=40).pack(side="left", padx=10)
        
        entry_new_pass.bind("<Return>", lambda e: confirmar())
        popup.transient(self.win)
        centrar_y_mostrar_ventana(popup)
        popup.grab_set()

def ui_crear_usuario(parent: tk.Misc, backend, id_usuario_a_editar=None, usuario_actual=None, callback_on_save=None):
    usuario_existente = None
    if id_usuario_a_editar:
        users = backend.obtener_usuarios_con_rol()
        usuario_existente = next((u for u in users if u['id_usuario'] == id_usuario_a_editar), None)
    
    CrearEditarUsuario(parent, backend, usuario_existente, usuario_actual=usuario_actual, callback_on_save=callback_on_save)