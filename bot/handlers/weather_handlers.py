"""
Обработчик текстовых сообщений с названием города.
"""

import logging
from aiogram import Router
from aiogram.types import Message

from ..database import DatabaseManager
from ..services import WeatherService, CityNotFoundError, APIConnectionError, WeatherAPIError
from ..keyboards import KeyboardFactory
from ..utils import MessageFormatter
from ..models import UserRequest

logger = logging.getLogger(__name__)

router = Router(name="weather_messages")


def setup_weather_handlers(
    db: DatabaseManager,
    weather_service: WeatherService,
) -> Router:
    """
    Фабричная функция обработчиков погоды.
    
    Args:
        db: менеджер базы данных (DI)
        weather_service: сервис погоды (DI)
        
    Returns:
        Настроенный Router
    """
    
    @router.message()
    async def handle_city_input(message: Message) -> None:
        """
        Обрабатывает любое текстовое сообщение как название города.
        Это последний роутер — ловит всё что не поймали команды.
        """
        user = message.from_user
        city = message.text.strip() if message.text else ""
        
        logger.info(f"Пользователь {user.id} ищет погоду: '{city}'")
        
        # Создаём объект запроса (User Request model)
        request = UserRequest(
            user_id=user.id,
            username=user.username,
            city_name=city,
        )
        
        # Проверка: пустой ввод
        if not city:
            await message.answer(
                MessageFormatter.format_error_empty_input(),
                parse_mode="HTML",
            )
            return
        
        # Проверка: слишком короткий ввод
        if len(city) < 2:
            await message.answer(
                "❗ Название города слишком короткое. Введите не менее 2 символов.",
                parse_mode="HTML",
            )
            return
        
        # Показываем "печатает..." пока грузим данные
        await message.bot.send_chat_action(
            chat_id=message.chat.id,
            action="typing"
        )
        
        try:
            # Запрашиваем погоду
            weather = await weather_service.get_current_weather(city)
            
            # Форматируем ответ
            text = MessageFormatter.format_current_weather(weather)
            
            # Помечаем запрос как успешный
            request.mark_success()
            
            await message.answer(
                text,
                parse_mode="HTML",
                reply_markup=KeyboardFactory.main_weather_keyboard(weather.city),
            )
            
        except CityNotFoundError:
            request.mark_failure("Город не найден")
            
            await message.answer(
                MessageFormatter.format_error_city_not_found(city),
                parse_mode="HTML",
                reply_markup=KeyboardFactory.error_keyboard(),
            )
            
        except APIConnectionError:
            request.mark_failure("Ошибка подключения")
            
            await message.answer(
                MessageFormatter.format_error_connection(),
                parse_mode="HTML",
                reply_markup=KeyboardFactory.error_keyboard(),
            )
            
        except WeatherAPIError as e:
            request.mark_failure(str(e))
            logger.error(f"Ошибка API для '{city}': {e}")
            
            await message.answer(
                f"⚠️ <b>Ошибка сервиса погоды</b>\n\n{e}",
                parse_mode="HTML",
                reply_markup=KeyboardFactory.error_keyboard(),
            )
        
        finally:
            # Всегда сохраняем запрос в историю (успешный или нет)
            db.save_request(
                user_id=request.user_id,
                city_name=request.city_name,
                was_successful=request.was_successful,
                error_message=request.error_message,
            )
    
    return router
