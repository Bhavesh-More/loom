"""
ponytail_adapter.py — Injects Ponytail's minimal-code philosophy into Loom agent prompts.

Reads the Ponytail SKILL.md from the ponytail sub-project and returns a
mode-filtered context string that is prepended to every agent system prompt.

Usage:
    from orchestration.agents.ponytail_adapter import get_ponytail_preamble
    system_prompt = get_ponytail_preamble() + FASTAPI_SYSTEM_PROMPT
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from functools import lru_cache

# ---------------------------------------------------------------------------
# Locate the ponytail skills directory relative to common repository layouts.
# Priority order:
#   1. PONYTAIL_SKILLS_DIR environment variable (absolute path to skills dir)
#   2. Sibling directory: ../../ponytail/skills/ponytail/SKILL.md
#   3. Inline fallback ruleset (always works, even without the ponytail repo)
# ---------------------------------------------------------------------------

_INLINE_FALLBACK = """\
## Ponytail Minimal-Code Rules (ACTIVE)

You are a lazy senior developer. Lazy means efficient, not careless.
The best code is the code never written.

### The Ladder — stop at the first rung that holds:
1. Does this need to exist at all? Speculative need = skip it. (YAGNI)
2. Already in this codebase? Reuse it. Look before writing.
3. Stdlib does it? Use it.
4. Native platform feature covers it? Use it.
5. Already-installed dependency solves it? Use it. Never add a new dep.
6. Can it be one line? One line.
7. Only then: the minimum code that works.

### Rules (mandatory):
- No unrequested abstractions: no interface with one implementation,
  no factory for one product, no config for a value that never changes.
- No boilerplate, no scaffolding "for later".
- Deletion over addition. Boring over clever.
- Fewest files possible. Shortest working diff wins.
- Mark deliberate simplifications: `# ponytail: <reason>`

### Never simplify away:
- Input validation at trust boundaries
- Error handling that prevents data loss
- Security measures and accessibility
- Anything explicitly requested

### Output format:
Produce only the code changes needed. Use SEARCH/REPLACE blocks for
modifications to existing files. Prefer targeted diffs over whole-file rewrites.
If you must create a new file, produce only what the task requires — no
extra modules, no placeholder files.
"""


def _find_skill_file() -> Path | None:
    """Locate the ponytail SKILL.md from environment or relative path."""
    # Environment override
    env_dir = os.environ.get("PONYTAIL_SKILLS_DIR")
    if env_dir:
        candidate = Path(env_dir) / "ponytail" / "SKILL.md"
        if candidate.exists():
            return candidate

    # Sibling repo layout: server/ → ../../ponytail/skills/ponytail/SKILL.md
    here = Path(__file__).resolve()
    # Walk up from: server/orchestration/agents/ponytail_adapter.py
    # → server/orchestration/agents → server/orchestration → server → loom → Projects/loom
    for parent in here.parents:
        candidate = parent / "ponytail" / "skills" / "ponytail" / "SKILL.md"
        if candidate.exists():
            return candidate

    return None


def _strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter block from skill markdown."""
    return re.sub(r"^---[\s\S]*?---\s*", "", text, count=1)


def _extract_core_rules(body: str) -> str:
    """Extract the essential sections from SKILL.md (ladder + rules + output)."""
    stripped = _strip_frontmatter(body)
    # Keep everything — the full skill is valuable as agent guidance
    return stripped.strip()


@lru_cache(maxsize=1)
def _load_ponytail_skill() -> str:
    """Load and cache the Ponytail skill text (file or inline fallback)."""
    skill_file = _find_skill_file()
    if skill_file is not None:
        try:
            raw = skill_file.read_text(encoding="utf-8")
            return _extract_core_rules(raw)
        except OSError:
            pass
    return _INLINE_FALLBACK


def get_ponytail_preamble(mode: str = "full") -> str:
    """
    Return the Ponytail minimal-code context to prepend to any agent prompt.

    Args:
        mode: Intensity level — "lite", "full" (default), "ultra".
              - lite:  add one-liner note about lazier alternatives.
              - full:  enforce the full ladder (recommended).
              - ultra: YAGNI extremist, deletion before addition.
              - off:   return empty string (no ponytail rules injected).

    Returns:
        Formatted string ready to be prepended to a system prompt.
    """
    if mode == "off":
        return ""

    skill_body = _load_ponytail_skill()

    header_lines = {
        "lite": "## Ponytail Guidance — Level: LITE (suggest minimal alternatives)",
        "full": "## Ponytail Guidance — Level: FULL (minimal-code ladder enforced)",
        "ultra": "## Ponytail Guidance — Level: ULTRA (YAGNI extremist, delete first)",
    }
    header = header_lines.get(mode, header_lines["full"])

    return f"{header}\n\n{skill_body}\n\n---\n"


def inject_into_prompt(system_prompt: str, mode: str = "full") -> str:
    """Prepend the Ponytail preamble to an existing agent system prompt."""
    preamble = get_ponytail_preamble(mode)
    if not preamble:
        return system_prompt
    return preamble + system_prompt
