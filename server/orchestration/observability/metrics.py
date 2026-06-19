from __future__ import annotations

import json
import logging
from typing import Any


logger = logging.getLogger("loom.orchestration.metrics")


def emit_metric(name: str, value: float | int | str, labels: dict[str, Any] | None = None) -> None:
    logger.info(
        json.dumps(
            {
                "metric": name,
                "value": value,
                "labels": labels or {},
            },
            default=str,
        )
    )


def agent_score(run_id: str, agent_id: str, score: float) -> None:
    emit_metric("agent_score", score, {"run_id": run_id, "agent_id": agent_id})


def threshold_delta(run_id: str, agent_id: str, delta: float) -> None:
    emit_metric("threshold_delta", delta, {"run_id": run_id, "agent_id": agent_id})


def contract_violations_total(run_id: str, agent_id: str, count: int) -> None:
    emit_metric("contract_violations_total", count, {"run_id": run_id, "agent_id": agent_id})


def retries_per_agent(run_id: str, agent_id: str, count: int) -> None:
    emit_metric("retries_per_agent", count, {"run_id": run_id, "agent_id": agent_id})


def pipeline_status(run_id: str, status: str) -> None:
    emit_metric("pipeline_status", status, {"run_id": run_id})


def fallback_activations_total(run_id: str, agent_id: str, count: int) -> None:
    emit_metric("fallback_activations_total", count, {"run_id": run_id, "agent_id": agent_id})
