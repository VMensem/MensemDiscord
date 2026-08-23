from .database import (
    get_relationship, create_proposal, get_pending_proposal, get_pending_proposal_by_id, 
    accept_proposal, reject_proposal, delete_relationship, get_love_room, add_love_room, delete_love_room
)
import datetime

async def is_user_in_relationship(guild_id: int, user_id: int) -> dict | None:
    return await get_relationship(guild_id, user_id)

async def propose(guild_id: int, from_user_id: int, to_user_id: int):
    if await is_user_in_relationship(guild_id, from_user_id) or await is_user_in_relationship(guild_id, to_user_id):
        raise ValueError("Один из пользователей уже состоит в отношениях.")
    
    if await get_pending_proposal(guild_id, from_user_id, to_user_id):
        raise ValueError("Предложение уже отправлено.")

    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    await create_proposal(guild_id, from_user_id, to_user_id, expires_at)

async def accept(proposal_id: int, guild_id: int):
    proposal = await get_pending_proposal_by_id(proposal_id)
    if not proposal:
        raise ValueError("Предложение не найдено или истекло.")
    
    if await is_user_in_relationship(guild_id, proposal['from_user_id']) or await is_user_in_relationship(guild_id, proposal['to_user_id']):
        raise ValueError("Один из пользователей уже состоит в отношениях.")

    await accept_proposal(proposal_id, guild_id, proposal['from_user_id'], proposal['to_user_id'])

async def divorce(relationship_id: int):
    await delete_relationship(relationship_id)
