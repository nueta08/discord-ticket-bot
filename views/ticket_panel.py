import discord
from discord.ui import View, Button
from utils.logger import get_logger
from services.ticket_service import TicketAlreadyExistsError, CategoryNotFoundError, TicketServiceError

logger = get_logger(__name__)


class TicketPanelView(View):

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Create Ticket",
        style=discord.ButtonStyle.primary,
        emoji="🎫",
        custom_id="ticket_panel:create"
    )
    async def create_ticket_button(
        self,
        interaction: discord.Interaction,
        button: Button
    ):
        await interaction.response.defer(ephemeral=True)

        try:
            existing = await self.bot.ticket_service.get_user_open_ticket(
                interaction.guild_id,
                interaction.user.id
            )

            if existing:
                channel = interaction.guild.get_channel(existing['channel_id'])
                if channel:
                    await interaction.followup.send(
                        f"You already have an open ticket: {channel.mention}",
                        ephemeral=True
                    )
                else:
                    logger.warning(
                        f"Ticket #{existing['ticket_number']} channel {existing['channel_id']} not found, "
                        f"but ticket is still open in database"
                    )
                    await interaction.followup.send(
                        "You already have an open ticket, but the channel was not found. "
                        "Contact an administrator.",
                        ephemeral=True
                    )
                return

            ticket_channel = await self.bot.ticket_service.create_ticket(
                guild=interaction.guild,
                user=interaction.user
            )

            await interaction.followup.send(
                f"Ticket created: {ticket_channel.mention}",
                ephemeral=True
            )

        except TicketAlreadyExistsError:
            await interaction.followup.send(
                "You already have an open ticket.",
                ephemeral=True
            )
        except CategoryNotFoundError:
            await interaction.followup.send(
                "Ticket category not configured. Contact an administrator.",
                ephemeral=True
            )
            logger.error(f"Ticket category not found: {self.bot.config.get('ticket_category_id')}")
        except TicketServiceError as e:
            await interaction.followup.send(
                f"Error creating ticket: {str(e)}",
                ephemeral=True
            )
            logger.error(f"Ticket service error: {e}")
        except Exception as e:
            self.bot.logger.error(f"Error creating ticket: {e}", exc_info=True)
            await interaction.followup.send(
                "An unexpected error occurred while creating the ticket.",
                ephemeral=True
            )
