"""Slash-команды для администрирования тикетов"""

import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import get_logger

logger = get_logger(__name__)


class AdminCommands(commands.Cog):
    """Cog с командами администрирования"""

    def __init__(self, bot):
        """
        Инициализирует cog

        Args:
            bot: Экземпляр бота
        """
        self.bot = bot

    @app_commands.command(
        name="ticket_panel",
        description="Отправить панель создания тикетов"
    )
    @app_commands.default_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        """Отправляет панель с кнопкой создания тикета"""
        from views.ticket_panel import TicketPanelView
        from utils.embeds import create_ticket_panel_embed

        embed = create_ticket_panel_embed(self.bot.config)
        view = TicketPanelView(self.bot)

        await interaction.response.send_message(embed=embed, view=view)
        logger.info(f"Ticket panel sent by {interaction.user} in channel {interaction.channel_id}")

    @app_commands.command(
        name="ticket_admin_add",
        description="Добавить роль администратора тикетов"
    )
    @app_commands.describe(role="Роль для добавления")
    @app_commands.default_permissions(administrator=True)
    async def ticket_admin_add(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):
        """Добавляет роль в список администраторов тикетов"""
        await interaction.response.defer(ephemeral=True)

        # Проверка что роль не @everyone
        if role.is_default():
            await interaction.followup.send(
                "❌ Нельзя добавить роль @everyone в администраторы тикетов.",
                ephemeral=True
            )
            return

        success = await self.bot.permission_service.add_admin_role(
            guild_id=interaction.guild_id,
            role_id=role.id,
            added_by=interaction.user.id
        )

        if success:
            await interaction.followup.send(
                f"✅ Роль {role.mention} добавлена в администраторы тикетов.",
                ephemeral=True
            )
            logger.info(f"Admin role {role.id} added by {interaction.user.id}")
        else:
            await interaction.followup.send(
                f"⚠️ Роль {role.mention} уже является администратором тикетов.",
                ephemeral=True
            )

    @app_commands.command(
        name="ticket_admin_remove",
        description="Удалить роль администратора тикетов"
    )
    @app_commands.describe(role="Роль для удаления")
    @app_commands.default_permissions(administrator=True)
    async def ticket_admin_remove(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):
        """Удаляет роль из списка администраторов тикетов"""
        await interaction.response.defer(ephemeral=True)

        success = await self.bot.permission_service.remove_admin_role(
            guild_id=interaction.guild_id,
            role_id=role.id
        )

        if success:
            await interaction.followup.send(
                f"✅ Роль {role.mention} удалена из администраторов тикетов.",
                ephemeral=True
            )
            logger.info(f"Admin role {role.id} removed by {interaction.user.id}")
        else:
            await interaction.followup.send(
                f"⚠️ Роль {role.mention} не является администратором тикетов.",
                ephemeral=True
            )

    @app_commands.command(
        name="ticket_admin_list",
        description="Список ролей администраторов тикетов"
    )
    @app_commands.default_permissions(administrator=True)
    async def ticket_admin_list(self, interaction: discord.Interaction):
        """Показывает список ролей администраторов тикетов"""
        roles = await self.bot.permission_service.get_admin_roles(
            interaction.guild_id
        )

        if not roles:
            await interaction.response.send_message(
                "ℹ️ Нет настроенных ролей администраторов тикетов.",
                ephemeral=True
            )
            return

        role_mentions = []
        for role_id in roles:
            role = interaction.guild.get_role(role_id)
            if role:
                role_mentions.append(f"• {role.mention} (`{role.id}`)")
            else:
                role_mentions.append(f"• Удаленная роль (`{role_id}`)")

        embed = discord.Embed(
            title="👑 Администраторы тикетов",
            description="\n".join(role_mentions) if role_mentions else "Нет ролей",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Всего ролей: {len(roles)}")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    """Загружает cog"""
    await bot.add_cog(AdminCommands(bot))
