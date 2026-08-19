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
        # SQLite compatible case-insensitive search
        # 'ILIKE' is PostgreSQL specific.
        if db_manager.db_type == 'local':
            # The query has 3 placeholders ($1, $2, $3)
            # We need to provide 3 arguments: guild_id, pattern, pattern
            query = """
            SELECT * FROM ai_knowledge_base 
            WHERE guild_id = $1 AND (title LIKE $2 COLLATE NOCASE OR content LIKE $3 COLLATE NOCASE)
            """
            return await db_manager.fetch(query, guild_id, f"%{query_text}%", f"%{query_text}%")
        else:
            query = """
            SELECT * FROM ai_knowledge_base 
            WHERE guild_id = $1 AND (title ILIKE $2 OR content ILIKE $2)
            """
            return await db_manager.fetch(query, guild_id, f"%{query_text}%")
    else:
        query = "SELECT * FROM ai_knowledge_base WHERE guild_id = $1"
        return await db_manager.fetch(query, guild_id)

async def delete_knowledge(kb_id: int):
    query = "DELETE FROM ai_knowledge_base WHERE kb_id = $1"
    await db_manager.execute(query, kb_id)
