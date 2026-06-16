from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from context_system.db import ContextDatabase, context_db
from context_system.models import ImportEdge


class ArchitectureAnalyzer:
    def analyze(self, edges: list[ImportEdge]) -> dict[str, list[str]]:
        if not edges:
            return {}
        try:
            import networkx as nx

            graph = nx.Graph()
            for edge in edges:
                graph.add_edge(edge.from_file, edge.to_file)
            clusters = list(nx.connected_components(graph))
        except Exception:
            clusters = [set([edge.from_file, edge.to_file]) for edge in edges]
        domains: dict[str, list[str]] = {}
        for cluster in clusters:
            label = self._label_cluster(cluster)
            domains[label] = sorted(cluster)
        return domains

    def _label_cluster(self, files) -> str:
        parts = Counter()
        for file_path in files:
            path = Path(file_path)
            for part in path.parts[-4:-1]:
                if part not in {"src", "server", "app", "lib"}:
                    parts[part] += 1
        if parts:
            return parts.most_common(1)[0][0]
        return "core"


class PatternRecognizer:
    def extract(self, central_files: list[str]) -> list[str]:
        patterns: list[str] = []
        suffixes = Counter(Path(file).suffix for file in central_files)
        if suffixes:
            patterns.append(f"Central files are primarily {suffixes.most_common(1)[0][0]} files")
        if any("route" in file.lower() or "api" in file.lower() for file in central_files):
            patterns.append("API behavior appears to be organized around route/controller files")
        if any("component" in file.lower() for file in central_files):
            patterns.append("UI behavior appears to be organized around component files")
        return patterns


class DomainSummarizer:
    def __init__(self, db: ContextDatabase = context_db):
        self.db = db

    async def summarize(self, repo_path: str, domains: dict[str, list[str]]) -> dict[str, str]:
        summaries: dict[str, str] = {}
        for name, files in domains.items():
            central = files[:8]
            summary = f"{name} domain contains {len(files)} indexed files. Central files: {', '.join(Path(file).name for file in central[:5])}."
            await self.db.upsert_domain_summary(repo_path, name, summary, central)
            summaries[name] = summary
        return summaries


class ProjectIntelligence:
    def __init__(self, db: ContextDatabase = context_db):
        self.architecture = ArchitectureAnalyzer()
        self.patterns = PatternRecognizer()
        self.summarizer = DomainSummarizer(db)

    async def analyze(self, repo_path: str, edges: list[ImportEdge], centrality: dict[str, float]) -> dict:
        domains = self.architecture.analyze(edges)
        central_files = [path for path, _ in sorted(centrality.items(), key=lambda item: item[1], reverse=True)[:30]]
        summaries = await self.summarizer.summarize(repo_path, domains)
        return {
            "domains": domains,
            "patterns": self.patterns.extract(central_files),
            "summaries": summaries,
        }
