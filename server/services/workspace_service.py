import os
import io
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional

from tools.file_tools import sanitize_project_name

class WorkspaceService:
    def __init__(self, base_dir: str = "outputs"):
        self.base_dir = Path(base_dir)

    def get_workspace_path(self, project_name: str) -> Path:
        """Resolves to outputs/<sanitized-name>/ as an absolute path."""
        safe_name = sanitize_project_name(project_name)
        # Resolve to absolute path to prevent traversal bypasses
        return (self.base_dir / safe_name).resolve()

    def get_tree(self, project_name: str) -> List[Dict[str, Any]]:
        """Recursively walks the workspace dir and returns a nested tree structure."""
        root_path = self.get_workspace_path(project_name)
        
        if not root_path.exists() or not root_path.is_dir():
            return []

        def _build_tree(current_path: Path) -> List[Dict[str, Any]]:
            nodes = []
            try:
                # Sort folders first, then files, both alphabetically
                entries = sorted(
                    list(current_path.iterdir()),
                    key=lambda e: (not e.is_dir(), e.name.lower())
                )
            except OSError:
                return []

            for entry in entries:
                # Get path relative to the workspace root
                rel_path = entry.relative_to(root_path).as_posix()
                
                if entry.is_dir():
                    nodes.append({
                        "name": entry.name,
                        "path": rel_path,
                        "type": "directory",
                        "children": _build_tree(entry)
                    })
                else:
                    nodes.append({
                        "name": entry.name,
                        "path": rel_path,
                        "type": "file"
                    })
            return nodes

        return _build_tree(root_path)

    def read_file(self, project_name: str, relative_path: str) -> str:
        """Reads a file with path traversal protection using relative_to checks."""
        root_path = self.get_workspace_path(project_name)
        file_path = (root_path / relative_path).resolve()

        # Prevent directory traversal
        try:
            file_path.relative_to(root_path)
        except ValueError:
            raise ValueError("Path traversal attempt detected")

        if not file_path.exists():
            raise FileNotFoundError(f"File {relative_path} not found")
        
        if not file_path.is_file():
            raise ValueError(f"Path {relative_path} is not a file")

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def save_file(self, project_name: str, relative_path: str, content: str) -> None:
        """Writes content to a file with path traversal protection."""
        root_path = self.get_workspace_path(project_name)
        file_path = (root_path / relative_path).resolve()

        # Prevent directory traversal
        try:
            file_path.relative_to(root_path)
        except ValueError:
            raise ValueError("Path traversal attempt detected")

        # Ensure parent directories exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def download_zip(self, project_name: str) -> bytes:
        """Creates an in-memory ZIP of the entire workspace and returns the raw bytes."""
        root_path = self.get_workspace_path(project_name)
        if not root_path.exists():
            raise FileNotFoundError(f"Workspace for project '{project_name}' does not exist")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in root_path.rglob("*"):
                if file_path.is_file():
                    archive_name = file_path.relative_to(root_path).as_posix()
                    zip_file.write(file_path, archive_name)

        return zip_buffer.getvalue()
