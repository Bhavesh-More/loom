import pytest

from context_system.graph_builder import GraphBuilder
from context_system.models import FileMatch


class NoopDB:
    def __init__(self):
        self.edges = []

    async def upsert_symbols(self, symbols):
        self.symbols = symbols

    async def upsert_edges(self, edges):
        self.edges.extend(edges)

    async def get_edges(self, repo_path):
        return self.edges


@pytest.mark.asyncio
async def test_graph_builder_extracts_symbols_and_import_edges(tmp_path):
    (tmp_path / "src").mkdir()
    provider = tmp_path / "src" / "ThemeProvider.tsx"
    hook = tmp_path / "src" / "useTheme.ts"
    provider.write_text("import { useTheme } from './useTheme'\nexport const ThemeProvider = () => null\n")
    hook.write_text("export function useTheme() { return {} }\n")

    db = NoopDB()
    builder = GraphBuilder(db=db)
    scores, edges = await builder.build_from_matches(str(tmp_path), [FileMatch(path=str(provider), score=1.0)])

    assert str(hook.resolve()) in {edge.to_file for edge in edges}
    assert scores[str(provider.resolve())] == 1.0
    assert any(symbol.name == "ThemeProvider" for symbol in db.symbols)
