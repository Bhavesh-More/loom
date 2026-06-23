import os
import re


# ---------------------------------------------------------------------------
# Agent → folder mapping
#
# Each entry defines exactly where an agent's files land inside the project:
#   "base"   : top-level section ("backend" or "frontend")
#   "subdir" : subfolder within that section (no agent name used)
#
# Final path: outputs/<project>/<base>/<subdir>/<filename>
# ---------------------------------------------------------------------------

AGENT_FOLDER_MAP: dict[str, dict[str, str]] = {
    # ── Data layer (backend/db/) ──────────────────────────────────────────
    "postgresql":     {"base": "backend", "subdir": "db"},
    "mongodb":        {"base": "backend", "subdir": "db"},
    "supabase":       {"base": "backend", "subdir": "db"},

    # ── Cache layer (backend/cache/) ─────────────────────────────────────
    "redis":          {"base": "backend", "subdir": "cache"},

    # ── API layer (backend/api/) ─────────────────────────────────────────
    "fastapi":        {"base": "backend", "subdir": "api"},

    # ── Auth layer (backend/auth/) ───────────────────────────────────────
    "auth":           {"base": "backend", "subdir": "auth"},

    # ── AI / ML layer (backend/ai/) ──────────────────────────────────────
    "rag":            {"base": "backend", "subdir": "ai"},
    "openai":         {"base": "backend", "subdir": "ai"},
    "langchain":      {"base": "backend", "subdir": "ai"},
    "langgraph":      {"base": "backend", "subdir": "ai"},

    # ── Scraper layer (backend/scraper/) ─────────────────────────────────
    "web_scraping":   {"base": "backend", "subdir": "scraper"},

    # ── Tests (backend/tests/) ───────────────────────────────────────────
    "pytest":         {"base": "backend", "subdir": "tests"},

    # ── Generic work (backend/misc/) ─────────────────────────────────────
    "all_rounder":    {"base": "backend", "subdir": "misc"},

    # ── Infrastructure (backend/infra/) ──────────────────────────────────
    "docker":         {"base": "backend", "subdir": "infra"},
    "github_actions": {"base": "backend", "subdir": "infra"},

    # ── Frontend (frontend/app/) ─────────────────────────────────────────
    "streamlit":      {"base": "frontend", "subdir": "app"},
}

# Fallback for any unknown agent
_DEFAULT_FOLDER = {"base": "backend", "subdir": "misc"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize_project_name(name: str) -> str:
    """Convert a project name to a safe folder name."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9\-_]", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")


def ensure_workspace(project_name: str, base_dir: str = "outputs") -> str:
    """
    Create outputs/<project-name>/ and return its absolute path.
    Does NOT pre-create backend/ or frontend/ — those are created on demand
    by write_agent_files so only used sections appear on disk.
    """
    safe_name      = sanitize_project_name(project_name)
    workspace_path = os.path.join(base_dir, safe_name)
    os.makedirs(workspace_path, exist_ok=True)
    return os.path.abspath(workspace_path)


def get_agent_target_dir(agent_name: str, workspace_path: str) -> str:
    """
    Return the absolute target directory for an agent's files.

    Example:
        agent_name    = "fastapi"
        workspace_path = "/server/outputs/task-manager"
        → "/server/outputs/task-manager/backend/api"
    """
    mapping = AGENT_FOLDER_MAP.get(agent_name, _DEFAULT_FOLDER)
    return os.path.join(workspace_path, mapping["base"], mapping["subdir"])


def parse_agent_output(raw_output: str) -> dict[str, str]:
    """
    Parse agent output that contains multiple files prefixed with:
        # FILE: <filename>
        <code content>

    Returns { filename: code_content }.
    Falls back to { "output.txt": raw_output } if no FILE markers found.
    """
    files: dict[str, str] = {}
    pattern = re.compile(r"#\s*FILE:\s*(.+?)\n(.*?)(?=\n#\s*FILE:|\Z)", re.DOTALL)
    matches = pattern.findall(raw_output)

    for filename, content in matches:
        filename = filename.strip()
        content  = content.strip()
        files[filename] = content

    if not matches:
        files["output.txt"] = raw_output.strip()

    return files


def write_agent_files(
    agent_name: str,
    raw_output: str,
    workspace_path: str,
) -> list[str]:
    """
    Parse the raw LLM output from an agent and write each file into
    the correct project subfolder as defined by AGENT_FOLDER_MAP.

    Structure example for agent "fastapi":
        outputs/<project>/backend/api/<filename>

    Returns a list of written absolute file paths.
    """
    target_dir = get_agent_target_dir(agent_name, workspace_path)
    os.makedirs(target_dir, exist_ok=True)

    files         = parse_agent_output(raw_output)
    written_paths = []

    for filename, content in files.items():
        # Agents can output nested filenames like routers/users.py
        full_path = os.path.join(target_dir, filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        written_paths.append(full_path)
        print(f"  [FileWriter] {agent_name} -> {os.path.relpath(full_path, workspace_path)}")

    return written_paths


def write_all_outputs(
    agent_outputs: dict[str, str],
    workspace_path: str,
) -> dict[str, list[str]]:
    """
    Write all agent outputs to the workspace using AGENT_FOLDER_MAP routing.
    Returns { agent_name: [written_file_paths] }.
    """
    results: dict[str, list[str]] = {}

    for agent_name, raw_output in agent_outputs.items():
        mapping = AGENT_FOLDER_MAP.get(agent_name, _DEFAULT_FOLDER)
        print(f"\n[FileWriter] {agent_name} -> {mapping['base']}/{mapping['subdir']}/")
        written          = write_agent_files(agent_name, raw_output, workspace_path)
        results[agent_name] = written

    return results
