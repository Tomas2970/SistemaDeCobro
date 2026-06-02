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
    """Ejecuta la carga de datos iniciales (roles, admin, categorías)"""
    print("\n" + "="*70)
    print("  🌱 CARGA DE DATOS INICIALES - Sistema Don Atilio")
    print("="*70 + "\n")
    
    try:
        import bcrypt
        import mysql.connector
        from dotenv import load_dotenv
        
        load_dotenv()
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = int(os.getenv("DB_PORT", "3307"))
        DB_USER = os.getenv("DB_USER", "root")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "")
        DB_NAME = os.getenv("DB_NAME", "supermercado_don_atilio")
        
        print(f"📡 Conectando a {DB_HOST}:{DB_PORT}...")
        
        conn = mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME,
            autocommit=False
        )
        cur = conn.cursor(buffered=True)
        
        # 1. Roles
        print("📋 Cargando roles...")
        cur.execute("INSERT IGNORE INTO Rol (id_rol, nombre, descripcion) VALUES (1, 'admin', 'Administrador'), (2, 'vendedor', 'Vendedor'), (3, 'supervisor', 'Supervisor')")
        
        # 2. Admin
        print("👤 Verificando admin...")
        cur.execute("SELECT 1 FROM Usuario WHERE nombre='admin'")
        if not cur.fetchone():
            hashed = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
            cur.execute("INSERT INTO Usuario (nombre, contraseña, id_rol, activo) VALUES (%s, %s, 1, 1)", ("admin", hashed))
            print("   ✓ Usuario 'admin' creado.")
        
        # 3. Categorías Básicas
        print("🏷️ Cargando categorías...")
        categorias = [
            (1, 'Bebidas', 30.00), (2, 'Almacén', 30.00), (3, 'Lácteos', 25.00),
            (4, 'Carnes', 35.00), (5, 'Limpieza', 30.00), (6, 'Panadería', 40.00),
            (7, 'Congelados', 30.00), (8, 'Golosinas', 40.00), (9, 'Verdulería', 35.00),
            (99, 'Varios', 30.00)
        ]
        for cid, nom, mar in categorias:
            cur.execute(
                "INSERT IGNORE INTO Categoria (id_categoria, nombre, margen_ganancia, activa) VALUES (%s, %s, %s, 1)",
                (cid, nom, mar)
            )
        
        conn.commit()
        cur.close()
        conn.close()
        print("\n✅ Carga inicial exitosa.")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR SEED: {e}")
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
        # AL CERRAR SESIÓN: Lógica de Caja Abierta (RECUPERADA)
        # -------------------------------------------------------------
        logging.info(f"Sesión cerrada para: {usuario.get('nombre')}")
        
        try:
            from app.database.permisos import tiene_permiso
            # Verificar si el USUARIO tiene caja abierta
            caja_abierta = backend.obtener_session_abierta(id_usuario=usuario['id_usuario'])
            
            if caja_abierta and tiene_permiso(usuario, 'cerrar_caja'):
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
                    from app.frontend.interfaz_reportes import ui_reportes
                    root_cierre = tk.Tk()
                    root_cierre.withdraw()
                    ui_reportes(parent=root_cierre, backend=backend, usuario=usuario)
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