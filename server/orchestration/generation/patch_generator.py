"""
patch_generator.py — Converts Loom agent output into structured patch blocks.

Agents currently produce output in the form:
    # FILE: filename.py
    <full file contents>

This module:
1. Parses those blocks into structured FilePatch objects.
2. Converts them to SEARCH/REPLACE edit blocks (Aider-style).
3. Generates a unified-diff-style summary for logging and review.
4. Applies diff-budget checks and returns a PatchResult.

Usage:
    generator = PatchGenerator()
    result = generator.process(agent_output_content, task_description="add auth route")
    if not result.budget.within_budget:
        # escalate for approval
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from orchestration.generation.diff_budget import DiffBudget, BudgetResult, TaskType, infer_task_type


# ---------------------------------------------------------------------------
# Data models (plain dataclasses — fast, no Pydantic overhead needed here)
# ---------------------------------------------------------------------------

@dataclass
class FilePatch:
    """A single file patch extracted from agent output."""
    filename: str
    content: str
    line_count: int = 0
    is_new_file: bool = True  # Assume new unless workspace tells us otherwise

    def __post_init__(self):
        self.line_count = len(self.content.splitlines())

    def to_search_replace_block(self) -> str:
        """
        Render as an Aider-style SEARCH/REPLACE edit block.
        For new files, the SEARCH block is empty (creates the file from scratch).
        """
        if self.is_new_file:
            return (
                f"<<<<<<< SEARCH [{self.filename}]\n"
                f"=======\n"
                f"{self.content}\n"
                f">>>>>>> REPLACE [{self.filename}]\n"
            )
        # For existing file modifications, the full content replaces the file.
        # A proper AST-aware implementation would narrow to the changed entity;
        # this provides the structural scaffolding for that future upgrade.
        return (
            f"<<<<<<< SEARCH [{self.filename}]\n"
            f"# (full file replacement — narrow to entity when AST context available)\n"
            f"=======\n"
            f"{self.content}\n"
            f">>>>>>> REPLACE [{self.filename}]\n"
        )


@dataclass
class PatchResult:
    """Complete result of patch generation for one agent output."""
    patches: list[FilePatch] = field(default_factory=list)
    budget: BudgetResult | None = None
    total_files: int = 0
    total_lines: int = 0
    search_replace_blocks: str = ""
    semantic_summary: list[str] = field(default_factory=list)
    task_type: str = "uncategorized"


# ---------------------------------------------------------------------------
# PatchGenerator
# ---------------------------------------------------------------------------

_FILE_HEADER_RE = re.compile(r"^#\s*FILE:\s*(.+)$", re.MULTILINE)


class PatchGenerator:
    """
    Converts agent output (# FILE: blocks) into structured patch format.

    Design principle (Ponytail): only parse what's needed, no AST unless the
    workspace provides existing-file context. The SEARCH/REPLACE format is
    already used by Aider and is the recommended approach per the Final Research.
    """

    def __init__(self, budget: DiffBudget | None = None) -> None:
        self.budget = budget or DiffBudget()

    def parse_file_blocks(self, content: str) -> list[FilePatch]:
        """
        Parse # FILE: delimited blocks from agent output.
        Returns a list of FilePatch objects, one per file block found.
        """
        patches: list[FilePatch] = []
        matches = list(_FILE_HEADER_RE.finditer(content))

        for i, match in enumerate(matches):
            filename = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            file_content = content[start:end].strip()
            patches.append(FilePatch(filename=filename, content=file_content))

        # If no FILE: blocks found, treat the whole content as a single unnamed block
        if not patches and content.strip():
            patches.append(FilePatch(filename="output.txt", content=content.strip()))

        return patches

    def generate_search_replace(self, patches: list[FilePatch]) -> str:
        """Convert patches to SEARCH/REPLACE edit block format."""
        return "\n\n".join(p.to_search_replace_block() for p in patches)

    def generate_semantic_summary(self, patches: list[FilePatch], task_description: str) -> list[str]:
        """
        Build a human-readable semantic change summary.
        Each entry describes what was added/modified in plain English.
        """
        summary: list[str] = []
        for patch in patches:
            fname = patch.filename
            lines = patch.line_count
            ext = fname.rsplit(".", 1)[-1] if "." in fname else "file"

            # Infer the nature of the change from filename and content
            if any(kw in fname.lower() for kw in ("schema", ".sql", "migration")):
                summary.append(f"✅ Added/updated database schema ({fname}, {lines} lines)")
            elif any(kw in fname.lower() for kw in ("route", "router", "api", "endpoint")):
                route_count = patch.content.count("@router.") + patch.content.count("@app.")
                if route_count:
                    summary.append(f"✅ Added {route_count} API route(s) in {fname}")
                else:
                    summary.append(f"✅ Updated API layer ({fname}, {lines} lines)")
            elif any(kw in fname.lower() for kw in ("auth", "token", "jwt", "session")):
                summary.append(f"✅ Added/updated authentication module ({fname})")
            elif any(kw in fname.lower() for kw in ("test_", "_test")):
                test_count = patch.content.count("def test_")
                summary.append(f"✅ Added {test_count} test(s) in {fname}")
            elif any(kw in fname.lower() for kw in ("readme", ".md", "docs")):
                summary.append(f"✅ Updated documentation ({fname})")
            elif any(kw in fname.lower() for kw in ("docker", "compose", "deploy")):
                summary.append(f"✅ Added/updated deployment configuration ({fname})")
            elif ext in ("py", "ts", "tsx", "js", "jsx"):
                summary.append(f"✅ Modified {ext.upper()} module: {fname} ({lines} lines)")
            else:
                summary.append(f"✅ Updated {fname} ({lines} lines)")

        return summary

    def infer_risk_level(self, patches: list[FilePatch]) -> str:
        """
        Infer the risk level for a set of patches.
        Low:    new files only, no core infrastructure
        Medium: existing backend/API modules modified
        High:   auth, billing, database schema, core infra changed
        """
        filenames = " ".join(p.filename.lower() for p in patches)
        if any(kw in filenames for kw in ("auth", "billing", "payment", "password", "token", "secret", "core", "main.py")):
            return "high"
        if any(kw in filenames for kw in ("route", "api", "schema", "model", "db", "database", "migration")):
            return "medium"
        return "low"

    def process(
        self,
        agent_output: str,
        task_description: str = "",
        task_type: str | None = None,
        existing_files: set[str] | None = None,
    ) -> PatchResult:
        """
        Full pipeline: parse → classify → budget check → generate blocks → summarize.

        Args:
            agent_output: The raw string output from an agent call.
            task_description: Human-readable description of the task (used for type inference).
            task_type: Explicit task type override ("bug_fix", "small_feature", etc.).
                       If None, inferred from task_description.
            existing_files: Set of filenames already in the workspace. Used to mark
                           patches as modifications vs new files.

        Returns:
            PatchResult with all patch data, budget check, and semantic summary.
        """
        patches = self.parse_file_blocks(agent_output)

        # Mark existing files
        if existing_files:
            for patch in patches:
                patch.is_new_file = patch.filename not in existing_files

        # Determine task type
        resolved_type: TaskType
        if task_type:
            try:
                resolved_type = TaskType(task_type)
            except ValueError:
                resolved_type = infer_task_type(task_description)
        else:
            resolved_type = infer_task_type(task_description)

        # Generate SEARCH/REPLACE blocks
        sr_blocks = self.generate_search_replace(patches)

        # Semantic summary
        semantic_summary = self.generate_semantic_summary(patches, task_description)

        # Diff budget check
        total_files = len(patches)
        total_lines = sum(p.line_count for p in patches)
        budget_result = self.budget.check(
            files_changed=total_files,
            lines_changed=total_lines,
            task_type=resolved_type,
        )

        return PatchResult(
            patches=patches,
            budget=budget_result,
            total_files=total_files,
            total_lines=total_lines,
            search_replace_blocks=sr_blocks,
            semantic_summary=semantic_summary,
            task_type=resolved_type.value,
        )
