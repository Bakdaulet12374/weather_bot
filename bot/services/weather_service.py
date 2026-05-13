
import logging
import aiohttp
from typing import Optional
from datetime import datetime

from ..config import Config
from ..models import WeatherData, ForecastDay

logger = logging.getLogger(__name__)


class WeatherAPIError(Exception):
    pass


class CityNotFoundError(WeatherAPIError):
    pass


class APIConnectionError(WeatherAPIError):
    pass


class WeatherService:

    def __init__(self, config: Config) -> None:
        self._config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._base_url = "https://api.weatherapi.com/v1"
        logger.info("WeatherService инициализирован (WeatherAPI.com)")

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def _make_request(self, endpoint: str, params: dict) -> dict:
        params["key"] = self._config.weather_api_key
        params["lang"] = self._config.default_lang

        try:
            session = await self._get_session()
            url = f"{self._base_url}/{endpoint}"

            async with session.get(url, params=params) as response:
                data = await response.json()

                if response.status == 200:
                    return data

                elif response.status == 400 or response.status == 404:
                    raise CityNotFoundError(
                        f"Город не найден: {params.get('q', '')}"
                    )

                elif response.status == 403:
                    raise WeatherAPIError("Неверный API ключ WeatherAPI")

                else:
                    error_msg = data.get("error", {}).get("message", "неизвестная ошибка")
                    raise WeatherAPIError(f"Ошибка API: {error_msg}")

        except aiohttp.ClientConnectorError:
            raise APIConnectionError(
                "Не удалось подключиться. Проверьте интернет."
            )
        except aiohttp.ServerTimeoutError:
            raise APIConnectionError("Сервер не ответил. Попробуйте позже.")
        except (CityNotFoundError, WeatherAPIError, APIConnectionError):
            raise
        except Exception as e:
            logger.exception(f"Неожиданная ошибка: {e}")
            raise WeatherAPIError(f"Внутренняя ошибка: {e}")

    async def get_current_weather(self, city: str) -> WeatherData:
        logger.info(f"Запрос текущей погоды для: {city}")
        data = await self._make_request(
            endpoint="current.json",
            params={"q": city},
        )
        return self._parse_current(data)

    async def get_forecast(self, city: str) -> list[ForecastDay]:
        logger.info(f"Запрос прогноза для: {city}")
        data = await self._make_request(
            endpoint="forecast.json",
            params={"q": city, "days": self._config.forecast_days},
        )
        return self._parse_forecast(data)

    def _parse_current(self, data: dict) -> WeatherData:
        loc = data["location"]
        cur = data["current"]
        cond = cur["condition"]


        icon_url = cond.get("icon", "")
        icon_code = icon_url.split("/")[-1].replace(".png", "") if icon_url else "113"

        return WeatherData(
            city=loc["name"],
            country=loc["country"],
            temperature=cur["temp_c"],
            feels_like=cur["feelslike_c"],
            humidity=cur["humidity"],
            wind_speed=cur["wind_kph"] / 3.6,  # km/h → м/с
            description=cond["text"],
            icon=self._map_icon(icon_code, cur.get("is_day", 1)),
            pressure=int(cur["pressure_mb"]),
            visibility=int(cur["vis_km"] * 1000),
            clouds=cur.get("cloud", 0),
        )

    def _parse_forecast(self, data: dict) -> list[ForecastDay]:
        forecast = []
        forecast_days = data.get("forecast", {}).get("forecastday", [])


        for day_data in forecast_days[1:]:
            day = day_data["day"]
            cond = day["condition"]

            dt = datetime.strptime(day_data["date"], "%Y-%m-%d")
            day_names = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
            month_names = {1: "янв", 2: "фев", 3: "мар", 4: "апр", 5: "май", 6: "июн",
                           7: "июл", 8: "авг", 9: "сен", 10: "окт", 11: "ноя", 12: "дек"}
            date_str = f"{day_names[dt.weekday()]}, {dt.day} {month_names[dt.month]}"

            icon_url = cond.get("icon", "")
            icon_code = icon_url.split("/")[-1].replace(".png", "") if icon_url else "113"

            forecast.append(ForecastDay(
                date=date_str,
                temp_min=day["mintemp_c"],
                temp_max=day["maxtemp_c"],
                description=cond["text"],
                icon=self._map_icon(icon_code, 1),
                humidity=day["avghumidity"],
                wind_speed=day["maxwind_kph"] / 3.6,
            ))

        return forecast

    def _map_icon(self, code: str, is_day: int) -> str:

        sunny = {"113"}
        partly_cloudy = {"116"}
        cloudy = {"119", "122"}
        fog = {"143", "248", "260"}
        rain = {"176", "263", "266", "281", "284", "293", "296", "299", "302", "305",
                "308", "311", "314", "317", "320", "353", "356", "359", "362", "365"}
        snow = {"179", "323", "326", "329", "332", "335", "338", "368", "371", "374", "377"}
        thunder = {"200", "386", "389", "392", "395"}

        if code in sunny:
            return "01d" if is_day else "01n"
        elif code in partly_cloudy:
            return "02d"
        elif code in cloudy:
            return "04d"
        elif code in fog:
            return "50d"
        elif code in thunder:
            return "11d"
        elif code in snow:
            return "13d"
        elif code in rain:
            return "10d"
        else:
            return "03d"