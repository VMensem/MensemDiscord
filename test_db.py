import asyncio
import os
from dotenv import load_dotenv
from core.database import db_manager

async def test_connection():
    load_dotenv()
    if not os.getenv("DATABASE_URL"):
        print("DATABASE_URL not set")
        return
    
    try:
        await db_manager.connect()
        print("Connection successful")
        await db_manager.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
