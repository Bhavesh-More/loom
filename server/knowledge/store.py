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
                "SELECT id, content, version, timestamp, source_agent, priority, tags, embedding FROM shared_knowledge WHERE id = $1",
                entry_id
            )
            if row:
                data = dict(row)
                if data.get("embedding") is not None:
                    from context_system.db import _parse_vector
                    data["embedding"] = _parse_vector(data["embedding"])
                return KnowledgeEntry(**data)
            return None
        finally:
            await self.db.release_conn(conn)

    async def get_all_entries(self) -> List[KnowledgeEntry]:
        if not self.has_pool:
            return []
        conn = await self.db.get_conn()
        try:
            rows = await conn.fetch(
                "SELECT id, content, version, timestamp, source_agent, priority, tags, embedding FROM shared_knowledge"
            )
            results = []
            for row in rows:
                data = dict(row)
                if data.get("embedding") is not None:
                    from context_system.db import _parse_vector
                    data["embedding"] = _parse_vector(data["embedding"])
                results.append(KnowledgeEntry(**data))
            return results
        finally:
            await self.db.release_conn(conn)

    async def get_entries_by_tag(self, tag: str) -> List[KnowledgeEntry]:
        if not self.has_pool:
            return []
        conn = await self.db.get_conn()
        try:
            rows = await conn.fetch(
                "SELECT id, content, version, timestamp, source_agent, priority, tags, embedding FROM shared_knowledge WHERE $1 = ANY(tags)",
                tag
            )
            results = []
            for row in rows:
                data = dict(row)
                if data.get("embedding") is not None:
                    from context_system.db import _parse_vector
                    data["embedding"] = _parse_vector(data["embedding"])
                results.append(KnowledgeEntry(**data))
            return results
        finally:
            await self.db.release_conn(conn)

    async def save_entry(self, entry: KnowledgeEntry) -> None:
        if not self.has_pool:
            return
        
        embedding_literal = None
        if entry.embedding is not None:
            from knowledge.memory_service import _vector_literal
            embedding_literal = _vector_literal(entry.embedding)

        conn = await self.db.get_conn()
        try:
            await conn.execute(
                """
                INSERT INTO shared_knowledge (id, content, version, timestamp, source_agent, priority, tags, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8::vector)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    version = EXCLUDED.version,
                    timestamp = EXCLUDED.timestamp,
                    source_agent = EXCLUDED.source_agent,
                    priority = EXCLUDED.priority,
                    tags = EXCLUDED.tags,
                    embedding = EXCLUDED.embedding
                """,
                entry.id,
                entry.content,
                entry.version,
                entry.timestamp,
                entry.source_agent,
                entry.priority,
                entry.tags,
                embedding_literal
            )
        finally:
            await self.db.release_conn(conn)

