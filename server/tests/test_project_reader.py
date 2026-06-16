import pytest

from context_system.models import FileMatch
from context_system.project_reader import ProjectReader


@pytest.mark.asyncio
async def test_project_reader_reads_only_candidate_files(tmp_path, monkeypatch):
    source = tmp_path / "auth.py"
    source.write_text("def auth_middleware(request):\n    return request\n")
    ignored = tmp_path / "unrelated.py"
    ignored.write_text("def unrelated():\n    pass\n")
    reader = ProjectReader(max_files=1)

    async def fail_llm(prompt, payloads, signals=None, memories=None):
        raise RuntimeError("force heuristic")

    monkeypatch.setattr(reader, "_decide_with_llm", fail_llm)

    chunks = await reader.read_and_rank(
        str(tmp_path),
        "add authentication middleware",
        [FileMatch(path=str(source), score=1.0)],
        "task-1",
    )

    assert len(chunks) == 1
    assert chunks[0].chunk.file_path == str(source.resolve())
    assert "auth_middleware" in chunks[0].chunk.content
