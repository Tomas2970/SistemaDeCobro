#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistema de Cobros Don Atilio - Punto de entrada principal
Modificado para soportar carga de datos iniciales desde instalador y Auto-Reparación.
"""

import sys
import os
import logging

# =========================================================
# 🔥 CRÍTICO: DETECTAR --seed-data ANTES DE CARGAR TKINTER
# =========================================================
MODO_SEED = len(sys.argv) > 1 and sys.argv[1] == '--seed-data'

if not MODO_SEED:
    # Solo importar tkinter si NO es modo seed
    import tkinter as tk

# =========================================================
# --- BLOQUE DE "ENGANCHE" PARA PYINSTALLER ---
# =========================================================
if not MODO_SEED:  
    try:
        from app.frontend import interfaz_inventario
        from app.frontend import interfaz_productos
        from app.frontend import interfaz_venta
        from app.frontend import interfaz_reportes
        from app.frontend import interfaz_gestion_clientes
        from app.frontend import interfaz_cuenta_corriente
        from app.frontend import interfaz_compra
        from app.frontend import interfaz_historiales
        from app.frontend import interfaz_gestion_usuarios
        from app.frontend import interfaz_forma_pago
        from app.frontend import stock_alerts 
    except ImportError:
        pass 

# =========================================================
# --- CONFIGURACIÓN DE PATHS ---
# =========================================================
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    base_path = sys._MEIPASS
    sys.path.insert(0, base_path)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(script_dir) == 'app':
        application_path = os.path.dirname(script_dir)
    else:
        application_path = script_dir
    base_path = application_path

sys.path.insert(0, application_path)
os.chdir(application_path)

app_path = os.path.join(application_path, 'app')
if os.path.exists(app_path) and app_path not in sys.path:
    sys.path.insert(0, app_path)

# =========================================================
# 🔥 PARCHE DE DIÁLOGOS MODERNOS UNIFICADOS
# =========================================================
if not MODO_SEED:
    import sys
    from app.frontend import custom_dialogs
    
    # Parchear dinámicamente sys.modules y el namespace de tkinter para redirigir
    # todas las llamadas de messagebox nativos a nuestra implementación moderna y unificada.
    sys.modules['tkinter.messagebox'] = custom_dialogs
    tk.messagebox = custom_dialogs

# --- Carga de Logs ---
try:
    from app.tools.logger_config import setup_logging
    setup_logging()
except ImportError as e:
    print(f"ADVERTENCIA: No se pudo cargar logger_config. {e}")
    logging.basicConfig(level=logging.INFO)

# --- Importar impresora (opcional) ---
if not MODO_SEED:
    try:
        from app import impresora
        logging.info("✓ Módulo impresora.py cargado correctamente")
    except ImportError:
        logging.warning(f"⚠️ ADVERTENCIA: app/impresora.py no encontrado.")

# =========================================================
# 🌱 FUNCIÓN DE SEED (Usada solo por el instalador)
# =========================================================
def seed_database():
    """Ejecuta la carga demo completa usada por el instalador."""
    print("\n" + "="*70)
    print("  CARGA DEMO COMPLETA - Sistema Don Atilio")
    print("="*70 + "\n")

    try:
        from app.tools.demo_seed import run_demo_seed

        print("ADVERTENCIA: esta operacion limpia la base operativa y recrea datos demo.")
        resumen = run_demo_seed()
        print("\nCarga demo exitosa.")
        print("\nResumen:")
        for clave, valor in resumen.items():
            print(f"   - {clave}: {valor}")
        print("\nCredenciales demo:")
        print("   - admin / admin123")
        print("   - supervisor / super123")
        print("   - lucia / lucia123")
        print("   - martin / martin123")
        print("   - sofia / sofia123")
        return True

    except Exception as e:
        print(f"\nERROR SEED DEMO: {e}")
        import traceback
        traceback.print_exc()
        return False

# =========================================================
# --- FUNCIÓN PRINCIPAL DE LA UI (RECUPERADA COMPLETA) ---
# =========================================================
def run_app():
    from app.frontend.interfaz_iniciosesion import ui_login
    from app.frontend.interfaz_menu_principal import ui_menu_principal
    from app.database.backend_adapter import BackendAdapter
    import customtkinter as ctk
    
    # Configuramos el tema de apariencia oscuro de forma global y permanente
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    backend = BackendAdapter()
    
    root_app = ctk.CTk()
    root_app.geometry("1x1+-100+-100")  # Fuera de pantalla para evitar flash
    root_app.update_idletasks()
    
    # 🔥 INICIALIZACIÓN GLOBAL DE ESTILOS (Treeview, Notebook, etc.)
    # Se hace AQUÍ para que todas las ventanas los hereden instantáneamente
    try:
        from app.frontend.theme_config import inicializar_estilos_globales
        inicializar_estilos_globales()
    except Exception as e:
        logging.error(f"Error al inicializar estilos globales: {e}")

    while True:
        # Login
        usuario = ui_login(parent=root_app, backend=backend)

        if not usuario:
            try: root_app.destroy()
            except: pass
            logging.info("Login cancelado. Saliendo de la aplicación.")
            break

        logging.info(f"Sesión iniciada: {usuario.get('nombre')}")
        
        # Dashboard Principal
        ui_menu_principal(parent=root_app, backend=backend, usuario=usuario)
        
        # -------------------------------------------------------------
        # AL CERRAR SESIÓN: Limpiar Token de Sesión Única
        # -------------------------------------------------------------
        try:
            backend.cerrar_sesion_usuario(usuario['id_usuario'])
        except Exception as e_sesion:
            logging.error(f"Error limpiando token de sesión: {e_sesion}")

        # -------------------------------------------------------------
        # AL CERRAR SESIÓN: Lógica de Caja Abierta (RECUPERADA)
        # -------------------------------------------------------------
        logging.info(f"Sesión cerrada para: {usuario.get('nombre')}")
        
        try:
            from app.database.permisos import tiene_permiso
            # Verificar si el USUARIO tiene caja abierta
            caja_abierta = backend.obtener_session_abierta(id_usuario=usuario['id_usuario'])
            
            # 🔒 FIX: Los Administradores (rol 1) operan la Tesorería (Caja Maestra).
            # Esta caja está diseñada para durar todo el día, NO deben ser forzados a cerrarla al salir.
            if caja_abierta and tiene_permiso(usuario, 'cerrar_caja') and usuario.get('id_rol') != 1:
                root_temp = tk.Tk()
                root_temp.withdraw()
                
                respuesta = tk.messagebox.askyesnocancel(
                    "⚠️ Caja Abierta",
                    f"Tienes una caja abierta.\n\n"
                    f"¿Deseas cerrar tu caja antes de salir?\n\n"
                    f"• SÍ: Cerrar caja ahora (arqueo)\n"
                    f"• NO: Salir sin cerrar (la caja queda abierta)\n"
                    f"• CANCELAR: Volver al sistema",
                    parent=root_temp
                )
                
                root_temp.destroy()
                
                if respuesta is None:  # Cancelar -> Volver al sistema (Login loop)
                    continue
                elif respuesta:  # Sí -> Abrir ventana de cierre
                    from app.frontend.interfaz_caja_operativa import ui_caja_operativa
                    root_cierre = tk.Tk()
                    root_cierre.withdraw()
                    ui_caja_operativa(parent=root_cierre, backend=backend, usuario=usuario)
                    root_cierre.mainloop()
                    root_cierre.destroy()
                    continue # Volver al login
                # else (NO) -> Salir del bucle y cerrar app
                
        except Exception as e:
            logging.error(f"Error al verificar caja al salir: {e}")

# =========================================================
# --- PUNTO DE ENTRADA ---
# =========================================================
def main():
    # 1. MODO SEED (Instalador)
    if MODO_SEED:
        if seed_database():
            sys.exit(0)
        else:
            sys.exit(1)
    
    # 2. AUTO-REPARACIÓN (Solución Definitiva)
    # Se ejecuta SIEMPRE antes de abrir la ventana
    try:
        print("🔧 Verificando integridad de la base de datos...")
        from app.database.auto_migrate import ejecutar_migraciones
        ejecutar_migraciones()
    except ImportError:
        logging.warning("⚠️ No se encontró el módulo 'auto_migrate'. Saltando verificación.")
    except Exception as e:
        logging.error(f"Fallo en auto-migración: {e}")
        # No detenemos el programa, intentamos seguir

    # 3. MODO NORMAL
    try:
        run_app()
    except Exception as e:
        logging.critical(f"Error fatal: {e}", exc_info=True)
        try:
            root_err = tk.Tk()
            root_err.withdraw()
            tk.messagebox.showerror("Error Crítico", f"Error fatal al iniciar:\n\n{e}")
            root_err.destroy()
        except: pass
        sys.exit(1)

if __name__ == "__main__":
    main()
