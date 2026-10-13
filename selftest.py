"""
Самопроверка проекта. Токен и интернет не нужны.

Запуск:
    python selftest.py
"""

from __future__ import annotations

import asyncio
import re
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402
import database as db  # noqa: E402
import i18n  # noqa: E402
import utils  # noqa: E402

PASSED = 0


def check(condition: bool, label: str) -> None:
    global PASSED
    if condition:
        PASSED += 1
        print(f"[OK] {label}")
    else:
        print(f"[ПРОВАЛ] {label}")
        raise SystemExit(1)


async def run() -> None:
    print("Проверка FindGig\n")

    # ── тэги ──
    check(len(config.TAGS) > 0, f"тэги описаны: {len(config.TAGS)} шт.")
    tag_keys = [tag.key for tag in config.TAGS]
    check(len(set(tag_keys)) == len(tag_keys), "коды тэгов уникальны")
    check(
        all(tag.ru and tag.en for tag in config.TAGS),
        "у каждого тэга есть название на русском и английском",
    )
    check(
        config.tag_label(tag_keys[0], "ru") != config.tag_label(tag_keys[0], "en"),
        "названия тэгов различаются по языкам",
    )
    check(config.tag_label("неизвестный", "ru") == "неизвестный",
          "неизвестный тэг не ломает вывод")

    # ── языки и переводы ──
    check(len(config.LANGUAGES) == 2, "языков ровно два")
    check(config.DEFAULT_LANG in config.LANGUAGES, "язык по умолчанию входит в список")
    for lang in config.LANGUAGES:
        check(lang in i18n.TEXTS, f"переводы для языка «{lang}» есть")

    ru_keys = set(i18n.TEXTS["ru"])
    en_keys = set(i18n.TEXTS["en"])
    only_ru = sorted(ru_keys - en_keys)
    only_en = sorted(en_keys - ru_keys)
    check(not only_ru, f"все русские ключи переведены на английский (нет: {only_ru})")
    check(not only_en, f"все английские ключи переведены на русский (нет: {only_en})")

    empty = sorted(k for k, v in i18n.TEXTS["ru"].items() if not v.strip())
    check(not empty, f"нет пустых переводов (нет: {empty})")

    # ── статусы ──
    for status in (config.STATUS_OPEN, config.STATUS_CLOSED, config.STATUS_CANCELLED):
        for lang in config.LANGUAGES:
            check(
                f"status_{status}" in i18n.TEXTS[lang],
                f"статус «{status}» переведён на {lang}",
            )

    # ── ключи, которые реально используются в коде ──
    used: set[str] = set()
    for path in Path(".").glob("handlers_*.py"):
        source = path.read_text(encoding="utf-8")
        used |= set(re.findall(r'i18n\.t\(\s*[^,]+,\s*"([a-zA-Z_0-9]+)"', source))
    for path in ("bot.py", "keyboards.py"):
        source = Path(path).read_text(encoding="utf-8")
        used |= set(re.findall(r'i18n\.t\(\s*[^,]+,\s*"([a-zA-Z_0-9]+)"', source))

    missing = sorted(key for key in used if key not in i18n.TEXTS["ru"])
    check(not missing, f"все ключи из кода переведены (потеряны: {missing})")
    print(f"     (проверено ключей из кода: {len(used)})")

    # ── база данных ──
    tmp_db = Path(tempfile.gettempdir()) / "findgig_selftest.db"
    tmp_db.unlink(missing_ok=True)
    config.DB_PATH = str(tmp_db)

    await db.init_db()
    check(tmp_db.exists(), "база данных создаётся")

    await db.upsert_user(1, "customer_acc", "Заказчик")
    await db.upsert_user(2, "performer_acc", "Исполнитель")
    await db.upsert_user(3, None, "Второй исполнитель")

    check(not await db.lang_chosen(1), "язык не считается выбранным до выбора")
    await db.set_lang(1, "ru")
    check(await db.get_lang(1) == "ru", "выбранный язык сохраняется")
    check(await db.lang_chosen(1), "после выбора язык считается выбранным")

    # ── задачи ──
    request_id = await db.create_request(
        1, config.TAGS[0].key, "Нужно сверстать лендинг под ключ"
    )
    check(request_id == 1, f"задача создаётся, номер {request_id}")
    check(await db.response_count(request_id) == 0, "у новой задачи нет откликов")
    check(await db.next_request_for(1) is None, "свою задачу в ленте не видно")
    check(
        (await db.next_request_for(2)) is not None,
        "чужая открытая задача попадается в ленте",
    )
    check(
        await db.next_request_for(2, "video") is None,
        "фильтр по другому тэгу задачу не показывает",
    )
    check(
        await db.next_request_for(2, config.TAGS[0].key) is not None,
        "фильтр по нужному тэгу задачу показывает",
    )

    # ── пропуск ──
    await db.skip_request(request_id, 2)
    check(
        await db.next_request_for(2) is None,
        "пропущенная задача больше не попадается",
    )

    # ── отклики ──
    check(await db.add_response(request_id, 2) is True, "отклик добавляется")
    check(await db.add_response(request_id, 2) is False, "повторный отклик не дублируется")
    check(await db.has_responded(request_id, 2), "отклик виден в базе")
    check(await db.response_count(request_id) == 1, "счётчик откликов верный")

    performers = await db.responses_for_request(request_id)
    check(
        len(performers) == 1 and performers[0]["user_id"] == 2,
        "список откликнувшихся собирается верно",
    )

    await db.add_response(request_id, 3)
    check(await db.response_count(request_id) == 2, "второй отклик учитывается")
    check(
        await db.responder_ids(request_id, exclude=2) == [3],
        "остальные откликнувшиеся определяются верно",
    )

    # ── мэтчинг ──
    check(await db.choose_performer(request_id, 2) is True, "выбор исполнителя проходит")
    check(
        await db.choose_performer(request_id, 3) is False,
        "закрытую задачу нельзя закрыть повторно",
    )
    row = await db.get_request(request_id)
    check(row is not None and row["status"] == config.STATUS_CLOSED, "задача закрывается")
    check(row is not None and row["chosen_performer_id"] == 2, "выбранный исполнитель записан")

    # ── отмена ──
    second = await db.create_request(1, "design", "Второй заказ: дизайн баннера")
    check(await db.cancel_request(second, 1) is True, "свою открытую задачу можно отменить")
    check(await db.cancel_request(second, 1) is False, "повторная отмена не проходит")
    check(await db.cancel_request(request_id, 1) is False, "закрытую задачу отменить нельзя")
    check(await db.cancel_request(second, 999) is False, "чужую задачу отменить нельзя")

    # ── статистика ──
    summary = await db.stats()
    check(summary["users"] == 3, f"пользователей: {summary['users']}")
    check(summary["requests"] == 2, f"задач: {summary['requests']}")
    check(summary["responses"] == 2, f"откликов: {summary['responses']}")
    check(summary["deals"] == 1, f"состоявшихся сделок: {summary['deals']}")
    check(summary["open_requests"] == 0, f"открытых задач: {summary['open_requests']}")

    # ── контакты ──
    with_nick = utils.contact_html(
        {"user_id": 5, "username": "vasya", "full_name": "Вася"}
    )
    check(with_nick == "@vasya", "контакт с @username показывается ником")
    without_nick = utils.contact_html(
        {"user_id": 5, "username": None, "full_name": "Вася"}
    )
    check("tg://user?id=5" in without_nick, "без @username даётся ссылка на профиль")
    check(utils.short("a" * 100, 10).endswith("…"), "длинный текст обрезается")
    check(utils.esc("<b>зло</b>") == "&lt;b&gt;зло&lt;/b&gt;", "опасные символы экранируются")

    tmp_db.unlink(missing_ok=True)
    print(f"\nВсе {PASSED} проверок пройдены.")


if __name__ == "__main__":
    asyncio.run(run())