# Discord Ticket Bot

A ticket system bot for Discord servers built with Python and discord.py 2.x.

## Features

- Private ticket channels created via button interaction
- Permission system for ticket creators and designated staff roles
- Automatic ticket numbering
- Full conversation history saved as HTML transcripts
- Ticket archiving to dedicated channel
- Role-based access control via slash commands
- Prevents users from creating duplicate tickets
- Persistent views that survive bot restarts

## Installation

Clone or download this repository, then install dependencies:

```bash
pip install -r requirements.txt
```

Copy the example config and fill in your details:

```bash
cp config.example.json config.json
```

Edit `config.json` with your bot token, server ID, category ID for tickets, archive channel ID, and any bot owner IDs.

## Discord Bot Setup

Go to the Discord Developer Portal and create a new application. Under the Bot tab, create a bot and copy the token. Enable these Privileged Gateway Intents:

- Server Members Intent
- Message Content Intent

In OAuth2 URL Generator, select bot and applications.commands scopes. For permissions, the bot needs:

- Manage Channels
- View Channels
- Send Messages
- Manage Messages
- Embed Links
- Attach Files
- Read Message History

Optionally add Manage Roles if you want the bot to handle role permissions directly.

## Running

```bash
python main.py
```

## Commands

Users can click the "Create Ticket" button on the panel to open a new ticket. Inside tickets:

- `/ticket_info` - shows ticket details
- `/ticket_close [reason]` - closes the current ticket

Ticket staff can use:

- `/ticket_add @user` - adds a user to the ticket
- `/ticket_remove @user` - removes a user from the ticket
- `/ticket_rename new_name` - renames the ticket channel

Server administrators can use:

- `/ticket_panel` - sends the ticket creation panel
- `/ticket_admin_add @role` - adds a staff role
- `/ticket_admin_remove @role` - removes a staff role
- `/ticket_admin_list` - lists all staff roles

## Project Structure

```
ticket_bot_test/
├── main.py                 # Entry point
├── config.json             # Configuration (not in git)
├── requirements.txt        # Dependencies
├── bot/                    # Bot initialization
├── database/               # SQLite operations
├── cogs/                   # Slash commands
├── views/                  # UI components
├── services/               # Business logic
├── utils/                  # Helper functions
├── logs/                   # Log files (auto-created)
└── transcripts/            # HTML transcripts (auto-created)
```

## Database

The bot uses SQLite to store ticket information, staff roles, ticket counters, and participant lists. The database is created automatically on first run.

## Transcripts

When a ticket is closed, an HTML file is generated containing the full message history, user information, timestamps, and attachments. The file is saved locally and sent to the archive channel. The HTML uses a dark theme similar to Discord's interface.

## Requirements

- Python 3.8 or higher
- discord.py 2.3.0 or higher
- aiofiles 23.0.0 or higher

## License

MIT

## Troubleshooting

If something isn't working, check:

1. Token and IDs in config.json are correct
2. Bot has the required permissions
3. Category and archive channel exist
4. Log files in the logs directory
