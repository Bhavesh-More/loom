"""
theme_route.py — Theme discovery and content API.

Scans server/themes/*.md at request time so newly added theme files
are immediately available without a server restart.
"""
from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Resolve the themes directory relative to this file:
# server/api/routes/theme_route.py → server/themes/
_THEMES_DIR = Path(__file__).parent.parent.parent / "themes"

router = APIRouter(prefix="/themes", tags=["Themes"])


class ThemeMetadata(BaseModel):
    id: str           # stem of the filename, e.g. "theme_claude"
    name: str         # human-readable name from frontmatter
    description: str  # short description from frontmatter
    filename: str     # e.g. "theme_claude.md"


def _parse_frontmatter(content: str) -> dict[str, str]:
    """
    Extract key: value pairs from the leading YAML-ish frontmatter block.
    Supports the format:
      ---
      key: value
      ...
    Returns an empty dict when no frontmatter is found.
    """
    stripped = content.lstrip()
    if not stripped.startswith("---"):
        return {}

    # Find the closing ---
    end = stripped.find("---", 3)
    if end == -1:
        return {}

    frontmatter_block = stripped[3:end]
    result: dict[str, str] = {}
    for line in frontmatter_block.splitlines():
        m = re.match(r"^(\w[\w\-]*)\s*:\s*(.+)$", line.strip())
        if m:
            key, value = m.group(1), m.group(2).strip()
            # Strip surrounding quotes if present
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            result[key] = value
    return result


def _load_theme_metadata(path: Path) -> ThemeMetadata:
    """Read a single theme file and return its metadata."""
    content = path.read_text(encoding="utf-8")
    fm = _parse_frontmatter(content)

    theme_id = path.stem  # e.g. "theme_claude"
    name = fm.get("name") or theme_id.replace("_", " ").title()
    description = fm.get("description", "")

    return ThemeMetadata(
        id=theme_id,
        name=name,
        description=description,
        filename=path.name,
    )


@router.get("", response_model=list[ThemeMetadata])
async def list_themes() -> list[ThemeMetadata]:
    """
    Discover and return all available themes from the themes directory.
    Scans the directory at request time — drop a new .md file and it
    appears immediately without restarting the server.
    """
    if not _THEMES_DIR.exists():
        return []

    themes: list[ThemeMetadata] = []
    for path in sorted(_THEMES_DIR.glob("*.md")):
        try:
            themes.append(_load_theme_metadata(path))
        except Exception:
            # Skip unreadable or malformed files gracefully
            continue

    return themes


@router.get("/{theme_id}/content")
async def get_theme_content(theme_id: str) -> dict[str, str]:
    """
    Return the full raw Markdown content of a theme file.
    Used internally by the prompt-construction pipeline and exposed
    here for transparency/debugging.
    """
    if not _THEMES_DIR.exists():
        raise HTTPException(status_code=404, detail="Themes directory not found")

    path = _THEMES_DIR / f"{theme_id}.md"
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Theme '{theme_id}' not found")

    content = path.read_text(encoding="utf-8")
    return {"theme_id": theme_id, "content": content}
