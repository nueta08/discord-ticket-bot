"""Сервис управления тикетами"""

import discord
import asyncio
from typing import Optional
from database import DatabaseManager
from utils.logger import get_logger
from utils.constants import TICKET_CHANNEL_NAME_FORMAT, TICKET_CLOSE_DELAY

logger = get_logger(__name__)


class TicketServiceError(Exception):
    """Базовое исключение для ошибок тикет-системы"""
    pass


class TicketAlreadyExistsError(TicketServiceError):
    """Пользователь уже имеет открытый тикет"""
    pass


class TicketNotFoundError(TicketServiceError):
    """Тикет не найден"""
    pass


class CategoryNotFoundError(TicketServiceError):
    """Категория для тикетов не найдена"""
    pass


class TicketService:
    """Сервис для управления тикетами"""

    def __init__(self, bot, db: DatabaseManager):
        """
        Инициализирует сервис

        Args:
            bot: Экземпляр бота
            db: Менеджер базы данных
        """
        self.bot = bot
        self.db = db

    async def create_ticket(
        self,
        guild: discord.Guild,
        user: discord.Member,
        topic: Optional[str] = None
    ) -> discord.TextChannel:
        """
        Создает новый тикет для пользователя

        Args:
            guild: Сервер
            user: Создатель тикета
            topic: Тема тикета (опционально)

        Returns:
            Созданный канал тикета

        Raises:
            TicketAlreadyExistsError: Если у пользователя уже есть открытый тикет
            CategoryNotFoundError: Если категория не найдена
        """
        # 1. Проверка на дубликат
        existing = await self.get_user_open_ticket(guild.id, user.id)
        if existing:
            raise TicketAlreadyExistsError(
                f"User {user.id} already has open ticket: {existing['channel_id']}"
            )

        # 2. Получение номера тикета
        ticket_number = await self.db.increment_ticket_counter(guild.id)

        # 3. Получение ролей администраторов
        admin_role_ids = await self.bot.permission_service.get_admin_roles(guild.id)

        # 4. Создание permission overwrites
        overwrites = self.bot.permission_service.create_ticket_overwrites(
            guild, user, admin_role_ids
        )

        # 5. Создание канала
        category_id = self.bot.config.get('ticket_category_id')
        category = guild.get_channel(category_id)

        if not category or not isinstance(category, discord.CategoryChannel):
            raise CategoryNotFoundError(f"Ticket category not found: {category_id}")

        channel_name = TICKET_CHANNEL_NAME_FORMAT.format(number=ticket_number)

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Тикет #{ticket_number} | Создатель: {user.name} ({user.id})",
                reason=f"Ticket created by {user}"
            )
        except discord.Forbidden:
            raise TicketServiceError("У бота недостаточно прав для создания канала")
        except discord.HTTPException as e:
            raise TicketServiceError(f"Ошибка Discord API: {e}")

        # 6. Сохранение в БД
        await self.db.create_ticket(
            ticket_number=ticket_number,
            channel_id=channel.id,
            user_id=user.id,
            guild_id=guild.id,
            topic=topic
        )

        # 7. Отправка приветственного сообщения
        from views.ticket_controls import TicketControlsView
        from utils.embeds import create_ticket_welcome_embed

        embed = create_ticket_welcome_embed(user, ticket_number)
        view = TicketControlsView(self.bot)

        await channel.send(
            content=f"{user.mention}",
            embed=embed,
            view=view
        )

        # 8. Логирование
        logger.info(
            f"Ticket #{ticket_number} created by {user} ({user.id}) "
            f"in guild {guild.id}, channel {channel.id}"
        )

        return channel

    async def close_ticket(
        self,
        channel: discord.TextChannel,
        closed_by: discord.Member,
        reason: Optional[str] = None
    ) -> None:
        """
        Закрывает тикет

        Args:
            channel: Канал тикета
            closed_by: Кто закрыл тикет
            reason: Причина закрытия (опционально)

        Raises:
            TicketNotFoundError: Если тикет не найден
        """
        # 1. Получение тикета
        ticket = await self.get_ticket_by_channel(channel.id)
        if not ticket:
            raise TicketNotFoundError(f"Ticket not found for channel {channel.id}")

        # 2. Проверка статуса
        if ticket['status'] == 'closed':
            raise TicketServiceError(f"Ticket #{ticket['ticket_number']} is already closed")

        # 3. Сообщение о закрытии
        from utils.embeds import create_warning_embed

        embed = create_warning_embed(
            "Тикет закрывается... Генерация транскрипта..."
        )
        status_msg = await channel.send(embed=embed)

        try:
            # 4. Генерация HTML-транскрипта
            transcript_path = await self.bot.transcript_service.generate_transcript(
                channel=channel,
                ticket=ticket,
                closed_by=closed_by,
                reason=reason
            )

            # 5. Отправка в архивный канал
            archive_channel_id = self.bot.config.get('archive_channel_id')
            archive_channel = channel.guild.get_channel(archive_channel_id)

            if not archive_channel:
                logger.error(f"Archive channel not found: {archive_channel_id}")
                raise TicketServiceError("Архивный канал не настроен")

            # Создание embed для архива
            from utils.embeds import create_archive_embed
            archive_embed = await create_archive_embed(
                self.bot, ticket, closed_by, reason
            )

            # Отправка файла и embed
            with open(transcript_path, 'rb') as f:
                file = discord.File(f, filename=f"ticket-{ticket['ticket_number']}.html")
                await archive_channel.send(embed=archive_embed, file=file)

            # 6. Обновление БД
            await self.db.close_ticket(
                ticket_id=ticket['id'],
                closed_by=closed_by.id
            )

            # 7. Удаление канала
            from utils.embeds import create_error_embed

            await status_msg.edit(
                embed=create_error_embed(
                    f"Тикет закрыт. Канал будет удален через {TICKET_CLOSE_DELAY} секунд..."
                )
            )

            await asyncio.sleep(TICKET_CLOSE_DELAY)
            await channel.delete(reason=f"Ticket closed by {closed_by}")

            # 8. Логирование
            logger.info(
                f"Ticket #{ticket['ticket_number']} closed by {closed_by} ({closed_by.id})"
            )

        except Exception as e:
            logger.error(f"Error closing ticket: {e}", exc_info=True)
            raise

    async def get_ticket_by_channel(self, channel_id: int) -> Optional[dict]:
        """
        Получает тикет по ID канала

        Args:
            channel_id: ID канала

        Returns:
            Словарь с данными тикета или None
        """
        return await self.db.get_ticket_by_channel(channel_id)

    async def get_user_open_ticket(self, guild_id: int, user_id: int) -> Optional[dict]:
        """
        Получает открытый тикет пользователя

        Args:
            guild_id: ID сервера
            user_id: ID пользователя

        Returns:
            Словарь с данными тикета или None
        """
        return await self.db.get_user_open_ticket(guild_id, user_id)

    async def add_user_to_ticket(
        self,
        ticket: dict,
        user: discord.Member,
        added_by: discord.Member
    ) -> None:
        """
        Добавляет пользователя в тикет

        Args:
            ticket: Данные тикета
            user: Пользователь для добавления
            added_by: Кто добавил
        """
        channel = user.guild.get_channel(ticket['channel_id'])
        if not channel:
            raise TicketServiceError("Канал тикета не найден")

        # Выдача прав доступа
        await self.bot.permission_service.add_user_to_ticket(channel, user)

        # Сохранение в БД
        await self.db.add_participant(
            ticket_id=ticket['id'],
            user_id=user.id,
            added_by=added_by.id
        )

        # Уведомление в канале
        await channel.send(f"{user.mention} был добавлен в тикет пользователем {added_by.mention}")

        logger.info(f"User {user.id} added to ticket #{ticket['ticket_number']} by {added_by.id}")

    async def remove_user_from_ticket(
        self,
        ticket: dict,
        user: discord.Member
    ) -> None:
        """
        Удаляет пользователя из тикета

        Args:
            ticket: Данные тикета
            user: Пользователь для удаления
        """
        channel = user.guild.get_channel(ticket['channel_id'])
        if not channel:
            raise TicketServiceError("Канал тикета не найден")

        # Убрать права доступа
        await self.bot.permission_service.remove_user_from_ticket(channel, user)

        # Удаление из БД
        await self.db.remove_participant(
            ticket_id=ticket['id'],
            user_id=user.id
        )

        # Уведомление в канале
        await channel.send(f"{user.mention} был удален из тикета")

        logger.info(f"User {user.id} removed from ticket #{ticket['ticket_number']}")
