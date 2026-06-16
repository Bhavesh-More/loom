from __future__ import annotations

import asyncio
import hashlib
import math
import re
from pathlib import Path

from context_system.db import ContextDatabase, context_db
from context_system.models import CodeChunk, FileMatch, RankedChunk


class EmbeddingProvider:
    _model = None
    _lock = asyncio.Lock()

    async def load(self) -> None:
        if self._model is not None:
            return
        async with self._lock:
            if self._model is not None:
                return
            try:
                from sentence_transformers import SentenceTransformer

                self._model = await asyncio.to_thread(SentenceTransformer, "all-MiniLM-L6-v2")
            except Exception:
                self._model = False

    async def encode(self, text: str) -> list[float]:
        await self.load()
        if self._model:
            vector = await asyncio.to_thread(self._model.encode, text)
            return [float(value) for value in vector]
        return self._hash_embedding(text)

    def _hash_embedding(self, text: str) -> list[float]:
        buckets = [0.0] * 384
        for token in re.findall(r"[A-Za-z0-9_]+", text.lower()):
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:2], "big") % 384
            sign = 1 if digest[2] % 2 == 0 else -1
            buckets[index] += sign
        norm = math.sqrt(sum(value * value for value in buckets)) or 1.0
        return [value / norm for value in buckets]


embedding_provider = EmbeddingProvider()


class SemanticSearcher:
    def __init__(self, db: ContextDatabase = context_db, provider: EmbeddingProvider = embedding_provider):
        self.db = db
        self.provider = provider

    async def search(
        self,
        repo_path: str,
        prompt: str,
        candidates: list[FileMatch],
        task_id: str,
        limit: int = 20,
    ) -> list[RankedChunk]:
        prompt_embedding = await self.provider.encode(prompt)
        chunks: list[CodeChunk] = []
        for match in candidates:
            chunks.extend(await self.chunk_file(Path(repo_path) / match.path))

        results: list[RankedChunk] = []
        for chunk in chunks:
            embedding = await self.db.get_cached_embedding(chunk.content_hash)
            if embedding is None:
                embedding = await self.provider.encode(chunk.content)
                await self.db.upsert_embedding(
                    chunk.content_hash,
                    chunk.file_path,
                    chunk.chunk_index,
                    embedding,
                    active_task_refs=[task_id],
                )
            score = cosine_similarity(prompt_embedding, embedding)
            results.append(RankedChunk(chunk=chunk, score=score))
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]

    async def chunk_file(self, path: Path, max_lines: int = 80) -> list[CodeChunk]:
        if not path.exists() or not path.is_file() or path.stat().st_size > 512_000:
            return []
        content = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        if not lines:
            return []

        boundaries = [0]
        for index, line in enumerate(lines):
            if re.match(r"^\s*(def|class|function|export\s+(function|class|const|interface|type)|const\s+\w+\s*=|async\s+function)\b", line):
                if index not in boundaries:
                    boundaries.append(index)
        boundaries.append(len(lines))

        chunks: list[CodeChunk] = []
        for chunk_index, start in enumerate(boundaries[:-1]):
            end = boundaries[chunk_index + 1]
            while end - start > max_lines:
                chunks.append(self._make_chunk(path, lines, start, start + max_lines, len(chunks)))
                start += max_lines
            if start < end:
                chunks.append(self._make_chunk(path, lines, start, end, len(chunks)))
        return chunks

    def _make_chunk(self, path: Path, lines: list[str], start: int, end: int, chunk_index: int) -> CodeChunk:
        content = "\n".join(lines[start:end])
        digest = hashlib.sha256(content.encode()).hexdigest()
        return CodeChunk(
            file_path=str(path),
            chunk_index=chunk_index,
            content=content,
            start_line=start + 1,
            end_line=end,
            content_hash=digest,
        )


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(size))
    left_norm = math.sqrt(sum(value * value for value in left[:size])) or 1.0
    right_norm = math.sqrt(sum(value * value for value in right[:size])) or 1.0
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))
