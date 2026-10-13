"""Мелкие помощники: экранирование и показ контактов."""

from __future__ import annotations

import html


def esc(value: object) -> str:
    """Экранирует пользовательский текст, чтобы он не сломал разметку HTML."""
    return html.escape(str(value or ""), quote=False)


def display_name(row: dict | None, fallback: str = "—") -> str:
    """Как показать человека в тексте."""
    if not row:
        return fallback
    name = (row.get("full_name") or "").strip()
    if name:
        return name
    username = row.get("username")
    if username:
        return f"@{username}"
    return fallback


def contact_html(row: dict | None, fallback: str = "—") -> str:
    """
    Контакт человека в виде, готовом для HTML-разметки.

    Если у человека есть @username — показываем его: по нему легко написать.
    Если нет — даём ссылку на профиль. Она работает, но у человека лучше
    попросить поставить username, иначе связаться с ним сложно.
    """
    if not row:
        return fallback

    username = row.get("username")
    if username:
        return f"@{esc(username)}"

    user_id = row.get("user_id")
    name = esc(display_name(row))
    if user_id:
        return f'<a href="tg://user?id={user_id}">{name}</a> (без @username)'
    return name


def person_card_html(row: dict | None, labels: dict[str, str]) -> str:
    """Карточка человека: имя и контакт, двумя строками."""
    if not row:
        return "—"
    return (
        f"{labels['name']}: {esc(display_name(row))}\n"
        f"{labels['contact']}: {contact_html(row)}"
    )


def short(text: str, limit: int = 60) -> str:
    """Обрезает длинный текст для списков."""
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"