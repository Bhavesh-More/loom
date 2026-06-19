from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt, StrictStr

from orchestration.planning.task_graph import TaskGraph


FieldType = Literal["str", "int", "float", "bool", "list", "dict", "any"]
PipelineStatus = Literal[
    "pending",
    "running",
    "success",
    "partial_success",
    "suspended_partial",
    "degraded_success",
    "failed",
]


class ExpectedOutputField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: FieldType
    required: StrictBool = True
    nullable: StrictBool = False
    min_length: StrictInt | None = None
    description: StrictStr | None = None


class FailurePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_retries: StrictInt = Field(default=3, ge=1)
    non_critical_failure: Literal["skip_continue"] = "skip_continue"
    critical_failure_no_downstream: Literal["fail_checkpoint_prior"] = "fail_checkpoint_prior"
    critical_failure_with_unblocked_siblings: Literal["suspend_blocked_continue_unblocked"] = (
        "suspend_blocked_continue_unblocked"
    )
    fallback_activation: Literal["degraded_success"] = "degraded_success"


class AgentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: StrictStr
    role: StrictStr
    task: StrictStr
    critical: StrictBool
    depends_on: list[StrictStr] = Field(default_factory=list)
    consumes_from: dict[StrictStr, list[StrictStr]] = Field(default_factory=dict)
    expected_output: dict[StrictStr, ExpectedOutputField]
    scoring_checks: list[StrictStr]
    confidence_threshold: StrictFloat = Field(ge=0.0, le=1.0)
    fallback: StrictStr | None = None
    max_retries: StrictInt = Field(default=3, ge=1)


class ExecutionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: StrictStr
    task: StrictStr
    context: dict[StrictStr, Any] = Field(default_factory=dict)
    agents: list[AgentSpec]
    failure_policy: FailurePolicy = Field(default_factory=FailurePolicy)
    status: PipelineStatus = "pending"
    task_graph: TaskGraph | None = Field(default=None, description="The hierarchical task graph for orchestration")

    def agent_map(self) -> dict[str, AgentSpec]:
        return {agent.id: agent for agent in self.agents}


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: StrictBool
    errors: list[StrictStr] = Field(default_factory=list)


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    producer_id: StrictStr
    consumer_id: StrictStr
    required_fields: list[StrictStr]


class ContractResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: StrictBool
    errors: list[StrictStr] = Field(default_factory=list)


class ScoringResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: StrictFloat
    threshold: StrictFloat
    passed: StrictBool
    details: list[StrictStr] = Field(default_factory=list)
    failed_checks: list[StrictStr] = Field(default_factory=list)


class AgentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: StrictStr
    status: Literal["pending", "success", "failed", "skipped", "suspended", "fallback_success"]
    output: dict[StrictStr, Any] | None = None
    score: StrictFloat | None = None
    attempts: StrictInt = 0
    errors: list[StrictStr] = Field(default_factory=list)
    retry_hint: StrictStr | None = None


class PipelineResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: StrictStr
    status: PipelineStatus
    plan: ExecutionPlan
    results: dict[StrictStr, AgentResult] = Field(default_factory=dict)
    suspended_agents: list[StrictStr] = Field(default_factory=list)
    skipped_agents: list[StrictStr] = Field(default_factory=list)
    errors: list[StrictStr] = Field(default_factory=list)
