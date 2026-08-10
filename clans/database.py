from core.database import db_manager
from typing import Optional, List, Dict, Any

async def init_db():
    pass

async def create_clan(guild_id: int, name: str, tag: str, description: str, leader_id: int) -> int:
    row = await db_manager.fetchrow(
        """
        INSERT INTO clans (guild_id, name, tag, description, leader_id)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING clan_id
        """,
        guild_id, name, tag, description, leader_id
    )
    return row["clan_id"] if row else 0

async def add_clan_member(clan_id: int, user_id: int):
    await db_manager.execute(
        "INSERT INTO clan_members (clan_id, user_id) VALUES ($1, $2)",
        clan_id, user_id
    )

async def remove_clan_member(clan_id: int, user_id: int):
    await db_manager.execute(
        "DELETE FROM clan_members WHERE clan_id = $1 AND user_id = $2",
        clan_id, user_id
    )

async def get_clan_members(clan_id: int) -> List[int]:
    rows = await db_manager.fetch("SELECT user_id FROM clan_members WHERE clan_id = $1", clan_id)
    return [row["user_id"] for row in rows]

async def get_clan_by_id(clan_id: int) -> Optional[Dict[str, Any]]:
    row = await db_manager.fetchrow("SELECT * FROM clans WHERE clan_id = $1", clan_id)
    return dict(row) if row else None

async def get_clans_by_guild(guild_id: int) -> List[Dict[str, Any]]:
    rows = await db_manager.fetch(
        """
        SELECT c.*, COUNT(cm.user_id) as member_count 
        FROM clans c 
        LEFT JOIN clan_members cm ON c.clan_id = cm.clan_id 
        WHERE c.guild_id = $1 
        GROUP BY c.clan_id
        ORDER BY c.level DESC, c.xp DESC
        """, 
        guild_id
    )
    return [dict(row) for row in rows]

async def update_clan_balance(clan_id: int, amount: int):
    await db_manager.execute(
        "UPDATE clans SET balance = balance + $1 WHERE clan_id = $2",
        amount, clan_id
    )

async def delete_clan(clan_id: int):
    await db_manager.execute("DELETE FROM clans WHERE clan_id = $1", clan_id)
