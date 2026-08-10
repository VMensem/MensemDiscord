from core.database import db_manager
import time

async def get_config(guild_id: int, key: str, default: str | None = None) -> str | None:
    row = await db_manager.fetchrow(
        "SELECT value FROM ai_config WHERE guild_id = $1 AND key = $2",
        guild_id, key
    )
    return str(row["value"]) if row else default

async def set_config(guild_id: int, key: str, value: str) -> None:
    await db_manager.execute(
        """
        INSERT INTO ai_config (guild_id, key, value) VALUES ($1, $2, $3)
        ON CONFLICT (guild_id, key) DO UPDATE SET value = $3
        """,
        guild_id, key, str(value)
    )

async def add_message(user_id: int, role: str, message: str, timestamp: float | None = None) -> None:
    await db_manager.execute(
        "INSERT INTO ai_history (user_id, role, message, timestamp) VALUES ($1, $2, $3, $4)",
        user_id, role, message, float(timestamp or time.time())
    )

async def get_history(user_id: int, limit: int = 12, ttl_days: int | None = None) -> list[dict[str, str]]:
    cutoff = None
    if ttl_days is not None:
        cutoff = time.time() - (ttl_days * 86400)

    query = "SELECT role, message, timestamp FROM ai_history WHERE user_id = $1"
    params = [user_id]
    if cutoff is not None:
        query += " AND timestamp >= $2"
        params.append(cutoff)
    query += f" ORDER BY timestamp DESC LIMIT ${len(params) + 1}"
    params.append(limit)

    rows = await db_manager.fetch(query, *params)
    return [{"role": row["role"], "message": row["message"], "timestamp": str(row["timestamp"])} for row in reversed(rows)]

async def clear_history(user_id: int) -> None:
    await db_manager.execute("DELETE FROM ai_history WHERE user_id = $1", user_id)
