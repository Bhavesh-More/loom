"""
diff_budget.py — Diff budget enforcement for the Loom patch-based generation system.

Per the Final Research document §1:
  | Task Type      | Max Files | Max Lines |
  |----------------|-----------|-----------|
  | bug_fix        | 1         | 20        |
  | small_feature  | 3         | 80        |
  | refactor       | 4         | 150       |
  | new_module     | 5         | 200       |
  | uncategorized  | 5         | 200       |

Agents exceeding their budget must either:
  - Request user approval (requires_approval=True in the result), or
  - Have their task split by the orchestrator.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt, StrictStr


class TaskType(str, Enum):
    BUG_FIX = "bug_fix"
    SMALL_FEATURE = "small_feature"
    REFACTOR = "refactor"
    NEW_MODULE = "new_module"
    UNCATEGORIZED = "uncategorized"


# Budget table: (max_files, max_lines)
_BUDGETS: dict[TaskType, tuple[int, int]] = {
    TaskType.BUG_FIX:       (1,  20),
    TaskType.SMALL_FEATURE: (3,  80),
    TaskType.REFACTOR:      (4, 150),
    TaskType.NEW_MODULE:    (5, 200),
    TaskType.UNCATEGORIZED: (5, 200),
}


class BudgetResult(BaseModel):
    """Result of a diff-budget check."""
    model_config = ConfigDict(extra="forbid")

    task_type: StrictStr
    files_changed: StrictInt
    lines_changed: StrictInt
    max_files: StrictInt
    max_lines: StrictInt
    within_budget: StrictBool
    requires_approval: StrictBool
    violation_reason: StrictStr | None = None
    overage_pct: StrictFloat = Field(
        default=0.0,
        description="How far over budget (as a fraction, e.g. 1.5 = 50% over)",
    )


def infer_task_type(task_description: str) -> TaskType:
    """
    Heuristically infer task type from a description string.
    Used when the caller doesn't provide an explicit task type.
    """
    lower = task_description.lower()
    if any(kw in lower for kw in ("fix", "bug", "patch", "hotfix", "repair")):
        return TaskType.BUG_FIX
    if any(kw in lower for kw in ("refactor", "reorganize", "restructure", "rename", "move")):
        return TaskType.REFACTOR
    if any(kw in lower for kw in ("new module", "new file", "create module", "add module", "scaffold")):
        return TaskType.NEW_MODULE
    if any(kw in lower for kw in ("add", "feature", "implement", "support", "enable", "introduce")):
        return TaskType.SMALL_FEATURE
    return TaskType.UNCATEGORIZED


class DiffBudget:
    """
    Enforces diff budgets per task type.

    Usage:
        budget = DiffBudget()
        result = budget.check(files_changed=2, lines_changed=45, task_type=TaskType.SMALL_FEATURE)
        if not result.within_budget:
            # handle overage — request approval or split task
    """

    def check(
        self,
        files_changed: int,
        lines_changed: int,
        task_type: TaskType | str = TaskType.UNCATEGORIZED,
    ) -> BudgetResult:
        """
        Check whether the diff is within the budget for the given task type.

        Args:
            files_changed: Number of files modified/created.
            lines_changed: Total lines added + removed.
            task_type: The classification of the task being performed.

        Returns:
            BudgetResult with compliance status and details.
        """
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                task_type = TaskType.UNCATEGORIZED

        max_files, max_lines = _BUDGETS[task_type]
        file_ok = files_changed <= max_files
        line_ok = lines_changed <= max_lines
        within_budget = file_ok and line_ok

        violation_reason: str | None = None
        overage_pct = 0.0
        if not within_budget:
            parts = []
            if not file_ok:
                parts.append(
                    f"files: {files_changed} > {max_files} allowed for {task_type.value}"
                )
                overage_pct = max(overage_pct, files_changed / max_files)
            if not line_ok:
                parts.append(
                    f"lines: {lines_changed} > {max_lines} allowed for {task_type.value}"
                )
                overage_pct = max(overage_pct, lines_changed / max_lines)
            violation_reason = "; ".join(parts)

        return BudgetResult(
            task_type=task_type.value,
            files_changed=files_changed,
            lines_changed=lines_changed,
            max_files=max_files,
            max_lines=max_lines,
            within_budget=within_budget,
            requires_approval=not within_budget,
            violation_reason=violation_reason,
            overage_pct=round(overage_pct, 3),
        )

    def check_from_patch_text(
        self,
        patch_text: str,
        task_type: TaskType | str = TaskType.UNCATEGORIZED,
    ) -> BudgetResult:
        """
        Convenience method: parse a unified diff or FILE-block output and check budget.
        Counts files from '# FILE:' headers or '--- a/' diff headers.
        Counts lines from '+' / '-' prefix lines (excluding file headers).
        """
        files: set[str] = set()
        lines_changed = 0

        for line in patch_text.splitlines():
            stripped = line.strip()
            # # FILE: pattern (Loom agent output)
            if stripped.startswith("# FILE:"):
                fname = stripped[len("# FILE:"):].strip()
                if fname:
                    files.add(fname)
                continue
            # Unified diff pattern
            if stripped.startswith("--- a/") or stripped.startswith("+++ b/"):
                fname = stripped[6:].strip()
                if fname and fname != "/dev/null":
                    files.add(fname)
                continue
            # SEARCH/REPLACE block — count non-header lines as changed
            if stripped.startswith("<<<<<<< SEARCH") or stripped.startswith(">>>>>>> REPLACE"):
                continue
            # Count added/removed lines from unified diffs
            if line.startswith("+") and not line.startswith("+++"):
                lines_changed += 1
            elif line.startswith("-") and not line.startswith("---"):
                lines_changed += 1

        # If no diff markers found but content exists, count all non-blank lines
        # as a rough proxy (whole-file output)
        if lines_changed == 0 and files:
            lines_changed = sum(
                1 for ln in patch_text.splitlines()
                if ln.strip() and not ln.strip().startswith("#")
            )

        return self.check(
            files_changed=len(files) or 1,
            lines_changed=lines_changed,
            task_type=task_type,
        )
