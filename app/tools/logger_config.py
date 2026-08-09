# app/tools/logger_config.py
import os
import sys
import logging
import logging.handlers

def setup_logging():
    """
    Configura el logging centralizado para toda la aplicación.
    Debe llamarse UNA SOLA VEZ al inicio de la aplicación.
    """
    
    # --- Configuración de Paths ---
    # Asumimos que este archivo está en app/tools/
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PROJECT_ROOT = os.path.dirname(APP_DIR)
    LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
    # --- Fin Configuración ---

    # Crear el directorio de logs si no existe
    os.makedirs(LOG_DIR, exist_ok=True)

    # Definir formato
    log_format = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)-20s: %(message)s (%(filename)s:%(lineno)d)",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # --- Handlers ---
    
    # 1. Handler para consola (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO) # Podés cambiar a DEBUG si necesitás más detalle
    console_handler.setFormatter(log_format)

    # 2. Handler para errores (logs/error.log)
    # Rota cada medianoche y guarda 7 días de logs de error
    error_handler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(LOG_DIR, 'error.log'),
        when='midnight',
        backupCount=7,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.WARNING) # Captura WARNING, ERROR, CRITICAL
    error_handler.setFormatter(log_format)

    # 3. Handler para info general (logs/info.log)
    # Rota cada medianoche y guarda 7 días de logs de info
    info_handler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(LOG_DIR, 'info.log'),
        when='midnight',
        backupCount=7,
        encoding='utf-8'
    )
    info_handler.setLevel(logging.INFO) # Captura INFO y superior
    # Filtro para que info.log NO contenga errores (ya están en error.log)
    info_handler.addFilter(lambda record: record.levelno < logging.WARNING)
    info_handler.setFormatter(log_format)

    # --- Configurar el Root Logger ---
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Nivel base
    
    # Evitar handlers duplicados si se llama a esta función más de una vez
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(console_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(info_handler)

    logger = logging.getLogger(__name__)
    logger.info("Logging configurado y listo.")