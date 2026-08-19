import asyncpg
from core.database import db_manager
import json

class AntiNukeDatabase:
    async def get_settings(self, guild_id):
        query = "SELECT * FROM antinuke_settings WHERE guild_id = $1"
        return await db_manager.fetchrow(query, guild_id)

    async def update_settings(self, guild_id, **kwargs):
        if not kwargs:
            return
        fields = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
        values = list(kwargs.values())
        query = f"UPDATE antinuke_settings SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE guild_id = $1"
        await db_manager.execute(query, guild_id, *values)

    async def create_settings(self, guild_id):
        query = "INSERT INTO antinuke_settings (guild_id) VALUES ($1) ON CONFLICT DO NOTHING"
        await db_manager.execute(query, guild_id)

    async def get_limit(self, guild_id, action_type):
        query = "SELECT * FROM antinuke_limits WHERE guild_id = $1 AND action_type = $2"
        return await db_manager.fetchrow(query, guild_id, action_type)

    async def get_all_limits(self, guild_id):
        query = "SELECT * FROM antinuke_limits WHERE guild_id = $1"
        return await db_manager.fetch(query, guild_id)

    async def set_limit(self, guild_id, action_type, max_actions, window_seconds, severity):
        query = """
        INSERT INTO antinuke_limits (guild_id, action_type, max_actions, window_seconds, severity)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (guild_id, action_type) DO UPDATE SET
        max_actions = $3, window_seconds = $4, severity = $5
        """
        await db_manager.execute(query, guild_id, action_type, max_actions, window_seconds, severity)

    async def is_whitelisted(self, guild_id, user_id):
        query = "SELECT 1 FROM antinuke_whitelist WHERE guild_id = $1 AND user_id = $2"
        return await db_manager.fetchrow(query, guild_id, user_id) is not None

    async def is_trusted(self, guild_id, user_id):
        query = "SELECT 1 FROM antinuke_trusted WHERE guild_id = $1 AND user_id = $2"
        return await db_manager.fetchrow(query, guild_id, user_id) is not None

    async def add_incident(self, guild_id, user_id, action_type, severity, count, data, action_taken, rollback_status):
        query = """
        INSERT INTO antinuke_incidents (guild_id, user_id, action_type, severity, action_count, action_data, action_taken, rollback_status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id
        """
        return await db_manager.fetchrow(query, guild_id, user_id, action_type, severity, count, data, action_taken, rollback_status)

    async def save_snapshot(self, guild_id, object_type, object_id, snapshot_data, incident_id):
        query = """
        INSERT INTO antinuke_snapshots (guild_id, object_type, object_id, snapshot_data, incident_id)
        VALUES ($1, $2, $3, $4, $5)
        """
        await db_manager.execute(query, guild_id, object_type, object_id, json.dumps(snapshot_data), incident_id)
