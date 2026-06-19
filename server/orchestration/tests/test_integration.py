"""
Integration tests for the orchestration layer (Step 8 verification).

Covers:
- Complex requests decompose into correct parent/child hierarchies.
- Capability scoring properly matches PostgreSQL / MongoDB / FastAPI to tasks.
- Selection reasoning is descriptive and present.
- TaskGraph is attached to ExecutionPlan after MasterPlanner.build_plan().
- TaskGraph topological ordering and parallel group detection.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from orchestration.planning.agent_router import route_task
from orchestration.planning.decomposition_engine import DecompositionEngine
from orchestration.planning.plan_schema import ExecutionPlan
from orchestration.planning.task_graph import TaskGraph, TaskNode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_node(
    node_id: str,
    agent_id: str,
    capabilities: list[str],
    depends_on: list[str] | None = None,
    parent_id: str | None = None,
) -> TaskNode:
    return TaskNode(
        id=node_id,
        parent_id=parent_id,
        agent_id=agent_id,
        task=f"Task for {node_id}",
        capabilities_required=capabilities,
        capability_score=1.0,
        selection_reasoning=f"Selected '{agent_id}' for {node_id}",
        depends_on=depends_on or [],
    )


# ---------------------------------------------------------------------------
# 1. Complex hierarchy: parent/child relationships
# ---------------------------------------------------------------------------

def test_task_graph_parent_child_hierarchy() -> None:
    """Nodes can express a parent/child hierarchy via parent_id."""
    root = _make_node("root", "all_rounder", [])
    child_a = _make_node("child_a", "fastapi", ["fastapi"], parent_id="root")
    child_b = _make_node("child_b", "postgresql", ["sql"], parent_id="root")
    grandchild = _make_node("grandchild", "auth", ["auth"], depends_on=["child_a"], parent_id="child_a")

    graph = TaskGraph(nodes=[root, child_a, child_b, grandchild])

    # Children refer back to root
    children_of_root = [n for n in graph.nodes if n.parent_id == "root"]
    assert len(children_of_root) == 2
    assert {n.id for n in children_of_root} == {"child_a", "child_b"}

    # Grandchild refers back to child_a
    grandchildren = [n for n in graph.nodes if n.parent_id == "child_a"]
    assert len(grandchildren) == 1
    assert grandchildren[0].id == "grandchild"


# ---------------------------------------------------------------------------
# 2. Topological sort produces a valid linear order
# ---------------------------------------------------------------------------

def test_task_graph_topological_sort_respects_dependencies() -> None:
    """Topological order must place each node after all its dependencies."""
    db = _make_node("db", "postgresql", ["sql"])
    backend = _make_node("backend", "fastapi", ["fastapi"], depends_on=["db"])
    auth = _make_node("auth", "auth", ["auth"], depends_on=["db"])
    frontend = _make_node("frontend", "streamlit", ["streamlit"], depends_on=["backend", "auth"])

    graph = TaskGraph(nodes=[db, backend, auth, frontend])
    # topological_sort returns list[TaskNode]
    order = [node.id for node in graph.topological_sort()]

    idx = {node_id: i for i, node_id in enumerate(order)}
    assert idx["db"] < idx["backend"]
    assert idx["db"] < idx["auth"]
    assert idx["backend"] < idx["frontend"]
    assert idx["auth"] < idx["frontend"]


# ---------------------------------------------------------------------------
# 3. Parallel groups — independent nodes should be in the same group
# ---------------------------------------------------------------------------

def test_task_graph_parallel_groups() -> None:
    """Backend and auth, which both only depend on db, can run in parallel."""
    db = _make_node("db", "postgresql", ["sql"])
    backend = _make_node("backend", "fastapi", ["fastapi"], depends_on=["db"])
    auth = _make_node("auth", "auth", ["auth"], depends_on=["db"])
    frontend = _make_node("frontend", "streamlit", ["streamlit"], depends_on=["backend", "auth"])

    graph = TaskGraph(nodes=[db, backend, auth, frontend])
    # get_parallel_groups returns list[list[TaskNode]]
    groups = [[node.id for node in group] for group in graph.get_parallel_groups()]

    # Group 0: db alone
    assert groups[0] == ["db"]
    # Group 1: backend and auth in any order (both unblocked after db)
    assert set(groups[1]) == {"backend", "auth"}
    # Group 2: frontend alone
    assert groups[2] == ["frontend"]


# ---------------------------------------------------------------------------
# 4. Capability scoring — PostgreSQL, MongoDB, FastAPI specific matching
# ---------------------------------------------------------------------------

def test_route_postgresql_capabilities() -> None:
    decision = route_task(["sql", "schema_design", "postgresql"])
    assert decision.agent_id == "postgresql"
    assert decision.capability_score == 1.0
    assert decision.explanation  # non-empty
    assert "postgresql" in decision.explanation.lower()


def test_route_mongodb_capabilities() -> None:
    # MongoDB agent capabilities: ["nosql", "mongodb", "documents", "aggregation", "collections", "indexing", "queries"]
    decision = route_task(["nosql", "mongodb", "documents"])
    assert decision.agent_id == "mongodb"
    assert decision.capability_score == 1.0
    assert decision.explanation


def test_route_fastapi_capabilities() -> None:
    decision = route_task(["fastapi", "rest_api", "routing"])
    assert decision.agent_id == "fastapi"
    assert decision.capability_score == 1.0
    assert decision.explanation


# ---------------------------------------------------------------------------
# 5. Selection reasoning is descriptive and present on every node
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_every_fallback_node_has_selection_reasoning(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY_1", raising=False)
    engine = DecompositionEngine()
    graph = await engine.decompose("build a calculator app with postgres and fastapi")

    for node in graph.nodes:
        assert node.selection_reasoning, f"Node '{node.id}' has no selection_reasoning"
        assert len(node.selection_reasoning) > 10, f"Node '{node.id}' reasoning too short"
        assert node.agent_id, f"Node '{node.id}' has no agent_id"


# ---------------------------------------------------------------------------
# 6. LLM path: complex multi-agent decomposition with hierarchy
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_llm_complex_hierarchy_decomposition() -> None:
    """Verify that the LLM path correctly builds a multi-level hierarchy."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = """
    {
      "subtasks": [
        {
          "id": "schema",
          "task": "Design PostgreSQL schema for e-commerce orders",
          "capabilities_required": ["sql", "postgresql", "schema_design"],
          "depends_on": []
        },
        {
          "id": "auth_service",
          "task": "Add JWT authentication layer",
          "capabilities_required": ["auth", "jwt"],
          "depends_on": []
        },
        {
          "id": "api_layer",
          "task": "Build FastAPI endpoints for order management",
          "capabilities_required": ["fastapi", "rest_api"],
          "depends_on": ["schema", "auth_service"]
        },
        {
          "id": "ui_dashboard",
          "task": "Create Streamlit dashboard for order tracking",
          "capabilities_required": ["streamlit", "python"],
          "depends_on": ["api_layer"]
        }
      ]
    }
    """
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    engine = DecompositionEngine(llm=mock_llm)
    graph = await engine.decompose("build an e-commerce order management system", {})

    assert isinstance(graph, TaskGraph)
    assert len(graph.nodes) == 4

    nodes_by_id = {n.id: n for n in graph.nodes}

    # Check agent assignments
    assert nodes_by_id["schema"].agent_id == "postgresql"
    assert nodes_by_id["auth_service"].agent_id == "auth"
    assert nodes_by_id["api_layer"].agent_id == "fastapi"
    assert nodes_by_id["ui_dashboard"].agent_id == "streamlit"

    # Check dependency chain
    assert "schema" in nodes_by_id["api_layer"].depends_on
    assert "auth_service" in nodes_by_id["api_layer"].depends_on
    assert "api_layer" in nodes_by_id["ui_dashboard"].depends_on

    # Check topological order — topological_sort returns list[TaskNode]
    order = [node.id for node in graph.topological_sort()]
    idx = {nid: i for i, nid in enumerate(order)}
    assert idx["schema"] < idx["api_layer"]
    assert idx["auth_service"] < idx["api_layer"]
    assert idx["api_layer"] < idx["ui_dashboard"]

    # All nodes must have reasoning
    for node in graph.nodes:
        assert node.selection_reasoning


# ---------------------------------------------------------------------------
# 7. MasterPlanner attaches task_graph to ExecutionPlan
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_master_planner_attaches_task_graph() -> None:
    """MasterPlanner.build_plan() should populate ExecutionPlan.task_graph."""
    from orchestration.planning.master_planner import MasterPlanner

    planner = MasterPlanner()

    # Stub the LLM planning step — returns a minimal valid plan dict
    raw_plan = {
        "run_id": "test-run-step8",
        "task": "build a simple calculator",
        "context": {},
        "agents": [
            {
                "id": "all_rounder",
                "role": "All-rounder fallback agent",
                "task": "Build the calculator",
                "critical": False,
                "depends_on": [],
                "consumes_from": {},
                "expected_output": {"content": {"type": "str", "required": True, "min_length": 1}},
                "scoring_checks": ["all_required_fields_present", "output_not_empty"],
                "confidence_threshold": 0.60,
                "fallback": None,
                "max_retries": 3,
            }
        ],
    }
    planner._llm_plan = AsyncMock(return_value=raw_plan)

    # Stub the decomposition engine with a known TaskGraph — no real LLM call
    fake_graph = TaskGraph(
        nodes=[
            _make_node("calc_logic", "all_rounder", ["python"]),
            _make_node("db_schema", "postgresql", ["sql"], depends_on=["calc_logic"]),
        ]
    )
    planner.decomposition_engine.decompose = AsyncMock(return_value=fake_graph)

    # Patch validator and DB persist to be no-ops
    planner.validator.validate = AsyncMock(
        return_value=MagicMock(passed=True, errors=[])
    )
    planner._persist_plan = AsyncMock()

    plan = await planner.build_plan(
        "build a simple calculator",
        {"run_id": "test-run-step8"},
    )

    assert isinstance(plan, ExecutionPlan)
    # task_graph must be attached
    assert plan.task_graph is not None
    assert isinstance(plan.task_graph, TaskGraph)
    assert len(plan.task_graph.nodes) == 2
    node_ids = {n.id for n in plan.task_graph.nodes}
    assert node_ids == {"calc_logic", "db_schema"}
    # decompose must have been called once
    planner.decomposition_engine.decompose.assert_called_once()


# ---------------------------------------------------------------------------
# 8. planner_node state updates & execution
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_planner_node_execution_populates_task_graph_in_state() -> None:
    """Verify that the async planner_node executes and populates task_graph / task_graph_logs."""
    from graph.planner_node import planner_node
    from graph.state import LoomState

    # Mock the LLM to return a simple mock plan
    mock_llm_response = MagicMock()
    mock_llm_response.content = '{"plan": [{"step": 1, "agent": "postgresql", "task": "setup table"}]}'
    
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)

    # Mock DecompositionEngine to return a mock TaskGraph
    from orchestration.planning.task_graph import TaskGraph
    fake_graph = TaskGraph(
        nodes=[
            _make_node("db_node", "postgresql", ["sql"])
        ]
    )

    # Initialize a mock LoomState
    state = LoomState(
        project_id="test-proj",
        project_name="test-name",
        goal="Setup database schema",
        selected_agents=["postgresql"],
        active_agents=["postgresql"],
        query_type="codegen",
        qa_response="",
        execution_plan=[],
        current_step=0,
        agent_outputs={},
        workspace_path="dummy-path",
        errors=[],
        context_payload={},
        context_payload_text="",
        chat_session_id="session-123",
        task_graph=None,
        task_graph_logs=[]
    )

    # Use patch to mock ChatGroq instantiation and DecompositionEngine
    with patch("graph.planner_node.ChatGroq", return_value=mock_llm), \
         patch("graph.planner_node.DecompositionEngine") as mock_engine_cls:
        
        mock_engine = MagicMock()
        mock_engine.decompose = AsyncMock(return_value=fake_graph)
        mock_engine_cls.return_value = mock_engine

        # Invoke the async planner_node
        updated_state = await planner_node(state)

        # Assertions
        assert updated_state["task_graph"] is not None
        assert len(updated_state["task_graph_logs"]) == 1
        assert "[db_node] agent=postgresql" in updated_state["task_graph_logs"][0]
        assert updated_state["execution_plan"] == [{"step": 1, "agent": "postgresql", "task": "setup table"}]

