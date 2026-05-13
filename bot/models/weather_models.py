"""
Модели данных (Data Models).
Используем dataclasses вместо обычных словарей — типизация и автодокументация.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UserRequest:
    """
    Модель запроса пользователя к боту.
    
    Хранит всю информацию об одном запросе погоды.
    Принцип инкапсуляции: поля сгруппированы логично.
    """
    
    user_id: int                          # Telegram ID пользователя
    username: Optional[str]               # @username (может быть None)
    city_name: str                        # Запрошенный город
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Заполняется после получения ответа от API
    was_successful: bool = False
    error_message: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Нормализация данных после инициализации."""
        self.city_name = self.city_name.strip()
    
    @property
    def display_name(self) -> str:
        """Отображаемое имя пользователя."""
        return self.username or f"user_{self.user_id}"
    
    def mark_success(self) -> None:
        """Помечает запрос как успешный."""
        self.was_successful = True
    
    def mark_failure(self, error: str) -> None:
        """Помечает запрос как неудачный с сообщением ошибки."""
        self.was_successful = False
        self.error_message = error


@dataclass
class WeatherData:
    """
    Модель данных о текущей погоде.
    
    Содержит обработанные данные от OpenWeatherMap API.
    Удобно передавать между слоями приложения.
    """
    
    city: str
    country: str
    temperature: float          # °C
    feels_like: float           # °C (ощущается как)
    humidity: int               # %
    wind_speed: float           # м/с
    description: str            # "небольшой дождь"
    icon: str                   # Код иконки (e.g. "10d")
    pressure: int               # гПа
    visibility: int             # метры
    clouds: int                 # % облачности
    
    @property
    def temperature_rounded(self) -> int:
        return round(self.temperature)
    
    @property
    def feels_like_rounded(self) -> int:
        return round(self.feels_like)
    
    @property
    def wind_speed_rounded(self) -> float:
        return round(self.wind_speed, 1)
    
    @property
    def weather_emoji(self) -> str:
        """Возвращает эмодзи на основе кода иконки."""
        icon_map = {
            "01": "☀️",   # ясно
            "02": "🌤",   # немного облаков
            "03": "☁️",   # облачно
            "04": "☁️",   # пасмурно
            "09": "🌧",   # дождь
            "10": "🌦",   # дождь с солнцем
            "11": "⛈",   # гроза
            "13": "❄️",   # снег
            "50": "🌫",   # туман
        }
        prefix = self.icon[:2] if self.icon else "01"
        return icon_map.get(prefix, "🌡")


@dataclass
class ForecastDay:
    """
    Модель одного дня прогноза погоды.
    """
    
    date: str               # "Пт, 17 янв"
    temp_min: float
    temp_max: float
    description: str
    icon: str
    humidity: int
    wind_speed: float
    
    @property
    def weather_emoji(self) -> str:
        icon_map = {
            "01": "☀️", "02": "🌤", "03": "☁️", "04": "☁️",
            "09": "🌧", "10": "🌦", "11": "⛈", "13": "❄️", "50": "🌫",
        }
        prefix = self.icon[:2] if self.icon else "01"
        return icon_map.get(prefix, "🌡")
