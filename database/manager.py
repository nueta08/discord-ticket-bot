"""Менеджер базы данных"""

import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime
from utils.logger import get_logger
from utils.constants import TicketStatus

logger = get_logger(__name__)


class DatabaseManager:
    """Менеджер для работы с базой данных SQLite"""

    def __init__(self, db_path: str = "tickets.db"):
        """
        Инициализирует менеджер базы данных

        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Инициализирует базу данных"""
        from database.migrations import initialize_database
        await initialize_database(self.db_path)
        logger.info(f"Database manager initialized with path: {self.db_path}")

    async def get_connection(self) -> aiosqlite.Connection:
        """Получает соединение с базой данных"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
            await self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    async def close(self) -> None:
        """Закрывает соединение с базой данных"""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    # === Методы для работы с тикетами ===

    async def create_ticket(
        self,
        ticket_number: int,
        channel_id: int,
        user_id: int,
        guild_id: int,
        topic: Optional[str] = None
    ) -> int:
        """
        Создает новый тикет

        Returns:
            ID созданного тикета
        """
        db = await self.get_connection()
        cursor = await db.execute(
            """
            INSERT INTO tickets (ticket_number, channel_id, user_id, guild_id, topic)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticket_number, channel_id, user_id, guild_id, topic)
        )
        await db.commit()
        ticket_id = cursor.lastrowid
        logger.info(f"Created ticket #{ticket_number} (ID: {ticket_id}) for user {user_id}")
        return ticket_id

    async def get_ticket_by_channel(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Получает тикет по ID канала"""
        db = await self.get_connection()
        cursor = await db.execute(
            "SELECT * FROM tickets WHERE channel_id = ?",
            (channel_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_ticket_by_id(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Получает тикет по ID"""
        db = await self.get_connection()
        cursor = await db.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (ticket_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_user_open_ticket(self, guild_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает открытый тикет пользователя"""
        db = await self.get_connection()
        cursor = await db.execute(
            """
            SELECT * FROM tickets
            WHERE guild_id = ? AND user_id = ? AND status = ?
            """,
            (guild_id, user_id, TicketStatus.OPEN.value)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def close_ticket(self, ticket_id: int, closed_by: int) -> None:
        """Закрывает тикет"""
        db = await self.get_connection()
        await db.execute(
            """
            UPDATE tickets
            SET status = ?, closed_at = CURRENT_TIMESTAMP, closed_by = ?
            WHERE id = ?
            """,
            (TicketStatus.CLOSED.value, closed_by, ticket_id)
        )
        await db.commit()
        logger.info(f"Closed ticket ID {ticket_id} by user {closed_by}")

    async def get_all_open_tickets(self, guild_id: int) -> List[Dict[str, Any]]:
        """Получает все открытые тикеты на сервере"""
        db = await self.get_connection()
        cursor = await db.execute(
            """
            SELECT * FROM tickets
            WHERE guild_id = ? AND status = ?
            ORDER BY created_at DESC
            """,
            (guild_id, TicketStatus.OPEN.value)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # === Методы для работы со счетчиком ===

    async def increment_ticket_counter(self, guild_id: int) -> int:
        """
        Увеличивает счетчик тикетов и возвращает новое значение

        Returns:
            Новый номер тикета
        """
        db = await self.get_connection()

        # Получаем текущее значение
        cursor = await db.execute(
            "SELECT counter FROM ticket_counter WHERE guild_id = ?",
            (guild_id,)
        )
        row = await cursor.fetchone()

        if row:
            new_counter = row['counter'] + 1
            await db.execute(
                "UPDATE ticket_counter SET counter = ? WHERE guild_id = ?",
                (new_counter, guild_id)
            )
        else:
            new_counter = 1
            await db.execute(
                "INSERT INTO ticket_counter (guild_id, counter) VALUES (?, ?)",
                (guild_id, new_counter)
            )

        await db.commit()
        logger.debug(f"Incremented ticket counter for guild {guild_id} to {new_counter}")
        return new_counter

    async def get_ticket_counter(self, guild_id: int) -> int:
        """Получает текущее значение счетчика"""
        db = await self.get_connection()
        cursor = await db.execute(
            "SELECT counter FROM ticket_counter WHERE guild_id = ?",
            (guild_id,)
        )
        row = await cursor.fetchone()
        return row['counter'] if row else 0

    # === Методы для работы с администраторами ===

    async def add_admin_role(self, guild_id: int, role_id: int, added_by: int) -> bool:
        """
        Добавляет роль администратора тикетов

        Returns:
            True если роль добавлена, False если уже существует
        """
        db = await self.get_connection()
        try:
            await db.execute(
                """
                INSERT INTO ticket_admins (guild_id, role_id, added_by)
                VALUES (?, ?, ?)
                """,
                (guild_id, role_id, added_by)
            )
            await db.commit()
            logger.info(f"Added admin role {role_id} to guild {guild_id}")
            return True
        except aiosqlite.IntegrityError:
            logger.debug(f"Admin role {role_id} already exists in guild {guild_id}")
            return False

    async def remove_admin_role(self, guild_id: int, role_id: int) -> bool:
        """
        Удаляет роль администратора тикетов

        Returns:
            True если роль удалена, False если не существовала
        """
        db = await self.get_connection()
        cursor = await db.execute(
            "DELETE FROM ticket_admins WHERE guild_id = ? AND role_id = ?",
            (guild_id, role_id)
        )
        await db.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Removed admin role {role_id} from guild {guild_id}")
        return deleted

    async def get_admin_roles(self, guild_id: int) -> List[int]:
        """Получает список ID ролей администраторов"""
        db = await self.get_connection()
        cursor = await db.execute(
            "SELECT role_id FROM ticket_admins WHERE guild_id = ?",
            (guild_id,)
        )
        rows = await cursor.fetchall()
        return [row['role_id'] for row in rows]

    # === Методы для работы с участниками ===

    async def add_participant(
        self,
        ticket_id: int,
        user_id: int,
        added_by: int
    ) -> bool:
        """
        Добавляет участника в тикет

        Returns:
            True если участник добавлен, False если уже существует
        """
        db = await self.get_connection()
        try:
            await db.execute(
                """
                INSERT INTO ticket_participants (ticket_id, user_id, added_by)
                VALUES (?, ?, ?)
                """,
                (ticket_id, user_id, added_by)
            )
            await db.commit()
            logger.info(f"Added participant {user_id} to ticket {ticket_id}")
            return True
        except aiosqlite.IntegrityError:
            logger.debug(f"Participant {user_id} already in ticket {ticket_id}")
            return False

    async def remove_participant(self, ticket_id: int, user_id: int) -> bool:
        """
        Удаляет участника из тикета

        Returns:
            True если участник удален, False если не существовал
        """
        db = await self.get_connection()
        cursor = await db.execute(
            "DELETE FROM ticket_participants WHERE ticket_id = ? AND user_id = ?",
            (ticket_id, user_id)
        )
        await db.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Removed participant {user_id} from ticket {ticket_id}")
        return deleted

    async def get_participants(self, ticket_id: int) -> List[int]:
        """Получает список ID участников тикета"""
        db = await self.get_connection()
        cursor = await db.execute(
            "SELECT user_id FROM ticket_participants WHERE ticket_id = ?",
            (ticket_id,)
        )
        rows = await cursor.fetchall()
        return [row['user_id'] for row in rows]
