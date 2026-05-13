"""
Точка входа в приложение.
Запускает WeatherBot с правильной конфигурацией.
"""

import asyncio
import logging
import sys

# Добавляем корневой каталог в path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot import WeatherBot, Config
from bot.utils import setup_logging


async def main() -> None:
    """
    Асинхронная точка входа.
    Загружает конфигурацию, настраивает логи, запускает бота.
    """
    
    # 1. Загружаем конфигурацию из .env
    try:
        config = Config.from_env()
    except ValueError as e:
        # Конфигурация некорректна — немедленно завершаем
        print(f"❌ Ошибка конфигурации: {e}")
        print("Убедитесь что файл .env создан и заполнен.")
        sys.exit(1)
    
    # 2. Настраиваем логирование
    setup_logging(
        log_level=config.log_level,
        log_file=config.log_file,
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("Запуск Weather Bot")
    logger.info(f"Конфигурация: {config}")
    logger.info("=" * 50)
    
    # 3. Создаём и запускаем бота
    bot = WeatherBot(config=config)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Приложение завершено")


if __name__ == "__main__":
    # Запускаем асинхронное приложение
    asyncio.run(main())
