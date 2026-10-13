"""
Сквозной прогон площадки без токена и без интернета.

Сетевой слой aiogram подменён заглушкой, которая записывает все обращения
к Telegram. Обработчики, FSM, клавиатуры и база — настоящие.

Запуск:
    python tests/test_flow.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.client.session.base import BaseSession  # noqa: E402
from aiogram.enums import ParseMode  # noqa: E402
from aiogram.fsm.storage.memory import MemoryStorage  # noqa: E402
from aiogram.types import CallbackQuery, Chat, Message, Update, User  # noqa: E402

import config  # noqa: E402
import database as db  # noqa: E402
from bot import fallback_router  # noqa: E402
from handlers_admin import router as admin_router  # noqa: E402
from handlers_common import router as common_router  # noqa: E402
from handlers_customer import router as customer_router  # noqa: E402
from handlers_performer import router as performer_router  # noqa: E402

TOKEN = "123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw"
CUSTOMER = 111000111
PERFORMER = 222000222
PERFORMER2 = 333000333
ADMIN = 999888777

PASSED = 0


def check(condition: bool, label: str) -> None:
    global PASSED
    if condition:
        PASSED += 1
        print(f"[OK] {label}")
    else:
        print(f"[ПРОВАЛ] {label}")
        raise SystemExit(1)


class MockSession(BaseSession):
    """Заглушка Telegram: ничего не отправляет, только записывает вызовы."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list = []

    async def close(self) -> None:
        return None

    async def stream_content(self, bot, method, timeout=None, chunk_size=65536):
        yield b""

    def _fake_result(self, method) -> object:
        name = type(method).__name__
        chat_id = getattr(method, "chat_id", 0) or 0

        if name == "GetMe":
            return {
                "id": 123456789,
                "is_bot": True,
                "first_name": "FindGig",
                "username": "findgig_test_bot",
            }
        if name in (
            "SendMessage",
            "EditMessageText",
            "EditMessageReplyMarkup",
            "SendChatAction",
        ):
            return {
                "message_id": len(self.calls),
                "date": int(datetime.now().timestamp()),
                "chat": {"id": chat_id, "type": "private"},
                "text": getattr(method, "text", "") or "",
            }
        return True

    async def make_request(self, bot, method, timeout=None):
        self.calls.append(method)
        body = json.dumps({"ok": True, "result": self._fake_result(method)})
        return self.check_response(bot, method, 200, body).result

    # ── помощники для проверок ──

    OUTGOING = ("SendMessage", "EditMessageText")

    def outgoing(self) -> list:
        return [c for c in self.calls if type(c).__name__ in self.OUTGOING]

    def edits(self) -> list:
        return [c for c in self.calls if type(c).__name__ == "EditMessageText"]

    def edits_to(self, chat_id: int) -> list:
        return [
            c for c in self.edits() if getattr(c, "chat_id", None) == chat_id
        ]

    def texts(self) -> list[str]:
        return [c.text for c in self.outgoing() if getattr(c, "text", None)]

    def last_text(self) -> str:
        found = self.texts()
        return found[-1] if found else ""

    def sent_to(self, chat_id: int) -> list:
        from aiogram.methods import SendMessage

        return [
            c
            for c in self.calls
            if isinstance(c, SendMessage) and c.chat_id == chat_id
        ]

    def answers(self) -> list[str]:
        """Тексты всплывающих уведомлений (answerCallbackQuery)."""
        from aiogram.methods import AnswerCallbackQuery

        return [
            c.text
            for c in self.calls
            if isinstance(c, AnswerCallbackQuery) and getattr(c, "text", None)
        ]

    def reset(self) -> None:
        self.calls.clear()


def _user(user_id: int, name: str, username: str | None) -> User:
    return User(
        id=user_id, is_bot=False, first_name=name, username=username
    )


USERS = {
    CUSTOMER: ("Заказчик", "customer_acc"),
    PERFORMER: ("Vasya", "performer_acc"),
    PERFORMER2: ("Пётр", "performer2_acc"),
    ADMIN: ("Админ", "admin_acc"),
}


def message_update(update_id: int, user_id: int, text: str) -> Update:
    name, username = USERS[user_id]
    return Update(
        update_id=update_id,
        message=Message(
            message_id=update_id,
            date=datetime.now(),
            chat=Chat(id=user_id, type="private"),
            from_user=_user(user_id, name, username),
            text=text,
        ),
    )


def callback_update(update_id: int, user_id: int, data: str) -> Update:
    name, username = USERS[user_id]
    bot_user = User(id=123456789, is_bot=True, first_name="FindGig")
    return Update(
        update_id=update_id,
        callback_query=CallbackQuery(
            id=str(update_id),
            from_user=_user(user_id, name, username),
            chat_instance="test",
            data=data,
            message=Message(
                message_id=update_id,
                date=datetime.now(),
                chat=Chat(id=user_id, type="private"),
                from_user=bot_user,
                text="предыдущее сообщение",
            ),
        ),
    )


class Runner:
    def __init__(self) -> None:
        self.session = MockSession()
        self.bot = Bot(
            token=TOKEN,
            session=self.session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.dp = Dispatcher(storage=MemoryStorage())
        self.dp.include_router(common_router)
        self.dp.include_router(admin_router)
        self.dp.include_router(customer_router)
        self.dp.include_router(performer_router)
        self.dp.include_router(fallback_router)
        self.n = 1000

    async def send(self, user_id: int, text: str) -> None:
        self.n += 1
        await self.dp.feed_update(self.bot, message_update(self.n, user_id, text))

    async def click(self, user_id: int, data: str) -> None:
        self.n += 1
        await self.dp.feed_update(self.bot, callback_update(self.n, user_id, data))


async def main() -> None:
    tmp_db = Path(tempfile.gettempdir()) / "findgig_flow.db"
    tmp_db.unlink(missing_ok=True)
    config.DB_PATH = str(tmp_db)
    config.ADMIN_IDS = [ADMIN]

    await db.init_db()
    run = Runner()
    s = run.session

    print("Сквозной прогон площадки (сеть подменена заглушкой)\n")

    # ── 1. Первый запуск: выбор языка ──
    s.reset()
    await run.send(CUSTOMER, "/start")
    check(
        "Choose your language" in s.last_text(),
        "при первом запуске бот предлагает выбрать язык",
    )
    check(not await db.lang_chosen(CUSTOMER), "язык ещё не выбран")

    # ── 2. Заказчик выбирает русский ──
    s.reset()
    await run.click(CUSTOMER, "lang:ru")
    check(await db.get_lang(CUSTOMER) == "ru", "выбор языка сохраняется")
    check("площадка" in " ".join(s.texts()).lower(), "приветствие пришло на русском")
    check(
        "no_username" not in s.last_text(),
        "предупреждение о нике не появляется, когда ник есть",
    )

    # ── 3. Создание задачи ──
    s.reset()
    await run.click(CUSTOMER, "menu:find")
    check("тэгу" in s.last_text(), "бот спрашивает тэг задачи")

    s.reset()
    await run.click(CUSTOMER, "tag:new:code")
    check("Опишите задачу" in s.last_text(), "после тэга бот просит описание")

    s.reset()
    await run.send(CUSTOMER, "мало")
    check("Слишком коротко" in s.last_text(), "слишком короткое описание отклоняется")

    s.reset()
    await run.send(CUSTOMER, "Нужно сверстать лендинг под ключ, срок — неделя")
    check("Проверьте задачу" in s.last_text(), "показано подтверждение задачи")
    check("Код и сайты" in s.last_text(), "в подтверждении верный тэг")

    s.reset()
    await run.click(CUSTOMER, "req:publish")
    check("опубликована" in s.last_text(), "задача опубликована")
    request_id = (await db.customer_requests(CUSTOMER))[0]["id"]
    check(request_id == 1, f"задача сохранена с номером {request_id}")

    # ── 4. Исполнитель приходит, язык английский ──
    s.reset()
    await run.send(PERFORMER, "/start")
    await run.click(PERFORMER, "lang:en")
    check(await db.get_lang(PERFORMER) == "en", "исполнитель выбрал английский")

    s.reset()
    await run.click(PERFORMER, "menu:work")
    card = s.last_text()
    check("Task #1" in card, "исполнитель видит задачу в ленте")
    check("Code & websites" in card, "тэг показан на языке исполнителя")
    check("customer_acc" not in card, "в ленте не раскрывается контакт заказчика")

    # ── 5. Отклик ──
    s.reset()
    await run.click(PERFORMER, f"req:respond:{request_id}")
    check("Response sent" in s.last_text(), "исполнитель видит подтверждение отклика")
    check(await db.response_count(request_id) == 1, "отклик сохранён в базу")

    notices = s.sent_to(CUSTOMER)
    check(len(notices) == 1, "заказчик получил ровно одно уведомление")
    check("Новая заявка" in notices[0].text, "уведомление заказчику на его языке")
    check("@performer_acc" in notices[0].text, "в уведомлении есть контакт исполнителя")
    check(
        notices[0].reply_markup is not None,
        "к уведомлению приложены кнопки выбора",
    )

    # ── 6. Повторный отклик того же человека ──
    s.reset()
    await run.click(PERFORMER, f"req:respond:{request_id}")
    check(
        "already responded" in " ".join(s.answers()),
        "повторный отклик отклонён всплывающим уведомлением",
    )
    check(await db.response_count(request_id) == 1, "дубликат отклика не создан")

    # ── 7. Второй исполнитель ──
    s.reset()
    await run.send(PERFORMER2, "/start")
    await run.click(PERFORMER2, "lang:ru")
    await run.click(PERFORMER2, "menu:work")
    check("Задача №1" in s.last_text(), "второй исполнитель тоже видит задачу")

    s.reset()
    await run.click(PERFORMER2, f"req:respond:{request_id}")
    check(await db.response_count(request_id) == 2, "откликов стало двое")

    # ── 8. Заказчик видит список откликов ──
    s.reset()
    await run.click(CUSTOMER, f"req:responses:{request_id}")
    picker = s.last_text()
    check("Отклики на задачу" in picker, "заказчик видит список откликов")

    # ── 9. Мэтчинг ──
    s.reset()
    await run.click(CUSTOMER, f"req:choose:{request_id}:{PERFORMER}")

    customer_edits = " ".join(
        c.text or "" for c in s.edits_to(CUSTOMER)
    )
    check("Исполнитель выбран" in customer_edits, "заказчик получил подтверждение выбора")
    check(
        "@performer_acc" in customer_edits,
        "заказчику выдан контакт исполнителя",
    )

    to_performer = s.sent_to(PERFORMER)
    check(len(to_performer) == 1, "исполнитель получил сообщение о выборе")
    check("You were chosen" in to_performer[0].text, "исполнителю написано на его языке")
    check(
        "@customer_acc" in to_performer[0].text,
        "исполнителю выдан контакт заказчика",
    )

    to_other = s.sent_to(PERFORMER2)
    check(len(to_other) == 1, "второй исполнитель уведомлён о закрытии задачи")
    check("закрыта" in to_other[0].text, "второму исполнителю объяснили причину")

    row = await db.get_request(request_id)
    check(row is not None and row["status"] == config.STATUS_CLOSED, "задача закрыта")
    check(
        row is not None and row["chosen_performer_id"] == PERFORMER,
        "записан выбранный исполнитель",
    )

    # ── 10. Повторный выбор невозможен ──
    s.reset()
    await run.click(CUSTOMER, f"req:choose:{request_id}:{PERFORMER2}")
    check("уже закрыта" in s.last_text(), "повторно выбрать исполнителя нельзя")
    check(
        row is not None and (await db.get_request(request_id))["chosen_performer_id"] == PERFORMER,
        "выбранный исполнитель не перезаписался",
    )

    # ── 11. На свою задачу откликнуться нельзя ──
    s.reset()
    await run.send(CUSTOMER, "/start")
    request_two = await db.create_request(CUSTOMER, "design", "Второй заказ: баннер")
    s.reset()
    await run.click(CUSTOMER, f"req:respond:{request_two}")
    check(
        await db.response_count(request_two) == 0,
        "на свою задачу отклик не записывается",
    )
    check(await db.next_request_for(CUSTOMER) is None, "свою задачу в ленте не видно")

    # ── 12. Пропуск ──
    s.reset()
    await run.click(PERFORMER, "menu:work")
    check("Task #2" in s.last_text() or "Задача №2" in s.last_text(),
          "исполнитель видит вторую задачу")
    s.reset()
    await run.click(PERFORMER, f"req:skip:{request_two}")
    check(
        await db.next_request_for(PERFORMER) is None,
        "после пропуска задача больше не попадается",
    )

    # ── 13. Фильтр по тэгу ──
    s.reset()
    await run.click(PERFORMER, "tag:filter:video")
    check(
        await db.next_request_for(PERFORMER, "video") is None,
        "под чужим тэгом открытых задач нет",
    )

    # ── 14. Мои отклики ──
    s.reset()
    await run.click(PERFORMER, "menu:myresp")
    check("Your responses" in s.last_text(), "исполнитель видит свои отклики")

    # ── 15. Мои задачи у заказчика ──
    s.reset()
    await run.click(CUSTOMER, "menu:myreq")
    check("Ваши задачи" in s.last_text(), "заказчик видит список своих задач")

    # ── 16. Админка ──
    # Админ сначала обычный пользователь: /start и выбор языка.
    s.reset()
    await run.send(ADMIN, "/start")
    await run.click(ADMIN, "lang:ru")
    check(await db.get_lang(ADMIN) == "ru", "админ тоже проходит выбор языка")

    s.reset()
    await run.send(ADMIN, "/admin")
    check("Админ-панель" in s.last_text(), "админ открывает панель")

    s.reset()
    await run.click(ADMIN, "admin:stats")
    stats = s.last_text()
    check("Пользователей: 4" in stats, "статистика считает людей верно")
    check("Задач всего: 2" in stats, "статистика считает задачи верно")
    check("Состоялось сделок: 1" in stats, "статистика считает сделки верно")

    # ── 17. Обычный пользователь в админку не попадёт ──
    s.reset()
    await run.click(CUSTOMER, "admin:stats")
    check("Статистика" not in s.last_text(), "обычный пользователь в админку не проходит")

    # ── 18. Неизвестный текст ──
    s.reset()
    await run.send(CUSTOMER, "абракадабра без смысла")
    check("Не понял" in s.last_text(), "непонятный текст обрабатывается заглушкой")

    await run.bot.session.close()
    tmp_db.unlink(missing_ok=True)

    print(f"\nВсе {PASSED} проверок пройдены. Площадка работает целиком.")


if __name__ == "__main__":
    asyncio.run(main())