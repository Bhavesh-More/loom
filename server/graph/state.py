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
    context_payload: dict
    context_payload_text: str
    chat_session_id: str

    # Populated by the planner node when decomposition succeeds.
    # Stores the serialized TaskGraph dict and per-node agent selection logs.
    task_graph: Optional[dict]
    task_graph_logs: Optional[list[str]]

    # Optional UI theme passed from the frontend.
    # Contains design tokens like colors, button sizes, font families, etc.
    # Example: {"primary_color": "#6366f1", "button_radius": "8px", "font": "Inter"}
    theme: Optional[dict]

    # The full enriched architecture blueprint produced by the Planner.
    # Stored separately so the executor can reference it without re-parsing the plan list.
    architecture_blueprint: Optional[dict]

