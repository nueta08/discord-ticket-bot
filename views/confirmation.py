import discord
from utils.logger import get_logger
from services.ticket_service import TicketServiceError

logger = get_logger(__name__)


class CloseConfirmationModal(discord.ui.Modal, title="Close Ticket"):

    reason = discord.ui.TextInput(
        label="Reason (optional)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500,
        placeholder="Enter the reason for closing this ticket..."
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            await self.bot.ticket_service.close_ticket(
                channel=interaction.channel,
                closed_by=interaction.user,
                reason=self.reason.value or None
            )
        except TicketServiceError as e:
            await interaction.followup.send(
                f"Error closing ticket: {str(e)}",
                ephemeral=True
            )
            logger.error(f"Error closing ticket: {e}")
        except Exception as e:
            self.bot.logger.error(f"Error closing ticket: {e}", exc_info=True)
            await interaction.followup.send(
                "An unexpected error occurred while closing the ticket.",
                ephemeral=True
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logger.error(f"Modal error: {error}", exc_info=True)
        try:
            await interaction.response.send_message(
                "An error occurred while processing the form.",
                ephemeral=True
            )
        except:
            pass
