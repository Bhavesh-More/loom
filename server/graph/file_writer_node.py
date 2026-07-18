import os
import shutil
from graph.state import LoomState
from tools.file_tools import ensure_workspace
from sandbox.config import HOST_PROJECTS_ROOT

def file_writer_node(state: LoomState) -> LoomState:
    """
    Copies the generated files from the sandbox bind mount to the host outputs directory.
    Updates state['workspace_path'] with the resolved absolute path.
    """
    print("\n[FileWriter] Copying sandbox files to host outputs...")

    project_name = state.get("project_name") or state.get("project_id", "unnamed-project")
    project_id = state.get("project_id")
    
    workspace_path = ensure_workspace(project_name)
    state["workspace_path"] = workspace_path
    
    if not project_id:
        print("[FileWriter] No project_id found in state.")
        return state

    sandbox_path = os.path.join(HOST_PROJECTS_ROOT, project_id)
    
    if not os.path.exists(sandbox_path):
        print(f"[FileWriter] Sandbox path {sandbox_path} does not exist.")
        return state

    # Copy files from sandbox to outputs
    copied_count = 0
    try:
        for item in os.listdir(sandbox_path):
            s = os.path.join(sandbox_path, item)
            d = os.path.join(workspace_path, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
            copied_count += 1
        print(f"[FileWriter] Successfully copied {copied_count} items from sandbox to {workspace_path}")
    except Exception as e:
        error_msg = f"Failed to copy files from sandbox: {e}"
        print(f"[FileWriter] {error_msg}")
        state["errors"].append(error_msg)

    return state
