"""
audit_route.py — REST API for the Loom semantic audit ledger.

Endpoints:
    GET /api/audit/{run_id}
        Returns all audit entries for the given pipeline run,
        ordered by creation time ascending.

    GET /api/audit/{run_id}/summary
        Returns a compact risk-annotated summary for the run:
        agent name → semantic change list + risk level.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, StrictStr

from orchestration.observability.audit_ledger import AuditLedger

router = APIRouter(prefix="/audit", tags=["audit"])
_ledger = AuditLedger()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class AuditEntryResponse(BaseModel):
    run_id: StrictStr
    agent_id: StrictStr
    task_description: StrictStr = ""
    files_changed: int = 0
    lines_changed: int = 0
    task_type: StrictStr = "uncategorized"
    risk_level: StrictStr = "low"
    within_budget: bool = True
    requires_approval: bool = False
    violation_reason: StrictStr | None = None
    integration_status: StrictStr = "pending"
    build_status: StrictStr = "unknown"
    validation_passed: bool = False
    confidence_score: float | None = None
    semantic_summary: list[StrictStr] = []
    created_at: StrictStr = ""


class RunAuditSummary(BaseModel):
    run_id: StrictStr
    total_agents: int
    total_files_changed: int
    total_lines_changed: int
    risk_distribution: dict[str, int]     # low/medium/high → count
    budget_violations: int
    requires_approval_count: int
    agents: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/{run_id}", response_model=list[AuditEntryResponse])
async def get_audit_entries(run_id: str) -> list[dict[str, Any]]:
    """
    Return all audit ledger entries for the given pipeline run.
    Entries are ordered chronologically (oldest first).
    """
    entries = await _ledger.get_entries(run_id)
    if not entries:
        raise HTTPException(
            status_code=404,
            detail=f"No audit entries found for run_id: {run_id}",
        )
    return entries


@router.get("/{run_id}/summary", response_model=RunAuditSummary)
async def get_audit_summary(run_id: str) -> RunAuditSummary:
    """
    Return a compact risk-annotated summary for the given run.
    Suitable for displaying in the frontend's SemanticChangeSummary panel.
    """
    entries = await _ledger.get_entries(run_id)
    if not entries:
        raise HTTPException(
            status_code=404,
            detail=f"No audit entries found for run_id: {run_id}",
        )

    risk_dist: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
    total_files = 0
    total_lines = 0
    violations = 0
    approval_needed = 0
    agents_summary: list[dict[str, Any]] = []

    for entry in entries:
        risk = entry.get("risk_level", "low")
        risk_dist[risk] = risk_dist.get(risk, 0) + 1
        total_files += entry.get("files_changed", 0)
        total_lines += entry.get("lines_changed", 0)
        if not entry.get("within_budget", True):
            violations += 1
        if entry.get("requires_approval", False):
            approval_needed += 1

        agents_summary.append({
            "agent_id": entry.get("agent_id", ""),
            "risk_level": risk,
            "semantic_summary": entry.get("semantic_summary", []),
            "files_changed": entry.get("files_changed", 0),
            "lines_changed": entry.get("lines_changed", 0),
            "within_budget": entry.get("within_budget", True),
            "confidence_score": entry.get("confidence_score"),
            "build_status": entry.get("build_status", "unknown"),
        })

    return RunAuditSummary(
        run_id=run_id,
        total_agents=len(entries),
        total_files_changed=total_files,
        total_lines_changed=total_lines,
        risk_distribution=risk_dist,
        budget_violations=violations,
        requires_approval_count=approval_needed,
        agents=agents_summary,
    )
