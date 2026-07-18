from .manager import SandboxManager

mgr = SandboxManager()

def list_files(project_id: str, subpath: str = ".") -> list[str]:
    result = mgr.exec_run(project_id, ["find", subpath, "-type", "f", "-not", "-path", "*/.*"])
    if result["exit_code"] != 0:
        raise RuntimeError(result["stderr"])
    return [line for line in result["stdout"].splitlines() if line]

def read_file(project_id: str, path: str) -> str:
    result = mgr.exec_run(project_id, ["cat", path])
    if result["exit_code"] != 0:
        raise FileNotFoundError(f"{path}: {result['stderr']}")
    return result["stdout"]

def grep(project_id: str, pattern: str, subpath: str = ".") -> list[dict]:
    result = mgr.exec_run(project_id, ["grep", "-rn", pattern, subpath])
    matches = []
    for line in result["stdout"].splitlines():
        # format: path:line_number:content
        parts = line.split(":", 2)
        if len(parts) >= 3:
            matches.append({"path": parts[0], "line": int(parts[1]), "content": parts[2]})
    return matches

def write_new_file(project_id: str, path: str, content: str) -> None:
    """Use ONLY for files that do not yet exist. Agents must call list_files
    or try read_file first and confirm absence before calling this."""
    import base64
    encoded = base64.b64encode(content.encode()).decode()
    cmd = ["sh", "-c", f"mkdir -p $(dirname {path}) && echo {encoded} | base64 -d > {path}"]
    result = mgr.exec_run(project_id, cmd)
    if result["exit_code"] != 0:
        raise RuntimeError(result["stderr"])

def edit_file(project_id: str, path: str, old_str: str, new_str: str) -> None:
    """Diff-style edit — old_str MUST match exactly once in the file."""
    current = read_file(project_id, path)
    occurrences = current.count(old_str)
    if occurrences == 0:
        raise ValueError(f"old_str not found in {path}")
    if occurrences > 1:
        raise ValueError(f"old_str is not unique in {path} ({occurrences} matches)")
    updated = current.replace(old_str, new_str, 1)
    write_new_file(project_id, path, updated)

def run_command(project_id: str, cmd: list[str]) -> dict:
    """For pip install, running tests, restarting the app, etc."""
    return mgr.exec_run(project_id, cmd)


def create_folder_structure(project_id: str, dirs: list[str]) -> dict:
    """
    Pre-create a list of directories inside the sandbox workspace.

    Each path in `dirs` is relative to the sandbox workspace root.
    Uses `mkdir -p` so nested paths are created in a single call and
    the operation is idempotent (safe to call on already-existing dirs).

    Returns {"created": [...successfully created dirs...], "errors": [...]}
    """
    created = []
    errors = []
    for dir_path in dirs:
        # Strip any leading slashes — paths must be relative to workspace root
        safe_path = dir_path.lstrip("/")
        if not safe_path:
            continue
        result = mgr.exec_run(project_id, ["mkdir", "-p", safe_path])
        if result["exit_code"] == 0:
            created.append(safe_path)
        else:
            errors.append({"path": safe_path, "error": result.get("stderr", "unknown error")})
    return {"created": created, "errors": errors}

