import ast
import os
import py_compile
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


def strip_wrapping_code_fence(content: str) -> str:
    """
    Remove markdown or triple-quote wrappers when the whole file is wrapped.
    Generated files must be written as executable source, not as chat markdown.
    """
    content = content.strip()
    fence_match = re.fullmatch(r"```[a-zA-Z0-9_+-]*\s*\n(.*?)\n?```", content, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    quote_match = re.fullmatch(r"'''[a-zA-Z0-9_+-]*\s*\n(.*?)\n?'''", content, re.DOTALL)
    if quote_match:
        return quote_match.group(1).strip()

    return content


def safe_output_filename(filename: str) -> str:
    """Keep agent-declared paths inside the agent's target directory."""
    normalized = os.path.normpath(filename.strip()).replace("\\", "/")
    if normalized.startswith("../") or normalized == ".." or os.path.isabs(normalized):
        return os.path.basename(normalized)
    return normalized


def parse_agent_output(raw_output: str, default_filename: str = "output.txt") -> dict[str, str]:
    """
    Parse agent output that contains multiple files prefixed with:
        # FILE: <filename>
        <code content>

    Returns { filename: code_content }.
    Falls back to { "output.txt": raw_output } if no FILE markers found.
    """
    raw_output = strip_wrapping_code_fence(raw_output)
    files: dict[str, str] = {}
    pattern = re.compile(r"#\s*FILE:\s*(.+?)\n(.*?)(?=\n#\s*FILE:|\Z)", re.DOTALL)
    matches = pattern.findall(raw_output)

    for filename, content in matches:
        filename = safe_output_filename(filename)
        content  = strip_wrapping_code_fence(content)
        files[filename] = content

    if not matches:
        files[default_filename] = strip_wrapping_code_fence(raw_output)

    return files


def default_filename_for_agent(agent_name: str) -> str:
    if agent_name == "streamlit":
        return "app.py"
    if agent_name in {"postgresql", "mongodb", "supabase"}:
        return "schema.sql"
    if agent_name in {"docker", "github_actions"}:
        return "output.yml"
    return "output.txt"


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

    files         = parse_agent_output(raw_output, default_filename_for_agent(agent_name))
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


def _is_session_state_attribute(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Attribute):
        return None
    value = node.value
    if (
        isinstance(value, ast.Attribute)
        and value.attr == "session_state"
        and isinstance(value.value, ast.Name)
        and value.value.id == "st"
    ):
        return node.attr
    if isinstance(value, ast.Name) and value.id == "session_state":
        return node.attr
    return None


def _session_state_keys_in_node(node: ast.AST) -> set[str]:
    keys: set[str] = set()
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Constant)
            and isinstance(child.value, str)
        ):
            keys.add(child.value)
    return keys


def _collect_session_state_writes(node: ast.AST) -> set[str]:
    writes: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Assign):
            for target in child.targets:
                attr_name = _is_session_state_attribute(target)
                if attr_name:
                    writes.add(attr_name)
                if (
                    isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Attribute)
                    and target.value.attr == "session_state"
                    and isinstance(target.slice, ast.Constant)
                    and isinstance(target.slice.value, str)
                ):
                    writes.add(target.slice.value)
        elif (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr == "setdefault"
            and isinstance(child.func.value, ast.Attribute)
            and child.func.value.attr == "session_state"
            and child.args
            and isinstance(child.args[0], ast.Constant)
            and isinstance(child.args[0].value, str)
        ):
            writes.add(child.args[0].value)
        elif isinstance(child, ast.If):
            writes.update(_session_state_keys_in_node(child.test))
    return writes


def _collect_session_state_reads(node: ast.AST) -> set[str]:
    reads: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, ast.Attribute) and isinstance(child.ctx, ast.Load):
            attr_name = _is_session_state_attribute(child)
            if attr_name:
                reads.add(attr_name)
        if (
            isinstance(child, ast.Subscript)
            and isinstance(child.ctx, ast.Load)
            and isinstance(child.value, ast.Attribute)
            and child.value.attr == "session_state"
            and isinstance(child.slice, ast.Constant)
            and isinstance(child.slice.value, str)
        ):
            reads.add(child.slice.value)
    return reads


def _is_streamlit_call(node: ast.AST, names: set[str]) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in names
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "st"
    )


def _validate_streamlit_app(files: dict[str, str], goal_or_task: str = "") -> list[str]:
    errors: list[str] = []
    app_source = files.get("app.py")
    requirements = files.get("requirements.txt", "")

    if not app_source:
        return ["Streamlit output must include # FILE: app.py."]
    if "requirements.txt" not in files:
        errors.append("Streamlit output must include # FILE: requirements.txt.")
    elif "streamlit" not in requirements.lower():
        errors.append("requirements.txt must include streamlit.")

    try:
        tree = ast.parse(app_source, filename="app.py")
    except SyntaxError as exc:
        return [f"app.py has invalid Python syntax: {exc.msg} at line {exc.lineno}."]

    if re.search(r"\bst\.listener\s*\(", app_source):
        errors.append("Streamlit has no st.listener API; remove fake keyboard listener code.")
    if re.search(r"\beval\s*\(", app_source):
        errors.append("Do not use Python eval() in generated calculator or Streamlit apps.")
    if "calculator" in goal_or_task.lower() and re.search(r"\bsimpleeval\b", app_source, re.IGNORECASE):
        errors.append("For calculator apps, avoid simpleeval and use a standard-library ast-based safe evaluator.")

    function_initializers = {
        statement.name: _collect_session_state_writes(statement)
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    initialized: set[str] = set()
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        reads = _collect_session_state_reads(statement)
        for key in sorted(reads - initialized):
            errors.append(
                f"st.session_state.{key} is read at module level before it is initialized."
            )
        initialized.update(_collect_session_state_writes(statement))
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
        ):
            initialized.update(function_initializers.get(statement.value.func.id, set()))

    for node in ast.walk(tree):
        if _is_streamlit_call(node, {"button", "form_submit_button"}):
            for keyword in node.keywords:
                if keyword.arg == "on_click" and isinstance(keyword.value, ast.Lambda):
                    errors.append("Do not pass lambda callbacks to Streamlit buttons; define named callback functions.")

    return errors


def validate_agent_files(
    agent_name: str,
    files: dict[str, str],
    goal_or_task: str = "",
) -> list[str]:
    """Return validation errors for parsed generated files before writing."""
    errors: list[str] = []
    for filename, content in files.items():
        if filename.endswith(".py"):
            try:
                ast.parse(content, filename=filename)
            except SyntaxError as exc:
                errors.append(f"{filename} has invalid Python syntax: {exc.msg} at line {exc.lineno}.")

    if agent_name == "streamlit":
        errors.extend(_validate_streamlit_app(files, goal_or_task))

    return errors


def validate_agent_output(agent_name: str, raw_output: str, goal_or_task: str = "") -> list[str]:
    files = parse_agent_output(raw_output, default_filename_for_agent(agent_name))
    return validate_agent_files(agent_name, files, goal_or_task)


def validate_written_files(
    paths: list[str],
    agent_name: str = "",
    goal_or_task: str = "",
) -> list[str]:
    """Return validation errors for generated files that cannot run as source."""
    errors: list[str] = []
    parsed_files: dict[str, str] = {}
    for path in paths:
        if path.endswith(".py"):
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"{os.path.relpath(path)} has invalid Python syntax: {exc.msg}")
        filename = os.path.basename(path)
        if filename in {"app.py", "requirements.txt"}:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    parsed_files[filename] = f.read()
            except OSError as exc:
                errors.append(f"Could not read generated file {os.path.relpath(path)}: {exc}")

    if agent_name == "streamlit" and parsed_files:
        errors.extend(_validate_streamlit_app(parsed_files, goal_or_task))
    return errors


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
