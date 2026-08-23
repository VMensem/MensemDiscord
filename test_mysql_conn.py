import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env before imports
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

from core.database import db_manager

async def test_mysql():
    print("Testing MySQL Live Connection...")
    try:
        await db_manager.connect()
        print("Connected to MySQL successfully!")
        
        # Test schema initialization
        print("Initializing schema on MySQL...")
        await db_manager.initialize_schema()
        print("Schema initialized successfully!")
        
        # Test basic query
        print("Testing SELECT 1...")
        row = await db_manager.fetchrow("SELECT 1")
        print(f"Query test success: {row}")
        
        # Test Knowledge Base Tables
        print("Testing Knowledge Base tables on MySQL...")
        await db_manager.execute("INSERT INTO ai_knowledge_base (guild_id, category, title, content) VALUES ($1, $2, $3, $4)", 
                                 123456, "Test", "MyTitle", "MySQL works flawlessly!")
        
        test_row = await db_manager.fetchrow("SELECT content FROM ai_knowledge_base WHERE guild_id = $1", 123456)
        print(f"Retrieved content: {test_row}")
        
        # Cleanup test row
        await db_manager.execute("DELETE FROM ai_knowledge_base WHERE guild_id = $1", 123456)
        print("Cleanup done!")
        
    except Exception as e:
        print(f"Connection/Query Failed: {type(e).__name__}")
        # Clean exception messaging to avoid printing password if it leaks in str(e)
        err_msg = str(e)
        if "password" in err_msg.lower():
            print("Error details hidden to protect password.")
        else:
            print(f"Details: {err_msg[:200]}")
    finally:
        await db_manager.close()
        print("Connection closed.")

asyncio.run(test_mysql())
