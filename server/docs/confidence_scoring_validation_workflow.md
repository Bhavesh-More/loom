# Confidence Scoring & Validation Workflow

The orchestration package adds a quality-control layer before agent outputs are allowed to feed downstream agents.

## Where It Lives

- `server/orchestration/planning/` builds and validates `ExecutionPlan` objects.
- `server/orchestration/contracts/` derives and validates inter-agent handoff contracts.
- `server/orchestration/scoring/` runs reusable core checks and registered custom checks.
- `server/orchestration/runtime/` runs pipelines, checkpoints successful outputs, resumes runs, and handles failures.
- `server/api/routes/orchestration_route.py` exposes the workflow over FastAPI.

## Writing A Custom Check

Custom checks must be synchronous callables with exactly this signature:

```python
def valid_smtp_config(output, spec) -> bool:
    return isinstance(output.get("smtp_host"), str) and bool(output.get("smtp_port"))
```

Registration runs four gates:

1. Signature is exactly `(output, spec)`.
2. Return value is `bool`.
3. Source does not import `os`, `subprocess`, `socket`, `sys`, or `shutil`.
4. The check completes within 2 seconds.

Register checks through `CheckRegistry.register_custom_check(check_name, check_fn, agent_id)`.

## Registering A New Agent

Add an async callable that accepts `(inputs: dict, retry_hint: str | None) -> dict`, then pass it in the orchestrator registry:

```python
orchestrator = PipelineOrchestrator(
    agent_registry={"my_agent": my_agent_callable}
)
```

The agent behavior comes from its `AgentSpec` in the execution plan: dependencies, consumed fields, expected output, checks, thresholds, fallback, and retry count.

## Reading PipelineResult

`PipelineResult.status` is one of:

- `success`: every required agent passed.
- `partial_success`: non-critical work failed or was skipped.
- `suspended_partial`: a critical branch failed, but unblocked branches completed.
- `degraded_success`: a fallback agent satisfied the failed agent contract.
- `failed`: critical work failed and no useful unblocked branch remained.

`PipelineResult.results` is keyed by agent id. Each `AgentResult` includes status, attempts, score, checkpointed output, errors, and precise retry hints when validation failed.
