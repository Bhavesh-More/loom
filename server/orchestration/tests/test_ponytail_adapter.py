"""
Tests for the Ponytail adapter (Phase 2).
Verifies that prompts are correctly injected with mode-filtered Ponytail rules.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from orchestration.agents.ponytail_adapter import (
    _find_skill_file,
    _load_ponytail_skill,
    get_ponytail_preamble,
    inject_into_prompt,
)


class TestPonytailAdapter:

    def test_get_ponytail_preamble_off_returns_empty(self):
        """mode='off' should return empty string — no injection."""
        result = get_ponytail_preamble("off")
        assert result == ""

    def test_get_ponytail_preamble_full_contains_ladder(self):
        """full mode must include YAGNI / ladder / rules content."""
        result = get_ponytail_preamble("full")
        assert len(result) > 50
        # The result should contain core Ponytail philosophy
        lower = result.lower()
        assert any(kw in lower for kw in ("lazy", "yagni", "ladder", "minimal", "ponytail"))

    def test_get_ponytail_preamble_lite_has_header(self):
        result = get_ponytail_preamble("lite")
        assert "LITE" in result.upper()

    def test_get_ponytail_preamble_ultra_has_header(self):
        result = get_ponytail_preamble("ultra")
        assert "ULTRA" in result.upper()

    def test_get_ponytail_preamble_unknown_mode_defaults_to_full(self):
        """Unrecognised mode falls through to 'full' header."""
        result = get_ponytail_preamble("nonsense")
        assert "FULL" in result.upper()

    def test_inject_into_prompt_prepends(self):
        base = "You are the FastAPI agent."
        result = inject_into_prompt(base, mode="full")
        # Ponytail preamble comes BEFORE the base prompt
        assert result.index("Ponytail") < result.index("FastAPI")

    def test_inject_into_prompt_off_returns_base(self):
        base = "You are the FastAPI agent."
        result = inject_into_prompt(base, mode="off")
        assert result == base

    def test_env_var_mode_respected(self, monkeypatch):
        """PONYTAIL_MODE env var should control the mode in prompts.py."""
        monkeypatch.setenv("PONYTAIL_MODE", "off")
        # Re-import prompts to re-evaluate build_agent_prompt
        import importlib
        import prompts.prompts as prompts_mod
        importlib.reload(prompts_mod)
        # With mode=off, AGENT_PROMPT_MAP values should NOT have Ponytail preamble
        # (they equal the raw prompt strings)
        fastapi_prompt = prompts_mod.AGENT_PROMPT_MAP["fastapi"]
        # After reload with mode=off, no ponytail header
        assert "PONYTAIL" not in fastapi_prompt.upper()
        # Restore
        monkeypatch.delenv("PONYTAIL_MODE", raising=False)
        importlib.reload(prompts_mod)

    def test_skill_file_found_or_fallback_used(self):
        """Either the real SKILL.md is found OR the inline fallback is used — never empty."""
        skill_text = _load_ponytail_skill()
        assert len(skill_text) > 100

    def test_preamble_ends_with_separator(self):
        result = get_ponytail_preamble("full")
        # The preamble ends with the --- separator so prompts parse cleanly
        assert result.strip().endswith("---")
