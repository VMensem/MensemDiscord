from __future__ import annotations

import sqlite3
import time
from pathlib import Path


DB_PATH = Path("ai_assistant/data/ai.db")


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ratelimits (
                user_id INTEGER PRIMARY KEY,
                count INTEGER NOT NULL,
                window_start REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        conn.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('enabled', 'true')")
        conn.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('limit_per_hour', '20')")
        conn.commit()


def get_config(key: str, default: str | None = None) -> str | None:
    with _connect() as conn:
        row = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row else default


def set_config(key: str, value: str) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO config (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, str(value)),
        )
        conn.commit()


def add_message(user_id: int, role: str, message: str, timestamp: float | None = None) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO history (user_id, role, message, timestamp) VALUES (?, ?, ?, ?)",
            (int(user_id), role, message, float(timestamp or time.time())),
        )
        conn.commit()


def get_history(user_id: int, limit: int = 12, ttl_days: int | None = None) -> list[dict[str, str]]:
    cutoff = None
    if ttl_days is not None:
        cutoff = time.time() - (ttl_days * 86400)

    query = "SELECT role, message, timestamp FROM history WHERE user_id = ?"
    params: list[object] = [int(user_id)]
    if cutoff is not None:
        query += " AND timestamp >= ?"
        params.append(cutoff)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(int(limit))

    with _connect() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()

    rows = list(reversed(rows))
    return [{"role": row["role"], "message": row["message"], "timestamp": str(row["timestamp"])} for row in rows]


def clear_history(user_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM history WHERE user_id = ?", (int(user_id),))
        conn.commit()


def trim_history(user_id: int, keep_limit: int) -> None:
    if keep_limit <= 0:
        clear_history(user_id)
        return

    with _connect() as conn:
        conn.execute(
            """
            DELETE FROM history
            WHERE rowid IN (
                SELECT rowid FROM history
                WHERE user_id = ?
                ORDER BY timestamp DESC, rowid DESC
                LIMIT -1 OFFSET ?
            )
            """,
            (int(user_id), int(keep_limit)),
        )
        conn.commit()


def purge_old_history(ttl_days: int) -> None:
    cutoff = time.time() - (int(ttl_days) * 86400)
    with _connect() as conn:
        conn.execute("DELETE FROM history WHERE timestamp < ?", (cutoff,))
        conn.commit()


def cleanup_history(user_id: int, keep_limit: int, ttl_days: int) -> None:
    purge_old_history(ttl_days)
    trim_history(user_id, keep_limit)


def check_rate_limit(user_id: int, limit_per_hour: int) -> bool:
    now = time.time()
    with _connect() as conn:
        row = conn.execute(
            "SELECT count, window_start FROM ratelimits WHERE user_id = ?",
            (int(user_id),),
        ).fetchone()

        if not row or (now - float(row["window_start"])) > 3600:
            conn.execute(
                "INSERT INTO ratelimits (user_id, count, window_start) VALUES (?, ?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET count = excluded.count, window_start = excluded.window_start",
                (int(user_id), 1, now),
            )
            conn.commit()
            return True

        if int(row["count"]) < int(limit_per_hour):
            conn.execute(
                "UPDATE ratelimits SET count = count + 1 WHERE user_id = ?",
                (int(user_id),),
            )
            conn.commit()
            return True

    return False
