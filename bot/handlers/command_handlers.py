

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..database import DatabaseManager
from ..keyboards import KeyboardFactory
from ..utils import MessageFormatter

logger = logging.getLogger(__name__)

# Создаём роутер для команд
router = Router(name="commands")


def setup_command_handlers(db: DatabaseManager) -> Router:
    """
    Фабричная функция, настраивает и возвращает роутер команд.
    Dependency Injection: получает DatabaseManager снаружи.
    
    Args:
        db: экземпляр DatabaseManager
        
    Returns:
        Настроенный Router
    """
    
    @router.message(Command("start"))
    async def cmd_start(message: Message) -> None:
        """
        Обработчик команды /start.
        Регистрирует пользователя и показывает приветствие.
        """
        user = message.from_user
        logger.info(f"Пользователь {user.id} запустил бота")
        
        # Сохраняем/обновляем пользователя в БД
        db.upsert_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        
        name = user.first_name or "друг"
        
        welcome_text = (
            f"👋 <b>Привет, {name}!</b>\n\n"
            f"🌤 Я <b>Weather Bot</b> — ваш персональный помощник по погоде.\n\n"
            f"<b>Что я умею:</b>\n"
            f"🌡 Показывать текущую погоду\n"
            f"📅 Давать прогноз на 5 дней\n"
            f"⭐ Сохранять избранные города\n"
            f"📊 Вести историю ваших запросов\n\n"
            f"<b>Как начать:</b>\n"
            f"Просто напишите название города!\n\n"
            f"<i>Например: <code>Алматы</code> или <code>Astana</code></i>\n\n"
            f"📌 Список команд: /help"
        )
        
        await message.answer(welcome_text, parse_mode="HTML")
    
    @router.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        """
        Обработчик команды /help.
        Показывает список всех доступных команд.
        """
        logger.info(f"Пользователь {message.from_user.id} запросил /help")
        
        help_text = (
            f"📖 <b>Список команд</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Основные:</b>\n"
            f"/start — Перезапустить бота\n"
            f"/help — Показать это сообщение\n\n"
            f"<b>Погода:</b>\n"
            f"🌍 <b>Название города</b> — Получить текущую погоду\n"
            f"/favorites — Избранные города\n\n"
            f"<b>История:</b>\n"
            f"/history — История ваших запросов\n"
            f"/stats — Ваша статистика\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Просто введите название города и получите погоду!</i>"
        )
        
        await message.answer(help_text, parse_mode="HTML")
    
    @router.message(Command("history"))
    async def cmd_history(message: Message) -> None:
        """
        Обработчик команды /history.
        Показывает последние 10 запросов пользователя.
        """
        user_id = message.from_user.id
        logger.info(f"Пользователь {user_id} запросил историю")
        
        history = db.get_user_history(user_id=user_id, limit=10)
        formatted = MessageFormatter.format_history(history)
        
        await message.answer(
            formatted,
            parse_mode="HTML",
            reply_markup=KeyboardFactory.history_keyboard(),
        )
    
    @router.message(Command("favorites"))
    async def cmd_favorites(message: Message) -> None:
        """
        Обработчик команды /favorites.
        Показывает список избранных городов.
        """
        user_id = message.from_user.id
        logger.info(f"Пользователь {user_id} запросил избранное")
        
        cities = db.get_favorite_cities(user_id=user_id)
        
        if cities:
            text = f"⭐ <b>Ваши избранные города</b> ({len(cities)}):"
        else:
            text = (
                "⭐ <b>Избранные города</b>\n\n"
                "У вас пока нет избранных городов.\n"
                "Получите погоду для любого города и нажмите ⭐"
            )
        
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=KeyboardFactory.favorites_keyboard(cities),
        )
    
    @router.message(Command("stats"))
    async def cmd_stats(message: Message) -> None:
        """
        Обработчик команды /stats.
        Показывает статистику пользователя.
        """
        user_id = message.from_user.id
        logger.info(f"Пользователь {user_id} запросил статистику")
        
        stats = db.get_user_stats(user_id=user_id)
        formatted = MessageFormatter.format_stats(stats)
        
        await message.answer(
            formatted,
            parse_mode="HTML",
            reply_markup=KeyboardFactory.back_keyboard("main_menu"),
        )

    @router.message(F.text == "/кнопка")
    async def cmd_button(message: Message):
        await message.answer(
            "Нажми кнопку:",
            reply_markup=hello_keyboard()
        )


    @router.callback_query(F.data == "hello")
    async def btn_click(callback: CallbackQuery):
        await callback.message.answer("Hello World!")
        await callback.answer()
    return router
