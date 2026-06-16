import shutil
from pathlib import Path

import pytest

from context_system.grep_scanner import GrepScanner
from context_system.models import IntentSignals, TaskType


class NoopDB:
    async def persist_grep_hits(self, *args, **kwargs):
        self.persisted = True


@pytest.mark.asyncio
async def test_grep_scanner_runs_rg_and_persists_hits(tmp_path):
    if not shutil.which("rg"):
        pytest.skip("ripgrep is not installed")
    source = tmp_path / "src"
    source.mkdir()
    (source / "ThemeProvider.tsx").write_text("export const ThemeProvider = () => null\nconst darkMode = true\n")
    db = NoopDB()
    scanner = GrepScanner(db=db)

    matches = await scanner.scan(
        str(tmp_path),
        IntentSignals(
            concepts=["theme"],
            likely_symbols=["darkMode"],
            fuzzy_synonyms=["appearance"],
            task_type=TaskType.NEW_FEATURE,
            domain="UI/styling",
        ),
        "task-1",
        "add dark mode",
    )

    assert matches
    assert Path(matches[0].path).name == "ThemeProvider.tsx"
    assert db.persisted is True
