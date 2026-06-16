from __future__ import annotations

from context_system.models import ImportEdge


class CentralityScorer:
    def compute(self, edges: list[ImportEdge]) -> dict[str, float]:
        if not edges:
            return {}
        try:
            import networkx as nx

            graph = nx.DiGraph()
            for edge in edges:
                graph.add_edge(edge.from_file, edge.to_file)
            scores = nx.pagerank(graph, alpha=0.85)
            max_score = max(scores.values()) or 1.0
            return {path: score / max_score for path, score in scores.items()}
        except Exception:
            indegree: dict[str, int] = {}
            nodes: set[str] = set()
            for edge in edges:
                nodes.add(edge.from_file)
                nodes.add(edge.to_file)
                indegree[edge.to_file] = indegree.get(edge.to_file, 0) + 1
            max_degree = max(indegree.values(), default=1)
            return {node: indegree.get(node, 0) / max_degree for node in nodes}
