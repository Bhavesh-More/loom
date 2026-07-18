from langchain_core.tools import tool
from sandbox.fs_tools import list_files, read_file, grep, write_new_file, edit_file, run_command, create_folder_structure
from sandbox.manifest import load_manifest, register_file

@tool
def tool_list_files(project_id: str, subpath: str = ".") -> list[str]:
    """List all files in the project workspace. ALWAYS call this before
    creating or editing any file, to see what already exists."""
    return list_files(project_id, subpath)

@tool
def tool_read_file(project_id: str, path: str) -> str:
    """Read the full contents of an existing file."""
    return read_file(project_id, path)

@tool
def tool_grep(project_id: str, pattern: str, subpath: str = ".") -> list[dict]:
    """Search file contents for a pattern across the project."""
    return grep(project_id, pattern, subpath)

@tool
def tool_edit_file(project_id: str, path: str, old_str: str, new_str: str) -> str:
    """Make a targeted edit to an EXISTING file by replacing an exact snippet.
    Use this instead of rewriting a whole file whenever the file already exists."""
    edit_file(project_id, path, old_str, new_str)
    return "edit applied"

@tool
def tool_write_new_file(project_id: str, path: str, content: str, responsibility: str) -> str:
    """Create a brand-new file. Only use when tool_list_files confirms this
    path does not already exist. `responsibility` is a one-line description
    of what this file is for — it will be recorded in the project manifest."""
    write_new_file(project_id, path, content)
    register_file(project_id, path, responsibility)
    return "file created"

@tool
def tool_get_manifest(project_id: str) -> dict:
    """Return the current project architecture manifest — file list and
    each file's responsibility, plus recorded conventions."""
    return load_manifest(project_id)

@tool
def tool_run_command(project_id: str, cmd: list[str]) -> dict:
    """Run a shell command inside the project sandbox (e.g. pip install, pytest)."""
    return run_command(project_id, cmd)

@tool
def tool_create_folder_structure(project_id: str, dirs: list[str]) -> dict:
    """Pre-create a list of directories inside the project sandbox workspace.
    Each path must be relative to the workspace root (e.g. 'backend/api').
    This is idempotent — safe to call on already-existing directories."""
    return create_folder_structure(project_id, dirs)

