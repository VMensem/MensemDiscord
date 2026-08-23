import os
import asyncpg
import logging
import aiosqlite
import re
import aiomysql

class DatabaseManager:
    def __init__(self):
        self.pool = None
        self.conn = None # For SQLite
        self.mysql_pool = None
        self.db_type = os.getenv("DATABASE", "local").lower()
        self.db_path = os.getenv("SQLITE_PATH", "mensembot.db")
        
    async def connect(self):
        if self.db_type == "local":
            logging.info("Database mode: LOCAL (SQLite)")
            self.conn = await aiosqlite.connect(self.db_path)
            self.conn.row_factory = aiosqlite.Row
            await self.initialize_schema()
            logging.info(f"Connected to local database: {self.db_path}")
            
        elif self.db_type == "postgres":
            logging.info("Database mode: POSTGRESQL")
            self.pool = await asyncpg.create_pool(
                dsn=os.getenv("DATABASE_URL"),
                ssl='require',
                min_size=5,
                max_size=20
            )
            logging.info("Connected to PostgreSQL")
            await self.initialize_schema()
            
        elif self.db_type == "mysql":
            logging.info("Database mode: MYSQL")
            self.mysql_pool = await aiomysql.create_pool(
                host=os.getenv("MYSQL_HOST"),
                port=int(os.getenv("MYSQL_PORT", 3306)),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                db=os.getenv("MYSQL_DATABASE"),
                autocommit=True
            )
            logging.info("Connected to MySQL")
            await self.initialize_schema()
        else:
            raise ValueError(f"Unsupported DATABASE backend: {self.db_type}")

    def _translate_query(self, query):
        if self.db_type == "local":
            return re.sub(r'\$\d+', '?', query)
        elif self.db_type == "mysql":
            return re.sub(r'\$\d+', '%s', query)
        return query

    async def initialize_schema(self):
        schema_file = f"core/schema_{self.db_type}.sql"
        if not os.path.exists(schema_file):
            # Fallback for now, but we should create them
            logging.warning(f"Schema file {schema_file} not found, trying core/schema.sql")
            schema_file = "core/schema.sql"
            
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = f.read()
        
        if self.db_type == "local":
            await self.conn.executescript(schema)
        elif self.db_type == "postgres":
            async with self.pool.acquire() as conn:
                await conn.execute(schema)
        elif self.db_type == "mysql":
            async with self.mysql_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(schema)
        logging.info("Database schema initialized")

    async def close(self):
        if self.db_type == "local":
            await self.conn.close()
        elif self.db_type == "postgres":
            await self.pool.close()
        elif self.db_type == "mysql":
            self.mysql_pool.close()
            await self.mysql_pool.wait_closed()
        logging.info("Closed database connection")

    async def execute(self, query, *args):
        query = self._translate_query(query)
        if self.db_type == "local":
            return await self.conn.execute(query, args)
        elif self.db_type == "postgres":
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)
        elif self.db_type == "mysql":
            async with self.mysql_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    return await cur.execute(query, args)

    async def fetch(self, query, *args):
        query = self._translate_query(query)
        if self.db_type == "local":
            cursor = await self.conn.execute(query, args)
            return await cursor.fetchall()
        elif self.db_type == "postgres":
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *args)
        elif self.db_type == "mysql":
            async with self.mysql_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(query, args)
                    return await cur.fetchall()

    async def fetchrow(self, query, *args):
        query = self._translate_query(query)
        if self.db_type == "local":
            cursor = await self.conn.execute(query, args)
            return await cursor.fetchone()
        elif self.db_type == "postgres":
            async with self.pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
        elif self.db_type == "mysql":
            async with self.mysql_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(query, args)
                    return await cur.fetchone()

    async def acquire_connection(self):
        if self.db_type == "postgres":
            return await self.pool.acquire()
        elif self.db_type == "mysql":
            return await self.mysql_pool.acquire()
        raise NotImplementedError("Connection acquisition not supported for this backend")

    async def release_connection(self, conn):
        if self.db_type == "postgres":
            await self.pool.release(conn)
        elif self.db_type == "mysql":
            self.mysql_pool.release(conn)

    # Context manager for transactions
    class TransactionContext:
        def __init__(self, manager):
            self.manager = manager
            self.conn = None
            self.transaction = None

        async def __aenter__(self):
            if self.manager.db_type == "local":
                self.conn = self.manager.conn
                await self.conn.execute("BEGIN")
            elif self.manager.db_type == "postgres":
                self.conn = await self.manager.pool.acquire()
                self.transaction = self.conn.transaction()
                await self.transaction.start()
            elif self.manager.db_type == "mysql":
                self.conn = await self.manager.mysql_pool.acquire()
                await self.conn.begin()
            return self.conn

        async def __aexit__(self, exc_type, exc, tb):
            if self.manager.db_type == "local":
                if exc:
                    await self.conn.execute("ROLLBACK")
                else:
                    await self.conn.execute("COMMIT")
            elif self.manager.db_type == "postgres":
                if exc:
                    await self.transaction.rollback()
                else:
                    await self.transaction.commit()
                await self.manager.pool.release(self.conn)
            elif self.manager.db_type == "mysql":
                if exc:
                    await self.conn.rollback()
                else:
                    await self.conn.commit()
                await self.manager.mysql_pool.release(self.conn)

    def transaction(self):
        return self.TransactionContext(self)

    async def get_guild_settings(self, guild_id):
        query = "SELECT * FROM guild_settings WHERE guild_id = $1"
        return await self.fetchrow(query, guild_id)

db_manager = DatabaseManager()
