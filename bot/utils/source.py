import re
from aiogram.types import Message

ALLOWED_SOURCES = {"landing", "telegram_channel", "instagram", "vk", "ads", "other"}


def parse_source(message: Message) -> str:
    """Достаёт start_parameter из /start deep-link."""
    text = message.text or ""
    m = re.match(r"^/start\s+(\S+)", text)
    if not m:
        return "other"

    payload = m.group(1).strip().lower()
    return payload if payload in ALLOWED_SOURCES else "other"