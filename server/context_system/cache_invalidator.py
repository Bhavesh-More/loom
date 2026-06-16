from __future__ import annotations

import asyncio
import hashlib
import time
from pathlib import Path

from context_system.ast_parser import ASTParser
from context_system.db import ContextDatabase, context_db
from context_system.models import ASTDiff, ImportEdge, InvalidationEvent
from context_system.semantic_searcher import cosine_similarity, embedding_provider


class ASTDiffer:
    def __init__(self, db: ContextDatabase = context_db, parser: ASTParser | None = None):
        self.db = db
        self.parser = parser or ASTParser()

    async def diff_against_store(self, repo_path: str, file_path: str) -> ASTDiff:
        info = await self.parser.parse_file(repo_path, file_path)
        stored_symbols = await self.db.get_symbols_for_file(repo_path, info.file_path)
        stored_edges = await self.db.get_edges_for_file(repo_path, info.file_path)
        old_symbols = {symbol.name: symbol.signature or "" for symbol in stored_symbols}
        new_symbols = {symbol.name: symbol.signature or "" for symbol in info.symbols}
        current_imports = {edge.to_file for edge in stored_edges if edge.from_file == info.file_path}
        new_imports = set(info.imports)
        common = set(old_symbols) & set(new_symbols)
        return ASTDiff(
            file_path=info.file_path,
            added_symbols=sorted(set(new_symbols) - set(old_symbols)),
            removed_symbols=sorted(set(old_symbols) - set(new_symbols)),
            changed_signatures=sorted(name for name in common if old_symbols[name] != new_symbols[name]),
            added_imports=sorted(new_imports - current_imports),
            removed_imports=sorted(current_imports - new_imports),
        )


class CascadeInvalidator:
    def __init__(self, db: ContextDatabase = context_db):
        self.db = db

    async def consumers(self, repo_path: str, changed_file: str) -> list[str]:
        edges = await self.db.get_edges(repo_path)
        reverse: dict[str, list[str]] = {}
        for edge in edges:
            reverse.setdefault(edge.to_file, []).append(edge.from_file)
        stale: list[str] = []
        queue = [changed_file]
        seen = {changed_file}
        while queue:
            file_path = queue.pop(0)
            for consumer in reverse.get(file_path, []):
                if consumer not in seen:
                    seen.add(consumer)
                    stale.append(consumer)
                    queue.append(consumer)
        return stale


class SemanticDriftChecker:
    async def should_reembed(self, old_content: str, new_content: str, threshold: float = 0.15) -> bool:
        old_embedding, new_embedding = await asyncio.gather(
            embedding_provider.encode(old_content),
            embedding_provider.encode(new_content),
        )
        drift = 1 - cosine_similarity(old_embedding, new_embedding)
        return drift > threshold


class CascadeInvalidationService:
    def __init__(
        self,
        db: ContextDatabase = context_db,
        parser: ASTParser | None = None,
        differ: ASTDiffer | None = None,
    ):
        self.db = db
        self.parser = parser or ASTParser()
        self.differ = differ or ASTDiffer(db, self.parser)
        self.cascade = CascadeInvalidator(db)
        self.drift = SemanticDriftChecker()

    async def invalidate_file(self, repo_path: str, file_path: str, task_id: str | None = None) -> InvalidationEvent:
        started = time.perf_counter()
        path = Path(file_path).resolve()
        diff = await self.differ.diff_against_store(repo_path, str(path))
        info = await self.parser.parse_file(repo_path, str(path))
        await self.db.upsert_symbols(info.symbols)
        await self.db.replace_edges_for_file(repo_path, info.file_path, self.parser.to_edges(repo_path, info))

        stale_files = [info.file_path]
        if diff.has_interface_change:
            stale_files.extend(await self.cascade.consumers(repo_path, info.file_path))
        await self.db.mark_files_stale(repo_path, stale_files)

        content = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="ignore")
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        await self.db.write_knowledge_version(repo_path, info.file_path, content_hash, task_id)

        latency_ms = (time.perf_counter() - started) * 1000
        await self.db.log_metric("invalidation_latency_ms", latency_ms, {"repo_path": repo_path})
        return InvalidationEvent(
            repo_path=repo_path,
            file_path=info.file_path,
            stale_files=sorted(set(stale_files)),
            latency_ms=latency_ms,
            diff=diff,
        )
