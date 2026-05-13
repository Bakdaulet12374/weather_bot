"""
Настройка логирования.
Центральная конфигурация логов для всего приложения.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_level: str = "INFO", log_file: str = "logs/bot.log") -> None:
    """
    Настраивает систему логирования.
    
    - Консольный вывод: INFO и выше
    - Файловый вывод: DEBUG и выше (ротация 5MB, 3 файла)
    
    Args:
        log_level: уровень логирования (DEBUG/INFO/WARNING/ERROR)
        log_file: путь к файлу логов
    """
    # Создаём директорию для логов
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Числовой уровень
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Формат сообщений
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Захватываем всё, фильтруем в handlers
    
    # Консольный handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    
    # Файловый handler с ротацией
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Приглушаем шумные библиотеки
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)
    
    logging.info(f"Логирование настроено: уровень={log_level}, файл={log_file}")
