
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """
    Класс конфигурации приложения.
    
    Принцип: Single Responsibility — отвечает только за хранение настроек.
    Использует dataclass для чистоты и читаемости.
    """
    
    # Telegram Bot
    bot_token: str
    
    weather_api_key: str
    weather_base_url: str = "https://api.openweathermap.org/data/2.5"
    weather_forecast_url: str = "https://api.openweathermap.org/data/2.5/forecast"
    
    # База данных
    db_path: str = "data/weather_bot.db"
    
    # Настройки погоды
    default_units: str = "metric"       # metric = Цельсий, imperial = Фаренгейт
    default_lang: str = "ru"            # Язык описания погоды
    forecast_days: int = 5              # Количество дней прогноза
    
    # Логирование
    log_level: str = "INFO"
    log_file: str = "logs/bot.log"
    
    @classmethod
    def from_env(cls) -> "Config":
        """
        Фабричный метод: создаёт Config из переменных окружения.
        
        Returns:
            Config: настроенный объект конфигурации
            
        Raises:
            ValueError: если обязательные переменные не заданы
        """
        bot_token = os.getenv("BOT_TOKEN")
        weather_api_key = os.getenv("WEATHER_API_KEY")
        
        if not bot_token:
            raise ValueError(
                "BOT_TOKEN не найден. Проверьте файл .env"
            )
        
        if not weather_api_key:
            raise ValueError(
                "WEATHER_API_KEY не найден. Проверьте файл .env"
            )
        
        return cls(
            bot_token=bot_token,
            weather_api_key=weather_api_key,
            db_path=os.getenv("DB_PATH", "data/weather_bot.db"),
            default_units=os.getenv("DEFAULT_UNITS", "metric"),
            default_lang=os.getenv("DEFAULT_LANG", "ru"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
    
    def __repr__(self) -> str:
        """Скрываем токены при выводе."""
        return (
            f"Config(bot_token='***', weather_api_key='***', "
            f"db_path='{self.db_path}', units='{self.default_units}')"
        )
