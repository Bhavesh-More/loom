from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path

from context_system.models import (
    ChangeInstruction,
    CodeSection,
    ContextPayload,
    FileContext,
    ImportEdge,
    IntentSignals,
    KnowledgeGap,
    RankedChunk,
    Relationship,
)


class PayloadBuilder:
    def __init__(self, token_budget: int = 2048):
        self.token_budget = token_budget
        self.relationship_extractor = RelationshipExtractor()
        self.change_surface = ChangeSurfaceComputer()
        self.gap_detector = GapDetector()

    async def build(
        self,
        repo_path: str,
        prompt: str,
        signals: IntentSignals,
        final_scores: dict[str, float],
        semantic_chunks: list[RankedChunk],
        edges: list[ImportEdge],
    ) -> ContextPayload:
        chunks_by_file: dict[str, list[RankedChunk]] = defaultdict(list)
        for chunk in semantic_chunks:
            chunks_by_file[chunk.chunk.file_path].append(chunk)

        files: list[FileContext] = []
        for file_path, score in list(final_scores.items())[:12]:
            sections = await self._sections_for_file(file_path, chunks_by_file.get(file_path, []))
            signatures = self._extract_signatures(sections)
            files.append(
                FileContext(
                    path=self._rel(repo_path, file_path),
                    role=self._infer_role(file_path, signals, edges),
                    relevant_sections=sections,
                    signatures=signatures[:8],
                    confidence=round(max(0.0, min(score, 1.0)), 3),
                    graph_position=self._graph_position(file_path, edges),
                )
            )

        relationships = self.relationship_extractor.extract(repo_path, edges, {path for path in final_scores})
        change_surface = self.change_surface.compute(repo_path, prompt, signals, final_scores, edges)
        gaps = self.gap_detector.detect(repo_path, final_scores, edges)
        payload = ContextPayload(
            task=prompt,
            files=files,
            relationships=relationships,
            change_surface=change_surface,
            gaps=gaps,
        )
        return self._fit_budget(payload)

    def to_prose(self, payload: ContextPayload) -> str:
        lines = [f"Task: {payload.task}", "", "Relevant files:"]
        for file in payload.files:
            lines.append(f"- {file.path}: {file.role} (confidence {file.confidence:.2f}, {file.graph_position})")
            if file.signatures:
                lines.append(f"  Signatures: {', '.join(file.signatures[:4])}")
        if payload.relationships:
            lines.extend(["", "Relationships:"])
            for rel in payload.relationships:
                lines.append(f"- {rel.from_} {rel.kind} {rel.to}")
        if payload.change_surface:
            lines.extend(["", "Change surface:"])
            for item in payload.change_surface:
                lines.append(f"{item.order}. {item.file_path}: {item.what_to_do}")
        if payload.gaps:
            lines.extend(["", "Knowledge gaps:"])
            for gap in payload.gaps:
                lines.append(f"- [{gap.severity}] {gap.description}")
        return "\n".join(lines)

    async def _sections_for_file(self, file_path: str, chunks: list[RankedChunk]) -> list[CodeSection]:
        sections = [
            CodeSection(
                content=item.chunk.content[:1200],
                start_line=item.chunk.start_line,
                end_line=item.chunk.end_line,
            )
            for item in sorted(chunks, key=lambda chunk: chunk.score, reverse=True)[:3]
        ]
        if sections:
            return sections
        path = Path(file_path)
        if not path.exists():
            return []
        import asyncio

        text = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="ignore")
        lines = text.splitlines()[:40]
        return [CodeSection(content="\n".join(lines), start_line=1, end_line=len(lines))]

    def _infer_role(self, file_path: str, signals: IntentSignals, edges: list[ImportEdge]) -> str:
        name = Path(file_path).name
        lower = file_path.lower()
        if "config" in lower:
            return f"{name} configures project behavior relevant to {signals.domain}"
        if any(part in lower for part in ["provider", "context", "store"]):
            return f"{name} owns shared state or dependency wiring for this task"
        if any(part in lower for part in ["component", "page", "view"]):
            return f"{name} is a likely UI surface for the requested change"
        if any(part in lower for part in ["route", "api", "controller"]):
            return f"{name} is a request handling surface for the task"
        if any(edge.to_file == file_path for edge in edges):
            return f"{name} is imported by task-relevant files"
        return f"{name} matched the task intent and may need inspection"

    def _graph_position(self, file_path: str, edges: list[ImportEdge]) -> str:
        indegree = sum(1 for edge in edges if edge.to_file == file_path)
        outdegree = sum(1 for edge in edges if edge.from_file == file_path)
        lower = file_path.lower()
        if "config" in lower:
            return "config"
        if indegree >= 3:
            return "shared abstraction"
        if indegree and outdegree:
            return "intermediate dependency"
        if indegree:
            return "dependency"
        if outdegree:
            return "consumer"
        return "isolated match"

    def _extract_signatures(self, sections: list[CodeSection]) -> list[str]:
        signatures: list[str] = []
        for section in sections:
            for line in section.content.splitlines():
                stripped = line.strip()
                if stripped.startswith(("def ", "class ", "export ", "function ", "const ", "type ", "interface ", "func ", "pub ")):
                    signatures.append(stripped[:180])
        return signatures

    def _fit_budget(self, payload: ContextPayload) -> ContextPayload:
        # Cheap token estimate: 4 chars/token. Trim sections first while keeping
        # file order, relationships, change surface, and gaps intact.
        while len(payload.model_dump_json(by_alias=True)) / 4 > self.token_budget and payload.files:
            if len(payload.files) > 8:
                payload.files.pop()
                continue
            if len(payload.relationships) > 20:
                payload.relationships = payload.relationships[:20]
                continue
            if len(payload.change_surface) > 8:
                payload.change_surface = payload.change_surface[:8]
                continue
            largest = max(payload.files, key=lambda file: sum(len(section.content) for section in file.relevant_sections))
            if largest.relevant_sections:
                section = largest.relevant_sections[-1]
                section.content = section.content[: max(400, len(section.content) // 2)]
                if len(section.content) <= 420 and len(largest.relevant_sections) > 1:
                    largest.relevant_sections.pop()
            elif len(payload.relationships) > 10:
                payload.relationships = payload.relationships[: max(10, len(payload.relationships) // 2)]
            elif len(payload.change_surface) > 5:
                payload.change_surface = payload.change_surface[: max(5, len(payload.change_surface) // 2)]
            elif len(payload.files) > 3:
                payload.files.pop()
            else:
                break
        return payload

    def _rel(self, repo_path: str, file_path: str) -> str:
        try:
            return str(Path(file_path).resolve().relative_to(Path(repo_path).resolve()))
        except ValueError:
            return file_path


class RelationshipExtractor:
    def extract(self, repo_path: str, edges: list[ImportEdge], relevant: set[str]) -> list[Relationship]:
        relationships: list[Relationship] = []
        for edge in edges:
            if edge.from_file not in relevant and edge.to_file not in relevant:
                continue
            relationships.append(
                Relationship(
                    from_=self._rel(repo_path, edge.from_file),
                    to=self._rel(repo_path, edge.to_file),
                    kind=self._kind(edge),
                )
            )
        return relationships[:40]

    def _kind(self, edge: ImportEdge) -> str:
        if edge.edge_type == "imports":
            return "imports"
        return edge.edge_type.replace("_", " ")

    def _rel(self, repo_path: str, file_path: str) -> str:
        try:
            return str(Path(file_path).resolve().relative_to(Path(repo_path).resolve()))
        except ValueError:
            return file_path


class ChangeSurfaceComputer:
    def compute(
        self,
        repo_path: str,
        prompt: str,
        signals: IntentSignals,
        final_scores: dict[str, float],
        edges: list[ImportEdge],
    ) -> list[ChangeInstruction]:
        ordered = self._dependency_order(list(final_scores.keys())[:12], edges)
        instructions: list[ChangeInstruction] = []
        for order, file_path in enumerate(ordered, start=1):
            instructions.append(
                ChangeInstruction(
                    file_path=self._rel(repo_path, file_path),
                    order=order,
                    what_to_do=self._instruction(file_path, prompt, signals),
                )
            )
        return instructions

    def _dependency_order(self, files: list[str], edges: list[ImportEdge]) -> list[str]:
        file_set = set(files)
        indegree = {file: 0 for file in files}
        outgoing: dict[str, list[str]] = defaultdict(list)
        for edge in edges:
            if edge.from_file in file_set and edge.to_file in file_set:
                outgoing[edge.to_file].append(edge.from_file)
                indegree[edge.from_file] += 1
        queue = deque([file for file in files if indegree[file] == 0])
        ordered: list[str] = []
        while queue:
            file = queue.popleft()
            ordered.append(file)
            for consumer in outgoing[file]:
                indegree[consumer] -= 1
                if indegree[consumer] == 0:
                    queue.append(consumer)
        ordered.extend(file for file in files if file not in ordered)
        return ordered

    def _instruction(self, file_path: str, prompt: str, signals: IntentSignals) -> str:
        lower = file_path.lower()
        if "config" in lower:
            return f"Update configuration needed for: {prompt}"
        if any(part in lower for part in ["provider", "context", "store"]):
            return f"Update shared state/interface for {signals.domain}"
        if any(part in lower for part in ["component", "page", "view"]):
            return "Wire the user-facing UI or interaction using the updated interface"
        if any(part in lower for part in ["route", "api", "controller"]):
            return "Apply the request-handling change and preserve existing route conventions"
        return f"Inspect and update the relevant section for: {prompt}"

    def _rel(self, repo_path: str, file_path: str) -> str:
        try:
            return str(Path(file_path).resolve().relative_to(Path(repo_path).resolve()))
        except ValueError:
            return file_path


class GapDetector:
    def detect(self, repo_path: str, final_scores: dict[str, float], edges: list[ImportEdge]) -> list[KnowledgeGap]:
        gaps: list[KnowledgeGap] = []
        if final_scores and not edges:
            gaps.append(KnowledgeGap(description="Relevant files were found, but their import graph is not indexed yet", severity="medium"))
        edge_nodes = {edge.from_file for edge in edges} | {edge.to_file for edge in edges}
        missing = [path for path in final_scores if path not in edge_nodes]
        if len(missing) >= 5:
            gaps.append(KnowledgeGap(description="Several relevant files have no adjacent graph edges yet", severity="medium"))
        elif missing:
            gaps.append(KnowledgeGap(description="Some relevant files have not been connected to the graph yet", severity="low"))
        return gaps[:5]
