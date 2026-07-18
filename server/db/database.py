import os
from pathlib import Path
import asyncpg

from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        print("DATABASE_URL:", repr(os.getenv("DATABASE_URL")))
        if self.pool is not None:
            return
        self.pool = await asyncpg.create_pool(
            dsn=os.getenv("DATABASE_URL"),
            min_size=5,
            max_size=20
        )
        await self._bootstrap_orchestration_schema()

    async def disconnect(self):
        if self.pool is not None:
            await self.pool.close()
            self.pool = None


    async def get_conn(self):
        if self.pool is None:
            raise RuntimeError("Database pool is not connected")
        return await self.pool.acquire()

    async def release_conn(self, conn):
        if self.pool is not None:
            await self.pool.release(conn)

    async def _bootstrap_orchestration_schema(self):
        migrations_dir = Path(__file__).resolve().parents[1] / "migrations"
        if not migrations_dir.exists():
            return
        conn = await self.get_conn()
        try:
            for migration in sorted(migrations_dir.glob("*.sql")):
                sql = migration.read_text(encoding="utf-8")
                statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
                for statement in statements:
                    await conn.execute(statement)
        finally:
            await self.release_conn(conn)



database = Database()
