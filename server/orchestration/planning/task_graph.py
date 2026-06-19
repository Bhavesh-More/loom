from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field, StrictStr


class TaskNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: StrictStr = Field(description="Unique identifier for the task node")
    parent_id: StrictStr | None = Field(
        default=None, description="Identifier of the parent task node, supporting hierarchy"
    )
    agent_id: StrictStr = Field(description="The ID of the agent assigned to this task")
    task: StrictStr = Field(description="Description of the task to be executed")
    capabilities_required: list[StrictStr] = Field(
        default_factory=list, description="Capabilities required for this specific task"
    )
    capability_score: float = Field(
        description="The capability match score of the assigned agent (0.0 to 1.0)"
    )
    selection_reasoning: StrictStr = Field(
        description="Detailed explanation for why this agent was selected"
    )
    depends_on: list[StrictStr] = Field(
        default_factory=list,
        description="List of task node IDs that this task depends on (must run before this task)"
    )


class TaskGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[TaskNode] = Field(default_factory=list)

    def topological_sort(self) -> list[TaskNode]:
        """
        Sorts the task nodes in topological order based on dependencies.
        Raises ValueError if a cycle is detected.
        """
        node_map = {node.id: node for node in self.nodes}
        visited: dict[str, int] = {}  # id -> state (0 = visiting, 1 = visited)
        sorted_nodes: list[TaskNode] = []

        def visit(node_id: str):
            if node_id not in node_map:
                # If dependency points to a node not in the graph, ignore it.
                return
            state = visited.get(node_id)
            if state == 0:
                raise ValueError(f"Dependency cycle detected involving node: {node_id}")
            if state == 1:
                return

            visited[node_id] = 0  # visiting
            node = node_map[node_id]
            for dep_id in node.depends_on:
                visit(dep_id)
            visited[node_id] = 1  # visited
            sorted_nodes.append(node)

        for node in self.nodes:
            if node.id not in visited:
                visit(node.id)

        return sorted_nodes

    def get_parallel_groups(self) -> list[list[TaskNode]]:
        """
        Groups nodes into parallel execution tiers. 
        Nodes in the same group/tier can run concurrently.
        """
        node_map = {node.id: node for node in self.nodes}
        
        # Verify graph is a DAG first (raises ValueError on cycle)
        self.topological_sort()

        levels: dict[str, int] = {}

        def get_level(node_id: str) -> int:
            if node_id not in node_map:
                return -1
            if node_id in levels:
                return levels[node_id]

            node = node_map[node_id]
            if not node.depends_on:
                levels[node_id] = 0
                return 0

            max_dep_level = -1
            for dep_id in node.depends_on:
                dep_level = get_level(dep_id)
                if dep_level > max_dep_level:
                    max_dep_level = dep_level

            level = max_dep_level + 1
            levels[node_id] = level
            return level

        for node in self.nodes:
            get_level(node.id)

        groups_map: dict[int, list[TaskNode]] = {}
        for node in self.nodes:
            lvl = levels.get(node.id, 0)
            if lvl not in groups_map:
                groups_map[lvl] = []
            groups_map[lvl].append(node)

        sorted_levels = sorted(groups_map.keys())
        return [groups_map[lvl] for lvl in sorted_levels]
