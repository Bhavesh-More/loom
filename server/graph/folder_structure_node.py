"""
folder_structure_node.py — LangGraph node that plans and pre-creates the
project's directory skeleton before any Ollama executor agent runs.

Flow position:  planner  →  [folder_structure]  →  executor

What it does:
  1. Reads the architecture blueprint + execution plan already in state.
  2. Calls Groq (the fast planner-tier LLM) to produce the ideal directory
     tree as a JSON object  {"dirs": [...], "file_hints": {...}}.
  3. Pre-creates every listed directory inside the sandbox via mkdir -p.
  4. Stores the result in state["folder_structure"] so executor agents
     receive a concrete "Pre-created Project Structure" block in their prompt.
  5. Emits a structured execution log event for observability.

The node is intentionally non-blocking on partial failures — if some dirs
can't be created (e.g. sandbox not available), it logs the error and
continues rather than halting the whole pipeline.
"""

import json

from graph.llm_clients import get_groq_planner_llm
from graph.state import LoomState
from observability.execution_logger import log_execution_event
from sandbox.fs_tools import create_folder_structure

# ---------------------------------------------------------------------------
# System prompt for the folder-structure planning call
# ---------------------------------------------------------------------------

_FOLDER_STRUCTURE_SYSTEM_PROMPT = """
You are the Loom Project Structure Planner.

Your ONLY job is to produce the canonical directory layout for a software
project based on the architecture blueprint and execution plan provided.

## Output Rules
- Return ONLY valid JSON — no markdown, no preamble, no explanation.
- The JSON must have exactly two keys: "dirs" and "file_hints".
  - "dirs"       : a flat list of relative directory paths to pre-create.
  - "file_hints" : a dict mapping relative file paths to a one-line
                   description of what that file contains.
- Paths are relative to the project workspace root.  No leading slashes.
- Always include standard boilerplate dirs when relevant:
    backend/           → for any server-side Python project
    backend/api/       → for FastAPI route handlers
    backend/db/        → for database schemas and migration files
    backend/auth/      → for authentication logic
    backend/ai/        → for AI/ML/RAG modules
    backend/cache/     → for Redis or caching utilities
    backend/scraper/   → for web scraping modules
    backend/infra/     → for Docker and CI/CD files
    backend/tests/     → for test suites
    frontend/          → for any frontend (Streamlit, React, etc.)
    frontend/app/      → for Streamlit app files
- Add project-specific sub-dirs that match the blueprint (e.g. routers/,
  models/, schemas/, utils/) nested under the correct base dir.
- Do NOT include dirs for agents that are NOT part of the plan.
- Keep the list minimal but complete — no fantasy dirs.

## Example output for a FastAPI + PostgreSQL + Streamlit project
{
  "dirs": [
    "backend",
    "backend/api",
    "backend/api/routers",
    "backend/db",
    "frontend",
    "frontend/app"
  ],
  "file_hints": {
    "backend/api/main.py": "FastAPI application entry point",
    "backend/api/routers/items.py": "Items CRUD router",
    "backend/db/schema.sql": "PostgreSQL schema migrations",
    "backend/db/db.py": "asyncpg connection pool and query helpers",
    "frontend/app/app.py": "Streamlit UI entry point",
    "frontend/app/requirements.txt": "Frontend Python dependencies"
  }
}
""".strip()


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

async def folder_structure_node(state: LoomState) -> LoomState:
    """
    Plans the full project directory tree and pre-creates it in the sandbox.
    Runs after planner_node, before executor_node.
    """
    print("\n[FolderStructure] Planning project directory layout...")

    project_id   = state.get("project_id", "default")
    blueprint    = state.get("architecture_blueprint") or {}
    plan         = state.get("execution_plan", [])
    goal         = state.get("goal", "")

    # ── 1. Check if planner already gave us a project_structure ───────────────
    planner_structure = blueprint.get("project_structure", {})
    planner_dirs      = planner_structure.get("folders", [])
    planner_hints     = {
        f["path"]: f.get("description", "")
        for f in planner_structure.get("files", [])
        if isinstance(f, dict) and "path" in f
    }

    folder_structure: dict = {}

    if planner_dirs:
        # Planner already gave us the structure — reuse it directly
        print(f"[FolderStructure] Using {len(planner_dirs)} dirs from architecture blueprint.")
        folder_structure = {
            "dirs":       planner_dirs,
            "file_hints": planner_hints,
            "source":     "planner",
        }
    else:
        # ── 2. Ask Groq to plan the directory layout ──────────────────────────
        print("[FolderStructure] Querying Groq for directory layout...")

        plan_summary = json.dumps(
            [{"step": s.get("step"), "agent": s.get("agent"), "task": s.get("task", "")[:120]}
             for s in plan],
            indent=2,
        )

        user_message = f"""
Project Goal: {goal}

Architecture Overview:
{blueprint.get("architecture_overview", "N/A")}

Execution Plan (agents and tasks):
{plan_summary}

Produce the canonical directory layout for this project.
Return ONLY the JSON object with "dirs" and "file_hints" keys.
""".strip()

        try:
            llm = get_groq_planner_llm()
            messages = [
                {"role": "system", "content": _FOLDER_STRUCTURE_SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ]
            response = await llm.ainvoke(messages)
            raw = response.content.strip()

            # Strip <think>...</think> if present (Qwen3 thinking mode)
            if "<think>" in raw and "</think>" in raw:
                raw = raw[raw.index("</think>") + len("</think>"):].strip()

            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip().rstrip("```").strip()

            parsed = json.loads(raw)
            folder_structure = {
                "dirs":       parsed.get("dirs", []),
                "file_hints": parsed.get("file_hints", {}),
                "source":     "groq",
            }
            print(f"[FolderStructure] Groq returned {len(folder_structure['dirs'])} dirs.")

        except Exception as exc:
            print(f"[FolderStructure] Groq call failed ({exc}); falling back to AGENT_FOLDER_MAP defaults.")
            folder_structure = _fallback_structure_from_plan(plan)

    # ── 3. Pre-create directories in the sandbox ──────────────────────────────
    dirs_to_create = folder_structure.get("dirs", [])
    if dirs_to_create and project_id and project_id != "default":
        try:
            result = create_folder_structure(project_id, dirs_to_create)
            created_count = len(result.get("created", []))
            error_count   = len(result.get("errors", []))
            print(f"[FolderStructure] Created {created_count} dirs in sandbox"
                  f"{', ' + str(error_count) + ' errors' if error_count else ''}.")
            folder_structure["sandbox_result"] = result
        except Exception as exc:
            print(f"[FolderStructure] Sandbox mkdir failed ({exc}); agents will create dirs on demand.")
            folder_structure["sandbox_result"] = {"created": [], "errors": [str(exc)]}
    else:
        print("[FolderStructure] No project_id — skipping sandbox mkdir.")
        folder_structure["sandbox_result"] = {"created": [], "errors": []}

    state["folder_structure"] = folder_structure

    log_execution_event(
        "folder_structure.output",
        {
            "project_id":       project_id,
            "chat_session_id":  state.get("chat_session_id"),
            "dirs":             folder_structure.get("dirs", []),
            "source":           folder_structure.get("source", "unknown"),
            "sandbox_result":   folder_structure.get("sandbox_result", {}),
        },
    )

    print(f"[FolderStructure] Done. Dirs planned: {folder_structure.get('dirs', [])}")
    return state


# ---------------------------------------------------------------------------
# Fallback: derive sensible dirs from the plan using AGENT_FOLDER_MAP
# ---------------------------------------------------------------------------

def _fallback_structure_from_plan(plan: list[dict]) -> dict:
    """
    When Groq is unavailable, derive a sensible directory tree from the
    execution plan by mapping agent names through AGENT_FOLDER_MAP.
    """
    from tools.file_tools import AGENT_FOLDER_MAP, _DEFAULT_FOLDER

    dirs_set: set[str] = set()
    for step in plan:
        agent_name = step.get("agent", "")
        mapping    = AGENT_FOLDER_MAP.get(agent_name, _DEFAULT_FOLDER)
        base       = mapping["base"]
        subdir     = mapping["subdir"]
        dirs_set.add(base)
        dirs_set.add(f"{base}/{subdir}")

    return {
        "dirs":       sorted(dirs_set),
        "file_hints": {},
        "source":     "fallback",
    }
