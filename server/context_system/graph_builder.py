from __future__ import annotations

import asyncio
from pathlib import Path

from context_system.ast_parser import ASTParser, EXTENSION_LANGUAGE
from context_system.db import ContextDatabase, context_db
from context_system.models import FileMatch, ImportEdge


SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "__pycache__",
    ".next",
    "target",
    "tests",
    "outputs",
}


class GraphBuilder:
    def __init__(self, db: ContextDatabase = context_db, parser: ASTParser | None = None):
        self.db = db
        self.parser = parser or ASTParser()

    async def build_from_matches(self, repo_path: str, matches: list[FileMatch]) -> tuple[dict[str, float], list[ImportEdge]]:
        seed_files = [str((Path(repo_path) / match.path).resolve()) for match in matches]
        all_edges: list[ImportEdge] = []
        discovered: set[str] = set(seed_files)

        for file_path in seed_files:
            info = await self.parser.parse_file(repo_path, file_path)
            await self.db.upsert_symbols(info.symbols)
            edges = self.parser.to_edges(repo_path, info)
            await self.db.upsert_edges(edges)
            all_edges.extend(edges)
            discovered.update(edge.to_file for edge in edges)

        reverse_edges = await self._discover_importers(repo_path, seed_files)
        await self.db.upsert_edges(reverse_edges)
        all_edges.extend(reverse_edges)
        discovered.update(edge.from_file for edge in reverse_edges)

        graph_scores = self._score_discovered(seed_files, discovered, all_edges)
        return graph_scores, all_edges

    async def index_repo(self, repo_path: str, limit: int | None = None) -> int:
        files = await list_source_files(repo_path)
        if limit:
            files = files[:limit]
        count = 0
        for file_path in files:
            info = await self.parser.parse_file(repo_path, file_path)
            await self.db.upsert_symbols(info.symbols)
            await self.db.upsert_edges(self.parser.to_edges(repo_path, info))
            count += 1
        return count

    async def load_edges(self, repo_path: str) -> list[ImportEdge]:
        return await self.db.get_edges(repo_path)

    async def _discover_importers(self, repo_path: str, seed_files: list[str]) -> list[ImportEdge]:
        existing = await self.db.get_edges(repo_path)
        seed_set = set(seed_files)
        edges = [edge for edge in existing if edge.to_file in seed_set]
        if edges:
            return edges

        seed_names = {Path(path).stem for path in seed_files}
        source_files = await list_source_files(repo_path)
        discovered: list[ImportEdge] = []
        for source in source_files:
            if source in seed_set:
                continue
            text = await asyncio.to_thread(Path(source).read_text, encoding="utf-8", errors="ignore")
            if not any(name in text for name in seed_names):
                continue
            info = await self.parser.parse_file(repo_path, source)
            file_edges = self.parser.to_edges(repo_path, info)
            discovered.extend(edge for edge in file_edges if edge.to_file in seed_set)
            await self.db.upsert_symbols(info.symbols)
            await self.db.upsert_edges(file_edges)
        return discovered

    def _score_discovered(self, seeds: list[str], discovered: set[str], edges: list[ImportEdge]) -> dict[str, float]:
        seed_set = set(seeds)
        scores = {path: (1.0 if path in seed_set else 0.55) for path in discovered}
        for edge in edges:
            if edge.from_file in seed_set:
                scores[edge.to_file] = max(scores.get(edge.to_file, 0.0), 0.7)
            if edge.to_file in seed_set:
                scores[edge.from_file] = max(scores.get(edge.from_file, 0.0), 0.75)
        return scores


async def list_source_files(repo_path: str) -> list[str]:
    def _walk() -> list[str]:
        root = Path(repo_path)
        files: list[str] = []
        for path in root.rglob("*"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in EXTENSION_LANGUAGE:
                files.append(str(path.resolve()))
        return files

    return await asyncio.to_thread(_walk)
