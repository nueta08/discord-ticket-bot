import asyncio
import sys
from bot import TicketBot, load_config, ConfigError
from utils import setup_logging


async def main():
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("Discord Ticket Bot starting...")
    logger.info("=" * 50)

    try:
        config = load_config('config.json')
        logger.info("Configuration loaded successfully")
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}", exc_info=True)
        sys.exit(1)

    bot = TicketBot(config)

    try:
        async with bot:
            await bot.start(config['token'])
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Bot stopped")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
