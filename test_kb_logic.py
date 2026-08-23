import asyncio
from ai_assistant.knowledge_base import upsert_knowledge, get_knowledge
from ai_assistant.database import clear_history
from core.database import db_manager

async def test_kb():
    # Setup
    await db_manager.connect()
    
    guild_id = 123
    guild_id_2 = 456
    user_id = 789
    fact = "Тестовый сервер Mensem был создан 17 августа 2026 года, владелец — TestOwner."
    
    print("--- Test 1: Saving ---")
    await upsert_knowledge(guild_id, fact)
    
    # Verify in DB
    row = await db_manager.fetchrow("SELECT * FROM ai_knowledge_base WHERE guild_id = ?", guild_id)
    print(f"Row found: {row}")
    assert row is not None
    assert row['content'] == fact
    
    print("--- Test 2: Clear and retrieve ---")
    await clear_history(user_id) # Clears conversation history
    
    kb_entries = await get_knowledge(guild_id, "создан")
    print(f"KB entries found: {kb_entries}")
    assert len(kb_entries) == 1
    
    print("--- Test 3: Guild Isolation ---")
    kb_entries_2 = await get_knowledge(guild_id_2, "создан")
    print(f"KB entries for guild 456: {kb_entries_2}")
    assert len(kb_entries_2) == 0
    
    print("--- Test 4: Duplicates ---")
    success = await upsert_knowledge(guild_id, fact)
    print(f"Duplicate add success: {success}")
    assert success is False
    
    await db_manager.close()
    print("All tests passed!")

asyncio.run(test_kb())
