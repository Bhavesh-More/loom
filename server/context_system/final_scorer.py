from __future__ import annotations

from context_system.models import FileMatch, RankedChunk, TaskType


class FinalScorer:
    WEIGHTS = {
        TaskType.NEW_FEATURE: {"grep": 0.25, "semantic": 0.25, "graph": 0.35, "centrality": 0.10, "recency": 0.05},
        TaskType.BUG_FIX: {"grep": 0.20, "semantic": 0.40, "graph": 0.20, "centrality": 0.10, "recency": 0.10},
        TaskType.REFACTOR: {"grep": 0.15, "semantic": 0.25, "graph": 0.25, "centrality": 0.30, "recency": 0.05},
        TaskType.QA: {"grep": 0.35, "semantic": 0.35, "graph": 0.15, "centrality": 0.10, "recency": 0.05},
        TaskType.UNKNOWN: {"grep": 0.30, "semantic": 0.30, "graph": 0.25, "centrality": 0.10, "recency": 0.05},
    }

    def merge(
        self,
        task_type: TaskType,
        grep_matches: list[FileMatch],
        semantic_chunks: list[RankedChunk],
        graph_scores: dict[str, float],
        centrality: dict[str, float],
        recency: dict[str, float] | None = None,
    ) -> dict[str, float]:
        weights = self.WEIGHTS.get(task_type, self.WEIGHTS[TaskType.UNKNOWN])
        recency = recency or {}
        grep = {match.path: match.score for match in grep_matches}
        semantic: dict[str, float] = {}
        for chunk in semantic_chunks:
            path = chunk.chunk.file_path
            semantic[path] = max(semantic.get(path, 0.0), chunk.score)

        all_paths = set(grep) | set(semantic) | set(graph_scores) | set(centrality)
        scores: dict[str, float] = {}
        for path in all_paths:
            scores[path] = (
                weights["grep"] * grep.get(path, 0.0)
                + weights["semantic"] * semantic.get(path, 0.0)
                + weights["graph"] * graph_scores.get(path, 0.0)
                + weights["centrality"] * centrality.get(path, 0.0)
                + weights["recency"] * recency.get(path, 0.0)
            )
        return dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))
