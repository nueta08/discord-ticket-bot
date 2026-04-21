import discord
from discord.ui import View, Button
from utils.logger import get_logger

logger = get_logger(__name__)


class TicketControlsView(View):

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="ticket_controls:close"
    )
    async def close_ticket_button(
        self,
        interaction: discord.Interaction,
        button: Button
    ):
        has_permission = await self.bot.permission_service.can_manage_ticket(
            interaction.user,
            interaction.channel
        )

        if not has_permission:
            await interaction.response.send_message(
                "You don't have permission to close this ticket.",
                ephemeral=True
            )
            return

        from views.confirmation import CloseConfirmationModal
        modal = CloseConfirmationModal(self.bot)
        await interaction.response.send_modal(modal)
