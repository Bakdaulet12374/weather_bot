from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


class NotificationScheduler:
    def __init__(self, bot, db_manager, weather_service):
        self._bot = bot
        self._db_manager = db_manager
        self._weather_service = weather_service
        self._scheduler = AsyncIOScheduler()

    def start(self):
        self._scheduler.add_job(
            self.send_weather_notifications,
            CronTrigger(hour=8, minute=0),
            id="morning_weather_notifications",
            replace_existing=True
        )

        self._scheduler.add_job(
            self.send_weather_notifications,
            CronTrigger(hour=13, minute=0),
            id="afternoon_weather_notifications",
            replace_existing=True
        )

        self._scheduler.add_job(
            self.send_weather_notifications,
            CronTrigger(hour=19, minute=0),
            id="evening_weather_notifications",
            replace_existing=True
        )

        self._scheduler.start()

    async def stop(self):
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    async def send_weather_notifications(self):
        users_with_favorites = await self._db_manager.get_all_users_with_favorites()

        if not users_with_favorites:
            return

        for user_id, cities in users_with_favorites.items():
            for city in cities:
                try:
                    weather = await self._weather_service.get_weather(city)

                    if not weather:
                        continue

                    temperature = weather["main"]["temp"]
                    feels_like = weather["main"]["feels_like"]
                    description = weather["weather"][0]["description"]
                    humidity = weather["main"]["humidity"]

                    message = (
                        f"🌤 Погода в {city}\n\n"
                        f"🌡 Температура: {temperature}°C\n"
                        f"🤗 Ощущается как: {feels_like}°C\n"
                        f"📝 {description}\n"
                        f"💧 Влажность: {humidity}%"
                    )

                    await self._bot.send_message(
                        chat_id=user_id,
                        text=message
                    )

                except Exception as e:
                    print(f"Ошибка отправки уведомления {user_id}: {e}")