"""
Tests for orchestration/generation — patch generator and diff budget.
Covers Phase 3 of the Final Research implementation.
"""
from __future__ import annotations

import pytest

from orchestration.generation.diff_budget import (
    DiffBudget,
    TaskType,
    infer_task_type,
)
from orchestration.generation.patch_generator import FilePatch, PatchGenerator


# ---------------------------------------------------------------------------
# DiffBudget tests
# ---------------------------------------------------------------------------

class TestDiffBudget:

    def test_bug_fix_within_budget(self):
        budget = DiffBudget()
        result = budget.check(files_changed=1, lines_changed=15, task_type=TaskType.BUG_FIX)
        assert result.within_budget is True
        assert result.requires_approval is False

    def test_bug_fix_exceeds_file_limit(self):
        budget = DiffBudget()
        result = budget.check(files_changed=2, lines_changed=10, task_type=TaskType.BUG_FIX)
        assert result.within_budget is False
        assert result.requires_approval is True
        assert "files" in (result.violation_reason or "")

    def test_bug_fix_exceeds_line_limit(self):
        budget = DiffBudget()
        result = budget.check(files_changed=1, lines_changed=25, task_type=TaskType.BUG_FIX)
        assert result.within_budget is False
        assert result.requires_approval is True
        assert "lines" in (result.violation_reason or "")

    def test_small_feature_at_exact_limit(self):
        budget = DiffBudget()
        result = budget.check(files_changed=3, lines_changed=80, task_type=TaskType.SMALL_FEATURE)
        assert result.within_budget is True

    def test_new_module_within_budget(self):
        budget = DiffBudget()
        result = budget.check(files_changed=4, lines_changed=150, task_type=TaskType.NEW_MODULE)
        assert result.within_budget is True

    def test_uncategorized_uses_new_module_limits(self):
        budget = DiffBudget()
        result = budget.check(files_changed=5, lines_changed=200, task_type=TaskType.UNCATEGORIZED)
        assert result.within_budget is True

    def test_refactor_exceeds_both_limits(self):
        budget = DiffBudget()
        result = budget.check(files_changed=10, lines_changed=500, task_type=TaskType.REFACTOR)
        assert result.within_budget is False
        assert result.overage_pct > 1.0  # More than 100% over budget

    def test_string_task_type_accepted(self):
        budget = DiffBudget()
        result = budget.check(files_changed=1, lines_changed=10, task_type="bug_fix")
        assert result.task_type == "bug_fix"
        assert result.within_budget is True

    def test_invalid_task_type_falls_back_to_uncategorized(self):
        budget = DiffBudget()
        result = budget.check(files_changed=5, lines_changed=200, task_type="totally_invalid")
        assert result.task_type == "uncategorized"
        assert result.within_budget is True

    def test_check_from_patch_text_file_blocks(self):
        budget = DiffBudget()
        patch_text = (
            "# FILE: main.py\n"
            "from fastapi import FastAPI\n"
            "app = FastAPI()\n"
            "# FILE: models.py\n"
            "from pydantic import BaseModel\n"
            "class Item(BaseModel): name: str\n"
        )
        result = budget.check_from_patch_text(patch_text, task_type=TaskType.SMALL_FEATURE)
        assert result.files_changed == 2
        assert result.within_budget is True

    def test_check_from_unified_diff(self):
        budget = DiffBudget()
        diff_text = (
            "--- a/main.py\n"
            "+++ b/main.py\n"
            "+from fastapi import FastAPI\n"
            "+app = FastAPI()\n"
            "-old_line = True\n"
        )
        result = budget.check_from_patch_text(diff_text, task_type=TaskType.BUG_FIX)
        assert result.files_changed == 1
        assert result.lines_changed == 3  # 2 additions + 1 deletion


class TestInferTaskType:

    def test_infer_bug_fix(self):
        assert infer_task_type("fix the auth bug") == TaskType.BUG_FIX
        assert infer_task_type("patch the login issue") == TaskType.BUG_FIX
        assert infer_task_type("hotfix for rate limiting") == TaskType.BUG_FIX

    def test_infer_refactor(self):
        assert infer_task_type("refactor the database layer") == TaskType.REFACTOR
        assert infer_task_type("reorganize module structure") == TaskType.REFACTOR

    def test_infer_new_module(self):
        assert infer_task_type("create new module for payments") == TaskType.NEW_MODULE
        assert infer_task_type("scaffold the auth service") == TaskType.NEW_MODULE

    def test_infer_small_feature(self):
        assert infer_task_type("add JWT authentication support") == TaskType.SMALL_FEATURE
        assert infer_task_type("implement rate limiting feature") == TaskType.SMALL_FEATURE

    def test_infer_uncategorized_fallback(self):
        assert infer_task_type("do something") == TaskType.UNCATEGORIZED


# ---------------------------------------------------------------------------
# PatchGenerator tests
# ---------------------------------------------------------------------------

class TestPatchGenerator:

    def test_parse_single_file_block(self):
        generator = PatchGenerator()
        content = "# FILE: main.py\nfrom fastapi import FastAPI\napp = FastAPI()\n"
        patches = generator.parse_file_blocks(content)
        assert len(patches) == 1
        assert patches[0].filename == "main.py"
        assert "FastAPI" in patches[0].content
        assert patches[0].line_count == 2

    def test_parse_multiple_file_blocks(self):
        generator = PatchGenerator()
        content = (
            "# FILE: db.py\nimport asyncpg\n\n"
            "# FILE: main.py\nfrom fastapi import FastAPI\n"
        )
        patches = generator.parse_file_blocks(content)
        assert len(patches) == 2
        assert patches[0].filename == "db.py"
        assert patches[1].filename == "main.py"

    def test_parse_no_file_blocks_returns_single_patch(self):
        generator = PatchGenerator()
        content = "SELECT * FROM users WHERE id = $1;"
        patches = generator.parse_file_blocks(content)
        assert len(patches) == 1
        assert patches[0].filename == "output.txt"

    def test_generate_search_replace_new_file(self):
        generator = PatchGenerator()
        patch = FilePatch(filename="app.py", content="print('hello')", is_new_file=True)
        sr = generator.generate_search_replace([patch])
        assert "<<<<<<< SEARCH [app.py]" in sr
        assert "=======" in sr
        assert "print('hello')" in sr
        assert ">>>>>>> REPLACE [app.py]" in sr

    def test_generate_search_replace_existing_file(self):
        generator = PatchGenerator()
        patch = FilePatch(filename="app.py", content="print('updated')", is_new_file=False)
        sr = generator.generate_search_replace([patch])
        assert "<<<<<<< SEARCH [app.py]" in sr
        assert "full file replacement" in sr

    def test_semantic_summary_sql_file(self):
        generator = PatchGenerator()
        patch = FilePatch(filename="schema.sql", content="CREATE TABLE users (id UUID PRIMARY KEY);")
        summary = generator.generate_semantic_summary([patch], "design db schema")
        assert any("schema" in s.lower() or "database" in s.lower() for s in summary)

    def test_semantic_summary_route_file(self):
        generator = PatchGenerator()
        patch = FilePatch(
            filename="routers/auth.py",
            content="@router.post('/login')\nasync def login(): pass\n@router.post('/register')\nasync def register(): pass",
        )
        summary = generator.generate_semantic_summary([patch], "add auth routes")
        assert any("route" in s.lower() or "API" in s for s in summary)

    def test_infer_risk_level_low(self):
        generator = PatchGenerator()
        patches = [FilePatch(filename="readme.md", content="# docs")]
        assert generator.infer_risk_level(patches) == "low"

    def test_infer_risk_level_medium(self):
        generator = PatchGenerator()
        patches = [FilePatch(filename="routers/api.py", content="@router.get('/items')")]
        assert generator.infer_risk_level(patches) == "medium"

    def test_infer_risk_level_high(self):
        generator = PatchGenerator()
        patches = [FilePatch(filename="auth/token.py", content="SECRET_KEY = ...")]
        assert generator.infer_risk_level(patches) == "high"

    def test_process_full_pipeline(self):
        generator = PatchGenerator()
        agent_output = (
            "# FILE: main.py\nfrom fastapi import FastAPI\napp = FastAPI()\n\n"
            "# FILE: routers/items.py\n@router.get('/items')\nasync def list_items(): pass\n"
        )
        result = generator.process(
            agent_output=agent_output,
            task_description="add REST API endpoints",
        )
        assert result.total_files == 2
        assert result.total_lines > 0
        assert result.budget is not None
        assert len(result.semantic_summary) > 0
        assert "<<<<<<< SEARCH" in result.search_replace_blocks
        assert result.task_type == "small_feature"

    def test_process_bug_fix_within_budget(self):
        generator = PatchGenerator()
        agent_output = "# FILE: utils.py\ndef fix(): return True\n"
        result = generator.process(
            agent_output=agent_output,
            task_description="fix the null pointer bug",
            task_type="bug_fix",
        )
        assert result.task_type == "bug_fix"
        assert result.budget is not None
        assert result.budget.within_budget is True

    def test_process_marks_existing_files(self):
        generator = PatchGenerator()
        agent_output = "# FILE: existing.py\nprint('updated')\n"
        result = generator.process(
            agent_output=agent_output,
            task_description="update existing module",
            existing_files={"existing.py"},
        )
        assert result.patches[0].is_new_file is False
