
import sqlite3
import logging
import os
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:

    
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._ensure_directory()
        self._initialize_tables()
        logger.info(f"DatabaseManager инициализирован: {db_path}")
    
    def _ensure_directory(self) -> None:
        directory = os.path.dirname(self._db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row  # Результаты как dict-like объекты
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка базы данных, откат транзакции: {e}")
            raise
        finally:
            conn.close()
    
    def _initialize_tables(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id     INTEGER PRIMARY KEY,
                    username    TEXT,
                    first_name  TEXT,
                    last_name   TEXT,
                    created_at  TEXT NOT NULL,
                    last_active TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS request_history (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         INTEGER NOT NULL,
                    city_name       TEXT NOT NULL,
                    was_successful  INTEGER NOT NULL DEFAULT 1,
                    error_message   TEXT,
                    requested_at    TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorite_cities (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    city_name   TEXT NOT NULL,
                    added_at    TEXT NOT NULL,
                    UNIQUE(user_id, city_name),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_user_id 
                ON request_history(user_id)
            """)
            
            logger.info("Таблицы БД успешно инициализированы")
    
    # ──────────────────────── Users ────────────────────────
    
    def upsert_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str],
    ) -> None:
        now = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, created_at, last_active)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username    = excluded.username,
                    first_name  = excluded.first_name,
                    last_name   = excluded.last_name,
                    last_active = excluded.last_active
            """, (user_id, username, first_name, last_name, now, now))
        
        logger.debug(f"Пользователь {user_id} сохранён/обновлён")
    

    def save_request(
        self,
        user_id: int,
        city_name: str,
        was_successful: bool,
        error_message: Optional[str] = None,
    ) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO request_history 
                    (user_id, city_name, was_successful, error_message, requested_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, city_name, int(was_successful), error_message,
                  datetime.utcnow().isoformat()))
        
        logger.debug(f"Запрос '{city_name}' от {user_id} сохранён")
    
    def get_user_history(self, user_id: int, limit: int = 10) -> list[dict]:

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT city_name, was_successful, requested_at
                FROM request_history
                WHERE user_id = ?
                ORDER BY requested_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_stats(self, user_id: int) -> dict:

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(was_successful) as successful_requests,
                    COUNT(DISTINCT city_name) as unique_cities
                FROM request_history
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else {}
    
    # ──────────────────────── Favorite Cities ────────────────────────
    
    def add_favorite_city(self, user_id: int, city_name: str) -> bool:

        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO favorite_cities (user_id, city_name, added_at)
                    VALUES (?, ?, ?)
                """, (user_id, city_name, datetime.utcnow().isoformat()))
            return True
        except sqlite3.IntegrityError:
            return False

    async def get_all_users_with_favorites(self) -> dict[int, list[str]]:
        query = """
                SELECT user_id, city_name
                FROM favorite_cities
                ORDER BY user_id \
                """

        async with self._connection.execute(query) as cursor:
            rows = await cursor.fetchall()

        result = {}

        for user_id, city_name in rows:
            if user_id not in result:
                result[user_id] = []
            result[user_id].append(city_name)

        return result
    def get_favorite_cities(self, user_id: int) -> list[str]:

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT city_name 
                FROM favorite_cities 
                WHERE user_id = ?
                ORDER BY added_at DESC
            """, (user_id,))
            
            return [row["city_name"] for row in cursor.fetchall()]
    
    def remove_favorite_city(self, user_id: int, city_name: str) -> bool:

        with self._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM favorite_cities 
                WHERE user_id = ? AND city_name = ?
            """, (user_id, city_name))
            
            return cursor.rowcount > 0
    
    def get_last_city(self, user_id: int) -> Optional[str]:

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT city_name 
                FROM request_history
                WHERE user_id = ? AND was_successful = 1
                ORDER BY requested_at DESC
                LIMIT 1
            """, (user_id,))
            
            row = cursor.fetchone()
            return row["city_name"] if row else None
