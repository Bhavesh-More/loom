from __future__ import annotations

import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_FILE = LOG_DIR / "loom_context_runs.jsonl"
LOG_ENABLED = os.getenv("LOOM_CONTEXT_LOGS", "").lower() in {"1", "true", "yes", "on"}
MAX_FIELD_CHARS = 120_000


def _logger() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("loom.execution_trace")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not LOG_ENABLED:
        return logger
    if not logger.handlers:
        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    return logger


def compact(value: Any, limit: int = MAX_FIELD_CHARS) -> Any:
    """Keep trace logs useful without allowing huge LLM payloads to explode disk usage."""
    if isinstance(value, str):
        if len(value) <= limit:
            return value
        return value[:limit] + f"\n...[truncated {len(value) - limit} chars]"
    if isinstance(value, list):
        return [compact(item, limit) for item in value]
    if isinstance(value, dict):
        return {key: compact(item, limit) for key, item in value.items()}
    return value


def log_execution_event(tag: str, payload: dict[str, Any]) -> None:
    if not LOG_ENABLED:
        return
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tag": tag,
        **compact(payload),
    }
    _logger().info(json.dumps(record, default=str, ensure_ascii=False))
