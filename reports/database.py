from core.database import db_manager

async def create_report(guild_id, author_id, channel_id, reason, description, target_id=None):
    row = await db_manager.fetchrow(
        """
        INSERT INTO reports (guild_id, author_id, target_id, channel_id, reason, description)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING report_id
        """,
        guild_id, author_id, target_id, channel_id, reason, description
    )
    report_id = row["report_id"]
    await db_manager.execute(
        "INSERT INTO report_history (report_id, action, actor_id) VALUES ($1, 'created', $2)",
        report_id, author_id
    )
    return report_id
