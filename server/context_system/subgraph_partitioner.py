from __future__ import annotations

from pathlib import Path

from context_system.domain_analyzer import ArchitectureAnalyzer
from context_system.models import ContextPayload, SubgraphAssignment


class SubgraphPartitioner:
    def __init__(self):
        self.architecture = ArchitectureAnalyzer()

    def partition(
        self,
        repo_path: str,
        prompt: str,
        agents: list[str],
        payload: ContextPayload,
        edges,
    ) -> list[SubgraphAssignment]:
        domains = self._payload_domains(payload)
        if not domains:
            domains = {"general": [file.path for file in payload.files]}
        assignments: list[SubgraphAssignment] = []
        agent_pool = agents or ["general"]
        for index, (domain, files) in enumerate(domains.items()):
            agent = self._agent_for_domain(domain, agent_pool, index)
            handoffs = self._payload_handoffs(domain, domains, payload)
            scoped_files = [self._display(file) for file in files]
            assignments.append(
                SubgraphAssignment(
                    agent=agent,
                    domain=domain,
                    files=scoped_files,
                    handoff_interfaces=handoffs,
                    payload=payload,
                )
            )
        return assignments

    def _payload_domains(self, payload: ContextPayload) -> dict[str, list[str]]:
        domains: dict[str, list[str]] = {}
        for file in payload.files:
            label = self._label_path(file.path)
            domains.setdefault(label, []).append(file.path)
        return domains

    def _label_path(self, file_path: str) -> str:
        parts = Path(file_path).parts
        if "api" in parts or "routes" in parts:
            return "api"
        if "context_system" in parts:
            return "context"
        if "graph" in parts:
            return "orchestration"
        if "ide" in parts or "components" in parts or "pages" in parts:
            return "frontend"
        if len(parts) > 1:
            return parts[0]
        return "general"

    def _agent_for_domain(self, domain: str, agents: list[str], index: int) -> str:
        lower = domain.lower()
        for agent in agents:
            if lower in agent.lower() or agent.lower() in lower:
                return agent
        return agents[index % len(agents)]

    def _handoffs(self, domain: str, domains: dict[str, list[str]], edges) -> list[str]:
        owned = set(domains.get(domain, []))
        handoffs: list[str] = []
        for edge in edges:
            if edge.from_file in owned and edge.to_file not in owned:
                handoffs.append(f"{Path(edge.from_file).name} imports {Path(edge.to_file).name}")
            elif edge.to_file in owned and edge.from_file not in owned:
                handoffs.append(f"{Path(edge.from_file).name} consumes {Path(edge.to_file).name}")
        return handoffs[:10]

    def _payload_handoffs(self, domain: str, domains: dict[str, list[str]], payload: ContextPayload) -> list[str]:
        owned = set(domains.get(domain, []))
        handoffs: list[str] = []
        for rel in payload.relationships:
            if rel.from_ in owned and rel.to not in owned:
                handoffs.append(f"{rel.from_} {rel.kind} {rel.to}")
            elif rel.to in owned and rel.from_ not in owned:
                handoffs.append(f"{rel.from_} {rel.kind} {rel.to}")
        return handoffs[:10]

    def _display(self, file_path: str) -> str:
        return str(Path(file_path))
