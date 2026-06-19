from __future__ import annotations

from orchestration.planning.plan_schema import ExecutionPlan


def get_cascade_impact(failed_agent_id: str, plan: ExecutionPlan) -> list[str]:
    dependents: dict[str, list[str]] = {agent.id: [] for agent in plan.agents}
    for agent in plan.agents:
        for dependency in agent.depends_on:
            dependents.setdefault(dependency, []).append(agent.id)

    impacted: list[str] = []
    seen: set[str] = set()

    def walk(agent_id: str) -> None:
        for child in dependents.get(agent_id, []):
            if child in seen:
                continue
            seen.add(child)
            impacted.append(child)
            walk(child)

    walk(failed_agent_id)
    return impacted
