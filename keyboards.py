"""Клавиатуры бота. Все собираются с учётом языка пользователя."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config
import i18n


def language_choice() -> InlineKeyboardMarkup:
    """Выбор языка при первом запуске. Не зависит от языка — он ещё не выбран."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🇬🇧 English", callback_data="lang:en")
    builder.button(text="🇷🇺 Русский", callback_data="lang:ru")
    builder.adjust(2)
    return builder.as_markup()


def main_menu(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=i18n.t(lang, "btn_find_performer"), callback_data="menu:find"
    )
    builder.button(text=i18n.t(lang, "btn_work"), callback_data="menu:work")
    builder.button(text=i18n.t(lang, "btn_my_requests"), callback_data="menu:myreq")
    builder.button(text=i18n.t(lang, "btn_my_responses"), callback_data="menu:myresp")
    builder.button(text=i18n.t(lang, "btn_change_lang"), callback_data="menu:lang")
    builder.button(text=i18n.t(lang, "btn_help"), callback_data="menu:help")
    builder.adjust(1, 1, 2, 2)
    return builder.as_markup()


def back_to_menu(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.t(lang, "btn_menu"), callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()


def tags_for_customer(lang: str) -> InlineKeyboardMarkup:
    """Выбор тэга при создании задачи."""
    builder = InlineKeyboardBuilder()
    for tag in config.TAGS:
        builder.button(
            text=config.tag_label(tag.key, lang), callback_data=f"tag:new:{tag.key}"
        )
    builder.button(text=i18n.t(lang, "btn_menu"), callback_data="menu:main")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def tags_for_filter(lang: str, current: str | None = None) -> InlineKeyboardMarkup:
    """Фильтр ленты по тэгу для исполнителя."""
    builder = InlineKeyboardBuilder()
    for tag in config.TAGS:
        label = config.tag_label(tag.key, lang)
        if tag.key == current:
            label = f"✅ {label}"
        builder.button(text=label, callback_data=f"tag:filter:{tag.key}")
    builder.button(text="🌐 ALL", callback_data="tag:filter:any")
    builder.button(text=i18n.t(lang, "btn_menu"), callback_data="menu:main")
    builder.adjust(2, 2, 2, 1, 1)
    return builder.as_markup()


def confirm_request(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.t(lang, "btn_publish"), callback_data="req:publish")
    builder.button(text=i18n.t(lang, "btn_cancel"), callback_data="req:cancel")
    builder.adjust(1, 1)
    return builder.as_markup()


def request_actions(lang: str, request_id: int) -> InlineKeyboardMarkup:
    """Кнопки под задачей в ленте исполнителя."""
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.t(lang, "btn_respond"), callback_data=f"req:respond:{request_id}")
    builder.button(text=i18n.t(lang, "btn_skip"), callback_data=f"req:skip:{request_id}")
    builder.button(text=i18n.t(lang, "btn_filter"), callback_data="menu:filter")
    builder.button(text=i18n.t(lang, "btn_menu"), callback_data="menu:main")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def response_notice(lang: str, request_id: int, performer_id: int) -> InlineKeyboardMarkup:
    """Кнопки в уведомлении заказчику о новом отклике."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=i18n.t(lang, "btn_choose"),
        callback_data=f"req:choose:{request_id}:{performer_id}",
    )
    builder.button(
        text=i18n.t(lang, "btn_keep_looking"), callback_data=f"req:wait:{request_id}"
    )
    builder.adjust(1, 1)
    return builder.as_markup()


def responses_picker(
    lang: str, request_id: int, performers: list[dict]
) -> InlineKeyboardMarkup:
    """Список откликнувшихся, чтобы заказчик выбрал одного."""
    builder = InlineKeyboardBuilder()
    for person in performers:
        name = person.get("full_name") or person.get("username") or person["user_id"]
        builder.button(
            text=f"✅ {name}"[:60],
            callback_data=f"req:choose:{request_id}:{person['user_id']}",
        )
    builder.button(text=i18n.t(lang, "btn_menu"), callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()


def my_requests(lang: str, requests: list[dict]) -> InlineKeyboardMarkup:
    """Список своих задач."""
    builder = InlineKeyboardBuilder()
    for row in requests:
        status = i18n.t(lang, f"status_{row['status']}")
        label = f"№{row['id']} · {config.tag_label(row['tag'], lang)} · {status}"
        builder.button(text=label[:60], callback_data=f"req:view:{row['id']}")
    builder.button(text=i18n.t(lang, "btn_menu"), callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()


def own_request_actions(lang: str, request_id: int, can_cancel: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Отклики" if lang == "ru" else "👥 Responses",
                   callback_data=f"req:responses:{request_id}")
    if can_cancel:
        builder.button(text=i18n.t(lang, "btn_cancel"), callback_data=f"req:close:{request_id}")
    builder.button(text=i18n.t(lang, "btn_menu"), callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()


def admin_menu(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.t(lang, "btn_admin_stats"), callback_data="admin:stats")
    builder.button(text=i18n.t(lang, "btn_admin_requests"), callback_data="admin:requests")
    builder.button(text=i18n.t(lang, "btn_admin_users"), callback_data="admin:users")
    builder.button(text=i18n.t(lang, "btn_admin_broadcast"), callback_data="admin:broadcast")
    builder.adjust(2, 2)
    return builder.as_markup()