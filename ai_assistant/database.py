from core.database import db_manager
import datetime

async def get_config(guild_id: int, key: str, default: str | None = None) -> str | None:
    row = await db_manager.fetchrow(
        "SELECT value FROM ai_config WHERE guild_id = $1 AND key_name = $2",
        guild_id, key
    )
    return str(row["value"]) if row else default

async def set_config(guild_id: int, key: str, value: str) -> None:
    await db_manager.execute(
        """
        INSERT INTO ai_config (guild_id, key_name, value) VALUES ($1, $2, $3)
        ON DUPLICATE KEY UPDATE value = VALUES(value)
        """,
        guild_id, key, str(value)
    )

async def add_message(user_id: int, role: str, message: str, timestamp: datetime.datetime | None = None) -> None:
    await db_manager.execute(
        "INSERT INTO ai_history (user_id, role, message, timestamp) VALUES ($1, $2, $3, $4)",
        user_id, role, message, timestamp or datetime.datetime.now(datetime.timezone.utc)
    )

async def get_history(user_id: int, limit: int = 12, ttl_days: int | None = None) -> list[dict[str, str]]:
    cutoff = None
    if ttl_days is not None:
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=ttl_days)

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

async def cleanup_history(user_id: int, keep_limit: int, ttl_days: int) -> None:
    await db_manager.execute("DELETE FROM ai_history WHERE user_id = $1 AND timestamp < $2", user_id, datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=ttl_days))

async def check_rate_limit(user_id: int, limit_per_hour: int) -> bool:
    now = datetime.datetime.now(datetime.timezone.utc)
    row = await db_manager.fetchrow(
        "SELECT count, window_start FROM ai_ratelimits WHERE user_id = $1",
        user_id
    )

    if not row or (now - row["window_start"]).total_seconds() > 3600:
        await db_manager.execute(
            """
            INSERT INTO ai_ratelimits (user_id, count, window_start) VALUES ($1, $2, $3)
            ON DUPLICATE KEY UPDATE count = VALUES(count), window_start = VALUES(window_start)
            """,
            user_id, 1, now
        )
        return True

    if int(row["count"]) < int(limit_per_hour):
        await db_manager.execute(
            "UPDATE ai_ratelimits SET count = count + 1 WHERE user_id = $1",
            user_id
        )
        return True

    return False
