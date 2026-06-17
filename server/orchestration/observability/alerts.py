from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque


logger = logging.getLogger("loom.orchestration.alerts")
_critical_failures: dict[str, deque[float]] = defaultdict(deque)
WINDOW_SECONDS = 24 * 60 * 60


def critical_below_threshold(agent_id: str, run_id: str, score: float, threshold: float, attempt: int) -> None:
    if attempt != 1:
        return
    now = time.time()
    events = _critical_failures[agent_id]
    events.append(now)
    while events and now - events[0] > WINDOW_SECONDS:
        events.popleft()
    if len(events) >= 3:
        logger.error(
            json.dumps(
                {
                    "alert": "critical_agent_below_threshold_3x_24h",
                    "agent_id": agent_id,
                    "run_id": run_id,
                    "score": score,
                    "threshold": threshold,
                    "count_24h": len(events),
                }
            )
        )


def contract_validation_failed(run_id: str, producer_id: str, consumer_id: str, errors: list[str]) -> None:
    logger.error(
        json.dumps(
            {
                "alert": "contract_validation_failed",
                "run_id": run_id,
                "producer_id": producer_id,
                "consumer_id": consumer_id,
                "errors": errors,
            }
        )
    )
