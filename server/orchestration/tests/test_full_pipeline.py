from __future__ import annotations

from typing import Any

import pytest

from orchestration.planning.master_planner import MasterPlanner
from orchestration.runtime.checkpoint import PipelineCheckpoint
from orchestration.runtime.orchestrator import PipelineOrchestrator


def _bad_db(inputs: dict[str, Any], retry_hint: str | None = None) -> dict[str, Any]:
    return {"content": ""}


def _fixed_db(inputs: dict[str, Any], retry_hint: str | None = None) -> dict[str, Any]:
    return {"content": "# FILE: schema.sql\nCREATE TABLE calculator_history (id uuid PRIMARY KEY);"}


@pytest.mark.asyncio
async def test_calculator_plan_is_valid_json_for_full_pipeline() -> None:
    plan = await MasterPlanner().build_plan(
        "Create a calculator app which should store data in a database and have a Streamlit frontend, use Python for it.",
        {"run_id": "calculator-plan"},
    )

    agent_ids = [agent.id for agent in plan.agents]
    assert agent_ids == ["postgresql", "fastapi", "streamlit", "all_rounder"]
    assert not {"db_agent", "python_agent", "backend_agent", "streamlit_agent", "readme_agent"} & set(agent_ids)
    assert next(agent for agent in plan.agents if agent.id == "postgresql").confidence_threshold == 0.85


@pytest.mark.asyncio
async def test_checkpoint_resume_skips_succeeded_python_agent_after_db_fix() -> None:
    run_id = "resume-after-db-fix"
    plan = await MasterPlanner().build_plan(
        "Create a calculator app which should store data in a database and have a Streamlit frontend, use Python for it.",
        {"run_id": run_id},
    )
    agents = [
        agent.model_copy(update={"fallback": None, "max_retries": 1}) if agent.id == "postgresql" else agent
        for agent in plan.agents
    ]
    plan = plan.model_copy(update={"agents": agents})
    checkpoint = PipelineCheckpoint(redis_url=None)
    calls = {"fastapi": 0}

    def counted_fastapi(inputs: dict[str, Any], retry_hint: str | None = None) -> dict[str, Any]:
        calls["fastapi"] += 1
        return {"content": "# FILE: main.py\nfrom fastapi import FastAPI\napp = FastAPI()"}

    first = await PipelineOrchestrator(
        checkpoint=checkpoint,
        agent_registry={"postgresql": _bad_db, "fastapi": counted_fastapi},
    ).run_pipeline(plan.task, plan.context, plan)

    assert first.status == "suspended_partial"
    assert calls["fastapi"] == 0

    second = await PipelineOrchestrator(
        checkpoint=checkpoint,
        agent_registry={"postgresql": _fixed_db, "fastapi": counted_fastapi},
    ).run_pipeline(plan.task, plan.context, plan)

    assert second.status == "success"
    assert calls["fastapi"] == 1
    assert second.results["fastapi"].status == "success"
