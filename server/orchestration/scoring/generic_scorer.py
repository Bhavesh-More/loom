from __future__ import annotations

from typing import Any

from orchestration.planning.plan_schema import AgentSpec, ScoringResult
from orchestration.scoring.check_registry import CheckRegistry, default_registry


class GenericConfidenceScorer:
    CORE_WEIGHT = 1.0
    CUSTOM_WEIGHT = 0.7

    def __init__(self, registry: CheckRegistry | None = None) -> None:
        self.registry = registry or default_registry

    async def score(
        self,
        agent_output: dict[str, Any],
        agent_plan_spec: AgentSpec,
        agent_manifest: dict[str, Any] | None = None,
    ) -> ScoringResult:
        agent_manifest = agent_manifest or {}
        check_names = list(dict.fromkeys(agent_plan_spec.scoring_checks + list(agent_manifest.get("custom_checks", []))))
        if not check_names:
            return ScoringResult(
                score=1.0,
                threshold=agent_plan_spec.confidence_threshold,
                passed=True,
                details=[],
                failed_checks=[],
            )

        total_weight = 0.0
        passed_weight = 0.0
        details: list[str] = []
        failed_checks: list[str] = []

        for check_name in check_names:
            check = self.registry.get_check(check_name)
            if check is None:
                total_weight += self.CORE_WEIGHT
                failed_checks.append(check_name)
                details.append(f"{check_name} (unknown): FAIL")
                continue
            check_fn, weight, source = check
            total_weight += weight
            try:
                passed = bool(check_fn(agent_output, agent_plan_spec))
            except Exception as exc:
                passed = False
                details.append(f"{check_name} ({source}): FAIL ({exc})")
            else:
                details.append(f"{check_name} ({source}): {'PASS' if passed else 'FAIL'}")
            if passed:
                passed_weight += weight
            else:
                failed_checks.append(check_name)

        score = passed_weight / total_weight if total_weight else 0.0
        threshold = agent_plan_spec.confidence_threshold
        return ScoringResult(
            score=round(score, 4),
            threshold=threshold,
            passed=score >= threshold,
            details=details,
            failed_checks=failed_checks,
        )
