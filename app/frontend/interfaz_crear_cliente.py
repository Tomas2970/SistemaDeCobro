# app/frontend/interfaz_crear_cliente.py
import tkinter as tk
from tkinter import messagebox
from typing import Optional 
# --- ¡NUEVO! Importamos las validaciones ---
try:
    from app.frontend.validaciones import validar_email, validar_dni_argentino
except ImportError:
    # Fallback por si el archivo no se encuentra
    print("ADVERTENCIA: No se pudo importar 'validaciones.py'. Se usarán validaciones simples.")
    def validar_email(email): return True
    def validar_dni_argentino(dni): return True
# --- FIN NUEVO ---

def ui_crear_cliente(parent: tk.Misc, backend, usuario: dict, id_cliente_a_editar: Optional[int] = None):
    
    win = tk.Toplevel(parent)
    win.geometry("500x375") 
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    modo_edicion = id_cliente_a_editar is not None
    
    if modo_edicion:
        win.title("Editar Cliente")
        try:
            datos_cliente = backend.obtener_cliente_para_editar(id_cliente_a_editar)
            if not datos_cliente:
                messagebox.showerror("Error", "No se pudieron cargar los datos del cliente.", parent=win)
                win.destroy()
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {e}", parent=win)
            win.destroy()
            return
    else:
        win.title("Crear Cliente")
        datos_cliente = {} 
    
    def on_guardar():
        nombre = entry_nombre.get().strip()
        dni = entry_dni.get().strip()
        direccion = entry_direccion.get().strip()
        telefono = entry_telefono.get().strip()
        email = entry_email.get().strip()
        limite_str = entry_limite.get().strip()
        
        # --- ¡INICIO VALIDACIONES! ---
        if not nombre:
            messagebox.showwarning("Campos vacíos", "El campo 'Nombre' es obligatorio.", parent=win)
            return
        
        if not validar_dni_argentino(dni):
            messagebox.showwarning("DNI Inválido",
                                   "El DNI debe tener 7 u 8 dígitos sin letras.\n"
                                   "Ejemplos válidos: 12345678 o 12.345.678\n\n"
                                   "Puede dejar el campo vacío.",
                                   parent=win)
            return
            
        if not validar_email(email):
            messagebox.showwarning("Email Inválido",
                                   "Por favor ingrese un email válido.\n"
                                   "Ejemplo: cliente@ejemplo.com\n\n"
                                   "Puede dejar el campo vacío si no tiene email.",
                                   parent=win)
            return
            
        try:
            limite_valido = float(limite_str.replace(",", "."))
            if limite_valido < 0:
                raise ValueError("El límite no puede ser negativo")
        except ValueError:
            messagebox.showwarning("Valor incorrecto",
                                   "El 'Límite Crédito' debe ser un número válido.\n"
                                   "Ejemplo: 50000.00",
                                   parent=win)
            return
        # --- FIN VALIDACIONES! ---
            
        try:
            if modo_edicion:
                exito = backend.actualizar_cliente(
                    id_cliente_a_editar, 
                    nombre, dni, direccion, telefono, email, limite_valido
                )
                if exito:
                    messagebox.showinfo("Cliente Actualizado", f"Cliente '{nombre}' actualizado correctamente.", parent=win)
                    win.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo actualizar el cliente.\nVerifique que el DNI o Email no estén duplicados.", parent=win)
            
            else: 
                nuevo_id = backend.insertar_cliente(
                    nombre, dni, direccion, telefono, email, limite_valido
                )
                if nuevo_id:
                    messagebox.showinfo("Cliente Guardado", f"Cliente '{nombre}' creado con ID {nuevo_id}", parent=win)
                    win.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo guardar el cliente.\nVerifique que el DNI o Email no estén duplicados.", parent=win)

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar cliente:\n{e}", parent=win)

    
    tk.Label(win, text="Nombre (*):", bg="#f4f4f8").place(x=40, y=60)
    entry_nombre = tk.Entry(win, width=40); entry_nombre.place(x=130, y=60)
    entry_nombre.insert(0, datos_cliente.get('nombre') or '')
    
    tk.Label(win, text="DNI:", bg="#f4f4f8").place(x=40, y=95)
    entry_dni = tk.Entry(win, width=40); entry_dni.place(x=130, y=95)
    entry_dni.insert(0, datos_cliente.get('dni') or '')
    
    tk.Label(win, text="Dirección:", bg="#f4f4f8").place(x=40, y=130)
    entry_direccion = tk.Entry(win, width=40); entry_direccion.place(x=130, y=130)
    entry_direccion.insert(0, datos_cliente.get('direccion') or '')
    
    tk.Label(win, text="Teléfono:", bg="#f4f4f8").place(x=40, y=165)
    entry_telefono = tk.Entry(win, width=40); entry_telefono.place(x=130, y=165)
    entry_telefono.insert(0, datos_cliente.get('telefono') or '')
    
    tk.Label(win, text="Email:", bg="#f4f4f8").place(x=40, y=200)
    entry_email = tk.Entry(win, width=40); entry_email.place(x=130, y=200)
    entry_email.insert(0, datos_cliente.get('email') or '')

    tk.Label(win, text="Límite Crédito:", bg="#f4f4f8").place(x=40, y=235)
    entry_limite = tk.Entry(win, width=40); entry_limite.place(x=130, y=235)
    limite_default = datos_cliente.get('limite_credito', 50000.00)
    try:
        entry_limite.insert(0, f"{float(limite_default):.2f}")
    except (ValueError, TypeError):
        entry_limite.insert(0, "50000.00")

    tk.Button(win, text="Guardar Datos", bg="#4CAF50", fg="white", width=15, command=on_guardar).place(x=130, y=295)
    tk.Button(win, text="Cancelar", bg="#f44336", fg="white", width=15, command=lambda: win.destroy()).place(x=280, y=295)
    
    entry_nombre.focus_set()
    
    win.grab_set()
    win.transient(parent)