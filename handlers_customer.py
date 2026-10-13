"""Сторона заказчика: публикация задачи, отклики, выбор исполнителя."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import config
import database as db
import i18n
import keyboards as kb
import utils

router = Router()


class NewRequest(StatesGroup):
    description = State()
    confirm = State()


# ─────────────────────── создание задачи ───────────────────────


@router.callback_query(F.data == "menu:find")
async def cb_start_new_request(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await db.get_lang(callback.from_user.id)
    if callback.message is not None:
        await callback.message.edit_text(
            i18n.t(lang, "ask_tag"), reply_markup=kb.tags_for_customer(lang)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("tag:new:"))
async def cb_pick_tag(callback: CallbackQuery, state: FSMContext) -> None:
    parts = (callback.data or "").split(":", 2)
    key = parts[2] if len(parts) > 2 else ""

    if key not in config.TAGS_BY_KEY:
        await callback.answer("?", show_alert=True)
        return

    lang = await db.get_lang(callback.from_user.id)
    await state.clear()
    await state.update_data(tag=key)
    await state.set_state(NewRequest.description)

    if callback.message is not None:
        await callback.message.edit_text(i18n.t(lang, "ask_desc"))
    await callback.answer()


@router.message(NewRequest.description)
async def form_description(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if user is None:
        return
    lang = await db.get_lang(user.id)
    text = (message.text or "").strip()

    if len(text) < config.MIN_DESCRIPTION:
        await message.answer(
            i18n.t(lang, "desc_short", min=config.MIN_DESCRIPTION)
        )
        return

    if len(text) > config.MAX_DESCRIPTION:
        await message.answer(i18n.t(lang, "desc_long", max=config.MAX_DESCRIPTION))
        return

    data = await state.get_data()
    tag = data.get("tag")
    if not tag:
        await state.clear()
        await message.answer(
            i18n.t(lang, "fallback"), reply_markup=kb.main_menu(lang)
        )
        return

    await state.update_data(description=text)
    await state.set_state(NewRequest.confirm)
    await message.answer(
        i18n.t(
            lang,
            "confirm_request",
            tag=config.tag_label(tag, lang),
            description=utils.esc(text),
        ),
        reply_markup=kb.confirm_request(lang),
    )


@router.callback_query(F.data == "req:publish", NewRequest.confirm)
async def cb_publish(callback: CallbackQuery, state: FSMContext) -> None:
    user = callback.from_user
    lang = await db.get_lang(user.id)
    data = await state.get_data()
    tag = data.get("tag")
    description = data.get("description")

    if not tag or not description:
        await callback.answer()
        return

    request_id = await db.create_request(user.id, tag, description)
    await state.clear()

    if callback.message is not None:
        await callback.message.edit_text(
            i18n.t(lang, "published", id=request_id),
            reply_markup=kb.back_to_menu(lang),
        )
    await callback.answer()


@router.callback_query(F.data == "req:cancel")
async def cb_cancel_creation(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await db.get_lang(callback.from_user.id)
    if callback.message is not None:
        await callback.message.edit_text(
            i18n.t(lang, "cancelled"), reply_markup=kb.main_menu(lang)
        )
    await callback.answer()


# ─────────────────────── свои задачи ───────────────────────


@router.callback_query(F.data == "menu:myreq")
async def cb_my_requests(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = callback.from_user
    lang = await db.get_lang(user.id)
    rows = await db.customer_requests(user.id)

    if callback.message is None:
        await callback.answer()
        return

    if not rows:
        await callback.message.edit_text(
            i18n.t(lang, "my_requests_empty"), reply_markup=kb.back_to_menu(lang)
        )
    else:
        await callback.message.edit_text(
            i18n.t(lang, "my_requests_header"),
            reply_markup=kb.my_requests(lang, rows),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("req:view:"))
async def cb_view_own_request(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = callback.from_user
    lang = await db.get_lang(user.id)

    try:
        request_id = int((callback.data or "").split(":")[2])
    except (IndexError, ValueError):
        await callback.answer("?", show_alert=True)
        return

    row = await db.get_request(request_id)
    if row is None or int(row["customer_id"]) != user.id:
        await callback.answer(i18n.t(lang, "no_requests"), show_alert=True)
        return

    count = await db.response_count(request_id)
    text = i18n.t(
        lang,
        "request_card_customer",
        id=request_id,
        tag=config.tag_label(row["tag"], lang),
        status=i18n.t(lang, f"status_{row['status']}"),
        responses=count,
        created=utils.esc(row["created_at"]),
        description=utils.esc(row["description"]),
    )

    if callback.message is not None:
        await callback.message.edit_text(
            text,
            reply_markup=kb.own_request_actions(
                lang, request_id, row["status"] == config.STATUS_OPEN
            ),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("req:responses:"))
async def cb_own_responses(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = callback.from_user
    lang = await db.get_lang(user.id)

    try:
        request_id = int((callback.data or "").split(":")[2])
    except (IndexError, ValueError):
        await callback.answer("?", show_alert=True)
        return

    row = await db.get_request(request_id)
    if row is None or int(row["customer_id"]) != user.id:
        await callback.answer("?", show_alert=True)
        return
    if callback.message is None:
        await callback.answer()
        return

    performers = await db.responses_for_request(request_id)
    if not performers:
        await callback.message.edit_text(
            i18n.t(lang, "no_responses_yet"), reply_markup=kb.back_to_menu(lang)
        )
    else:
        await callback.message.edit_text(
            i18n.t(lang, "responses_list_header", id=request_id)
            + "\n\n"
            + i18n.t(lang, "choose_hint"),
            reply_markup=kb.responses_picker(lang, request_id, performers),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("req:wait:"))
async def cb_keep_looking(callback: CallbackQuery) -> None:
    lang = await db.get_lang(callback.from_user.id)
    try:
        request_id = int((callback.data or "").split(":")[2])
    except (IndexError, ValueError):
        request_id = 0
    if callback.message is not None:
        await callback.message.edit_text(
            i18n.t(lang, "keep_looking", id=request_id),
            reply_markup=kb.back_to_menu(lang),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("req:close:"))
async def cb_close_own_request(callback: CallbackQuery) -> None:
    user = callback.from_user
    lang = await db.get_lang(user.id)
    try:
        request_id = int((callback.data or "").split(":")[2])
    except (IndexError, ValueError):
        await callback.answer("?", show_alert=True)
        return

    ok = await db.cancel_request(request_id, user.id)
    text = i18n.t(lang, "cancelled") if ok else i18n.t(lang, "request_already_closed")
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=kb.back_to_menu(lang))
    await callback.answer()


# ─────────────────────── мэтчинг ───────────────────────


@router.callback_query(F.data.startswith("req:choose:"))
async def cb_choose_performer(
    callback: CallbackQuery, bot: Bot, state: FSMContext
) -> None:
    """
    Заказчик выбрал исполнителя.

    Задача закрывается, и обе стороны немедленно получают контакты друг друга.
    Если задачу успели закрыть раньше — контакты не выдаём.
    """
    await state.clear()
    customer_id = callback.from_user.id
    lang = await db.get_lang(customer_id)

    parts = (callback.data or "").split(":")
    if len(parts) < 4:
        await callback.answer("?", show_alert=True)
        return
    try:
        request_id = int(parts[2])
        performer_id = int(parts[3])
    except ValueError:
        await callback.answer("?", show_alert=True)
        return

    row = await db.get_request(request_id)
    if row is None or int(row["customer_id"]) != customer_id:
        await callback.answer("?", show_alert=True)
        return

    if not await db.choose_performer(request_id, performer_id):
        if callback.message is not None:
            await callback.message.edit_text(
                i18n.t(lang, "request_already_closed"),
                reply_markup=kb.back_to_menu(lang),
            )
        await callback.answer()
        return

    customer = await db.get_user(customer_id)
    performer = await db.get_user(performer_id)
    performer_lang = await db.get_lang(performer_id)

    # заказчику — контакт исполнителя
    if callback.message is not None:
        await callback.message.edit_text(
            i18n.t(
                lang,
                "chosen_customer",
                id=request_id,
                contact=utils.contact_html(performer),
            ),
            reply_markup=kb.back_to_menu(lang),
        )

    # исполнителю — контакт заказчика
    try:
        await bot.send_message(
            performer_id,
            i18n.t(
                performer_lang,
                "chosen_performer",
                id=request_id,
                contact=utils.contact_html(customer),
            ),
            reply_markup=kb.back_to_menu(performer_lang),
        )
    except Exception:
        # Исполнитель мог заблокировать бота — задачу это не отменяет.
        pass

    # остальным откликнувшимся сообщаем, что задача закрыта
    for other_id in await db.responder_ids(request_id, exclude=performer_id):
        other_lang = await db.get_lang(other_id)
        try:
            await bot.send_message(
                other_id,
                i18n.t(other_lang, "closed_for_others", id=request_id),
                reply_markup=kb.back_to_menu(other_lang),
            )
        except Exception:
            continue

    await callback.answer()