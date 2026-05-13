"""
Фабрика клавиатур для Telegram бота.
Инкапсулирует создание всех inline и reply клавиатур.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class KeyboardFactory:
    """
    Фабрика клавиатур (Factory Pattern).
    
    Принципы ООП:
    - Единственная ответственность: только создание клавиатур
    - Инкапсуляция: детали построения скрыты от других классов
    - Статические методы: не требуют состояния объекта
    
    Все методы возвращают готовые объекты InlineKeyboardMarkup.
    """
    
    @staticmethod
    def main_weather_keyboard(city: str) -> InlineKeyboardMarkup:
        """
        Клавиатура под сообщением с текущей погодой.
        
        Args:
            city: текущий город (для кнопки обновления)
            
        Returns:
            InlineKeyboardMarkup с кнопками действий
        """
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=f"refresh:{city}"
            ),
            InlineKeyboardButton(
                text="📅 Прогноз",
                callback_data=f"forecast:{city}"
            ),
        )
        
        builder.row(
            InlineKeyboardButton(
                text="⭐ В избранное",
                callback_data=f"favorite_add:{city}"
            ),
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="stats"
            ),
        )
        
        return builder.as_markup()
    
    @staticmethod
    def forecast_keyboard(city: str) -> InlineKeyboardMarkup:
        """
        Клавиатура под прогнозом погоды.
        
        Args:
            city: текущий город
        """
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🌡 Текущая погода",
                callback_data=f"current:{city}"
            ),
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=f"refresh_forecast:{city}"
            ),
        )
        
        builder.row(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"refresh:{city}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def favorites_keyboard(cities: list[str]) -> InlineKeyboardMarkup:
        """
        Клавиатура со списком избранных городов.
        
        Args:
            cities: список названий городов
        """
        builder = InlineKeyboardBuilder()
        
        if cities:
            # Кнопка для каждого города
            for city in cities:
                builder.row(
                    InlineKeyboardButton(
                        text=f"🌍 {city}",
                        callback_data=f"current:{city}"
                    ),
                    InlineKeyboardButton(
                        text="❌",
                        callback_data=f"favorite_remove:{city}"
                    ),
                )
        else:
            builder.row(
                InlineKeyboardButton(
                    text="Список пуст. Добавьте города!",
                    callback_data="noop"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="◀️ В меню",
                callback_data="main_menu"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def history_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура под историей запросов."""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🗑 Очистить историю",
                callback_data="history_clear"
            ),
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="main_menu"
            ),
        )
        
        return builder.as_markup()
    
    @staticmethod
    def back_keyboard(callback: str = "main_menu") -> InlineKeyboardMarkup:
        """
        Простая клавиатура с кнопкой "Назад".
        
        Args:
            callback: callback_data для кнопки
        """
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data=callback)
        )
        return builder.as_markup()
    
    @staticmethod
    def error_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура при ошибке."""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🔁 Попробовать снова",
                callback_data="main_menu"
            )
        )
        
        return builder.as_markup()
