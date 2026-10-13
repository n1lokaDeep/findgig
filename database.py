"""База данных: пользователи, задачи, отклики, пропуски."""

from __future__ import annotations

from datetime import datetime

import aiosqlite

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id    INTEGER PRIMARY KEY,
    username   TEXT,
    full_name  TEXT,
    lang       TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS requests (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id         INTEGER NOT NULL,
    tag                 TEXT NOT NULL,
    description         TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'open',
    chosen_performer_id INTEGER,
    created_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS responses (
    request_id   INTEGER NOT NULL,
    performer_id INTEGER NOT NULL,
    created_at   TEXT NOT NULL,
    PRIMARY KEY (request_id, performer_id)
);

CREATE TABLE IF NOT EXISTS skips (
    request_id   INTEGER NOT NULL,
    performer_id INTEGER NOT NULL,
    created_at   TEXT NOT NULL,
    PRIMARY KEY (request_id, performer_id)
);

CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_customer ON requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_responses_performer ON responses(performer_id);
"""


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


async def init_db() -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def _fetchone(query: str, params: tuple = ()) -> dict | None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            row = await cursor.fetchone()
    return dict(row) if row else None


async def _fetchall(query: str, params: tuple = ()) -> list[dict]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def _execute(query: str, params: tuple = ()) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(query, params)
        await db.commit()


# ──────────────────────────── пользователи ────────────────────────────


async def upsert_user(user_id: int, username: str | None, full_name: str) -> None:
    """Заводит или обновляет пользователя, не сбрасывая выбранный язык."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, full_name, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username  = excluded.username,
                full_name = excluded.full_name
            """,
            (user_id, username, full_name, _now()),
        )
        await db.commit()


async def get_user(user_id: int) -> dict | None:
    return await _fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))


async def set_lang(user_id: int, lang: str) -> None:
    await _execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))


async def get_lang(user_id: int) -> str:
    """Язык пользователя. Если он ещё не выбран — язык по умолчанию."""
    row = await _fetchone("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    if not row:
        return config.DEFAULT_LANG
    return str(row["lang"] or config.DEFAULT_LANG)


async def lang_chosen(user_id: int) -> bool:
    """Выбирал ли пользователь язык. Пустая строка означает «ещё не выбирал»."""
    row = await _fetchone("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    return bool(row and row["lang"])


# ────────────────────────────── задачи ──────────────────────────────


async def create_request(customer_id: int, tag: str, description: str) -> int:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO requests (customer_id, tag, description, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (customer_id, tag, description, _now()),
        )
        await db.commit()
        return int(cursor.lastrowid or 0)


async def get_request(request_id: int) -> dict | None:
    return await _fetchone("SELECT * FROM requests WHERE id = ?", (request_id,))


async def next_request_for(
    performer_id: int, tag: str | None = None
) -> dict | None:
    """
    Следующая задача для исполнителя.

    Не показывает: свои задачи, уже пропущенные и те, на которые он откликнулся.
    Свежие — первыми.
    """
    query = """
        SELECT r.* FROM requests r
        WHERE r.status = ?
          AND r.customer_id != ?
          AND NOT EXISTS (
              SELECT 1 FROM skips s
              WHERE s.request_id = r.id AND s.performer_id = ?
          )
          AND NOT EXISTS (
              SELECT 1 FROM responses p
              WHERE p.request_id = r.id AND p.performer_id = ?
          )
    """
    params: list = [config.STATUS_OPEN, performer_id, performer_id, performer_id]

    if tag:
        query += " AND r.tag = ?"
        params.append(tag)

    query += " ORDER BY r.id DESC LIMIT 1"
    return await _fetchone(query, tuple(params))


async def skip_request(request_id: int, performer_id: int) -> None:
    """Запоминает пропуск, чтобы задача не попадалась снова."""
    await _execute(
        """
        INSERT INTO skips (request_id, performer_id, created_at)
        VALUES (?, ?, ?)
        ON CONFLICT(request_id, performer_id) DO NOTHING
        """,
        (request_id, performer_id, _now()),
    )


async def add_response(request_id: int, performer_id: int) -> bool:
    """Добавляет отклик. False, если он уже был."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO responses (request_id, performer_id, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(request_id, performer_id) DO NOTHING
            """,
            (request_id, performer_id, _now()),
        )
        await db.commit()
        return cursor.rowcount > 0


async def has_responded(request_id: int, performer_id: int) -> bool:
    row = await _fetchone(
        "SELECT 1 AS x FROM responses WHERE request_id = ? AND performer_id = ?",
        (request_id, performer_id),
    )
    return row is not None


async def responses_for_request(request_id: int) -> list[dict]:
    """Кто откликнулся на задачу — с данными о людях."""
    return await _fetchall(
        """
        SELECT u.*, p.created_at AS responded_at
        FROM responses p
        JOIN users u ON u.user_id = p.performer_id
        WHERE p.request_id = ?
        ORDER BY p.created_at
        """,
        (request_id,),
    )


async def responder_ids(request_id: int, exclude: int | None = None) -> list[int]:
    """ID откликнувшихся — чтобы уведомить их о закрытии задачи."""
    if exclude is None:
        rows = await _fetchall(
            "SELECT performer_id FROM responses WHERE request_id = ?", (request_id,)
        )
    else:
        rows = await _fetchall(
            "SELECT performer_id FROM responses WHERE request_id = ? AND performer_id != ?",
            (request_id, exclude),
        )
    return [int(row["performer_id"]) for row in rows]


async def response_count(request_id: int) -> int:
    row = await _fetchone(
        "SELECT COUNT(*) AS c FROM responses WHERE request_id = ?", (request_id,)
    )
    return int(row["c"]) if row else 0


async def choose_performer(request_id: int, performer_id: int) -> bool:
    """
    Закрывает задачу за выбранным исполнителем.

    Возвращает False, если задачу уже кто-то успел закрыть —
    тогда контакты выдавать нельзя.
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            """
            UPDATE requests
               SET status = ?, chosen_performer_id = ?
             WHERE id = ? AND status = ?
            """,
            (config.STATUS_CLOSED, performer_id, request_id, config.STATUS_OPEN),
        )
        await db.commit()
        return cursor.rowcount > 0


async def cancel_request(request_id: int, customer_id: int) -> bool:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            """
            UPDATE requests SET status = ?
             WHERE id = ? AND customer_id = ? AND status = ?
            """,
            (config.STATUS_CANCELLED, request_id, customer_id, config.STATUS_OPEN),
        )
        await db.commit()
        return cursor.rowcount > 0


async def customer_requests(customer_id: int, limit: int | None = None) -> list[dict]:
    limit = limit or config.LIST_LIMIT
    return await _fetchall(
        "SELECT * FROM requests WHERE customer_id = ? ORDER BY id DESC LIMIT ?",
        (customer_id, limit),
    )


async def performer_responses(performer_id: int, limit: int | None = None) -> list[dict]:
    limit = limit or config.LIST_LIMIT
    return await _fetchall(
        """
        SELECT r.*, p.created_at AS responded_at
        FROM responses p
        JOIN requests r ON r.id = p.request_id
        WHERE p.performer_id = ?
        ORDER BY p.created_at DESC
        LIMIT ?
        """,
        (performer_id, limit),
    )


# ───────────────────────────── админ ─────────────────────────────


async def stats() -> dict[str, int]:
    row = await _fetchone(
        """
        SELECT
          (SELECT COUNT(*) FROM users)                                   AS users,
          (SELECT COUNT(*) FROM requests)                                AS requests,
          (SELECT COUNT(*) FROM requests WHERE status = 'open')          AS open_requests,
          (SELECT COUNT(*) FROM responses)                               AS responses,
          (SELECT COUNT(*) FROM requests
            WHERE status = 'closed' AND chosen_performer_id IS NOT NULL) AS deals
        """
    )
    if not row:
        return {
            "users": 0,
            "requests": 0,
            "open_requests": 0,
            "responses": 0,
            "deals": 0,
        }
    return {key: int(value) for key, value in row.items()}


async def recent_requests(limit: int = 10) -> list[dict]:
    return await _fetchall("SELECT * FROM requests ORDER BY id DESC LIMIT ?", (limit,))


async def recent_users(limit: int = 10) -> list[dict]:
    return await _fetchall(
        "SELECT * FROM users ORDER BY created_at DESC LIMIT ?", (limit,)
    )


async def all_user_ids() -> list[int]:
    rows = await _fetchall("SELECT user_id FROM users")
    return [int(row["user_id"]) for row in rows]