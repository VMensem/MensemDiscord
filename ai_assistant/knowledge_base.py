from core.database import db_manager

async def add_knowledge(guild_id: int, category: str, title: str, content: str):
    query = """
    INSERT INTO ai_knowledge_base (guild_id, category, title, content)
    VALUES ($1, $2, $3, $4)
    """
    await db_manager.execute(query, guild_id, category, title, content)

async def get_knowledge(guild_id: int, query_text: str = None):
    if query_text:
        # Simple search - could be improved with tsvector
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
