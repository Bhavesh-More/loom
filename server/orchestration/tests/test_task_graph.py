from __future__ import annotations

import pytest
from pydantic import ValidationError

from orchestration.planning.task_graph import TaskGraph, TaskNode


def test_task_node_validation() -> None:
    # Test valid task node creation
    node = TaskNode(
        id="task_1",
        parent_id=None,
        agent_id="postgresql",
        task="Set up database schema",
        capabilities_required=["sql", "postgresql"],
        capability_score=1.0,
        selection_reasoning="Only postgresql matches the sql skill",
        depends_on=[],
    )
    assert node.id == "task_1"
    assert node.parent_id is None
    assert node.agent_id == "postgresql"
    assert node.task == "Set up database schema"
    assert node.capabilities_required == ["sql", "postgresql"]
    assert node.capability_score == 1.0
    assert node.selection_reasoning == "Only postgresql matches the sql skill"
    assert node.depends_on == []

    # Invalid task node creation (missing critical field)
    with pytest.raises(ValidationError):
        TaskNode(
            id="task_2",
            agent_id="fastapi",
            # task is missing!
            capability_score=0.9,
            selection_reasoning="Reason",
        )


def test_task_graph_topological_sort() -> None:
    # Graph structure:
    # A (no deps)
    # B (no deps)
    # C depends on A and B
    # D depends on C
    # Expected sort order: A, B must come before C, and C must come before D.

    node_a = TaskNode(
        id="A",
        agent_id="all_rounder",
        task="Task A",
        capability_score=1.0,
        selection_reasoning="Reason",
        depends_on=[],
    )
    node_b = TaskNode(
        id="B",
        agent_id="all_rounder",
        task="Task B",
        capability_score=1.0,
        selection_reasoning="Reason",
        depends_on=[],
    )
    node_c = TaskNode(
        id="C",
        agent_id="all_rounder",
        task="Task C",
        capability_score=1.0,
        selection_reasoning="Reason",
        depends_on=["A", "B"],
    )
    node_d = TaskNode(
        id="D",
        agent_id="all_rounder",
        task="Task D",
        capability_score=1.0,
        selection_reasoning="Reason",
        depends_on=["C"],
    )

    graph = TaskGraph(nodes=[node_d, node_c, node_b, node_a])  # added in jumbled order
    sorted_nodes = graph.topological_sort()
    
    assert len(sorted_nodes) == 4
    
    # Check positions in the sorted list
    positions = {node.id: i for i, node in enumerate(sorted_nodes)}
    
    assert positions["A"] < positions["C"]
    assert positions["B"] < positions["C"]
    assert positions["C"] < positions["D"]


def test_task_graph_cycle_detection() -> None:
    # Graph structure:
    # A depends on B
    # B depends on A (Cycle!)
    node_a = TaskNode(
        id="A",
        agent_id="all_rounder",
        task="Task A",
        capability_score=1.0,
        selection_reasoning="Reason",
        depends_on=["B"],
    )
    node_b = TaskNode(
        id="B",
        agent_id="all_rounder",
        task="Task B",
        capability_score=1.0,
        selection_reasoning="Reason",
        depends_on=["A"],
    )

    graph = TaskGraph(nodes=[node_a, node_b])
    with pytest.raises(ValueError, match="Dependency cycle detected"):
        graph.topological_sort()


def test_task_graph_parallel_groups() -> None:
    # Graph structure:
    # A, B (level 0)
    # C depends on A and B (level 1)
    # D depends on C (level 2)
    # E depends on B (level 1)
    
    node_a = TaskNode(
        id="A",
        agent_id="all_rounder",
        task="Task A",
        capability_score=1.0,
        selection_reasoning="Reason",
        depends_on=[],
    )
    node_b = TaskNode(
        id="B",
        agent_id="all_rounder",
        task="Task B",
        capability_score=1.0,
        selection_reasoning="Reason",
        depends_on=[],
    )
    node_c = TaskNode(
        id="C",
        agent_id="all_rounder",
        task="Task C",
        capability_score=1.0,
        selection_reasoning="Reason",
        depends_on=["A", "B"],
    )
    node_d = TaskNode(
        id="D",
        agent_id="all_rounder",
        task="Task D",
        capability_score=1.0,
        selection_reasoning="Reason",
        depends_on=["C"],
    )
    node_e = TaskNode(
        id="E",
        agent_id="all_rounder",
        task="Task E",
        capability_score=1.0,
        selection_reasoning="Reason",
        depends_on=["B"],
    )

    graph = TaskGraph(nodes=[node_a, node_b, node_c, node_d, node_e])
    groups = graph.get_parallel_groups()
    
    assert len(groups) == 3
    
    # Tier 0 should contain A and B
    tier_0_ids = {node.id for node in groups[0]}
    assert tier_0_ids == {"A", "B"}
    
    # Tier 1 should contain C and E
    tier_1_ids = {node.id for node in groups[1]}
    assert tier_1_ids == {"C", "E"}
    
    # Tier 2 should contain D
    tier_2_ids = {node.id for node in groups[2]}
    assert tier_2_ids == {"D"}
