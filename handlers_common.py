"""Общее для всех: запуск, выбор языка, главное меню, помощь."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
import database as db
import i18n
import keyboards as kb

router = Router()


async def send_welcome(message: Message, lang: str) -> None:
    """Приветствие и главное меню."""
    await message.answer(i18n.t(lang, "welcome", brand=config.BRAND))
    await message.answer(i18n.t(lang, "menu_title"), reply_markup=kb.main_menu(lang))


async def warn_no_username(message: Message, lang: str) -> None:
    """
    Напоминает поставить @username.

    Без него связаться можно только по ссылке на профиль, и часть людей
    просто не напишет — то есть сделка не состоится.
    """
    user = message.from_user
    if user is not None and not user.username:
        await message.answer(i18n.t(lang, "no_username_warning"))


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    if user is None:
        return

    await db.upsert_user(user.id, user.username, user.full_name)

    if not await db.lang_chosen(user.id):
        await message.answer(
            i18n.t(config.DEFAULT_LANG, "choose_language"),
            reply_markup=kb.language_choice(),
        )
        return

    lang = await db.get_lang(user.id)
    await send_welcome(message, lang)
    await warn_no_username(message, lang)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    user = message.from_user
    if user is None:
        return
    lang = await db.get_lang(user.id)
    await message.answer(
        i18n.t(lang, "help_text"), reply_markup=kb.back_to_menu(lang)
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    if user is None:
        return
    lang = await db.get_lang(user.id)
    await message.answer(i18n.t(lang, "cancelled"), reply_markup=kb.main_menu(lang))


@router.callback_query(F.data.startswith("lang:"))
async def cb_language(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    code = (callback.data or "").split(":", 1)[1]
    lang = i18n.normalize_lang(code)

    user = callback.from_user
    await db.upsert_user(user.id, user.username, user.full_name)
    await db.set_lang(user.id, lang)

    if callback.message is not None:
        await callback.message.edit_text(i18n.t(lang, "lang_changed"))
        await send_welcome(callback.message, lang)
        await warn_no_username(callback.message, lang)
    await callback.answer()


@router.callback_query(F.data == "menu:main")
async def cb_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await db.get_lang(callback.from_user.id)
    if callback.message is not None:
        await callback.message.edit_text(
            i18n.t(lang, "menu_title"), reply_markup=kb.main_menu(lang)
        )
    await callback.answer()


@router.callback_query(F.data == "menu:lang")
async def cb_change_language(callback: CallbackQuery) -> None:
    lang = await db.get_lang(callback.from_user.id)
    if callback.message is not None:
        await callback.message.edit_text(
            i18n.t(lang, "choose_language"), reply_markup=kb.language_choice()
        )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def cb_help(callback: CallbackQuery) -> None:
    lang = await db.get_lang(callback.from_user.id)
    if callback.message is not None:
        await callback.message.edit_text(
            i18n.t(lang, "help_text"), reply_markup=kb.back_to_menu(lang)
        )
    await callback.answer()