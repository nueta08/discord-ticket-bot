import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_format = logging.Formatter(
        '[{asctime}] [{levelname:<8}] {name}: {message}',
        datefmt='%Y-%m-%d %H:%M:%S',
        style='{'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(level)

    file_handler = logging.FileHandler(
        log_dir / 'bot.log',
        encoding='utf-8',
        mode='a'
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.DEBUG)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
