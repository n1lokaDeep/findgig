"""Сторона исполнителя: лента задач, отклик, пропуск, фильтр по тэгу."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import config
import database as db
import i18n
import keyboards as kb
import utils

router = Router()


async def send_next_request(callback: CallbackQuery, state: FSMContext) -> None:
    """Показывает следующую подходящую задачу или сообщает, что их нет."""
    user_id = callback.from_user.id
    lang = await db.get_lang(user_id)

    data = await state.get_data()
    raw_filter = data.get("tag_filter")
    tag = None if raw_filter in (None, "any") else str(raw_filter)

    row = await db.next_request_for(user_id, tag)

    if callback.message is None:
        await callback.answer()
        return

    if row is None:
        await callback.message.edit_text(
            i18n.t(lang, "no_requests"),
            reply_markup=kb.tags_for_filter(lang, raw_filter),
        )
        await callback.answer()
        return

    customer = await db.get_user(int(row["customer_id"]))
    text = i18n.t(
        lang,
        "request_card",
        id=row["id"],
        tag=config.tag_label(row["tag"], lang),
        author=utils.esc(utils.display_name(customer)),
        created=utils.esc(row["created_at"]),
        description=utils.esc(row["description"]),
    )
    await callback.message.edit_text(
        text, reply_markup=kb.request_actions(lang, int(row["id"]))
    )
    await callback.answer()


@router.callback_query(F.data == "menu:work")
async def cb_start_browsing(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await send_next_request(callback, state)


@router.callback_query(F.data == "menu:filter")
async def cb_filter_menu(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await db.get_lang(callback.from_user.id)
    data = await state.get_data()
    if callback.message is not None:
        await callback.message.edit_text(
            i18n.t(lang, "ask_tag"),
            reply_markup=kb.tags_for_filter(lang, data.get("tag_filter")),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("tag:filter:"))
async def cb_set_filter(callback: CallbackQuery, state: FSMContext) -> None:
    parts = (callback.data or "").split(":", 2)
    key = parts[2] if len(parts) > 2 else "any"

    if key != "any" and key not in config.TAGS_BY_KEY:
        await callback.answer("?", show_alert=True)
        return

    await state.update_data(tag_filter=key)
    await send_next_request(callback, state)


@router.callback_query(F.data.startswith("req:skip:"))
async def cb_skip(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        request_id = int((callback.data or "").split(":")[2])
    except (IndexError, ValueError):
        await callback.answer("?", show_alert=True)
        return

    await db.skip_request(request_id, callback.from_user.id)
    await send_next_request(callback, state)


@router.callback_query(F.data.startswith("req:respond:"))
async def cb_respond(
    callback: CallbackQuery, bot: Bot, state: FSMContext
) -> None:
    """Исполнитель откликается. Откликов может быть много — выбор за заказчиком."""
    user = callback.from_user
    lang = await db.get_lang(user.id)

    try:
        request_id = int((callback.data or "").split(":")[2])
    except (IndexError, ValueError):
        await callback.answer("?", show_alert=True)
        return

    row = await db.get_request(request_id)
    if row is None:
        await callback.answer("?", show_alert=True)
        return

    if int(row["customer_id"]) == user.id:
        await callback.answer(i18n.t(lang, "respond_own"), show_alert=True)
        return

    if row["status"] != config.STATUS_OPEN:
        if callback.message is not None:
            await callback.message.edit_text(
                i18n.t(lang, "request_already_closed"),
                reply_markup=kb.back_to_menu(lang),
            )
        await callback.answer()
        return

    if await db.has_responded(request_id, user.id):
        await callback.answer(i18n.t(lang, "already_responded"), show_alert=True)
        return

    await db.add_response(request_id, user.id)

    # уведомляем заказчика о новом отклике
    customer_id = int(row["customer_id"])
    customer_lang = await db.get_lang(customer_id)
    performer = await db.get_user(user.id)

    try:
        await bot.send_message(
            customer_id,
            i18n.t(
                customer_lang,
                "new_response_to_customer",
                id=request_id,
                performer=utils.person_card_html(
                    performer, i18n.person_labels(customer_lang)
                ),
            ),
            reply_markup=kb.response_notice(customer_lang, request_id, user.id),
        )
    except Exception:
        # Заказчик мог заблокировать бота. Отклик всё равно сохранён.
        pass

    if callback.message is not None:
        await callback.message.edit_text(
            i18n.t(lang, "responded"), reply_markup=kb.back_to_menu(lang)
        )
    await callback.answer()


@router.callback_query(F.data == "menu:myresp")
async def cb_my_responses(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = callback.from_user
    lang = await db.get_lang(user.id)
    rows = await db.performer_responses(user.id)

    if callback.message is None:
        await callback.answer()
        return

    if not rows:
        await callback.message.edit_text(
            i18n.t(lang, "my_responses_empty"), reply_markup=kb.back_to_menu(lang)
        )
        await callback.answer()
        return

    lines = [i18n.t(lang, "my_responses_header"), ""]
    for row in rows:
        lines.append(
            i18n.t(
                lang,
                "my_response_item",
                id=row["id"],
                tag=config.tag_label(row["tag"], lang),
                status=i18n.t(lang, f"status_{row['status']}"),
                preview=utils.esc(utils.short(row["description"])),
            )
        )
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=kb.back_to_menu(lang)
    )
    await callback.answer()