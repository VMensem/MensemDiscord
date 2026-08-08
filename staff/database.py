from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import aiosqlite


DB_PATH = Path("supportbot.db")


class StaffDatabaseError(RuntimeError):
    pass


class StaffApplicationNotFound(StaffDatabaseError):
    pass


class StaffApplicationConflict(StaffDatabaseError):
    def __init__(self, message: str, application: dict[str, Any] | None = None):
        super().__init__(message)
        self.application = application


class StaffApplicationStateError(StaffDatabaseError):
    def __init__(self, message: str, application: dict[str, Any] | None = None):
        super().__init__(message)
        self.application = application


def _dict_from_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def _dump_answers(answers: Any) -> str:
    if isinstance(answers, str):
        return answers
    return json.dumps(answers, ensure_ascii=False, sort_keys=True)


def _connect() -> aiosqlite.Connection:
    return aiosqlite.connect(DB_PATH)


async def _fetchone(db: aiosqlite.Connection, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    async with db.execute(query, params) as cursor:
        row = await cursor.fetchone()
    return _dict_from_row(row)


async def _fetchall(db: aiosqlite.Connection, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    async with db.execute(query, params) as cursor:
        rows = await cursor.fetchall()
    return [_dict_from_row(row) for row in rows if row is not None]


async def _ensure_column(db: aiosqlite.Connection, table: str, column: str, definition: str) -> None:
    async with db.execute(f"PRAGMA table_info({table})") as cursor:
        columns = {row[1] for row in await cursor.fetchall()}
    if column not in columns:
        await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


async def init_db() -> None:
    async with _connect() as db:
        db.row_factory = sqlite3.Row
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS staff_applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                position TEXT NOT NULL,
                answers TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                reviewer_id INTEGER,
                rejection_reason TEXT,
                channel_id INTEGER,
                message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP
            )
            """
        )
        await _ensure_column(db, "staff_applications", "channel_id", "INTEGER")
        await _ensure_column(db, "staff_applications", "message_id", "INTEGER")
        await _ensure_column(db, "staff_applications", "reviewed_at", "TIMESTAMP")
        await _ensure_column(db, "staff_applications", "rejection_reason", "TEXT")
        await _ensure_column(db, "staff_applications", "reviewer_id", "INTEGER")
        await _ensure_column(db, "staff_applications", "updated_at", "TIMESTAMP")
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_staff_applications_user_position
            ON staff_applications (guild_id, user_id, position)
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_staff_applications_status
            ON staff_applications (guild_id, status)
            """
        )
        await db.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_staff_active_unique
            ON staff_applications (guild_id, user_id, position)
            WHERE status IN ('pending', 'claimed')
            """
        )
        await db.commit()


async def get_application(application_id: int) -> dict[str, Any] | None:
    async with _connect() as db:
        db.row_factory = sqlite3.Row
        return await _fetchone(
            db,
            """
            SELECT *
            FROM staff_applications
            WHERE application_id = ?
            """,
            (application_id,),
        )


async def list_open_applications(guild_id: int | None = None) -> list[dict[str, Any]]:
    async with _connect() as db:
        db.row_factory = sqlite3.Row
        if guild_id is None:
            return await _fetchall(
                db,
                """
                SELECT *
                FROM staff_applications
                WHERE status IN ('pending', 'claimed')
                ORDER BY created_at ASC, application_id ASC
                """,
            )

        return await _fetchall(
            db,
            """
            SELECT *
            FROM staff_applications
            WHERE guild_id = ? AND status IN ('pending', 'claimed')
            ORDER BY created_at ASC, application_id ASC
            """,
            (guild_id,),
        )


async def get_active_application(user_id: int, guild_id: int, position: str) -> dict[str, Any] | None:
    async with _connect() as db:
        db.row_factory = sqlite3.Row
        return await _fetchone(
            db,
            """
            SELECT *
            FROM staff_applications
            WHERE user_id = ? AND guild_id = ? AND position = ? AND status IN ('pending', 'claimed')
            ORDER BY application_id DESC
            LIMIT 1
            """,
            (user_id, guild_id, position),
        )


async def create_application(user_id: int, guild_id: int, position: str, answers: Any) -> dict[str, Any]:
    async with _connect() as db:
        db.row_factory = sqlite3.Row
        await db.execute("BEGIN IMMEDIATE")
        existing = await _fetchone(
            db,
            """
            SELECT *
            FROM staff_applications
            WHERE user_id = ? AND guild_id = ? AND position = ? AND status IN ('pending', 'claimed')
            ORDER BY application_id DESC
            LIMIT 1
            """,
            (user_id, guild_id, position),
        )
        if existing is not None:
            await db.rollback()
            raise StaffApplicationConflict("active_application_exists", existing)

        cursor = await db.execute(
            """
            INSERT INTO staff_applications (
                user_id, guild_id, position, answers, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (user_id, guild_id, position, _dump_answers(answers)),
        )
        application_id = cursor.lastrowid
        await db.commit()
        application = await _fetchone(
            db,
            """
            SELECT *
            FROM staff_applications
            WHERE application_id = ?
            """,
            (application_id,),
        )
        if application is None:
            raise StaffDatabaseError("Application was created but could not be loaded")
        return application


async def set_application_message(application_id: int, channel_id: int, message_id: int) -> None:
    async with _connect() as db:
        db.row_factory = sqlite3.Row
        await db.execute(
            """
            UPDATE staff_applications
            SET channel_id = ?, message_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE application_id = ?
            """,
            (channel_id, message_id, application_id),
        )
        await db.commit()


async def cancel_application(application_id: int, *, reason: str | None = None) -> None:
    async with _connect() as db:
        db.row_factory = sqlite3.Row
        await db.execute(
            """
            UPDATE staff_applications
            SET status = 'cancelled',
                rejection_reason = COALESCE(?, rejection_reason),
                updated_at = CURRENT_TIMESTAMP
            WHERE application_id = ?
            """,
            (reason, application_id),
        )
        await db.commit()


async def mark_application_review_state(
    application_id: int,
    *,
    reviewer_id: int,
    status: str,
    rejection_reason: str | None = None,
) -> dict[str, Any]:
    if status not in {"claimed", "accepted", "rejected"}:
        raise ValueError(f"Unsupported staff application status: {status}")

    async with _connect() as db:
        db.row_factory = sqlite3.Row
        await db.execute("BEGIN IMMEDIATE")
        application = await _fetchone(
            db,
            """
            SELECT *
            FROM staff_applications
            WHERE application_id = ?
            """,
            (application_id,),
        )
        if application is None:
            await db.rollback()
            raise StaffApplicationNotFound("application_not_found")

        current_status = application["status"]
        current_reviewer = application["reviewer_id"]

        if current_status in {"accepted", "rejected"}:
            await db.rollback()
            raise StaffApplicationStateError("application_already_closed", application)

        if status == "claimed":
            if current_status == "claimed" and current_reviewer not in (None, reviewer_id):
                await db.rollback()
                raise StaffApplicationStateError("application_claimed_by_other", application)

            if current_status == "pending":
                await db.execute(
                    """
                    UPDATE staff_applications
                    SET status = 'claimed',
                        reviewer_id = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE application_id = ? AND status = 'pending'
                    """,
                    (reviewer_id, application_id),
                )
            elif current_status == "claimed" and current_reviewer is None:
                await db.execute(
                    """
                    UPDATE staff_applications
                    SET reviewer_id = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE application_id = ? AND status = 'claimed' AND reviewer_id IS NULL
                    """,
                    (reviewer_id, application_id),
                )
            await db.commit()
            updated = await _fetchone(
                db,
                "SELECT * FROM staff_applications WHERE application_id = ?",
                (application_id,),
            )
            if updated is None:
                raise StaffDatabaseError("Claim succeeded but application was not reloaded")
            return updated

        if current_status == "claimed" and current_reviewer not in (None, reviewer_id):
            await db.rollback()
            raise StaffApplicationStateError("application_claimed_by_other", application)

        await db.execute(
            """
            UPDATE staff_applications
            SET status = ?,
                reviewer_id = COALESCE(reviewer_id, ?),
                rejection_reason = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE application_id = ? AND status IN ('pending', 'claimed')
            """,
            (status, reviewer_id, rejection_reason, application_id),
        )
        await db.commit()
        updated = await _fetchone(
            db,
            "SELECT * FROM staff_applications WHERE application_id = ?",
            (application_id,),
        )
        if updated is None:
            raise StaffDatabaseError("Decision succeeded but application was not reloaded")
        return updated
