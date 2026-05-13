"""
Утилиты форматирования сообщений.
Отвечают за преобразование данных в красивые Telegram-сообщения.
"""

from ..models import WeatherData, ForecastDay


class MessageFormatter:
    """
    Форматирует данные о погоде в текстовые сообщения для Telegram.
    
    Принцип единственной ответственности:
    - только форматирование, никакой бизнес-логики
    - использует HTML-разметку Telegram
    """
    
    @staticmethod
    def format_current_weather(weather: WeatherData) -> str:
        """
        Форматирует текущую погоду.
        
        Args:
            weather: данные о текущей погоде
            
        Returns:
            Отформатированная строка с HTML-разметкой
        """
        emoji = weather.weather_emoji
        
        return (
            f"{emoji} <b>Погода в {weather.city}, {weather.country}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌡 <b>Температура:</b> {weather.temperature_rounded}°C\n"
            f"🤔 <b>Ощущается как:</b> {weather.feels_like_rounded}°C\n"
            f"💧 <b>Влажность:</b> {weather.humidity}%\n"
            f"💨 <b>Ветер:</b> {weather.wind_speed_rounded} м/с\n"
            f"📋 <b>Описание:</b> {weather.description}\n"
            f"☁️ <b>Облачность:</b> {weather.clouds}%\n"
            f"👁 <b>Видимость:</b> {weather.visibility // 1000} км\n"
            f"📊 <b>Давление:</b> {weather.pressure} гПа\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Нажмите 🔄 для обновления</i>"
        )
    
    @staticmethod
    def format_forecast(city: str, forecast: list[ForecastDay]) -> str:
        """
        Форматирует прогноз на несколько дней.
        
        Args:
            city: название города
            forecast: список дней прогноза
            
        Returns:
            Отформатированная строка
        """
        lines = [f"📅 <b>Прогноз погоды для {city}</b>\n"]
        
        for day in forecast:
            emoji = day.weather_emoji
            lines.append(
                f"{emoji} <b>{day.date}</b>\n"
                f"   🌡 {round(day.temp_min)}°C ... {round(day.temp_max)}°C\n"
                f"   💧 {day.humidity}%  💨 {round(day.wind_speed, 1)} м/с\n"
                f"   📋 {day.description}\n"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def format_history(history: list[dict]) -> str:
        """
        Форматирует историю запросов.
        
        Args:
            history: список словарей с историей
            
        Returns:
            Отформатированная строка
        """
        if not history:
            return "📭 <b>История запросов пуста</b>\n\nВведите название города, чтобы узнать погоду!"
        
        lines = ["📜 <b>Ваша история запросов</b>\n"]
        
        for i, item in enumerate(history, 1):
            status = "✅" if item["was_successful"] else "❌"
            city = item["city_name"]
            
            # Форматируем дату (убираем микросекунды)
            raw_date = item["requested_at"][:16].replace("T", " ")
            
            lines.append(f"{i}. {status} <b>{city}</b> — <i>{raw_date}</i>")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_stats(stats: dict) -> str:
        """
        Форматирует статистику пользователя.
        
        Args:
            stats: словарь со статистикой
            
        Returns:
            Отформатированная строка
        """
        if not stats:
            return "📊 Статистика пока недоступна."
        
        total = stats.get("total_requests", 0)
        successful = stats.get("successful_requests", 0) or 0
        unique = stats.get("unique_cities", 0)
        
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return (
            f"📊 <b>Ваша статистика</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 Всего запросов: <b>{total}</b>\n"
            f"✅ Успешных: <b>{successful}</b>\n"
            f"🌍 Уникальных городов: <b>{unique}</b>\n"
            f"📈 Успешность: <b>{success_rate:.1f}%</b>\n"
        )
    
    @staticmethod
    def format_error_city_not_found(city: str) -> str:
        """Сообщение об ошибке — город не найден."""
        return (
            f"❌ <b>Город «{city}» не найден</b>\n\n"
            f"Возможные причины:\n"
            f"• Опечатка в названии\n"
            f"• Используйте английское название\n"
            f"• Проверьте правильность написания\n\n"
            f"<i>Пример: Moscow, London, Almaty</i>"
        )
    
    @staticmethod
    def format_error_connection() -> str:
        """Сообщение об ошибке подключения."""
        return (
            f"🌐 <b>Ошибка подключения</b>\n\n"
            f"Не удалось получить данные о погоде.\n"
            f"Проверьте интернет-соединение и попробуйте снова."
        )
    
    @staticmethod
    def format_error_empty_input() -> str:
        """Сообщение об ошибке — пустой ввод."""
        return (
            f"✏️ <b>Введите название города</b>\n\n"
            f"Просто напишите название города, например:\n"
            f"<code>Алматы</code> или <code>London</code>"
        )
