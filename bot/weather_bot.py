import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from .config import Config
from .database import DatabaseManager
from .services import WeatherService
from bot.services.notification_scheduler import NotificationScheduler

from .handlers import (
    setup_command_handlers,
    setup_weather_handlers,
    setup_callback_handlers,
)


logger = logging.getLogger(__name__)


class WeatherBot:
    def __init__(self, config: Config) -> None:
        """
        Инициализирует все компоненты бота.

        Args:
            config: объект конфигурации
        """
        self._config = config

        # 1. База данных
        self._db = DatabaseManager(db_path=config.db_path)

        # 2. Сервис погоды
        self._weather_service = WeatherService(config=config)

        # 3. Telegram Bot
        self._bot = Bot(
            token=config.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

        # 4. Планировщик уведомлений
        self._notification_scheduler = NotificationScheduler(
            bot=self._bot,
            db_manager=self._db,
            weather_service=self._weather_service,
        )

        # 5. Dispatcher
        self._dp = Dispatcher()

        # 6. Регистрация роутеров
        self._register_routers()

        logger.info("WeatherBot успешно инициализирован")

    def _register_routers(self) -> None:
        # Команды
        self._dp.include_router(
            setup_command_handlers(db=self._db)
        )

        # Callback-кнопки
        self._dp.include_router(
            setup_callback_handlers(
                db=self._db,
                weather_service=self._weather_service,
            )
        )

        # Текстовые сообщения (должен быть последним)
        self._dp.include_router(
            setup_weather_handlers(
                db=self._db,
                weather_service=self._weather_service,
            )
        )

        logger.info("Роутеры зарегистрированы")

    async def start(self) -> None:
        """
        Запускает бота в режиме long-polling.
        """
        logger.info("Запуск WeatherBot...")

        # Удаляем webhook, если был установлен
        await self._bot.delete_webhook(drop_pending_updates=True)

        # Запускаем планировщик уведомлений
        self._notification_scheduler.start()

        try:
            logger.info("Бот запущен. Ожидаю сообщения...")
            await self._dp.start_polling(self._bot)

        finally:
            # Гарантированно освобождаем ресурсы
            await self.stop()

    async def stop(self) -> None:
        """
        Корректно завершает работу.
        """
        logger.info("Остановка WeatherBot...")

        # Останавливаем планировщик
        await self._notification_scheduler.stop()

        # Закрываем ресурсы
        await self._weather_service.close()
        await self._bot.session.close()

        logger.info("WeatherBot остановлен")