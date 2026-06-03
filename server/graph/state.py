from typing import TypedDict, Optional


class LoomState(TypedDict):
    project_id: str
    project_name: str
    goal: str

    # All agents attached to this project (the full team)
    selected_agents: list[str]

    # Agents the router decided are actually needed for THIS query.
    # For "generate frontend" this would be ["streamlit"] only.
    # For full codegen it mirrors selected_agents.
    active_agents: list[str]

    # "qa" → skip codegen, return qa_response directly
    # "codegen" → run planner → executor → file_writer
    query_type: str

    # Populated by the QA node when query_type == "qa"
    qa_response: str

    execution_plan: list[dict]
    current_step: int
    agent_outputs: dict[str, str]
    workspace_path: str
    errors: list[str]
