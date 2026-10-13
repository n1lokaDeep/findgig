"""
Точка входа. Запуск:

    python bot.py
"""

from __future__ import annotations

import asyncio
import logging
import sys

# Чтобы русский текст в логах не превращался в кракозябры в консоли Windows.
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

from aiogram import Bot, Dispatcher, Router  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.client.session.aiohttp import AiohttpSession  # noqa: E402
from aiogram.enums import ParseMode  # noqa: E402
from aiogram.fsm.storage.memory import MemoryStorage  # noqa: E402
from aiogram.types import BotCommand, Message  # noqa: E402

import config  # noqa: E402
import database as db  # noqa: E402
import i18n  # noqa: E402
import keyboards as kb  # noqa: E402
from handlers_admin import router as admin_router  # noqa: E402
from handlers_common import router as common_router  # noqa: E402
from handlers_customer import router as customer_router  # noqa: E402
from handlers_performer import router as performer_router  # noqa: E402

fallback_router = Router()


@fallback_router.message()
async def fallback(message: Message) -> None:
    """Ловит всё, что не обработали роутеры выше."""
    if message.from_user is None:
        return
    lang = await db.get_lang(message.from_user.id)
    await message.answer(i18n.t(lang, "fallback"), reply_markup=kb.main_menu(lang))


async def main() -> None:
    # Логирование настраивается ДО любых записей в лог.
    # Иначе logging.warning() сам неявно вызовет basicConfig() с уровнем WARNING,
    # и следующий basicConfig(level=INFO) уже ничего не изменит.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if not config.BOT_TOKEN:
        raise SystemExit(
            "BOT_TOKEN не задан.\n"
            "Скопируйте .env.example в .env и впишите токен от @BotFather."
        )
    if not config.ADMIN_IDS:
        logging.warning(
            "ADMIN_IDS пуст — админ-панель будет недоступна никому. "
            "Свой ID можно узнать у бота @userinfobot."
        )
    if not config.TAGS:
        raise SystemExit("В config.TAGS не описано ни одного тэга.")

    await db.init_db()

    session = AiohttpSession(proxy=config.PROXY_URL) if config.PROXY_URL else None
    if config.PROXY_URL:
        logging.info("Работаю через прокси: %s", config.PROXY_URL)

    bot = Bot(
        token=config.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher(storage=MemoryStorage())

    # Порядок важен: команды и навигация идут первыми,
    # а заглушка «не понял» — самой последней.
    dispatcher.include_router(common_router)
    dispatcher.include_router(admin_router)
    dispatcher.include_router(customer_router)
    dispatcher.include_router(performer_router)
    dispatcher.include_router(fallback_router)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Главное меню / Main menu"),
            BotCommand(command="help", description="Помощь / Help"),
            BotCommand(command="cancel", description="Отменить / Cancel"),
        ]
    )

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info(
        "Бот запущен: %s. Администраторы: %s", config.BRAND, config.ADMIN_IDS
    )
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as error:
        if str(error):
            print(error)