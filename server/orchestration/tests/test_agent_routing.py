from __future__ import annotations

from orchestration.planning.agent_router import (
    RoutingDecision,
    route_task,
    score_agent_capabilities,
)


def test_score_agent_capabilities_exact() -> None:
    # Postgres agent has capabilities: ["sql", "postgresql", "schema_design", ...]
    # If we require ["sql", "postgresql"], it should be a 1.0 exact match.
    score, exact, partial = score_agent_capabilities(
        ["sql", "postgresql", "schema_design"],
        ["sql", "postgresql"],
    )
    assert score == 1.0
    assert "sql" in exact
    assert "postgresql" in exact
    assert len(partial) == 0


def test_score_agent_capabilities_partial() -> None:
    # Requiring 'postgres' (not in list) should partially match 'postgresql'
    score, exact, partial = score_agent_capabilities(
        ["postgresql", "schema_design"],
        ["postgres"],
    )
    # 1 partial match / 1 required = 0.5 score
    assert score == 0.5
    assert len(exact) == 0
    assert len(partial) == 1
    assert partial[0] == ("postgres", "postgresql")


def test_route_task_no_requirements() -> None:
    # No requirements should route to all_rounder
    decision = route_task([])
    assert decision.agent_id == "all_rounder"
    assert decision.capability_score == 1.0
    assert "No specific capabilities were required" in decision.explanation

    decision_none = route_task(None)
    assert decision_none.agent_id == "all_rounder"
    assert decision_none.capability_score == 1.0


def test_route_task_specific_agent() -> None:
    # Requiring 'sql' should route to postgresql
    decision = route_task(["sql"])
    assert decision.agent_id == "postgresql"
    assert decision.capability_score == 1.0
    assert "Selected 'postgresql'" in decision.explanation

    # Requiring 'fastapi' should route to fastapi
    decision_fastapi = route_task(["fastapi"])
    assert decision_fastapi.agent_id == "fastapi"
    assert decision_fastapi.capability_score == 1.0


def test_route_task_tie_breaking() -> None:
    # If we require something that multiple agents support:
    # e.g., 'python' is supported by fastapi, streamlit, and all_rounder.
    # fastapi is specialized, medium cost.
    # streamlit is specialized, low cost.
    # all_rounder is generalist, high cost.
    # Therefore, streamlit should win due to being specialized and having the lowest cost.
    decision = route_task(["python"])
    assert decision.agent_id == "streamlit"
    assert decision.capability_score == 1.0
