import json
from pathlib import Path
from typing import Dict, Any, List
from utils.logger import get_logger

logger = get_logger(__name__)


class ConfigError(Exception):
    pass


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    config_file = Path(config_path)

    if not config_file.exists():
        raise ConfigError(
            f"Config file not found: {config_path}\n"
            f"Copy config.example.json to config.json and fill it out."
        )

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"JSON parse error: {e}")

    required_fields = [
        'token',
        'guild_id',
        'ticket_category_id',
        'archive_channel_id'
    ]

    missing_fields = [field for field in required_fields if field not in config]
    if missing_fields:
        raise ConfigError(
            f"Missing required fields: {', '.join(missing_fields)}"
        )

    if not config['token'] or config['token'] == "YOUR_BOT_TOKEN_HERE":
        raise ConfigError("Bot token not configured in config.json")

    for field in ['guild_id', 'ticket_category_id', 'archive_channel_id']:
        if not isinstance(config[field], int) or config[field] <= 0:
            raise ConfigError(f"Field {field} must be a positive integer")

    config.setdefault('embed_color', '#5865F2')
    config.setdefault('owners', [])

    if not isinstance(config['owners'], list):
        raise ConfigError("Field 'owners' must be a list")

    logger.info(f"Configuration loaded successfully from {config_path}")
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    color = config.get('embed_color', '#5865F2')
    if not color.startswith('#') or len(color) != 7:
        raise ConfigError(
            f"Invalid color format: {color}. Use #RRGGBB format"
        )

    try:
        int(color.replace('#', ''), 16)
    except ValueError:
        raise ConfigError(f"Invalid hex color: {color}")

    return True
