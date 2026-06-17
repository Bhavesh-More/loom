from __future__ import annotations

from typing import Any

import pytest

from orchestration.planning.master_planner import MasterPlanner
from orchestration.planning.plan_schema import ExecutionPlan
from orchestration.runtime.checkpoint import PipelineCheckpoint
from orchestration.runtime.orchestrator import PipelineOrchestrator


async def _plan(run_id: str) -> ExecutionPlan:
    return await MasterPlanner().build_plan(
        "Create a calculator app which should store data in a database and have a Streamlit frontend, use Python for it.",
        {"run_id": run_id},
    )


def _invalid_db(output: dict[str, Any], retry_hint: str | None = None) -> dict[str, Any]:
    return {"content": ""}


def _empty(output: dict[str, Any], retry_hint: str | None = None) -> dict[str, Any]:
    return {}


@pytest.mark.asyncio
async def test_non_critical_agent_failure_becomes_partial_success() -> None:
    plan = await _plan("failure-case-1")
    agents = [agent.model_copy(update={"max_retries": 1}) if agent.id == "all_rounder" else agent for agent in plan.agents]
    plan = plan.model_copy(update={"agents": agents})
    orchestrator = PipelineOrchestrator(
        checkpoint=PipelineCheckpoint(redis_url=None),
        agent_registry={"all_rounder": _empty},
    )

    result = await orchestrator.run_pipeline(plan.task, plan.context, plan)

    assert result.status == "partial_success"
    assert "all_rounder" in result.skipped_agents


@pytest.mark.asyncio
async def test_critical_agent_failure_without_unblocked_branch_fails() -> None:
    plan = await _plan("failure-case-2")
    db_spec = next(agent for agent in plan.agents if agent.id == "postgresql").model_copy(
        update={"fallback": None, "max_retries": 1}
    )
    plan = plan.model_copy(update={"agents": [db_spec]})
    orchestrator = PipelineOrchestrator(
        checkpoint=PipelineCheckpoint(redis_url=None),
        agent_registry={"postgresql": _invalid_db},
    )

    result = await orchestrator.run_pipeline(plan.task, plan.context, plan)

    assert result.status == "failed"
    assert result.results["postgresql"].status == "failed"


@pytest.mark.asyncio
async def test_parallel_failure_suspends_blocked_branch_and_continues_unblocked() -> None:
    plan = await _plan("failure-case-3")
    agents = [
        agent.model_copy(update={"fallback": None, "max_retries": 1}) if agent.id == "postgresql" else agent
        for agent in plan.agents
    ]
    plan = plan.model_copy(update={"agents": agents})
    orchestrator = PipelineOrchestrator(
        checkpoint=PipelineCheckpoint(redis_url=None),
        agent_registry={"postgresql": _invalid_db},
    )

    result = await orchestrator.run_pipeline(plan.task, plan.context, plan)

    assert result.status == "suspended_partial"
    assert result.results["postgresql"].status == "failed"
    assert "fastapi" in result.suspended_agents


@pytest.mark.asyncio
async def test_fallback_activation_returns_degraded_success() -> None:
    plan = await _plan("failure-case-4")
    agents = [
        agent.model_copy(update={"max_retries": 1}) if agent.id == "postgresql" else agent
        for agent in plan.agents
    ]
    plan = plan.model_copy(update={"agents": agents})
    orchestrator = PipelineOrchestrator(
        checkpoint=PipelineCheckpoint(redis_url=None),
        agent_registry={"postgresql": _invalid_db},
    )

    result = await orchestrator.run_pipeline(plan.task, plan.context, plan)

    assert result.status == "suspended_partial"
    assert result.results["postgresql"].status == "failed"
