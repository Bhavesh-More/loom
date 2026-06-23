from typing import List, Optional
from db.database import database
from knowledge.schema import KnowledgeEntry

class KnowledgeStore:
    def __init__(self, db=database):
        self.db = db

    @property
    def has_pool(self) -> bool:
        return bool(getattr(self.db, "pool", None))

    async def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        if not self.has_pool:
            return None
        conn = await self.db.get_conn()
        try:
            row = await conn.fetchrow(
                "SELECT id, content, version, timestamp, source_agent, priority, tags FROM shared_knowledge WHERE id = $1",
                entry_id
            )
            if row:
                return KnowledgeEntry(**dict(row))
            return None
        finally:
            await self.db.release_conn(conn)

    async def get_all_entries(self) -> List[KnowledgeEntry]:
        if not self.has_pool:
            return []
        conn = await self.db.get_conn()
        try:
            rows = await conn.fetch(
                "SELECT id, content, version, timestamp, source_agent, priority, tags FROM shared_knowledge"
            )
            return [KnowledgeEntry(**dict(row)) for row in rows]
        finally:
            await self.db.release_conn(conn)

    async def get_entries_by_tag(self, tag: str) -> List[KnowledgeEntry]:
        if not self.has_pool:
            return []
        conn = await self.db.get_conn()
        try:
            rows = await conn.fetch(
                "SELECT id, content, version, timestamp, source_agent, priority, tags FROM shared_knowledge WHERE $1 = ANY(tags)",
                tag
            )
            return [KnowledgeEntry(**dict(row)) for row in rows]
        finally:
            await self.db.release_conn(conn)

    async def save_entry(self, entry: KnowledgeEntry) -> None:
        if not self.has_pool:
            return
        conn = await self.db.get_conn()
        try:
            await conn.execute(
                """
                INSERT INTO shared_knowledge (id, content, version, timestamp, source_agent, priority, tags)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    version = EXCLUDED.version,
                    timestamp = EXCLUDED.timestamp,
                    source_agent = EXCLUDED.source_agent,
                    priority = EXCLUDED.priority,
                    tags = EXCLUDED.tags
                """,
                entry.id,
                entry.content,
                entry.version,
                entry.timestamp,
                entry.source_agent,
                entry.priority,
                entry.tags
            )
        finally:
            await self.db.release_conn(conn)
