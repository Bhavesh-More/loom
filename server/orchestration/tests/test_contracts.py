from __future__ import annotations

import pytest

from orchestration.contracts.contract_builder import ContractBuilder
from orchestration.contracts.contract_validator import ContractValidator
from orchestration.planning.master_planner import MasterPlanner
from orchestration.planning.plan_validator import PlanValidator


@pytest.mark.asyncio
async def test_contract_validator_catches_field_name_mismatch() -> None:
    plan = await MasterPlanner().build_plan(
        "Create a calculator app which should store data in a database and have a Streamlit frontend, use Python for it.",
        {"run_id": "contracts-mismatch"},
    )
    contract = next(
        item
        for item in ContractBuilder().build(plan)
        if item.producer_id == "postgresql" and item.consumer_id == "fastapi"
    )

    result = await ContractValidator().validate(
        {"table_name": "calculator_history"},
        contract,
    )

    assert not result.passed
    assert "missing field 'content'" in result.errors[0]


@pytest.mark.asyncio
async def test_plan_validator_rejects_unknown_consumed_field() -> None:
    plan = await MasterPlanner().build_plan(
        "Create a calculator app which should store data in a database and have a Streamlit frontend, use Python for it.",
        {"run_id": "invalid-plan"},
    )
    fastapi = next(agent for agent in plan.agents if agent.id == "fastapi")
    updated_fastapi = fastapi.model_copy(update={"consumes_from": {"postgresql": ["unknown_field"]}})
    updated_agents = [updated_fastapi if agent.id == "fastapi" else agent for agent in plan.agents]
    invalid_plan = plan.model_copy(update={"agents": updated_agents})

    result = await PlanValidator().validate(invalid_plan)

    assert not result.passed
    assert "postgresql.expected_output does not define it" in result.errors[0]
