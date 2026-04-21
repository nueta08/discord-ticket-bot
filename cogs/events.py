"""Event handlers для бота"""

import discord
from discord.ext import commands
from utils.logger import get_logger

logger = get_logger(__name__)


class Events(commands.Cog):
    """Cog для обработки событий Discord"""

    def __init__(self, bot):
        """
        Инициализирует cog

        Args:
            bot: Экземпляр бота
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Вызывается когда бот готов"""
        logger.info(f"Events cog loaded")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """
        Обработчик удаления канала
        Обновляет статус тикета в БД если канал был удален вручную
        """
        if not isinstance(channel, discord.TextChannel):
            return

        # Проверяем, был ли это канал тикета
        ticket = await self.bot.db.get_ticket_by_channel(channel.id)
        if ticket and ticket['status'] == 'open':
            # Закрываем тикет в БД
            await self.bot.db.close_ticket(
                ticket_id=ticket['id'],
                closed_by=self.bot.user.id  # Закрыт системой
            )
            logger.warning(
                f"Ticket #{ticket['ticket_number']} channel was deleted manually, "
                f"updated status in database"
            )

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Обработчик ошибок команд"""
        if isinstance(error, commands.CommandNotFound):
            return  # Игнорируем неизвестные команды

        logger.error(f"Command error: {error}", exc_info=error)

    @commands.Cog.listener()
    async def on_error(self, event: str, *args, **kwargs):
        """Обработчик общих ошибок"""
        logger.error(f"Error in event {event}", exc_info=True)


async def setup(bot):
    """Загружает cog"""
    await bot.add_cog(Events(bot))
