import math

import pytest

from context_system.models import FileMatch
from context_system.semantic_searcher import SemanticSearcher


class FakeDB:
    def __init__(self):
        self.cache = {}
        self.hits = 0

    async def get_cached_embedding(self, content_hash):
        if content_hash in self.cache:
            self.hits += 1
            return self.cache[content_hash]
        return None

    async def upsert_embedding(self, content_hash, file_path, chunk_index, embedding, active_task_refs=None):
        self.cache[content_hash] = embedding


class FakeProvider:
    async def encode(self, text):
        value = 1.0 if "theme" in text.lower() or "dark" in text.lower() else 0.2
        return [value, 0.0, 0.0]


@pytest.mark.asyncio
async def test_semantic_searcher_uses_content_hash_cache(tmp_path):
    file_path = tmp_path / "ThemeProvider.tsx"
    file_path.write_text("export function ThemeProvider() {\n  return 'dark theme'\n}\n")
    db = FakeDB()
    searcher = SemanticSearcher(db=db, provider=FakeProvider())
    matches = [FileMatch(path=str(file_path), score=1.0)]

    first = await searcher.search(str(tmp_path), "dark mode", matches, "task-1")
    second = await searcher.search(str(tmp_path), "dark mode", matches, "task-2")

    assert first[0].score == pytest.approx(1.0)
    assert second[0].chunk.content_hash == first[0].chunk.content_hash
    assert db.hits >= 1
