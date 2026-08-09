# app/tools/backup_db.py
import os
import subprocess
import logging
import sys
from datetime import datetime, timedelta # ¡Importamos timedelta!
from dotenv import load_dotenv

# --- Configuración de Paths ---
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(APP_DIR)
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')
BACKUP_DIR = os.path.join(PROJECT_ROOT, 'backup')
# --- Fin Configuración ---

# --- ¡NUEVO! Definir cuántos días guardar ---
DIAS_DE_RETENCION = 15 # Guardará los últimos 15 días de backups

# Logger simple solo para este script
logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)


# --- ¡NUEVA FUNCIÓN DE LIMPIEZA! ---
def limpiar_backups_viejos():
    """
    Revisa la carpeta BACKUP_DIR y borra los archivos .sql
    que tengan más días que DIAS_DE_RETENCION.
    """
    logger.info(f"Limpiando backups con más de {DIAS_DE_RETENCION} días...")
    try:
        now = datetime.now()
        limite_tiempo = now - timedelta(days=DIAS_DE_RETENCION)
        archivos_borrados = 0
        
        # Asegurarse que el directorio exista
        if not os.path.exists(BACKUP_DIR):
            logger.warning(f"El directorio de backup {BACKUP_DIR} no existe. No se limpió nada.")
            return

        for filename in os.listdir(BACKUP_DIR):
            if not filename.endswith(".sql"):
                continue # Ignorar archivos que no sean .sql
            
            filepath = os.path.join(BACKUP_DIR, filename)
            
            try:
                # Obtener el tiempo de modificación del archivo
                file_time_stamp = os.path.getmtime(filepath)
                file_time = datetime.fromtimestamp(file_time_stamp)
                
                # Si el archivo es más viejo que el límite de tiempo, borrarlo
                if file_time < limite_tiempo:
                    logger.warning(f"Borrando archivo viejo: {filename} (creado el {file_time.strftime('%Y-%m-%d')})")
                    os.remove(filepath)
                    archivos_borrados += 1
            
            except Exception as e_file:
                logger.error(f"No se pudo procesar el archivo {filename}: {e_file}")

        logger.info(f"Limpieza completada. Se borraron {archivos_borrados} archivos.")

    except Exception as e:
        logger.error(f"Error crítico durante la limpieza de backups: {e}")
# --- FIN NUEVA FUNCIÓN ---


def realizar_backup():
    """
    Ejecuta mysqldump para crear un backup de la base de datos.
    """
    logger.info("Iniciando proceso de backup...")
    
    # Cargar variables de entorno desde .env
    if not os.path.exists(DOTENV_PATH):
        logger.error(f"Error: No se encontró el archivo .env en {PROJECT_ROOT}")
        return False
        
    load_dotenv(dotenv_path=DOTENV_PATH)
    
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "3307")

    if not all([db_user, db_pass, db_name, db_host, db_port]):
        logger.error("Error: Faltan variables de entorno (DB_USER, DB_PASSWORD, etc.).")
        return False

    # Crear el directorio de backup si no existe
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
    except OSError as e:
        logger.error(f"No se pudo crear el directorio de backup en {BACKUP_DIR}: {e}")
        return False

    # Definir nombre del archivo de backup
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"backup_{db_name}_{timestamp}.sql"
    backup_filepath = os.path.join(BACKUP_DIR, backup_filename)

    # Comando mysqldump
    command = [
        "mysqldump",
        "-u", db_user,
        f"-p{db_pass}",
        "-h", db_host,
        "-P", str(db_port),
        "--routines",
        "--skip-lock-tables",
        db_name
    ]

    try:
        logger.info(f"Creando backup en: {backup_filepath}")
        
        with open(backup_filepath, 'wb') as f_out:
            process = subprocess.Popen(command, stdout=f_out, stderr=subprocess.PIPE, shell=True)
            stderr = process.communicate()[1]
            
            if process.returncode == 0:
                logger.info(f"Backup completado exitosamente: {backup_filename}")
                # --- ¡CAMBIO! Llamamos a la limpieza DESPUÉS de un backup exitoso ---
                limpiar_backups_viejos()
                # --- FIN CAMBIO ---
                return True
            else:
                logger.error(f"Error durante mysqldump: {stderr.decode('utf-8', 'ignore')}")
                if os.path.exists(backup_filepath):
                    os.remove(backup_filepath)
                return False

    except Exception as e:
        logger.error(f"Excepción al ejecutar mysqldump: {e}")
        if os.path.exists(backup_filepath):
            os.remove(backup_filepath)
        return False

if __name__ == "__main__":
    # Cuando ejecutás 'python app/tools/backup_db.py', esto se llama:
    if not realizar_backup():
        sys.exit(1)
    
    # Ya no llamamos a 'limpiar_backups_viejos()' aquí,
    # porque 'realizar_backup()' ya lo hace internamente.