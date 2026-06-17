from __future__ import annotations

from typing import Any

from orchestration.planning.plan_schema import Contract, ContractResult


class ContractValidator:
    async def validate(self, producer_output: dict[str, Any], contract: Contract) -> ContractResult:
        errors: list[str] = []
        available = set(producer_output.keys())
        for field in contract.required_fields:
            if field not in available:
                errors.append(
                    f"Contract violation {contract.producer_id}->{contract.consumer_id}: "
                    f"missing field '{field}'. Available fields: {sorted(available)}"
                )
        return ContractResult(passed=not errors, errors=errors)
