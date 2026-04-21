import discord
from datetime import datetime
from typing import Optional
from utils.constants import Colors, Emojis


def create_ticket_panel_embed(config: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"{Emojis.TICKET} Ticket System",
        description=(
            "Click the button below to create a ticket.\n\n"
            "**What is a ticket?**\n"
            "A ticket is a private channel for communicating with server staff.\n\n"
            "**Rules:**\n"
            f"{Emojis.SUCCESS} One ticket per user at a time\n"
            f"{Emojis.SUCCESS} Be respectful and patient\n"
            f"{Emojis.SUCCESS} Describe your issue clearly"
        ),
        color=int(config.get('embed_color', '#5865F2').replace('#', '0x'), 16)
    )
    embed.set_footer(text="Click the button below to create a ticket")
    return embed


def create_ticket_welcome_embed(user: discord.Member, ticket_number: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"{Emojis.TICKET} Ticket #{ticket_number}",
        description=(
            f"Welcome, {user.mention}!\n\n"
            "Staff will respond to your request shortly.\n"
            "Please describe your issue or question in detail.\n\n"
            f"{Emojis.INFO} To close this ticket, use the button below."
        ),
        color=Colors.SUCCESS.value,
        timestamp=datetime.utcnow()
    )
    embed.add_field(
        name=f"{Emojis.USER} Creator",
        value=f"{user.mention} (`{user.id}`)",
        inline=True
    )
    embed.add_field(
        name=f"{Emojis.CLOCK} Created",
        value=f"<t:{int(datetime.utcnow().timestamp())}:R>",
        inline=True
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    return embed

    embed.set_thumbnail(url=user.display_avatar.url)
    return embed


async def create_ticket_info_embed(bot, ticket: dict) -> discord.Embed:
    creator = await bot.fetch_user(ticket['user_id'])

    embed = discord.Embed(
        title=f"{Emojis.INFO} Ticket Information",
        color=Colors.INFO.value,
        timestamp=datetime.utcnow()
    )

    embed.add_field(
        name="Ticket Number",
        value=f"#{ticket['ticket_number']}",
        inline=True
    )
    embed.add_field(
        name="Status",
        value=f"{Emojis.UNLOCK if ticket['status'] == 'open' else Emojis.LOCK} {ticket['status'].upper()}",
        inline=True
    )
    embed.add_field(
        name="Channel ID",
        value=f"`{ticket['channel_id']}`",
        inline=True
    )
    embed.add_field(
        name=f"{Emojis.USER} Creator",
        value=f"{creator.mention} (`{creator.id}`)",
        inline=False
    )
    embed.add_field(
        name=f"{Emojis.CLOCK} Created",
        value=f"<t:{int(datetime.fromisoformat(ticket['created_at']).timestamp())}:F>",
        inline=False
    )

    if ticket.get('closed_at'):
        embed.add_field(
            name="Closed",
            value=f"<t:{int(datetime.fromisoformat(ticket['closed_at']).timestamp())}:F>",
            inline=False
        )

    return embed


async def create_archive_embed(bot, ticket: dict, closed_by: discord.Member, reason: Optional[str] = None) -> discord.Embed:
    creator = await bot.fetch_user(ticket['user_id'])

    embed = discord.Embed(
        title=f"{Emojis.ARCHIVE} Ticket #{ticket['ticket_number']} Closed",
        color=Colors.DANGER.value,
        timestamp=datetime.utcnow()
    )

    embed.add_field(
        name=f"{Emojis.USER} Creator",
        value=f"{creator.mention} (`{creator.id}`)",
        inline=True
    )
    embed.add_field(
        name=f"{Emojis.ADMIN} Closed By",
        value=f"{closed_by.mention} (`{closed_by.id}`)",
        inline=True
    )
    embed.add_field(
        name=f"{Emojis.CLOCK} Created",
        value=f"<t:{int(datetime.fromisoformat(ticket['created_at']).timestamp())}:R>",
        inline=True
    )
    embed.add_field(
        name=f"{Emojis.CLOCK} Closed",
        value=f"<t:{int(datetime.utcnow().timestamp())}:R>",
        inline=True
    )

    if reason:
        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )

    embed.set_footer(text=f"Ticket ID: {ticket['id']}")

    return embed


def create_error_embed(message: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"{Emojis.ERROR} Error",
        description=message,
        color=Colors.DANGER.value
    )
    return embed


def create_success_embed(message: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"{Emojis.SUCCESS} Success",
        description=message,
        color=Colors.SUCCESS.value
    )
    return embed


def create_warning_embed(message: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"{Emojis.WARNING} Warning",
        description=message,
        color=Colors.WARNING.value
    )
    return embed
