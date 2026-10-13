"""
Настройки проекта.

Здесь меняется всё, что относится к конкретной площадке:
название, список тэгов, администраторы.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# ───────────────────────────── доступ ─────────────────────────────

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")


def _parse_admins(raw: str) -> list[int]:
    """Разбирает строку вида "123456, 789012" в список чисел."""
    ids: list[int] = []
    for chunk in raw.replace(" ", "").split(","):
        if chunk.lstrip("-").isdigit():
            ids.append(int(chunk))
    return ids


ADMIN_IDS: list[int] = _parse_admins(os.getenv("ADMIN_IDS", ""))

DB_PATH: str = os.getenv("DB_PATH", "bot.db")

# Прокси для доступа к Telegram API. Нужен, если api.telegram.org
# недоступен напрямую. Пример: socks5://127.0.0.1:1080
PROXY_URL: str = os.getenv("PROXY_URL", "")

# ───────────────────────────── бренд ─────────────────────────────

# Название площадки. Оно же ставится в имя бота командой setMyName.
BRAND = "FindGig"

# Языки интерфейса. Пользователь выбирает сам при первом запуске.
LANGUAGES: tuple[str, ...] = ("en", "ru")
DEFAULT_LANG = "en"

# ────────────────────────────── тэги ──────────────────────────────
# key — служебный код, латиницей, менять не нужно
# ru / en — как тэг называется на каждом языке


@dataclass(frozen=True)
class Tag:
    key: str
    ru: str
    en: str


TAGS: list[Tag] = [
    Tag(key="design", ru="Дизайн", en="Design"),
    Tag(key="code", ru="Код и сайты", en="Code & websites"),
    Tag(key="video", ru="Видео и монтаж", en="Video & editing"),
    Tag(key="text", ru="Тексты и переводы", en="Writing & translation"),
    Tag(key="audio", ru="Музыка и звук", en="Music & audio"),
    Tag(key="other", ru="Другое", en="Other"),
]

TAGS_BY_KEY: dict[str, Tag] = {tag.key: tag for tag in TAGS}


def tag_label(key: str, lang: str) -> str:
    """Название тэга на нужном языке."""
    tag = TAGS_BY_KEY.get(key)
    if tag is None:
        return key
    return tag.ru if lang == "ru" else tag.en


# ───────────────────────── ограничения ─────────────────────────

MIN_DESCRIPTION = 15
MAX_DESCRIPTION = 700

# Сколько анкет показывать в списках
LIST_LIMIT = 10

# Статусы анкет
STATUS_OPEN = "open"
STATUS_CLOSED = "closed"
STATUS_CANCELLED = "cancelled"