from __future__ import annotations

from orchestration.planning.plan_schema import AgentSpec, ExecutionPlan, ValidationResult


class PlanValidator:
    async def validate(self, plan: ExecutionPlan) -> ValidationResult:
        errors: list[str] = []
        agents = plan.agent_map()

        for agent in plan.agents:
            for dependency in agent.depends_on:
                if dependency not in agents:
                    errors.append(f"{agent.id}.depends_on references unknown agent '{dependency}'")

            for producer_id, fields in agent.consumes_from.items():
                producer = agents.get(producer_id)
                if producer is None:
                    errors.append(f"{agent.id}.consumes_from references unknown producer '{producer_id}'")
                    continue
                for field in fields:
                    if field not in producer.expected_output:
                        errors.append(
                            f"{agent.id} consumes '{field}' from {producer_id}, "
                            f"but {producer_id}.expected_output does not define it"
                        )

        for agent in plan.agents:
            if agent.fallback and agent.fallback in agents:
                fallback = agents[agent.fallback]
                errors.extend(self._validate_fallback_contract(agent, fallback))

        return ValidationResult(passed=not errors, errors=errors)

    def _validate_fallback_contract(self, original: AgentSpec, fallback: AgentSpec) -> list[str]:
        errors: list[str] = []
        for field_name, field_spec in original.expected_output.items():
            fallback_field = fallback.expected_output.get(field_name)
            if fallback_field is None:
                errors.append(
                    f"Fallback {fallback.id} for {original.id} is missing output field '{field_name}'"
                )
                continue
            if fallback_field.type != field_spec.type:
                errors.append(
                    f"Fallback {fallback.id}.{field_name} type '{fallback_field.type}' "
                    f"does not satisfy {original.id}.{field_name} type '{field_spec.type}'"
                )
        return errors
