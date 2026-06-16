from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TaskType(str, Enum):
    NEW_FEATURE = "new_feature"
    BUG_FIX = "bug_fix"
    REFACTOR = "refactor"
    QA = "qa"
    UNKNOWN = "unknown"


class IntentSignals(BaseModel):
    concepts: list[str] = Field(default_factory=list)
    likely_symbols: list[str] = Field(default_factory=list)
    fuzzy_synonyms: list[str] = Field(default_factory=list)
    task_type: TaskType = TaskType.UNKNOWN
    domain: str = "general"

    @property
    def grep_terms(self) -> list[str]:
        seen: set[str] = set()
        terms: list[str] = []
        for term in [*self.concepts, *self.likely_symbols, *self.fuzzy_synonyms]:
            cleaned = term.strip()
            key = cleaned.lower()
            if cleaned and key not in seen:
                seen.add(key)
                terms.append(cleaned)
        return terms


class FileMatch(BaseModel):
    path: str
    score: float = 0.0
    line_numbers: list[int] = Field(default_factory=list)
    snippets: list[str] = Field(default_factory=list)
    matched_terms: list[str] = Field(default_factory=list)


class CodeChunk(BaseModel):
    file_path: str
    chunk_index: int
    content: str
    start_line: int
    end_line: int
    content_hash: str


class RankedChunk(BaseModel):
    chunk: CodeChunk
    score: float


class SymbolEntry(BaseModel):
    name: str
    kind: str
    file_path: str
    repo_path: str
    signature: str | None = None
    description: str | None = None


class ImportEdge(BaseModel):
    repo_path: str
    from_file: str
    to_file: str
    edge_type: str = "imports"
    verified: bool = False


class RepoOrientation(BaseModel):
    repo_path: str
    manifests: dict[str, Any] = Field(default_factory=dict)
    directory_shape: list[str] = Field(default_factory=list)
    named_concepts: list[str] = Field(default_factory=list)
    detected_languages: dict[str, int] = Field(default_factory=dict)
    conventions: list[str] = Field(default_factory=list)


class ASTFileInfo(BaseModel):
    file_path: str
    language: str
    imports: list[str] = Field(default_factory=list)
    symbols: list[SymbolEntry] = Field(default_factory=list)
    parse_ok: bool = True


class ASTDiff(BaseModel):
    file_path: str
    added_symbols: list[str] = Field(default_factory=list)
    removed_symbols: list[str] = Field(default_factory=list)
    changed_signatures: list[str] = Field(default_factory=list)
    added_imports: list[str] = Field(default_factory=list)
    removed_imports: list[str] = Field(default_factory=list)

    @property
    def has_interface_change(self) -> bool:
        return bool(self.added_symbols or self.removed_symbols or self.changed_signatures)


class CodeSection(BaseModel):
    content: str
    start_line: int
    end_line: int


class FileContext(BaseModel):
    path: str
    role: str
    relevant_sections: list[CodeSection]
    signatures: list[str]
    confidence: float
    graph_position: str


class Relationship(BaseModel):
    from_: str = Field(alias="from")
    to: str
    kind: str

    model_config = ConfigDict(populate_by_name=True)


class ChangeInstruction(BaseModel):
    file_path: str
    order: int
    what_to_do: str


class KnowledgeGap(BaseModel):
    description: str
    severity: Literal["low", "medium", "high"]


class ContextPayload(BaseModel):
    task: str
    files: list[FileContext]
    relationships: list[Relationship]
    change_surface: list[ChangeInstruction]
    gaps: list[KnowledgeGap]


class ContextMemory(BaseModel):
    repo_path: str
    task_signature: str
    prompt: str
    domain: str
    files: list[str]
    summary: str
    confidence: float = 0.0


class ContextAnalyzeRequest(BaseModel):
    repo_path: str
    prompt: str
    task_id: str
    token_budget: int = 2048


class ContextIndexRequest(BaseModel):
    repo_path: str


class PartitionRequest(BaseModel):
    repo_path: str
    prompt: str
    agents: list[str] = Field(default_factory=list)


class SubgraphAssignment(BaseModel):
    agent: str
    domain: str
    files: list[str]
    handoff_interfaces: list[str]
    payload: ContextPayload | None = None


class ContextStatus(BaseModel):
    repo_path: str
    index_coverage: float
    file_count: int
    indexed_file_count: int
    cache_entries: int
    cache_hit_rate: float
    graph_edge_count: int
    memory_count: int = 0


class InvalidationEvent(BaseModel):
    repo_path: str
    file_path: str
    stale_files: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    diff: ASTDiff | None = None
