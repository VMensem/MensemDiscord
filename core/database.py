import os
import asyncpg
import logging

class DatabaseManager:
    def __init__(self):
        self.pool = None

    async def connect(self):
        raw_url = os.getenv("DATABASE_URL")
        url = "".join(raw_url.split()) if raw_url else None
        logging.info(f"Connecting to database with URL: {url}")
        self.pool = await asyncpg.create_pool(
            dsn=url,
            min_size=5,
            max_size=20
        )
        logging.info("Connected to PostgreSQL")
        await self.initialize_schema()

    async def initialize_schema(self):
        with open("core/schema.sql", "r", encoding="utf-8") as f:
            schema = f.read()
        async with self.pool.acquire() as conn:
            await conn.execute(schema)
        logging.info("Database schema initialized")

    async def close(self):
        await self.pool.close()
        logging.info("Closed PostgreSQL connection")

    async def execute(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

db_manager = DatabaseManager()
