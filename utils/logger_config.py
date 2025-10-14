import logging
import os
from datetime import datetime

def setup_logger():
    """
    Configura el sistema de logging para la aplicación.
    Crea un directorio de logs si no existe y configura un logger con un archivo de log diario.
    """
    # Crear directorio de logs si no existe
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configurar el formato del log
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(log_format, date_format)

    # Obtener el logger principal
    logger = logging.getLogger('bascula')
    
    # Si el logger ya tiene handlers, no agregar más
    if logger.handlers:
        return logger

    # Configurar nivel de log
    logger.setLevel(logging.INFO)

    # Crear handler para archivo
    log_file = os.path.join(log_dir, f'bascula_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Crear handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Agregar handlers al logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger 