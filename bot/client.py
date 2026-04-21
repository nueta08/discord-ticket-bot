import discord
from discord.ext import commands
from typing import Optional
from database import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)


class TicketBot(commands.Bot):

    def __init__(self, config: dict):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )

        self.config = config
        self.logger = logger

        self.db: Optional[DatabaseManager] = None
        self.ticket_service = None
        self.permission_service = None
        self.transcript_service = None

    async def setup_hook(self):
        self.logger.info("Running setup hook...")

        self.db = DatabaseManager('tickets.db')
        await self.db.initialize()
        self.logger.info("Database initialized")

        from services.ticket_service import TicketService
        from services.permission_service import PermissionService
        from services.transcript_service import TranscriptService

        self.ticket_service = TicketService(self, self.db)
        self.permission_service = PermissionService(self, self.db)
        self.transcript_service = TranscriptService(self, self.db)
        self.logger.info("Services initialized")

        from views.ticket_panel import TicketPanelView
        from views.ticket_controls import TicketControlsView

        self.add_view(TicketPanelView(self))
        self.add_view(TicketControlsView(self))
        self.logger.info("Persistent views registered")

        await self.load_extension('cogs.ticket_commands')
        await self.load_extension('cogs.admin_commands')
        await self.load_extension('cogs.events')
        self.logger.info("Cogs loaded")

        guild = discord.Object(id=self.config['guild_id'])
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        self.logger.info(f"Commands synced to guild {self.config['guild_id']}")

    async def on_ready(self):
        self.logger.info(f"Bot is ready! Logged in as {self.user} (ID: {self.user.id})")
        self.logger.info(f"Connected to {len(self.guilds)} guild(s)")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="tickets | /ticket_panel"
            )
        )

    async def close(self):
        self.logger.info("Shutting down bot...")

        if self.db:
            await self.db.close()

        await super().close()
        self.logger.info("Bot shutdown complete")
