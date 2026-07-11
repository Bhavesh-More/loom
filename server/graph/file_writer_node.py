from graph.state import LoomState
from tools.file_tools import ensure_workspace, validate_written_files, write_all_outputs


def file_writer_node(state: LoomState) -> LoomState:
    """
    Takes all agent_outputs from state and writes them to disk.

    Folder structure (defined in tools/file_tools.py AGENT_FOLDER_MAP):
        outputs/<project-name>/
            backend/
                api/          ← fastapi
                db/           ← postgresql, mongodb, supabase
                cache/        ← redis
                auth/         ← auth
                ai/           ← rag, openai, langchain, langgraph
                scraper/      ← web_scraping
                tests/        ← pytest
                infra/        ← docker, github_actions
            frontend/
                app/          ← streamlit

    Updates state['workspace_path'] with the resolved absolute path.
    """
    print("\n[FileWriter] Writing all agent outputs to disk...")

    project_name   = state.get("project_name") or state.get("project_id", "unnamed-project")
    workspace_path = ensure_workspace(project_name)
    state["workspace_path"] = workspace_path

    print(f"[FileWriter] Workspace: {workspace_path}")

    agent_outputs = state.get("agent_outputs", {})

    if not agent_outputs:
        print("[FileWriter] No agent outputs to write.")
        return state

    results = write_all_outputs(agent_outputs, workspace_path)
    validation_errors = []
    for agent_name, paths in results.items():
        validation_errors.extend(
            validate_written_files(
                paths,
                agent_name=agent_name,
                goal_or_task=state.get("goal", ""),
            )
        )
    if validation_errors:
        state["errors"].extend(validation_errors)
        for error in validation_errors:
            print(f"[FileWriter] Validation error: {error}")

    total_files = sum(len(paths) for paths in results.values())
    print(f"\n[FileWriter] Done. Written {total_files} file(s) across {len(results)} agent(s).")

    return state
