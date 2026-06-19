from __future__ import annotations

from dataclasses import dataclass, field

from orchestration.planning.plan_schema import AgentResult, ExecutionPlan, PipelineStatus
from orchestration.runtime.cascade import get_cascade_impact


@dataclass(frozen=True)
class FailureDecision:
    status: PipelineStatus
    suspended_agents: list[str] = field(default_factory=list)
    skipped_agents: list[str] = field(default_factory=list)
    continue_pipeline: bool = True
    degraded: bool = False


class FailureHandler:
    def decide(
        self,
        failed_agent_id: str,
        plan: ExecutionPlan,
        results: dict[str, AgentResult],
        fallback_activated: bool = False,
    ) -> FailureDecision:
        agent = plan.agent_map()[failed_agent_id]

        if fallback_activated and plan.failure_policy.fallback_activation == "degraded_success":
            return FailureDecision(status="degraded_success", degraded=True, continue_pipeline=True)

        if not agent.critical and plan.failure_policy.non_critical_failure == "skip_continue":
            return FailureDecision(
                status="partial_success",
                skipped_agents=[failed_agent_id],
                continue_pipeline=True,
            )

        impacted = get_cascade_impact(failed_agent_id, plan)
        downstream_ran = any(
            results.get(agent_id) is not None and results[agent_id].status in {"success", "fallback_success"}
            for agent_id in impacted
        )
        unblocked = self._unblocked_pending_agents(failed_agent_id, impacted, plan, results)

        if agent.critical and not downstream_ran and not unblocked:
            return FailureDecision(
                status="failed",
                suspended_agents=impacted,
                continue_pipeline=False,
            )

        if agent.critical and unblocked and plan.failure_policy.critical_failure_with_unblocked_siblings:
            return FailureDecision(
                status="suspended_partial",
                suspended_agents=impacted,
                continue_pipeline=True,
            )

        return FailureDecision(status="failed", suspended_agents=impacted, continue_pipeline=False)

    def _unblocked_pending_agents(
        self,
        failed_agent_id: str,
        impacted: list[str],
        plan: ExecutionPlan,
        results: dict[str, AgentResult],
    ) -> list[str]:
        blocked = set(impacted) | {failed_agent_id}
        successful = {
            agent_id
            for agent_id, result in results.items()
            if result.status in {"success", "fallback_success"}
        }
        unblocked: list[str] = []
        for agent in plan.agents:
            if agent.id in blocked or agent.id in results:
                continue
            if all(dependency in successful for dependency in agent.depends_on):
                unblocked.append(agent.id)
        return unblocked
