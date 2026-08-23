from core.database import db_manager
import json
from typing import Any

class StaffDatabaseError(Exception):
    pass

class StaffApplicationNotFound(StaffDatabaseError):
    pass

class StaffApplicationConflict(StaffDatabaseError):
    def __init__(self, message, application=None):
        super().__init__(message)
        self.application = application

class StaffApplicationStateError(StaffDatabaseError):
    def __init__(self, message, application=None):
        super().__init__(message)
        self.application = application

async def init_db():
    pass

async def create_application(user_id: int, guild_id: int, position: str, answers: Any) -> dict[str, Any]:
    row = await db_manager.fetchrow(
        """
        INSERT INTO staff_applications (user_id, guild_id, position, answers, status)
        VALUES ($1, $2, $3, $4, 'pending')
        RETURNING *
        """,
        user_id, guild_id, position, json.dumps(answers)
    )
    return dict(row) if row else {}

async def get_application(application_id: int) -> dict[str, Any] | None:
    row = await db_manager.fetchrow(
        "SELECT * FROM staff_applications WHERE application_id = $1",
        application_id
    )
    return dict(row) if row else None

async def list_open_applications(guild_id: int | None = None) -> list[dict[str, Any]]:
    query = "SELECT * FROM staff_applications WHERE status IN ('pending', 'claimed') ORDER BY created_at ASC"
    params = []
    if guild_id:
        query = "SELECT * FROM staff_applications WHERE guild_id = $1 AND status IN ('pending', 'claimed') ORDER BY created_at ASC"
        params = [guild_id]
    rows = await db_manager.fetch(query, *params)
    return [dict(row) for row in rows]

async def set_application_message(application_id: int, channel_id: int, message_id: int) -> None:
    await db_manager.execute(
        "UPDATE staff_applications SET channel_id = $1, message_id = $2, updated_at = CURRENT_TIMESTAMP WHERE application_id = $3",
        channel_id, message_id, application_id
    )

async def cancel_application(application_id: int, *, reason: str | None = None) -> None:
    await db_manager.execute(
        """
        UPDATE staff_applications
        SET status = 'cancelled', rejection_reason = $1, updated_at = CURRENT_TIMESTAMP
        WHERE application_id = $2
        """,
        reason, application_id
    )

async def mark_application_review_state(application_id: int, *, reviewer_id: int, status: str, rejection_reason: str | None = None) -> dict[str, Any]:
    await db_manager.execute(
        """
        UPDATE staff_applications
        SET status = $1, reviewer_id = $2, rejection_reason = $3, reviewed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE application_id = $4
        """,
        status, reviewer_id, rejection_reason, application_id
    )
    row = await db_manager.fetchrow("SELECT * FROM staff_applications WHERE application_id = $1", application_id)
    return dict(row) if row else {}
