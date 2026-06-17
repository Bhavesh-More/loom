import os
from pathlib import Path
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
        await self._bootstrap_orchestration_schema()

    async def disconnect(self):
        if self.pool is not None:
            await self.pool.close()

    async def get_conn(self):
        if self.pool is None:
            raise RuntimeError("Database pool is not connected")
        return await self.pool.acquire()

    async def release_conn(self, conn):
        if self.pool is not None:
            await self.pool.release(conn)

    async def _bootstrap_orchestration_schema(self):
        migration = Path(__file__).resolve().parents[1] / "migrations" / "20260617_confidence_scoring.sql"
        if not migration.exists():
            return
        sql = migration.read_text(encoding="utf-8")
        statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
        conn = await self.get_conn()
        try:
            for statement in statements:
                await conn.execute(statement)
        finally:
            await self.release_conn(conn)


database = Database()
