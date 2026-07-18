import json
from .fs_tools import read_file, write_new_file, mgr

MANIFEST_PATH = ".agent_manifest.json"

def load_manifest(project_id: str) -> dict:
    try:
        raw = read_file(project_id, MANIFEST_PATH)
        return json.loads(raw)
    except FileNotFoundError:
        return {"files": {}, "conventions": []}

def save_manifest(project_id: str, manifest: dict) -> None:
    current_exists = True
    try:
        read_file(project_id, MANIFEST_PATH)
    except FileNotFoundError:
        current_exists = False
    
    content = json.dumps(manifest, indent=2)
    if current_exists:
        # overwrite via exec since this file is machine-managed, not agent-edited
        import base64
        encoded = base64.b64encode(content.encode()).decode()
        mgr.exec_run(project_id, ["sh", "-c", f"echo {encoded} | base64 -d > {MANIFEST_PATH}"])
    else:
        write_new_file(project_id, MANIFEST_PATH, content)

def register_file(project_id: str, path: str, responsibility: str) -> None:
    manifest = load_manifest(project_id)
    manifest["files"][path] = responsibility
    save_manifest(project_id, manifest)
