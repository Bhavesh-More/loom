import uuid
from graph import loom_graph, LoomState


def run_project(
    goal: str,
    selected_agents: list[str],
    project_name: str,
    project_id: str | None = None,
) -> LoomState:
    """
    Entry point to run a Loom project.

    Args:
        goal:             The user's project description / goal.
        selected_agents:  List of agent names selected by the user.
        project_name:     Human-readable project name (used for output folder).
        project_id:       Optional UUID. Auto-generated if not provided.

    Returns:
        The final LoomState after graph execution completes.
    """
    if project_id is None:
        project_id = str(uuid.uuid4())

    initial_state: LoomState = {
        "project_id":      project_id,
        "project_name":    project_name,
        "goal":            goal,
        "selected_agents": selected_agents,
        "execution_plan":  [],
        "current_step":    0,
        "agent_outputs":   {},
        "workspace_path":  "",
        "errors":          [],
    }

    print(f"\n{'='*60}")
    print(f"  LOOM — Starting project: {project_name}")
    print(f"  Project ID : {project_id}")
    print(f"  Agents     : {', '.join(selected_agents)}")
    print(f"  Goal       : {goal[:100]}{'...' if len(goal) > 100 else ''}")
    print(f"{'='*60}\n")

    final_state = loom_graph.invoke(initial_state)

    print(f"\n{'='*60}")
    print(f"  LOOM — Project complete!")
    print(f"  Workspace  : {final_state.get('workspace_path')}")
    if final_state.get("errors"):
        print(f"  Errors ({len(final_state['errors'])}):")
        for err in final_state["errors"]:
            print(f"    - {err}")
    print(f"{'='*60}\n")

    return final_state
