#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistema de Cobros Don Atilio - Punto de entrada principal
Modificado para soportar carga de datos iniciales desde instalador
"""

import sys
import os
import tkinter as tk
import logging

# --- Configuración de Paths ---
# (Esto es crucial para que PyInstaller encuentre los archivos)
if getattr(sys, 'frozen', False):
    # Si está empaquetado (ejecutando el .exe)
    application_path = os.path.dirname(sys.executable)
    # En PyInstaller, sys._MEIPASS es donde están los assets empaquetados
    base_path = sys._MEIPASS
    sys.path.insert(0, base_path)
else:
    # Si se ejecuta como script (python main.py desde la raíz)
    # Obtener la ruta absoluta del directorio donde está main.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Si main.py está en app/main.py, subir un nivel
    if os.path.basename(script_dir) == 'app':
        application_path = os.path.dirname(script_dir)
    else:
        # Si main.py está en la raíz
        application_path = script_dir
    
    base_path = application_path

# Agregar la ruta base al path para que Python encuentre el módulo 'app'
sys.path.insert(0, application_path)
os.chdir(application_path)  # Cambia el directorio de trabajo a la raíz

# Agregar también la carpeta 'app' específicamente
app_path = os.path.join(application_path, 'app')
if os.path.exists(app_path) and app_path not in sys.path:
    sys.path.insert(0, app_path)

# --- Fin Configuración ---


# --- Carga de Logs ---
# Tiene que estar ANTES de importar tus otros módulos
try:
    from app.tools.logger_config import setup_logging
    setup_logging()
except ImportError as e:
    print(f"ADVERTENCIA: No se pudo cargar logger_config. {e}")
    logging.basicConfig(level=logging.INFO)
# --- Fin Carga ---


# --- Importar impresora (opcional) ---
try:
    from app import impresora
    logging.info("✓ Módulo impresora.py cargado correctamente")
    IMPRESORA_DISPONIBLE = True
except ImportError as e:
    logging.warning(f"⚠️ ADVERTENCIA: app/impresora.py no encontrado. La función de imprimir no estará disponible.")
    impresora = None
    IMPRESORA_DISPONIBLE = False
# --- Fin importar impresora ---


# --- Carga de Datos (Seed) ---
def seed_database():
    """Ejecuta el script de seed_initial_data.py para cargar datos de prueba"""
    try:
        # Usamos los imports relativos de la app
        from app.tools.seed_initial_data import main as seed_main
        logging.info("Iniciando carga de datos iniciales...")
        seed_main()
        logging.info("¡Datos iniciales cargados exitosamente!")
        return True
    except Exception as e:
        logging.error(f"Error fatal al cargar datos iniciales: {e}", exc_info=True)
        return False
# --- Fin Seed ---


# --- Función Principal de la App ---
def run_app():
    """Modo normal: iniciar la interfaz gráfica"""
    
    # Importamos los módulos de la app AHORA
    from app.frontend.interfaz_iniciosesion import ui_login
    from app.frontend.interfaz_menu_principal import ui_menu_principal
    from app.database.backend_adapter import BackendAdapter
    
    backend = BackendAdapter()
    
    # Bucle de sesión: Login -> Menú Principal -> (al cerrar) -> Login
    while True:
        root_login = tk.Tk()
        root_login.withdraw()  # Ocultar la ventana raíz principal
        
        # 1. Mostrar Login
        usuario = ui_login(parent=root_login, backend=backend)
        
        root_login.destroy()  # Destruir la ventana de login

        # 2. Si el usuario cerró el login (usuario=None), terminar
        if not usuario:
            logging.info("Login cancelado. Saliendo de la aplicación.")
            break  # Rompe el 'while True' y termina el programa

        # 3. Si el login fue exitoso, mostrar Menú Principal
        logging.info(f"Iniciando sesión como: {usuario.get('nombre')}")
        root_main = tk.Tk()
        
        ui_menu_principal(parent=root_main, backend=backend, usuario=usuario)
        
        root_main.mainloop()  # La app se queda aquí hasta que se cierre el menú
        
        # 4. Cuando el menú se cierra, el bucle vuelve a empezar
        logging.info(f"Sesión cerrada para: {usuario.get('nombre')}")


# --- Punto de Entrada ---
def main():
    """Punto de entrada principal de la aplicación"""
    
    # Modo instalación: solo cargar datos y salir
    if len(sys.argv) > 1 and sys.argv[1] == '--seed-data':
        success = seed_database()
        sys.exit(0 if success else 1)
    
    # Modo normal: Iniciar la UI
    try:
        run_app()
    except Exception as e:
        # Si algo falla MUY feo (ej. no se puede cargar Tkinter)
        logging.critical(f"Error fatal al iniciar la aplicación: {e}", exc_info=True)
        # Intentar mostrar un messagebox de último recurso
        try:
            root_err = tk.Tk()
            root_err.withdraw()
            tk.messagebox.showerror("Error Crítico", f"No se pudo iniciar la aplicación:\n\n{e}")
            root_err.destroy()
        except Exception:
            pass  # Si ni Tkinter funciona, no hay nada que hacer
        sys.exit(1)


if __name__ == "__main__":
    main()