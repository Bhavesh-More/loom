import os
import sys

# Make sure server/ root is on the path when running this file directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from orchestrator.runner import run_project

if __name__ == "__main__":
    final_state = run_project(
        project_name="task-manager",
        project_id="test-001",
        goal="""
            Build a simple task management app.
            Users can create, read, update and delete tasks.
            Each task has a title, description, status (todo/in-progress/done), and created_at timestamp.
            The backend should expose a REST API.
            The frontend should be a clean Streamlit UI that talks to the API.
        """,
        selected_agents=["supabase", "fastapi", "streamlit"],
    )

    print("\n--- Final State Summary ---")
    print(f"Workspace  : {final_state['workspace_path']}")
    print(f"Steps done : {final_state['current_step']} / {len(final_state['execution_plan'])}")
    print(f"Agents ran : {list(final_state['agent_outputs'].keys())}")
    if final_state["errors"]:
        print(f"Errors     : {final_state['errors']}")
    else:
        print("Errors     : None")