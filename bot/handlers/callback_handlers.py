

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from ..database import DatabaseManager
from ..services import WeatherService, CityNotFoundError, APIConnectionError, WeatherAPIError
from ..keyboards import KeyboardFactory
from ..utils import MessageFormatter

logger = logging.getLogger(__name__)

router = Router(name="callbacks")


def setup_callback_handlers(
    db: DatabaseManager,
    weather_service: WeatherService,
) -> Router:

    
    async def _send_weather(callback: CallbackQuery, city: str) -> None:

        await callback.message.bot.send_chat_action(
            chat_id=callback.message.chat.id,
            action="typing"
        )
        
        try:
            weather = await weather_service.get_current_weather(city)
            text = MessageFormatter.format_current_weather(weather)
            
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=KeyboardFactory.main_weather_keyboard(weather.city),
            )
            
            db.save_request(
                user_id=callback.from_user.id,
                city_name=weather.city,
                was_successful=True,
            )
            
        except CityNotFoundError:
            await callback.answer("❌ Город не найден", show_alert=True)
            
        except APIConnectionError:
            await callback.answer(
                "🌐 Ошибка подключения. Попробуйте позже.",
                show_alert=True
            )
            
        except WeatherAPIError as e:
            await callback.answer(f"⚠️ {e}", show_alert=True)
    

    @router.callback_query(F.data.startswith("refresh:"))
    async def cb_refresh_weather(callback: CallbackQuery) -> None:
        city = callback.data.split(":", 1)[1]
        logger.info(f"Обновление погоды для '{city}' от {callback.from_user.id}")
        
        await callback.answer("🔄 Обновляю...")
        await _send_weather(callback, city)
    

    @router.callback_query(F.data.startswith("current:"))
    async def cb_current_weather(callback: CallbackQuery) -> None:
        city = callback.data.split(":", 1)[1]
        logger.info(f"Текущая погода '{city}' от {callback.from_user.id}")
        
        await callback.answer("🌡 Загружаю...")
        await _send_weather(callback, city)
    

    @router.callback_query(F.data.startswith("forecast:"))
    async def cb_show_forecast(callback: CallbackQuery) -> None:
        city = callback.data.split(":", 1)[1]
        logger.info(f"Прогноз для '{city}' от {callback.from_user.id}")
        
        await callback.answer("📅 Загружаю прогноз...")
        
        try:
            forecast = await weather_service.get_forecast(city)
            
            if not forecast:
                await callback.answer(
                    "Прогноз недоступен для этого города.",
                    show_alert=True
                )
                return
            
            text = MessageFormatter.format_forecast(city, forecast)
            
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=KeyboardFactory.forecast_keyboard(city),
            )
            
        except (CityNotFoundError, APIConnectionError, WeatherAPIError) as e:
            await callback.answer(f"⚠️ Ошибка: {e}", show_alert=True)
    

    @router.callback_query(F.data.startswith("refresh_forecast:"))
    async def cb_refresh_forecast(callback: CallbackQuery) -> None:
        city = callback.data.split(":", 1)[1]
        await callback.answer("🔄 Обновляю прогноз...")
        
        callback.data = f"forecast:{city}"
        await cb_show_forecast(callback)
    

    @router.callback_query(F.data.startswith("favorite_add:"))
    async def cb_add_favorite(callback: CallbackQuery) -> None:
        city = callback.data.split(":", 1)[1]
        user_id = callback.from_user.id
        
        added = db.add_favorite_city(user_id=user_id, city_name=city)
        
        if added:
            await callback.answer(f"⭐ {city} добавлен в избранное!")
            logger.info(f"Пользователь {user_id} добавил '{city}' в избранное")
        else:
            await callback.answer(f"❕ {city} уже в вашем избранном")
    

    @router.callback_query(F.data.startswith("favorite_remove:"))
    async def cb_remove_favorite(callback: CallbackQuery) -> None:
        city = callback.data.split(":", 1)[1]
        user_id = callback.from_user.id
        
        removed = db.remove_favorite_city(user_id=user_id, city_name=city)
        
        if removed:
            await callback.answer(f"🗑 {city} удалён из избранного")
            
            cities = db.get_favorite_cities(user_id=user_id)
            text = (
                f"⭐ <b>Ваши избранные города</b> ({len(cities)}):"
                if cities else
                "⭐ <b>Избранные города</b>\n\nСписок пуст."
            )
            
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=KeyboardFactory.favorites_keyboard(cities),
            )
        else:
            await callback.answer("Город не найден в избранном")
    
    # ──────────────── Кнопка "Статистика" ────────────────
    
    @router.callback_query(F.data == "stats")
    async def cb_stats(callback: CallbackQuery) -> None:
        """Показывает статистику пользователя."""
        stats = db.get_user_stats(user_id=callback.from_user.id)
        text = MessageFormatter.format_stats(stats)
        
        await callback.answer()
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=KeyboardFactory.back_keyboard("main_menu"),
        )
    

    @router.callback_query(F.data == "history_clear")
    async def cb_clear_history(callback: CallbackQuery) -> None:
        """Информирует что очистка пока недоступна (можно реализовать)."""
        await callback.answer(
            "ℹ️ Очистка истории будет добавлена в следующей версии",
            show_alert=True
        )
    

    @router.callback_query(F.data == "main_menu")
    async def cb_main_menu(callback: CallbackQuery) -> None:
        await callback.answer()
        await callback.message.edit_text(
            "🏠 <b>Главное меню</b>\n\nВведите название города для получения погоды!",
            parse_mode="HTML",
        )
    

    
    @router.callback_query(F.data == "noop")
    async def cb_noop(callback: CallbackQuery) -> None:
        await callback.answer()

    @router.callback_query(F.data == "hello_world")
    async def cb_hello_world(callback: CallbackQuery) -> None:
        await callback.answer()
        await callback.message.answer("Привет мир!")

    return router
    return router
