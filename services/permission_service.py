"""Сервис управления правами доступа"""

import discord
from typing import List, Dict
from database import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)


class PermissionService:
    """Сервис для управления правами доступа к тикетам"""

    def __init__(self, bot, db: DatabaseManager):
        """
        Инициализирует сервис

        Args:
            bot: Экземпляр бота
            db: Менеджер базы данных
        """
        self.bot = bot
        self.db = db

    async def can_manage_ticket(
        self,
        user: discord.Member,
        channel: discord.TextChannel
    ) -> bool:
        """
        Проверяет может ли пользователь управлять тикетом

        Args:
            user: Пользователь
            channel: Канал тикета

        Returns:
            True если пользователь может управлять тикетом
        """
        # Владельцы бота
        if user.id in self.bot.config.get('owners', []):
            return True

        # Администраторы сервера
        if user.guild_permissions.administrator:
            return True

        # Проверка ролей администраторов тикетов
        admin_roles = await self.get_admin_roles(user.guild.id)
        user_role_ids = [role.id for role in user.roles]

        if any(role_id in admin_roles for role_id in user_role_ids):
            return True

        # Создатель тикета
        ticket = await self.db.get_ticket_by_channel(channel.id)
        if ticket and ticket['user_id'] == user.id:
            return True

        return False

    async def add_admin_role(
        self,
        guild_id: int,
        role_id: int,
        added_by: int
    ) -> bool:
        """
        Добавляет роль администратора тикетов

        Args:
            guild_id: ID сервера
            role_id: ID роли
            added_by: ID пользователя, который добавил

        Returns:
            True если роль добавлена, False если уже существует
        """
        return await self.db.add_admin_role(guild_id, role_id, added_by)

    async def remove_admin_role(self, guild_id: int, role_id: int) -> bool:
        """
        Удаляет роль администратора тикетов

        Args:
            guild_id: ID сервера
            role_id: ID роли

        Returns:
            True если роль удалена, False если не существовала
        """
        return await self.db.remove_admin_role(guild_id, role_id)

    async def get_admin_roles(self, guild_id: int) -> List[int]:
        """
        Получает список ID ролей администраторов тикетов

        Args:
            guild_id: ID сервера

        Returns:
            Список ID ролей
        """
        return await self.db.get_admin_roles(guild_id)

    def create_ticket_overwrites(
        self,
        guild: discord.Guild,
        user: discord.Member,
        admin_role_ids: List[int]
    ) -> Dict[discord.Role | discord.Member, discord.PermissionOverwrite]:
        """
        Создает permission overwrites для канала тикета

        Args:
            guild: Сервер
            user: Создатель тикета
            admin_role_ids: Список ID ролей администраторов

        Returns:
            Словарь с permission overwrites
        """
        overwrites = {
            # Скрыть от всех
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            # Доступ создателю
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),
            # Доступ боту
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                manage_permissions=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )
        }

        # Добавить роли администраторов тикетов
        for role_id in admin_role_ids:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True,
                    manage_messages=True
                )

        return overwrites

    async def add_user_to_ticket(
        self,
        channel: discord.TextChannel,
        user: discord.Member
    ) -> None:
        """
        Добавляет пользователя в тикет (выдает права доступа)

        Args:
            channel: Канал тикета
            user: Пользователь для добавления
        """
        await channel.set_permissions(
            user,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True
        )
        logger.info(f"Added user {user.id} to ticket channel {channel.id}")

    async def remove_user_from_ticket(
        self,
        channel: discord.TextChannel,
        user: discord.Member
    ) -> None:
        """
        Удаляет пользователя из тикета (убирает права доступа)

        Args:
            channel: Канал тикета
            user: Пользователь для удаления
        """
        await channel.set_permissions(user, overwrite=None)
        logger.info(f"Removed user {user.id} from ticket channel {channel.id}")
