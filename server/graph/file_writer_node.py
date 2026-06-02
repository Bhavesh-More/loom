from graph.state import LoomState
from tools.file_tools import ensure_workspace, write_all_outputs


def file_writer_node(state: LoomState) -> LoomState:
    """
    Takes all agent_outputs from state and writes them to disk.
    Creates outputs/<project-name>/ directory structure.
    Each agent gets its own subfolder: outputs/<project-name>/<agent-name>/
    Updates state['workspace_path'] with the resolved absolute path.
    """
    print("\n[FileWriter] Writing all agent outputs to disk...")

    project_name = state.get("project_name") or state.get("project_id", "unnamed-project")
    workspace_path = ensure_workspace(project_name)
    state["workspace_path"] = workspace_path

    print(f"[FileWriter] Workspace: {workspace_path}")

    agent_outputs = state.get("agent_outputs", {})

    if not agent_outputs:
        print("[FileWriter] No agent outputs to write.")
        return state

    results = write_all_outputs(agent_outputs, workspace_path)

    total_files = sum(len(paths) for paths in results.values())
    print(f"\n[FileWriter] Done. Written {total_files} file(s) across {len(results)} agent(s).")

    return state
