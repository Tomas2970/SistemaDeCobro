# app/main.py
import tkinter as tk
from tkinter import messagebox
import logging # Mantenemos el import de logging

# --- ¡NUEVO! ---
# Importamos el configurador de logging
from app.tools.logger_config import setup_logging
# Lo ejecutamos UNA SOLA VEZ al inicio de todo
setup_logging()
# --- FIN NUEVO ---

from app.frontend.interfaz_iniciosesion import ui_login
from app.frontend.interfaz_menu_principal import ui_menu_principal
from app.database.backend_adapter import BackendAdapter


# --- ¡CAMBIO! ---
# Ya no necesitamos esta línea, porque setup_logging() la reemplaza
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
# --- FIN CAMBIO ---

def main() -> None:
    backend = BackendAdapter()
    
    # --- ¡NUEVO BUCLE DE SESIÓN! ---
    while True:
        # 1. Crear y mostrar la ventana de Login
        root_login = tk.Tk()
        root_login.withdraw() # Ocultar la ventana raíz de login
        
        usuario = ui_login(parent=root_login, backend=backend)
        
        root_login.destroy() # Destruir la ventana de login al terminar

        # 2. Si el usuario cerró el login (usuario=None), terminar la aplicación
        if not usuario:
            logging.info("Login cancelado. Saliendo de la aplicación.")
            break # Rompe el 'while True' y termina el programa

        # 3. Si el login fue exitoso, crear y mostrar la ventana principal
        logging.info(f"Iniciando sesión como: {usuario.get('nombre')}")
        root_main = tk.Tk()
        
        # (Aquí va la lógica del Menú Principal)
        ui_menu_principal(parent=root_main, backend=backend, usuario=usuario)
        
        root_main.mainloop() # La aplicación se queda aquí hasta que se cierre el menú
        
        # 4. Cuando el menú se cierra (por 'Cerrar Sesión' o la 'X'), 
        #    mainloop() termina y el 'while True' vuelve a empezar,
        #    mostrando el Login de nuevo.
        logging.info(f"Sesión cerrada para: {usuario.get('nombre')}")

if __name__ == "__main__":
    main()