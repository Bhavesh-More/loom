import os
import re


def sanitize_project_name(name: str) -> str:
    """Convert project name to a safe folder name."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9\-_]", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")


def ensure_workspace(project_name: str, base_dir: str = "outputs") -> str:
    """
    Create outputs/<project-name>/ directory if it doesn't exist.
    Returns the absolute path to the project workspace.
    """
    safe_name = sanitize_project_name(project_name)
    workspace_path = os.path.join(base_dir, safe_name)
    os.makedirs(workspace_path, exist_ok=True)
    return os.path.abspath(workspace_path)


def parse_agent_output(raw_output: str) -> dict[str, str]:
    """
    Parse agent output that contains multiple files prefixed with:
        # FILE: <filename>
        <code content>

    Returns a dict of { filename: code_content }
    """
    files: dict[str, str] = {}
    pattern = re.compile(r"#\s*FILE:\s*(.+?)\n(.*?)(?=\n#\s*FILE:|\Z)", re.DOTALL)
    matches = pattern.findall(raw_output)

    for filename, content in matches:
        filename = filename.strip()
        content = content.strip()
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
    Parse the raw LLM output from an agent and write each file
    into workspace_path/<agent_name>/.

    Returns a list of written file paths.
    """
    agent_dir = os.path.join(workspace_path, agent_name)
    os.makedirs(agent_dir, exist_ok=True)

    files = parse_agent_output(raw_output)
    written_paths = []

    for filename, content in files.items():
        # Support nested paths like routers/users.py
        full_path = os.path.join(agent_dir, filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        written_paths.append(full_path)
        print(f"  [FileWriter] Written: {full_path}")

    return written_paths


def write_all_outputs(
    agent_outputs: dict[str, str],
    workspace_path: str,
) -> dict[str, list[str]]:
    """
    Write all agent outputs to workspace.
    Returns a dict of { agent_name: [written_file_paths] }
    """
    results: dict[str, list[str]] = {}

    for agent_name, raw_output in agent_outputs.items():
        print(f"\n[FileWriter] Writing files for agent: {agent_name}")
        written = write_agent_files(agent_name, raw_output, workspace_path)
        results[agent_name] = written

    return results
