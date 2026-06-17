from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db.database import database
from orchestration.planning.plan_schema import ExecutionPlan, PipelineResult
from orchestration.runtime.checkpoint import PipelineCheckpoint
from orchestration.runtime.orchestrator import PipelineOrchestrator


router = APIRouter(prefix="/api/orchestration", tags=["Orchestration"])


class RunRequest(BaseModel):
    task: str
    context: dict[str, Any] = Field(default_factory=dict)


class RetryRequest(BaseModel):
    fix_description: str


@router.post("/run", response_model=PipelineResult)
async def run_orchestration(request: RunRequest) -> PipelineResult:
    orchestrator = PipelineOrchestrator()
    return await orchestrator.run_pipeline(request.task, request.context)


@router.get("/status/{run_id}")
async def get_orchestration_status(run_id: str) -> dict[str, Any]:
    conn = await database.get_conn()
    try:
        row = await conn.fetchrow(
            """
            SELECT run_id, task, status, plan_json, created_at, updated_at
            FROM pipeline_execution_plans
            WHERE run_id = $1
            """,
            run_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Pipeline run not found")
        return dict(row)
    finally:
        await database.release_conn(conn)


@router.get("/agent/{run_id}/{agent_id}/output")
async def get_agent_output(run_id: str, agent_id: str) -> dict[str, Any]:
    output = await PipelineCheckpoint().get_output(run_id, agent_id)
    if output is None:
        raise HTTPException(status_code=404, detail="Checkpointed output not found")
    return {"run_id": run_id, "agent_id": agent_id, "output": output}


@router.post("/retry/{run_id}", response_model=PipelineResult)
async def retry_orchestration(run_id: str, request: RetryRequest) -> PipelineResult:
    plan = await _load_plan(run_id)
    context = dict(plan.context)
    context["fix_description"] = request.fix_description
    plan = plan.model_copy(update={"context": context})
    orchestrator = PipelineOrchestrator()
    return await orchestrator.run_pipeline(plan.task, context, plan=plan)


async def _load_plan(run_id: str) -> ExecutionPlan:
    conn = await database.get_conn()
    try:
        row = await conn.fetchrow(
            "SELECT plan_json FROM pipeline_execution_plans WHERE run_id = $1",
            run_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Pipeline run not found")
        plan_json = row["plan_json"]
        if isinstance(plan_json, str):
            return ExecutionPlan.model_validate(json.loads(plan_json))
        return ExecutionPlan.model_validate(dict(plan_json))
    finally:
        await database.release_conn(conn)
