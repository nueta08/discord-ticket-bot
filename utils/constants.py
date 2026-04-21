from enum import Enum


class TicketStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"


class Colors:
    PRIMARY = 0x5865F2
    SUCCESS = 0x57F287
    WARNING = 0xFEE75C
    DANGER = 0xED4245
    INFO = 0x3498DB


class Emojis:
    TICKET = "🎫"
    LOCK = "🔒"
    UNLOCK = "🔓"
    INFO = "ℹ️"
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    ADMIN = "👑"
    USER = "👤"
    CLOCK = "🕐"
    ARCHIVE = "📁"


MAX_OPEN_TICKETS_PER_USER = 1
TICKET_CLOSE_DELAY = 5
MESSAGE_FETCH_LIMIT = None

TICKET_CHANNEL_NAME_FORMAT = "ticket-{number}"
TRANSCRIPT_FILENAME_FORMAT = "ticket-{number}-{id}.html"
DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"
