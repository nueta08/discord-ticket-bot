"""Slash-команды для работы с тикетами"""

import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import get_logger
from services.ticket_service import TicketServiceError, TicketNotFoundError

logger = get_logger(__name__)


class TicketCommands(commands.Cog):
    """Cog с командами для работы с тикетами"""

    def __init__(self, bot):
        """
        Инициализирует cog

        Args:
            bot: Экземпляр бота
        """
        self.bot = bot

    @app_commands.command(
        name="ticket_close",
        description="Закрыть текущий тикет"
    )
    @app_commands.describe(reason="Причина закрытия (опционально)")
    async def ticket_close(
        self,
        interaction: discord.Interaction,
        reason: str = None
    ):
        """Закрывает тикет через команду"""
        # Проверка что это канал тикета
        ticket = await self.bot.ticket_service.get_ticket_by_channel(
            interaction.channel_id
        )

        if not ticket:
            await interaction.response.send_message(
                "❌ Эта команда работает только в каналах тикетов.",
                ephemeral=True
            )
            return

        # Проверка прав
        has_permission = await self.bot.permission_service.can_manage_ticket(
            interaction.user,
            interaction.channel
        )

        if not has_permission:
            await interaction.response.send_message(
                "❌ У вас нет прав для закрытия этого тикета.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            await self.bot.ticket_service.close_ticket(
                channel=interaction.channel,
                closed_by=interaction.user,
                reason=reason
            )
        except TicketServiceError as e:
            await interaction.followup.send(
                f"❌ Ошибка при закрытии тикета: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name="ticket_info",
        description="Информация о текущем тикете"
    )
    async def ticket_info(self, interaction: discord.Interaction):
        """Показывает информацию о тикете"""
        ticket = await self.bot.ticket_service.get_ticket_by_channel(
            interaction.channel_id
        )

        if not ticket:
            await interaction.response.send_message(
                "❌ Эта команда работает только в каналах тикетов.",
                ephemeral=True
            )
            return

        from utils.embeds import create_ticket_info_embed
        embed = await create_ticket_info_embed(self.bot, ticket)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="ticket_rename",
        description="Переименовать канал тикета"
    )
    @app_commands.describe(new_name="Новое название канала")
    async def ticket_rename(
        self,
        interaction: discord.Interaction,
        new_name: str
    ):
        """Переименовывает канал тикета"""
        ticket = await self.bot.ticket_service.get_ticket_by_channel(
            interaction.channel_id
        )

        if not ticket:
            await interaction.response.send_message(
                "❌ Эта команда работает только в каналах тикетов.",
                ephemeral=True
            )
            return

        has_permission = await self.bot.permission_service.can_manage_ticket(
            interaction.user,
            interaction.channel
        )

        if not has_permission:
            await interaction.response.send_message(
                "❌ У вас нет прав для переименования этого тикета.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # Валидация имени (Discord требования)
        validated_name = new_name.lower().replace(' ', '-')
        validated_name = ''.join(c for c in validated_name if c.isalnum() or c in '-_')

        if not validated_name:
            await interaction.followup.send(
                "❌ Неверное название канала.",
                ephemeral=True
            )
            return

        try:
            await interaction.channel.edit(
                name=validated_name,
                reason=f"Renamed by {interaction.user}"
            )
            await interaction.followup.send(
                f"✅ Канал переименован в: `{validated_name}`"
            )
            logger.info(f"Ticket #{ticket['ticket_number']} renamed to {validated_name} by {interaction.user.id}")
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ У бота недостаточно прав для переименования канала.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.followup.send(
                f"❌ Ошибка при переименовании: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name="ticket_add",
        description="Добавить пользователя в тикет"
    )
    @app_commands.describe(user="Пользователь для добавления")
    async def ticket_add(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):
        """Добавляет пользователя в тикет"""
        ticket = await self.bot.ticket_service.get_ticket_by_channel(
            interaction.channel_id
        )

        if not ticket:
            await interaction.response.send_message(
                "❌ Эта команда работает только в каналах тикетов.",
                ephemeral=True
            )
            return

        has_permission = await self.bot.permission_service.can_manage_ticket(
            interaction.user,
            interaction.channel
        )

        if not has_permission:
            await interaction.response.send_message(
                "❌ У вас нет прав для добавления пользователей.",
                ephemeral=True
            )
            return

        # Проверка что пользователь не бот
        if user.bot:
            await interaction.response.send_message(
                "❌ Нельзя добавить бота в тикет.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            await self.bot.ticket_service.add_user_to_ticket(
                ticket=ticket,
                user=user,
                added_by=interaction.user
            )

            await interaction.followup.send(
                f"✅ {user.mention} добавлен в тикет."
            )
        except TicketServiceError as e:
            await interaction.followup.send(
                f"❌ Ошибка: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name="ticket_remove",
        description="Убрать пользователя из тикета"
    )
    @app_commands.describe(user="Пользователь для удаления")
    async def ticket_remove(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):
        """Убирает пользователя из тикета"""
        ticket = await self.bot.ticket_service.get_ticket_by_channel(
            interaction.channel_id
        )

        if not ticket:
            await interaction.response.send_message(
                "❌ Эта команда работает только в каналах тикетов.",
                ephemeral=True
            )
            return

        has_permission = await self.bot.permission_service.can_manage_ticket(
            interaction.user,
            interaction.channel
        )

        if not has_permission:
            await interaction.response.send_message(
                "❌ У вас нет прав для удаления пользователей.",
                ephemeral=True
            )
            return

        # Нельзя удалить создателя тикета
        if user.id == ticket['user_id']:
            await interaction.response.send_message(
                "❌ Нельзя удалить создателя тикета.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            await self.bot.ticket_service.remove_user_from_ticket(
                ticket=ticket,
                user=user
            )

            await interaction.followup.send(
                f"✅ {user.mention} удален из тикета."
            )
        except TicketServiceError as e:
            await interaction.followup.send(
                f"❌ Ошибка: {str(e)}",
                ephemeral=True
            )


async def setup(bot):
    """Загружает cog"""
    await bot.add_cog(TicketCommands(bot))
