from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
import pytest

from orchestration.planning.decomposition_engine import DecompositionEngine
from orchestration.planning.task_graph import TaskGraph


@pytest.mark.anyio
async def test_fallback_decomposition(monkeypatch: pytest.MonkeyPatch) -> None:
    # Clear the API key to force fallback path and prevent ChatGroq instantiation
    monkeypatch.delenv("GROQ_API_KEY_1", raising=False)

    engine = DecompositionEngine()
    graph = await engine.decompose("build a calculator application with postgres and fastapi")

    assert isinstance(graph, TaskGraph)
    assert len(graph.nodes) == 5

    # Verify fallback node details
    nodes_by_id = {node.id: node for node in graph.nodes}
    assert "db_schema" in nodes_by_id
    assert "calc_logic" in nodes_by_id
    assert "api_backend" in nodes_by_id
    assert "streamlit_ui" in nodes_by_id
    assert "documentation" in nodes_by_id

    # Verify agent routing and scoring worked on fallback items
    db_node = nodes_by_id["db_schema"]
    assert db_node.agent_id == "postgresql"
    assert db_node.capability_score == 1.0
    assert "Selected 'postgresql'" in db_node.selection_reasoning

    api_node = nodes_by_id["api_backend"]
    assert api_node.agent_id == "fastapi"
    assert api_node.capability_score == 1.0
    assert "Selected 'fastapi'" in api_node.selection_reasoning

    # Verify dependencies are retained
    assert "db_schema" in api_node.depends_on


@pytest.mark.anyio
async def test_llm_decomposition() -> None:
    # Mock LLM response
    mock_llm = MagicMock()
    mock_response = MagicMock()

    # We want it to return JSON string in the content field
    mock_response.content = """
    {
      "subtasks": [
        {
          "id": "task_auth",
          "task": "Build login authentication and jwt logic",
          "capabilities_required": ["auth", "jwt"],
          "depends_on": []
        },
        {
          "id": "task_db",
          "task": "Create mongo collections for user data",
          "capabilities_required": ["mongodb"],
          "depends_on": ["task_auth"]
        }
      ]
    }
    """

    # Set up async mock for ainvoke
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    engine = DecompositionEngine(llm=mock_llm)
    graph = await engine.decompose("build user accounts database", {"user_id": 123})

    assert isinstance(graph, TaskGraph)
    assert len(graph.nodes) == 2

    nodes_by_id = {node.id: node for node in graph.nodes}
    assert "task_auth" in nodes_by_id
    assert "task_db" in nodes_by_id

    auth_node = nodes_by_id["task_auth"]
    assert auth_node.agent_id == "auth"
    assert auth_node.capability_score == 0.75

    db_node = nodes_by_id["task_db"]
    assert db_node.agent_id == "mongodb"
    assert db_node.capability_score == 1.0
    assert db_node.depends_on == ["task_auth"]
