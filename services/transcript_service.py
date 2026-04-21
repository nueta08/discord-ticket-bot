"""Сервис генерации HTML-транскриптов"""

import discord
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from database import DatabaseManager
from utils.logger import get_logger
from utils.constants import TRANSCRIPT_FILENAME_FORMAT, MESSAGE_FETCH_LIMIT, DATETIME_FORMAT

logger = get_logger(__name__)


class TranscriptService:
    """Сервис для генерации HTML-транскриптов тикетов"""

    def __init__(self, bot, db: DatabaseManager):
        """
        Инициализирует сервис

        Args:
            bot: Экземпляр бота
            db: Менеджер базы данных
        """
        self.bot = bot
        self.db = db
        self.transcript_dir = Path("transcripts")
        self.transcript_dir.mkdir(exist_ok=True)

    async def generate_transcript(
        self,
        channel: discord.TextChannel,
        ticket: dict,
        closed_by: discord.Member,
        reason: Optional[str] = None
    ) -> str:
        """
        Генерирует HTML-транскрипт канала

        Args:
            channel: Канал тикета
            ticket: Данные тикета
            closed_by: Кто закрыл тикет
            reason: Причина закрытия

        Returns:
            Путь к созданному файлу
        """
        logger.info(f"Generating transcript for ticket #{ticket['ticket_number']}")

        # Получение всех сообщений
        messages = await self._fetch_all_messages(channel)
        logger.debug(f"Fetched {len(messages)} messages")

        # Получение информации о создателе
        try:
            creator = await self.bot.fetch_user(ticket['user_id'])
        except discord.NotFound:
            creator = None
            logger.warning(f"Creator user {ticket['user_id']} not found")

        # Подготовка данных для шаблона
        data = {
            'ticket_number': ticket['ticket_number'],
            'ticket_id': ticket['id'],
            'creator_name': str(creator) if creator else f"Unknown User ({ticket['user_id']})",
            'creator_id': ticket['user_id'],
            'creator_avatar': creator.display_avatar.url if creator else "https://cdn.discordapp.com/embed/avatars/0.png",
            'created_at': ticket['created_at'],
            'closed_at': datetime.utcnow().isoformat(),
            'closed_by_name': str(closed_by),
            'closed_by_id': closed_by.id,
            'reason': reason,
            'messages': await self._format_messages(messages),
            'guild_name': channel.guild.name,
            'guild_icon': channel.guild.icon.url if channel.guild.icon else None
        }

        # Генерация HTML
        html_content = self._render_html(data)

        # Сохранение файла
        filename = TRANSCRIPT_FILENAME_FORMAT.format(
            number=ticket['ticket_number'],
            id=ticket['id']
        )
        filepath = self.transcript_dir / filename

        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(html_content)

        logger.info(f"Transcript saved to {filepath}")
        return str(filepath)

    async def _fetch_all_messages(
        self,
        channel: discord.TextChannel
    ) -> List[discord.Message]:
        """
        Получает все сообщения из канала

        Args:
            channel: Канал

        Returns:
            Список сообщений
        """
        messages = []
        try:
            async for message in channel.history(limit=MESSAGE_FETCH_LIMIT, oldest_first=True):
                messages.append(message)
        except discord.Forbidden:
            logger.error(f"No permission to read message history in {channel.id}")
        except discord.HTTPException as e:
            logger.error(f"Error fetching messages: {e}")

        return messages

    async def _format_messages(
        self,
        messages: List[discord.Message]
    ) -> List[Dict]:
        """
        Форматирует сообщения для HTML

        Args:
            messages: Список сообщений

        Returns:
            Список отформатированных сообщений
        """
        formatted = []

        for msg in messages:
            # Обработка вложений
            attachments = [
                {
                    'url': att.url,
                    'filename': att.filename,
                    'is_image': att.content_type and att.content_type.startswith('image/')
                }
                for att in msg.attachments
            ]

            # Обработка embeds
            embeds_data = []
            for embed in msg.embeds:
                embeds_data.append({
                    'title': embed.title,
                    'description': embed.description,
                    'color': str(embed.color) if embed.color else None,
                    'fields': [
                        {'name': f.name, 'value': f.value}
                        for f in embed.fields
                    ]
                })

            formatted.append({
                'id': msg.id,
                'author_name': str(msg.author),
                'author_id': msg.author.id,
                'author_avatar': msg.author.display_avatar.url,
                'author_bot': msg.author.bot,
                'content': msg.content,
                'timestamp': msg.created_at.isoformat(),
                'edited_timestamp': msg.edited_at.isoformat() if msg.edited_at else None,
                'attachments': attachments,
                'embeds': embeds_data,
                'reference': msg.reference.message_id if msg.reference else None
            })

        return formatted

    def _render_html(self, data: dict) -> str:
        """
        Генерирует HTML из данных

        Args:
            data: Данные для рендеринга

        Returns:
            HTML строка
        """
        # Генерация HTML сообщений
        messages_html = ""
        for msg in data['messages']:
            author_class = "bot-message" if msg['author_bot'] else "user-message"

            # Форматирование времени
            try:
                timestamp = datetime.fromisoformat(msg['timestamp']).strftime(DATETIME_FORMAT)
            except:
                timestamp = msg['timestamp']

            # Контент сообщения
            content_html = self._escape_html(msg['content']) if msg['content'] else '<em>Нет текста</em>'

            # Вложения
            attachments_html = ""
            if msg['attachments']:
                attachments_html = '<div class="attachments">'
                for att in msg['attachments']:
                    if att['is_image']:
                        attachments_html += f'<a href="{att["url"]}" target="_blank"><img src="{att["url"]}" alt="{self._escape_html(att["filename"])}" class="attachment-image"></a>'
                    else:
                        attachments_html += f'<a href="{att["url"]}" target="_blank" class="attachment-link">📎 {self._escape_html(att["filename"])}</a>'
                attachments_html += '</div>'

            # Embeds
            embeds_html = ""
            if msg['embeds']:
                embeds_html = '<div class="embeds">'
                for embed in msg['embeds']:
                    embed_color = embed['color'] or '#5865F2'
                    embeds_html += f'<div class="embed" style="border-left-color: {embed_color};">'
                    if embed['title']:
                        embeds_html += f'<div class="embed-title">{self._escape_html(embed["title"])}</div>'
                    if embed['description']:
                        embeds_html += f'<div class="embed-description">{self._escape_html(embed["description"])}</div>'
                    if embed['fields']:
                        for field in embed['fields']:
                            embeds_html += f'<div class="embed-field"><strong>{self._escape_html(field["name"])}</strong><br>{self._escape_html(field["value"])}</div>'
                    embeds_html += '</div>'
                embeds_html += '</div>'

            messages_html += f'''
            <div class="message {author_class}">
                <img src="{msg['author_avatar']}" alt="{self._escape_html(msg['author_name'])}" class="avatar">
                <div class="message-content">
                    <div class="message-header">
                        <span class="author-name">{self._escape_html(msg['author_name'])}</span>
                        <span class="author-id">ID: {msg['author_id']}</span>
                        <span class="timestamp">{timestamp}</span>
                    </div>
                    <div class="message-text">{content_html}</div>
                    {attachments_html}
                    {embeds_html}
                </div>
            </div>
            '''

        # Форматирование дат
        try:
            created_at_formatted = datetime.fromisoformat(data['created_at']).strftime(DATETIME_FORMAT)
        except:
            created_at_formatted = data['created_at']

        try:
            closed_at_formatted = datetime.fromisoformat(data['closed_at']).strftime(DATETIME_FORMAT)
        except:
            closed_at_formatted = data['closed_at']

        # Полный HTML документ
        html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Тикет #{data['ticket_number']} - {self._escape_html(data['creator_name'])}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #36393f;
            color: #dcddde;
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: #2f3136;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}

        .header {{
            background-color: #202225;
            padding: 30px;
            border-bottom: 2px solid #5865F2;
        }}

        .header h1 {{
            color: #ffffff;
            margin-bottom: 15px;
            font-size: 28px;
        }}

        .header-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}

        .info-item {{
            background-color: #2f3136;
            padding: 15px;
            border-radius: 5px;
            border-left: 3px solid #5865F2;
        }}

        .info-label {{
            color: #b9bbbe;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 5px;
            font-weight: 600;
        }}

        .info-value {{
            color: #ffffff;
            font-size: 14px;
        }}

        .messages {{
            padding: 20px;
            max-height: none;
        }}

        .message {{
            display: flex;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            transition: background-color 0.2s;
        }}

        .message:hover {{
            background-color: #32353b;
        }}

        .avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 15px;
            flex-shrink: 0;
        }}

        .message-content {{
            flex: 1;
            min-width: 0;
        }}

        .message-header {{
            display: flex;
            align-items: center;
            margin-bottom: 5px;
            flex-wrap: wrap;
            gap: 8px;
        }}

        .author-name {{
            color: #ffffff;
            font-weight: 600;
            font-size: 15px;
        }}

        .author-id {{
            color: #72767d;
            font-size: 11px;
        }}

        .bot-message .author-name {{
            color: #5865F2;
        }}

        .bot-message .author-name::after {{
            content: "BOT";
            background-color: #5865F2;
            color: white;
            font-size: 10px;
            padding: 2px 4px;
            border-radius: 3px;
            margin-left: 5px;
        }}

        .timestamp {{
            color: #72767d;
            font-size: 12px;
            margin-left: auto;
        }}

        .message-text {{
            color: #dcddde;
            line-height: 1.5;
            word-wrap: break-word;
            white-space: pre-wrap;
            margin-top: 5px;
        }}

        .attachments {{
            margin-top: 10px;
        }}

        .attachment-image {{
            max-width: 400px;
            max-height: 300px;
            border-radius: 5px;
            margin: 5px 0;
            display: block;
        }}

        .attachment-link {{
            display: inline-block;
            color: #00b0f4;
            text-decoration: none;
            padding: 8px 12px;
            background-color: #2f3136;
            border-radius: 3px;
            margin: 5px 5px 5px 0;
            border: 1px solid #202225;
        }}

        .attachment-link:hover {{
            background-color: #36393f;
            text-decoration: underline;
        }}

        .embeds {{
            margin-top: 10px;
        }}

        .embed {{
            background-color: #2f3136;
            border-left: 4px solid #5865F2;
            border-radius: 4px;
            padding: 12px 16px;
            margin: 8px 0;
            max-width: 520px;
        }}

        .embed-title {{
            color: #ffffff;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 15px;
        }}

        .embed-description {{
            color: #dcddde;
            font-size: 14px;
            margin-bottom: 8px;
        }}

        .embed-field {{
            margin-top: 8px;
            font-size: 13px;
        }}

        .footer {{
            background-color: #202225;
            padding: 20px;
            text-align: center;
            color: #72767d;
            font-size: 12px;
            border-top: 1px solid #202225;
        }}

        .footer p {{
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎫 Тикет #{data['ticket_number']}</h1>
            <div class="header-info">
                <div class="info-item">
                    <div class="info-label">Создатель</div>
                    <div class="info-value">{self._escape_html(data['creator_name'])} (ID: {data['creator_id']})</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Дата создания</div>
                    <div class="info-value">{created_at_formatted}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Закрыл</div>
                    <div class="info-value">{self._escape_html(data['closed_by_name'])} (ID: {data['closed_by_id']})</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Дата закрытия</div>
                    <div class="info-value">{closed_at_formatted}</div>
                </div>
                {f'<div class="info-item"><div class="info-label">Причина закрытия</div><div class="info-value">{self._escape_html(data["reason"])}</div></div>' if data['reason'] else ''}
            </div>
        </div>

        <div class="messages">
            {messages_html if messages_html else '<p style="text-align: center; color: #72767d; padding: 40px;">Нет сообщений в этом тикете</p>'}
        </div>

        <div class="footer">
            <p><strong>Транскрипт тикета из {self._escape_html(data['guild_name'])}</strong></p>
            <p>Ticket ID: {data['ticket_id']}</p>
            <p>Сгенерировано: {datetime.utcnow().strftime(DATETIME_FORMAT)} UTC</p>
        </div>
    </div>
</body>
</html>'''

        return html

    @staticmethod
    def _escape_html(text: str) -> str:
        """
        Экранирует HTML символы

        Args:
            text: Текст для экранирования

        Returns:
            Экранированный текст
        """
        if not text:
            return ""
        return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))
