

import pytest
import os
import sys
import tempfile

# Добавляем корень проекта в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabaseManager:
    """Тесты для DatabaseManager."""
    
    @pytest.fixture
    def db(self):
        """Создаёт временную базу данных для тестов."""
        from bot.database import DatabaseManager
        
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        manager = DatabaseManager(db_path=db_path)
        yield manager
        
        os.unlink(db_path)
    
    def test_upsert_user(self, db):
        """Тест создания пользователя."""
        db.upsert_user(
            user_id=12345,
            username="testuser",
            first_name="Test",
            last_name="User",
        )
        # Повторный вызов — обновление (не ошибка)
        db.upsert_user(
            user_id=12345,
            username="testuser_updated",
            first_name="Test",
            last_name="User",
        )
    
    def test_save_and_get_history(self, db):
        """Тест сохранения и получения истории."""
        db.upsert_user(1, "user", "First", None)
        
        db.save_request(user_id=1, city_name="Moscow", was_successful=True)
        db.save_request(user_id=1, city_name="London", was_successful=True)
        db.save_request(user_id=1, city_name="BadCity", was_successful=False, error_message="Not found")
        
        history = db.get_user_history(user_id=1)
        
        assert len(history) == 3
        assert history[0]["city_name"] == "BadCity"  # Новые сначала
    
    def test_get_stats(self, db):
        """Тест получения статистики."""
        db.upsert_user(2, None, "Alice", None)
        db.save_request(2, "Paris", True)
        db.save_request(2, "Paris", True)
        db.save_request(2, "Berlin", False)
        
        stats = db.get_user_stats(user_id=2)
        
        assert stats["total_requests"] == 3
        assert stats["successful_requests"] == 2
        assert stats["unique_cities"] == 2
    
    def test_favorite_cities(self, db):
        """Тест избранных городов."""
        db.upsert_user(3, None, "Bob", None)
        
        # Добавляем
        assert db.add_favorite_city(3, "Tokyo") is True
        assert db.add_favorite_city(3, "Seoul") is True
        
        # Дубликат
        assert db.add_favorite_city(3, "Tokyo") is False
        
        # Список
        cities = db.get_favorite_cities(3)
        assert len(cities) == 2
        assert "Tokyo" in cities
        
        # Удаление
        assert db.remove_favorite_city(3, "Tokyo") is True
        assert db.remove_favorite_city(3, "NotExist") is False
        
        cities = db.get_favorite_cities(3)
        assert len(cities) == 1


class TestWeatherModels:
    """Тесты для моделей данных."""
    
    def test_weather_data_emoji(self):
        """Тест эмодзи для WeatherData."""
        from bot.models import WeatherData
        
        weather = WeatherData(
            city="Moscow", country="RU",
            temperature=20, feels_like=18,
            humidity=60, wind_speed=5,
            description="Ясно", icon="01d",
            pressure=1013, visibility=10000, clouds=0,
        )
        
        assert weather.weather_emoji == "☀️"
        assert weather.temperature_rounded == 20
    
    def test_user_request_mark_success(self):
        """Тест модели UserRequest."""
        from bot.models import UserRequest
        
        req = UserRequest(user_id=1, username="test", city_name="  Moscow  ")
        
        # Нормализация: убирает пробелы
        assert req.city_name == "Moscow"
        assert req.was_successful is False
        
        req.mark_success()
        assert req.was_successful is True
    
    def test_user_request_mark_failure(self):
        """Тест ошибки в UserRequest."""
        from bot.models import UserRequest
        
        req = UserRequest(user_id=1, username=None, city_name="xyz")
        req.mark_failure("Город не найден")
        
        assert req.was_successful is False
        assert req.error_message == "Город не найден"
        assert req.display_name == "user_1"


class TestMessageFormatter:
    """Тесты для MessageFormatter."""
    
    def test_format_history_empty(self):
        """Тест форматирования пустой истории."""
        from bot.utils import MessageFormatter
        
        result = MessageFormatter.format_history([])
        assert "пуста" in result.lower()
    
    def test_format_error_city_not_found(self):
        """Тест форматирования ошибки города."""
        from bot.utils import MessageFormatter
        
        result = MessageFormatter.format_error_city_not_found("Xyzzy123")
        assert "Xyzzy123" in result
        assert "не найден" in result.lower()
    
    def test_format_stats(self):
        """Тест форматирования статистики."""
        from bot.utils import MessageFormatter
        
        stats = {
            "total_requests": 10,
            "successful_requests": 8,
            "unique_cities": 5,
        }
        result = MessageFormatter.format_stats(stats)
        
        assert "10" in result
        assert "80.0%" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
