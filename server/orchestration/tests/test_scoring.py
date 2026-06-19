from __future__ import annotations

import time

import pytest

from orchestration.planning.master_planner import MasterPlanner
from orchestration.scoring.check_registry import CheckRegistry
from orchestration.scoring.custom_check_validator import CheckValidator
from orchestration.scoring.generic_scorer import GenericConfidenceScorer


@pytest.mark.asyncio
async def test_nullable_pk_scores_below_threshold() -> None:
    plan = await MasterPlanner().build_plan(
        "Create a calculator app which should store data in a database and have a Streamlit frontend, use Python for it.",
        {"run_id": "nullable-pk"},
    )
    db_spec = next(agent for agent in plan.agents if agent.id == "postgresql")
    output = {
        "content": "",
    }

    result = await GenericConfidenceScorer().score(output, db_spec, {})

    assert result.score < 0.85
    assert not result.passed
    assert "output_not_empty" in result.failed_checks


def valid_smtp_config(output, spec) -> bool:
    return True


def bad_os_check(output, spec) -> bool:
    import os

    return bool(os.name)


def slow_check(output, spec) -> bool:
    time.sleep(3)
    return True


@pytest.mark.asyncio
async def test_custom_check_registration_gates() -> None:
    registry = CheckRegistry()
    accepted, errors = await registry.register_custom_check("valid_smtp_config", valid_smtp_config, "email_agent")
    assert accepted
    assert errors == []

    accepted, errors = await registry.register_custom_check("bad_os_check", bad_os_check, "email_agent")
    assert not accepted
    assert "blocked module 'os'" in errors[0]

    accepted, errors = await registry.register_custom_check("slow_check", slow_check, "email_agent")
    assert not accepted
    assert "2 seconds" in errors[0]


def test_custom_check_signature_gate() -> None:
    def wrong_name(output, agent_spec) -> bool:
        return True

    valid, errors = CheckValidator().validate_custom_check(wrong_name, "agent")

    assert not valid
    assert errors == ["Custom check signature must be exactly (output, spec)"]
