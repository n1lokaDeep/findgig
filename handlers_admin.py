"""Админ-панель: статистика, списки, рассылка."""

from __future__ import annotations

import asyncio

from aiogram import Bot, F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import config
import database as db
import i18n
import keyboards as kb
import utils

router = Router()


class Broadcast(StatesGroup):
    text = State()


class IsAdmin(BaseFilter):
    """Пускает дальше только администраторов из config.ADMIN_IDS."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        return user is not None and user.id in config.ADMIN_IDS


# Весь роутер доступен только администраторам.
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    lang = await db.get_lang(user.id) if user else config.DEFAULT_LANG
    await message.answer(i18n.t(lang, "admin_menu"), reply_markup=kb.admin_menu(lang))


@router.callback_query(F.data == "admin:stats")
async def cb_stats(callback: CallbackQuery) -> None:
    lang = await db.get_lang(callback.from_user.id)
    data = await db.stats()
    text = i18n.t(
        lang,
        "admin_stats",
        users=data["users"],
        requests=data["requests"],
        open_requests=data["open_requests"],
        responses=data["responses"],
        closed=data["deals"],
    )
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=kb.admin_menu(lang))
    await callback.answer()


@router.callback_query(F.data == "admin:requests")
async def cb_requests(callback: CallbackQuery) -> None:
    lang = await db.get_lang(callback.from_user.id)
    rows = await db.recent_requests(limit=10)

    if callback.message is None:
        await callback.answer()
        return

    if not rows:
        await callback.message.edit_text(
            i18n.t(lang, "admin_no_data"), reply_markup=kb.admin_menu(lang)
        )
        await callback.answer()
        return

    blocks = [i18n.t(lang, "admin_requests_header")]
    for row in rows:
        count = await db.response_count(int(row["id"]))
        status = i18n.t(lang, f"status_{row['status']}")
        tag = config.tag_label(row["tag"], lang)
        preview = utils.esc(utils.short(row["description"], 80))
        blocks.append(
            f"№{row['id']} · {tag} · {status} · откликов: {count}\n{preview}"
        )

    await callback.message.edit_text(
        "\n\n".join(blocks), reply_markup=kb.admin_menu(lang)
    )
    await callback.answer()


@router.callback_query(F.data == "admin:users")
async def cb_users(callback: CallbackQuery) -> None:
    lang = await db.get_lang(callback.from_user.id)
    rows = await db.recent_users(limit=10)

    if callback.message is None:
        await callback.answer()
        return

    if not rows:
        await callback.message.edit_text(
            i18n.t(lang, "admin_no_data"), reply_markup=kb.admin_menu(lang)
        )
        await callback.answer()
        return

    lines = [i18n.t(lang, "admin_users_header"), ""]
    for row in rows:
        name = utils.esc(utils.display_name(row))
        lang_code = utils.esc(row["lang"] or "—")
        lines.append(
            f"<code>{row['user_id']}</code> · {name} · "
            f"{utils.contact_html(row)} · {lang_code}"
        )

    await callback.message.edit_text(
        "\n".join(lines), reply_markup=kb.admin_menu(lang)
    )
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast")
async def cb_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await db.get_lang(callback.from_user.id)
    await state.set_state(Broadcast.text)
    if callback.message is not None:
        await callback.message.edit_text(i18n.t(lang, "admin_broadcast_ask"))
    await callback.answer()


@router.message(Broadcast.text)
async def do_broadcast(message: Message, state: FSMContext, bot: Bot) -> None:
    user = message.from_user
    lang = await db.get_lang(user.id) if user else config.DEFAULT_LANG
    await state.clear()

    text = message.html_text
    user_ids = await db.all_user_ids()
    sent = 0
    failed = 0

    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text)
            sent += 1
        except Exception:
            # Пользователь мог заблокировать бота — это не ошибка рассылки.
            failed += 1
        await asyncio.sleep(0.05)

    await message.answer(
        i18n.t(lang, "admin_broadcast_done", sent=sent, failed=failed),
        reply_markup=kb.admin_menu(lang),
    )