from typing import TypedDict, Optional


class LoomState(TypedDict):
    project_id: str
    project_name: str
    goal: str
    selected_agents: list[str]
    execution_plan: list[dict]
    current_step: int
    agent_outputs: dict[str, str]
    workspace_path: str
    errors: list[str]
