from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from db.database import database

from context_system.models import ContextMemory, FileMatch, ImportEdge, SymbolEntry

logger = logging.getLogger(__name__)


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def _parse_vector(value: Any) -> list[float] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [float(item) for item in value]
    if isinstance(value, str):
        return [float(item) for item in value.strip("[]").split(",") if item]
    return list(value)


class ContextDatabase:
    """Async Postgres/pgvector access for the context system."""

    def __init__(self, db=database):
        self.db = db
        self.cache_hits = 0
        self.cache_misses = 0

    @property
    def has_pool(self) -> bool:
        return bool(getattr(self.db, "pool", None))

    async def _fetch(self, query: str, *args):
        if not self.has_pool:
            return []
        conn = await self.db.get_conn()
        try:
            return await conn.fetch(query, *args)
        finally:
            await self.db.release_conn(conn)

    async def _fetchrow(self, query: str, *args):
        if not self.has_pool:
            return None
        conn = await self.db.get_conn()
        try:
            return await conn.fetchrow(query, *args)
        finally:
            await self.db.release_conn(conn)

    async def _execute(self, query: str, *args) -> None:
        if not self.has_pool:
            return
        conn = await self.db.get_conn()
        try:
            await conn.execute(query, *args)
        finally:
            await self.db.release_conn(conn)

    async def persist_grep_hits(
        self,
        repo_path: str,
        task_id: str,
        prompt: str,
        matches: list[FileMatch],
        concepts: list[str],
    ) -> None:
        if not matches:
            return
        if not self.has_pool:
            return
        conn = await self.db.get_conn()
        try:
            async with conn.transaction():
                for match in matches:
                    await conn.execute(
                        """
                        INSERT INTO grep_hits (
                            repo_path, task_id, prompt, file_path, score,
                            line_numbers, snippets, matched_terms, concepts
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (repo_path, task_id, file_path)
                        DO UPDATE SET
                            score = EXCLUDED.score,
                            line_numbers = EXCLUDED.line_numbers,
                            snippets = EXCLUDED.snippets,
                            matched_terms = EXCLUDED.matched_terms,
                            concepts = EXCLUDED.concepts,
                            updated_at = NOW()
                        """,
                        repo_path,
                        task_id,
                        prompt,
                        match.path,
                        match.score,
                        match.line_numbers,
                        match.snippets,
                        match.matched_terms,
                        concepts,
                    )
        finally:
            await self.db.release_conn(conn)

    async def upsert_symbols(self, symbols: list[SymbolEntry]) -> None:
        if not symbols or not self.has_pool:
            return
        conn = await self.db.get_conn()
        try:
            async with conn.transaction():
                for symbol in symbols:
                    await conn.execute(
                        """
                        INSERT INTO symbol_index (
                            name, kind, file_path, repo_path, signature, description
                        )
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (name, file_path, repo_path)
                        DO UPDATE SET
                            kind = EXCLUDED.kind,
                            signature = EXCLUDED.signature,
                            description = EXCLUDED.description,
                            last_verified = NOW()
                        """,
                        symbol.name,
                        symbol.kind,
                        symbol.file_path,
                        symbol.repo_path,
                        symbol.signature,
                        symbol.description,
                    )
        finally:
            await self.db.release_conn(conn)

    async def upsert_edges(self, edges: list[ImportEdge]) -> None:
        if not edges or not self.has_pool:
            return
        conn = await self.db.get_conn()
        try:
            async with conn.transaction():
                for edge in edges:
                    await conn.execute(
                        """
                        INSERT INTO import_graph_edges (
                            repo_path, from_file, to_file, edge_type, verified
                        )
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (repo_path, from_file, to_file)
                        DO UPDATE SET
                            edge_type = EXCLUDED.edge_type,
                            verified = EXCLUDED.verified
                        """,
                        edge.repo_path,
                        edge.from_file,
                        edge.to_file,
                        edge.edge_type,
                        edge.verified,
                    )
        finally:
            await self.db.release_conn(conn)

    async def replace_edges_for_file(self, repo_path: str, from_file: str, edges: list[ImportEdge]) -> None:
        if not self.has_pool:
            return
        conn = await self.db.get_conn()
        try:
            async with conn.transaction():
                await conn.execute(
                    "DELETE FROM import_graph_edges WHERE repo_path = $1 AND from_file = $2",
                    repo_path,
                    from_file,
                )
                for edge in edges:
                    await conn.execute(
                        """
                        INSERT INTO import_graph_edges (
                            repo_path, from_file, to_file, edge_type, verified
                        )
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (repo_path, from_file, to_file)
                        DO UPDATE SET edge_type = EXCLUDED.edge_type, verified = EXCLUDED.verified
                        """,
                        edge.repo_path,
                        edge.from_file,
                        edge.to_file,
                        edge.edge_type,
                        edge.verified,
                    )
        finally:
            await self.db.release_conn(conn)

    async def get_edges(self, repo_path: str) -> list[ImportEdge]:
        rows = await self._fetch(
            """
            SELECT repo_path, from_file, to_file, edge_type, verified
            FROM import_graph_edges
            WHERE repo_path = $1
            """,
            repo_path,
        )
        return [ImportEdge(**dict(row)) for row in rows]

    async def get_edges_for_file(self, repo_path: str, file_path: str) -> list[ImportEdge]:
        rows = await self._fetch(
            """
            SELECT repo_path, from_file, to_file, edge_type, verified
            FROM import_graph_edges
            WHERE repo_path = $1 AND (from_file = $2 OR to_file = $2)
            """,
            repo_path,
            file_path,
        )
        return [ImportEdge(**dict(row)) for row in rows]

    async def get_symbols_for_file(self, repo_path: str, file_path: str) -> list[SymbolEntry]:
        rows = await self._fetch(
            """
            SELECT name, kind, file_path, repo_path, signature, description
            FROM symbol_index
            WHERE repo_path = $1 AND file_path = $2
            """,
            repo_path,
            file_path,
        )
        return [SymbolEntry(**dict(row)) for row in rows]

    async def get_cached_embedding(self, content_hash: str) -> list[float] | None:
        row = await self._fetchrow(
            "SELECT embedding FROM embedding_cache WHERE content_hash = $1 AND valid_until IS NULL",
            content_hash,
        )
        if row:
            self.cache_hits += 1
            return _parse_vector(row["embedding"])
        self.cache_misses += 1
        return None

    async def upsert_embedding(
        self,
        content_hash: str,
        file_path: str,
        chunk_index: int,
        embedding: list[float],
        active_task_refs: list[str] | None = None,
    ) -> None:
        await self._execute(
            """
            INSERT INTO embedding_cache (
                content_hash, file_path, chunk_index, embedding, active_task_refs
            )
            VALUES ($1, $2, $3, $4::vector, $5)
            ON CONFLICT (content_hash)
            DO UPDATE SET
                file_path = EXCLUDED.file_path,
                chunk_index = EXCLUDED.chunk_index,
                embedding = EXCLUDED.embedding,
                updated_at = NOW()
            """,
            content_hash,
            file_path,
            chunk_index,
            _vector_literal(embedding),
            active_task_refs or [],
        )

    async def write_knowledge_version(
        self,
        repo_path: str,
        file_path: str,
        content_hash: str,
        task_id: str | None = None,
    ) -> int:
        if not self.has_pool:
            return 1
        row = await self._fetchrow(
            """
            SELECT COALESCE(MAX(version), 0) + 1 AS next_version
            FROM knowledge_versions
            WHERE repo_path = $1 AND file_path = $2
            """,
            repo_path,
            file_path,
        )
        version = int(row["next_version"] if row else 1)
        await self._execute(
            """
            UPDATE knowledge_versions
            SET is_current = FALSE, valid_until = NOW()
            WHERE repo_path = $1 AND file_path = $2 AND is_current = TRUE
            """,
            repo_path,
            file_path,
        )
        await self._execute(
            """
            INSERT INTO knowledge_versions (
                repo_path, file_path, version, content_hash, active_task_refs
            )
            VALUES ($1, $2, $3, $4, $5)
            """,
            repo_path,
            file_path,
            version,
            content_hash,
            [task_id] if task_id else [],
        )
        return version

    async def mark_files_stale(self, repo_path: str, file_paths: list[str]) -> None:
        if not file_paths:
            return
        await self._execute(
            """
            UPDATE knowledge_versions
            SET is_current = FALSE, valid_until = NOW()
            WHERE repo_path = $1 AND file_path = ANY($2::text[]) AND is_current = TRUE
            """,
            repo_path,
            file_paths,
        )

    async def upsert_domain_summary(
        self,
        repo_path: str,
        domain_name: str,
        summary: str,
        central_files: list[str],
    ) -> None:
        await self._execute(
            """
            INSERT INTO domain_summaries (repo_path, domain_name, summary, central_files)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (repo_path, domain_name)
            DO UPDATE SET
                summary = EXCLUDED.summary,
                central_files = EXCLUDED.central_files,
                created_at = NOW()
            """,
            repo_path,
            domain_name,
            summary,
            central_files,
        )

    async def get_context_memories(
        self,
        repo_path: str,
        terms: list[str],
        domain: str | None = None,
        limit: int = 5,
    ) -> list[ContextMemory]:
        if not self.has_pool:
            return []
        rows = await self._fetch(
            """
            SELECT repo_path, task_signature, prompt, domain, files, summary, confidence
            FROM context_memories
            WHERE repo_path = $1
              AND ($2::text IS NULL OR domain = $2)
            ORDER BY
              (
                SELECT COUNT(*)
                FROM unnest($3::text[]) term
                WHERE prompt ILIKE '%' || term || '%'
                   OR summary ILIKE '%' || term || '%'
                   OR EXISTS (
                     SELECT 1 FROM unnest(files) file WHERE file ILIKE '%' || term || '%'
                   )
              ) DESC,
              confidence DESC,
              updated_at DESC
            LIMIT $4
            """,
            repo_path,
            domain,
            terms,
            limit,
        )
        return [ContextMemory(**dict(row)) for row in rows]

    async def upsert_context_memory(self, memory: ContextMemory) -> None:
        await self._execute(
            """
            INSERT INTO context_memories (
                repo_path, task_signature, prompt, domain, files, summary, confidence
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (repo_path, task_signature)
            DO UPDATE SET
                prompt = EXCLUDED.prompt,
                domain = EXCLUDED.domain,
                files = EXCLUDED.files,
                summary = EXCLUDED.summary,
                confidence = GREATEST(context_memories.confidence, EXCLUDED.confidence),
                updated_at = NOW()
            """,
            memory.repo_path,
            memory.task_signature,
            memory.prompt,
            memory.domain,
            memory.files,
            memory.summary,
            memory.confidence,
        )

    async def status(self, repo_path: str, file_count: int) -> dict[str, Any]:
        symbol_rows = await self._fetch(
            "SELECT COUNT(DISTINCT file_path) AS count FROM symbol_index WHERE repo_path = $1",
            repo_path,
        )
        cache_rows = await self._fetch(
            "SELECT COUNT(*) AS count FROM embedding_cache WHERE file_path LIKE $1",
            f"{repo_path}%",
        )
        edge_rows = await self._fetch(
            "SELECT COUNT(*) AS count FROM import_graph_edges WHERE repo_path = $1",
            repo_path,
        )
        memory_rows = await self._fetch(
            "SELECT COUNT(*) AS count FROM context_memories WHERE repo_path = $1",
            repo_path,
        )
        indexed = int(symbol_rows[0]["count"]) if symbol_rows else 0
        cache_entries = int(cache_rows[0]["count"]) if cache_rows else 0
        edge_count = int(edge_rows[0]["count"]) if edge_rows else 0
        memory_count = int(memory_rows[0]["count"]) if memory_rows else 0
        total_cache = self.cache_hits + self.cache_misses
        return {
            "indexed_file_count": indexed,
            "cache_entries": cache_entries,
            "graph_edge_count": edge_count,
            "memory_count": memory_count,
            "cache_hit_rate": self.cache_hits / total_cache if total_cache else 0.0,
            "index_coverage": indexed / file_count if file_count else 0.0,
        }

    async def log_metric(self, name: str, value: float, labels: dict[str, Any] | None = None) -> None:
        logger.info(
            "context_metric",
            extra={"metric": name, "value": value, "labels": json.dumps(labels or {}), "time": datetime.utcnow().isoformat()},
        )


context_db = ContextDatabase()
