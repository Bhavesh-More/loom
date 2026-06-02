import os
import asyncpg

from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            dsn=os.getenv("DATABASE_URL"),
            min_size=5,
            max_size=20
        )

    async def disconnect(self):
        await self.pool.close()

    async def get_conn(self):
        return await self.pool.acquire()

    async def release_conn(self, conn):
        await self.pool.release(conn)


database = Database()