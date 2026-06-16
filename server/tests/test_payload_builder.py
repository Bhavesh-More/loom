import pytest

from context_system.models import ImportEdge, IntentSignals, RankedChunk, CodeChunk, TaskType
from context_system.payload_builder import PayloadBuilder


@pytest.mark.asyncio
async def test_payload_builder_matches_context_payload_shape(tmp_path):
    source = tmp_path / "ThemeProvider.tsx"
    source.write_text("export const ThemeProvider = () => null\n")
    chunk = CodeChunk(
        file_path=str(source),
        chunk_index=0,
        content="export const ThemeProvider = () => null",
        start_line=1,
        end_line=1,
        content_hash="abc",
    )
    payload = await PayloadBuilder().build(
        str(tmp_path),
        "add dark mode toggle",
        IntentSignals(
            concepts=["theme"],
            likely_symbols=["ThemeProvider"],
            fuzzy_synonyms=["darkMode"],
            task_type=TaskType.NEW_FEATURE,
            domain="UI/styling",
        ),
        {str(source): 0.95},
        [RankedChunk(chunk=chunk, score=0.95)],
        [ImportEdge(repo_path=str(tmp_path), from_file=str(source), to_file=str(tmp_path / "App.tsx"))],
    )

    dumped = payload.model_dump(by_alias=True)
    assert set(dumped) == {"task", "files", "relationships", "change_surface", "gaps"}
    assert dumped["files"][0]["path"] == "ThemeProvider.tsx"
    assert "relevant_sections" in dumped["files"][0]
