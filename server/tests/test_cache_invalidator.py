import pytest

from context_system.cache_invalidator import ASTDiffer, CascadeInvalidator
from context_system.models import ImportEdge, SymbolEntry


class FakeDB:
    async def get_symbols_for_file(self, repo_path, file_path):
        return [
            SymbolEntry(
                name="useTheme",
                kind="function",
                file_path=file_path,
                repo_path=repo_path,
                signature="export function useTheme()",
            )
        ]

    async def get_edges_for_file(self, repo_path, file_path):
        return []

    async def get_edges(self, repo_path):
        return [
            ImportEdge(repo_path=repo_path, from_file="/repo/App.tsx", to_file="/repo/ThemeProvider.tsx"),
            ImportEdge(repo_path=repo_path, from_file="/repo/Navbar.tsx", to_file="/repo/App.tsx"),
        ]


@pytest.mark.asyncio
async def test_ast_differ_reports_symbol_signature_changes(tmp_path):
    file_path = tmp_path / "ThemeProvider.tsx"
    file_path.write_text("export function useTheme(value: string) { return value }\n")
    differ = ASTDiffer(db=FakeDB())

    diff = await differ.diff_against_store(str(tmp_path), str(file_path))

    assert diff.changed_signatures == ["useTheme"]


@pytest.mark.asyncio
async def test_cascade_invalidator_walks_consumers():
    invalidator = CascadeInvalidator(db=FakeDB())

    consumers = await invalidator.consumers("/repo", "/repo/ThemeProvider.tsx")

    assert consumers == ["/repo/App.tsx", "/repo/Navbar.tsx"]
