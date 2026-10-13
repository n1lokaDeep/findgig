"""
Все тексты интерфейса на двух языках.

Пользователь выбирает язык при первом запуске. Добавить третий язык —
значит дописать сюда ещё один словарь и добавить код в config.LANGUAGES.
"""

from __future__ import annotations

import config

# Подписи в карточке человека
PERSON_LABELS: dict[str, dict[str, str]] = {
    "ru": {"name": "Имя", "contact": "Контакт"},
    "en": {"name": "Name", "contact": "Contact"},
}

TEXTS: dict[str, dict[str, str]] = {
    # ───────────────────────────── русский ─────────────────────────────
    "ru": {
        "choose_language": "Выберите язык / Choose your language",
        "lang_changed": "Язык переключён на русский.",
        "welcome": (
            "👋 <b>{brand}</b> — площадка, где одни публикуют задачи, "
            "а другие берутся за них.\n\n"
            "🔎 <b>Ищу исполнителя</b> — опубликуйте задачу с тэгом.\n"
            "💼 <b>Хочу подработать</b> — листайте задачи и откликайтесь.\n\n"
            "Когда заказчик выберет исполнителя, бот сразу даст вам "
            "контакты друг друга."
        ),
        "menu_title": "Главное меню. Что делаем?",
        "btn_find_performer": "🔎 Ищу исполнителя",
        "btn_work": "💼 Хочу подработать",
        "btn_my_requests": "📋 Мои задачи",
        "btn_my_responses": "📨 Мои отклики",
        "btn_change_lang": "🌐 Сменить язык",
        "btn_help": "❓ Помощь",
        "btn_back": "◀ Назад",
        "btn_menu": "🏠 Меню",
        # заказчик
        "ask_tag": "По какому тэгу задача?",
        "ask_desc": (
            "Опишите задачу: что нужно сделать, в какие сроки, "
            "какие детали важны.\n\nЧем конкретнее — тем больше будет откликов."
        ),
        "desc_short": "Слишком коротко. Напишите хотя бы {min} символов.",
        "desc_long": "Слишком длинно. Максимум {max} символов.",
        "confirm_request": (
            "Проверьте задачу перед публикацией:\n\n"
            "<b>Тэг:</b> {tag}\n"
            "<b>Описание:</b> {description}"
        ),
        "btn_publish": "✅ Опубликовать",
        "btn_cancel": "❌ Отменить",
        "published": (
            "✅ Задача №{id} опубликована.\n\n"
            "Исполнители увидят её и смогут откликнуться. "
            "Я сообщу, когда кто-то откликнется."
        ),
        "cancelled": "Отменено.",
        "my_requests_empty": "Вы ещё не публиковали задач.",
        "my_requests_header": "Ваши задачи:",
        "my_request_item": (
            "№{id} · {tag} · {status} · откликов: {responses}\n{preview}"
        ),
        "status_open": "открыта",
        "status_closed": "закрыта",
        "status_cancelled": "отменена",
        "request_card_customer": (
            "📌 <b>Задача №{id}</b>\n"
            "<b>Тэг:</b> {tag}\n"
            "<b>Статус:</b> {status}\n"
            "<b>Откликов:</b> {responses}\n"
            "<b>Опубликована:</b> {created}\n\n"
            "{description}"
        ),
        # исполнитель
        "no_requests": (
            "Пока нет открытых задач. Загляните позже — "
            "или смените тэг, если хотите посмотреть другие."
        ),
        "request_card": (
            "📌 <b>Задача №{id}</b>\n"
            "<b>Тэг:</b> {tag}\n"
            "<b>Заказчик:</b> {author}\n"
            "<b>Опубликована:</b> {created}\n\n"
            "{description}"
        ),
        "btn_respond": "✋ Берусь",
        "btn_skip": "⏭ Дальше",
        "btn_filter": "🏷 Тэг",
        "responded": (
            "✋ Отклик отправлен.\n\n"
            "Заказчик увидит вас в списке откликнувшихся и выберет. "
            "Я сообщу, если выберет вас."
        ),
        "already_responded": "Вы уже откликались на эту задачу.",
        "respond_own": "Это ваша собственная задача — откликнуться нельзя.",
        "my_responses_empty": "Вы пока ни на что не откликались.",
        "my_responses_header": "Ваши отклики:",
        "my_response_item": "№{id} · {tag} · {status}\n{preview}",
        # мэтчинг
        "new_response_to_customer": (
            "🔔 Новая заявка на вашу задачу №{id}\n\n"
            "{performer}\n\n"
            "Можете выбрать этого исполнителя или подождать других."
        ),
        "btn_choose": "✅ Выбрать",
        "btn_keep_looking": "⏳ Ждать других",
        "keep_looking": (
            "Хорошо, ждём других.\n\n"
            "Все отклики по задаче №{id} можно посмотреть в разделе «Мои задачи»."
        ),
        "responses_list_header": "Отклики на задачу №{id}:",
        "no_responses_yet": "По этой задаче пока нет откликов.",
        "choose_hint": "Выберите исполнителя из списка ниже.",
        "chosen_customer": (
            "✅ Исполнитель выбран.\n\n"
            "<b>Задача №{id}</b>\n\n"
            "<b>Контакт исполнителя:</b>\n{contact}\n\n"
            "Напишите ему сами и обсудите детали. Удачи!"
        ),
        "chosen_performer": (
            "🎉 Вас выбрали по задаче №{id}!\n\n"
            "<b>Контакт заказчика:</b>\n{contact}\n\n"
            "Напишите ему сами и обсудите детали. Удачи!"
        ),
        "closed_for_others": (
            "Задача №{id}, на которую вы откликались, закрыта — "
            "заказчик выбрал другого исполнителя."
        ),
        "request_already_closed": "Эта задача уже закрыта.",
        # общее
        "no_username_warning": (
            "⚠️ <b>У вас не задан @username в Telegram.</b>\n\n"
            "Тогда связаться с вами можно только по ссылке на профиль, "
            "а это неудобно и часть людей просто не напишет.\n\n"
            "Поставьте себе имя пользователя: Telegram → Настройки → "
            "Имя пользователя. Это займёт полминуты."
        ),
        "help_text": (
            "<b>Как это работает</b>\n\n"
            "🔎 <b>Ищу исполнителя.</b> Выбираете тэг, описываете задачу — "
            "она попадает в общую ленту.\n\n"
            "💼 <b>Хочу подработать.</b> Листаете чужие задачи и жмёте "
            "«Берусь». Откликов может быть много.\n\n"
            "✅ <b>Мэтчинг.</b> Заказчик выбирает одного исполнителя — "
            "и бот сразу даёт им контакты друг друга.\n\n"
            "Задачу можно закрыть в любой момент: «Мои задачи»."
        ),
        "fallback": "Не понял сообщение. Воспользуйтесь кнопками ниже.",
        # админ
        "admin_menu": "Админ-панель.",
        "admin_stats": (
            "<b>Статистика</b>\n\n"
            "Пользователей: {users}\n"
            "Задач всего: {requests}\n"
            "Открытых: {open_requests}\n"
            "Откликов: {responses}\n"
            "Состоялось сделок: {closed}"
        ),
        "admin_requests_header": "Последние задачи:",
        "admin_users_header": "Последние пользователи:",
        "admin_no_data": "Данных пока нет.",
        "admin_broadcast_ask": "Отправьте текст для рассылки всем пользователям.",
        "admin_broadcast_done": "Рассылка: доставлено {sent}, не доставлено {failed}.",
        "btn_admin_requests": "📋 Задачи",
        "btn_admin_users": "👥 Люди",
        "btn_admin_stats": "📊 Статистика",
        "btn_admin_broadcast": "📣 Рассылка",
    },
    # ───────────────────────────── english ─────────────────────────────
    "en": {
        "choose_language": "Выберите язык / Choose your language",
        "lang_changed": "Language switched to English.",
        "welcome": (
            "👋 <b>{brand}</b> — a place where people post tasks "
            "and others take them on.\n\n"
            "🔎 <b>I need something done</b> — post a task with a tag.\n"
            "💼 <b>I want to earn</b> — browse tasks and respond.\n\n"
            "When the customer picks a performer, the bot instantly "
            "exchanges your contacts."
        ),
        "menu_title": "Main menu. What are we doing?",
        "btn_find_performer": "🔎 I need something done",
        "btn_work": "💼 I want to earn",
        "btn_my_requests": "📋 My tasks",
        "btn_my_responses": "📨 My responses",
        "btn_change_lang": "🌐 Change language",
        "btn_help": "❓ Help",
        "btn_back": "◀ Back",
        "btn_menu": "🏠 Menu",
        "ask_tag": "Which tag fits your task?",
        "ask_desc": (
            "Describe the task: what needs to be done, by when, "
            "which details matter.\n\nThe more specific, the more responses."
        ),
        "desc_short": "Too short. Write at least {min} characters.",
        "desc_long": "Too long. Maximum {max} characters.",
        "confirm_request": (
            "Check your task before publishing:\n\n"
            "<b>Tag:</b> {tag}\n"
            "<b>Description:</b> {description}"
        ),
        "btn_publish": "✅ Publish",
        "btn_cancel": "❌ Cancel",
        "published": (
            "✅ Task #{id} is published.\n\n"
            "Performers will see it and can respond. "
            "I will let you know when someone does."
        ),
        "cancelled": "Cancelled.",
        "my_requests_empty": "You have not published any tasks yet.",
        "my_requests_header": "Your tasks:",
        "my_request_item": (
            "#{id} · {tag} · {status} · responses: {responses}\n{preview}"
        ),
        "status_open": "open",
        "status_closed": "closed",
        "status_cancelled": "cancelled",
        "request_card_customer": (
            "📌 <b>Task #{id}</b>\n"
            "<b>Tag:</b> {tag}\n"
            "<b>Status:</b> {status}\n"
            "<b>Responses:</b> {responses}\n"
            "<b>Published:</b> {created}\n\n"
            "{description}"
        ),
        "no_requests": (
            "No open tasks right now. Check back later — "
            "or switch the tag to look at others."
        ),
        "request_card": (
            "📌 <b>Task #{id}</b>\n"
            "<b>Tag:</b> {tag}\n"
            "<b>Customer:</b> {author}\n"
            "<b>Published:</b> {created}\n\n"
            "{description}"
        ),
        "btn_respond": "✋ I'll take it",
        "btn_skip": "⏭ Next",
        "btn_filter": "🏷 Tag",
        "responded": (
            "✋ Response sent.\n\n"
            "The customer will see you among the responders and choose. "
            "I will tell you if it is you."
        ),
        "already_responded": "You have already responded to this task.",
        "respond_own": "This is your own task — you cannot respond to it.",
        "my_responses_empty": "You have not responded to anything yet.",
        "my_responses_header": "Your responses:",
        "my_response_item": "#{id} · {tag} · {status}\n{preview}",
        "new_response_to_customer": (
            "🔔 New response to your task #{id}\n\n"
            "{performer}\n\n"
            "You can choose this performer or wait for others."
        ),
        "btn_choose": "✅ Choose",
        "btn_keep_looking": "⏳ Wait for others",
        "keep_looking": (
            "Alright, waiting for others.\n\n"
            "All responses to task #{id} are in the “My tasks” section."
        ),
        "responses_list_header": "Responses to task #{id}:",
        "no_responses_yet": "No responses to this task yet.",
        "choose_hint": "Pick a performer from the list below.",
        "chosen_customer": (
            "✅ Performer chosen.\n\n"
            "<b>Task #{id}</b>\n\n"
            "<b>Performer's contact:</b>\n{contact}\n\n"
            "Message them yourself and sort out the details. Good luck!"
        ),
        "chosen_performer": (
            "🎉 You were chosen for task #{id}!\n\n"
            "<b>Customer's contact:</b>\n{contact}\n\n"
            "Message them yourself and sort out the details. Good luck!"
        ),
        "closed_for_others": (
            "Task #{id} you responded to is now closed — "
            "the customer chose another performer."
        ),
        "request_already_closed": "This task is already closed.",
        "no_username_warning": (
            "⚠️ <b>You have no @username set in Telegram.</b>\n\n"
            "That means people can reach you only through a profile link, "
            "which is inconvenient and some will simply not write.\n\n"
            "Set a username: Telegram → Settings → Username. Takes 30 seconds."
        ),
        "help_text": (
            "<b>How it works</b>\n\n"
            "🔎 <b>I need something done.</b> Pick a tag, describe the task — "
            "it goes to the shared feed.\n\n"
            "💼 <b>I want to earn.</b> Browse other people's tasks and hit "
            "“I'll take it”. Many people can respond to one task.\n\n"
            "✅ <b>Matching.</b> The customer picks one performer — and the bot "
            "instantly gives both sides each other's contacts.\n\n"
            "You can close a task any time in “My tasks”."
        ),
        "fallback": "I did not understand that. Use the buttons below.",
        "admin_menu": "Admin panel.",
        "admin_stats": (
            "<b>Statistics</b>\n\n"
            "Users: {users}\n"
            "Tasks total: {requests}\n"
            "Open: {open_requests}\n"
            "Responses: {responses}\n"
            "Deals made: {closed}"
        ),
        "admin_requests_header": "Latest tasks:",
        "admin_users_header": "Latest users:",
        "admin_no_data": "No data yet.",
        "admin_broadcast_ask": "Send the text to broadcast to all users.",
        "admin_broadcast_done": "Broadcast: delivered {sent}, failed {failed}.",
        "btn_admin_requests": "📋 Tasks",
        "btn_admin_users": "👥 People",
        "btn_admin_stats": "📊 Statistics",
        "btn_admin_broadcast": "📣 Broadcast",
    },
}


def t(lang: str, key: str, **kwargs: object) -> str:
    """
    Текст по ключу на нужном языке.

    Если языка нет или ключ не переведён — берётся язык по умолчанию.
    Никогда не падает: в худшем случае вернёт сам ключ.
    """
    if lang not in TEXTS:
        lang = config.DEFAULT_LANG

    text = TEXTS[lang].get(key)
    if text is None:
        text = TEXTS[config.DEFAULT_LANG].get(key, key)

    for name, value in kwargs.items():
        text = text.replace("{" + name + "}", str(value))
    return text


def person_labels(lang: str) -> dict[str, str]:
    return PERSON_LABELS.get(lang, PERSON_LABELS[config.DEFAULT_LANG])


def normalize_lang(value: str | None) -> str:
    """Приводит код языка к поддерживаемому."""
    if value in config.LANGUAGES:
        return str(value)
    return config.DEFAULT_LANG