from core.database import db_manager

async def add_knowledge(guild_id: int, category: str, title: str, content: str):
    query = """
    INSERT INTO ai_knowledge_base (guild_id, category, title, content)
    VALUES ($1, $2, $3, $4)
    """
    await db_manager.execute(query, guild_id, category, title, content)

async def upsert_knowledge(guild_id: int, content: str):
    # Check if duplicate exists
    query_check = "SELECT 1 FROM ai_knowledge_base WHERE guild_id = $1 AND content = $2"
    exists = await db_manager.fetchrow(query_check, guild_id, content)
    if exists:
        return False
    
    title = (content[:47] + '...') if len(content) > 50 else content
    await add_knowledge(guild_id, "Fact", title, content)
    return True

async def get_knowledge(guild_id: int, query_text: str = None):
    if query_text:
        # MySQL is case-insensitive by default for text comparisons.
        # Use simple LIKE with proper parameter binding.
        # We use $1, $2, $3 to ensure each placeholder maps to one argument.
        query = """
        SELECT * FROM ai_knowledge_base 
        WHERE guild_id = $1 AND (title LIKE $2 OR content LIKE $3)
        """
        # The DatabaseManager will translate $1, $2, $3 to %s, %s, %s for MySQL.
        pattern = f"%{query_text}%"
        return await db_manager.fetch(query, guild_id, pattern, pattern)
    else:
        query = "SELECT * FROM ai_knowledge_base WHERE guild_id = $1"
        return await db_manager.fetch(query, guild_id)

async def delete_knowledge(kb_id: int):
    query = "DELETE FROM ai_knowledge_base WHERE kb_id = $1"
    await db_manager.execute(query, kb_id)
