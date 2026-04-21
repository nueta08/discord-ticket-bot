"""Миграции базы данных"""

import aiosqlite
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


async def initialize_database(db_path: str) -> None:
    """
    Инициализирует базу данных и создает все необходимые таблицы

    Args:
        db_path: Путь к файлу базы данных
    """
    async with aiosqlite.connect(db_path) as db:
        # Включение foreign keys
        await db.execute("PRAGMA foreign_keys = ON")

        # Таблица тикетов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_number INTEGER NOT NULL UNIQUE,
                channel_id INTEGER NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP NULL,
                closed_by INTEGER NULL,
                topic TEXT NULL
            )
        """)

        # Индексы для таблицы tickets
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tickets_channel_id
            ON tickets(channel_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tickets_user_status
            ON tickets(user_id, status)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tickets_guild_id
            ON tickets(guild_id)
        """)

        # Таблица администраторов тикетов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ticket_admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                added_by INTEGER NOT NULL,
                UNIQUE(guild_id, role_id)
            )
        """)

        # Индекс для таблицы ticket_admins
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_ticket_admins_guild_id
            ON ticket_admins(guild_id)
        """)

        # Таблица участников тикетов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ticket_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                added_by INTEGER NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
                UNIQUE(ticket_id, user_id)
            )
        """)

        # Индекс для таблицы ticket_participants
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_ticket_participants_ticket_id
            ON ticket_participants(ticket_id)
        """)

        # Таблица счетчика тикетов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ticket_counter (
                guild_id INTEGER PRIMARY KEY,
                counter INTEGER NOT NULL DEFAULT 0
            )
        """)

        await db.commit()
        logger.info("Database initialized successfully")


async def reset_database(db_path: str) -> None:
    """
    Удаляет все таблицы (используется для тестирования)

    Args:
        db_path: Путь к файлу базы данных
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute("DROP TABLE IF EXISTS ticket_participants")
        await db.execute("DROP TABLE IF EXISTS ticket_admins")
        await db.execute("DROP TABLE IF EXISTS tickets")
        await db.execute("DROP TABLE IF EXISTS ticket_counter")
        await db.commit()
        logger.warning("Database reset completed")
