import pytest

from context_system.intent_parser import IntentParser
from context_system.models import TaskType


@pytest.mark.asyncio
async def test_intent_parser_falls_back_to_useful_theme_signals(monkeypatch):
    parser = IntentParser()

    async def fail_llm(prompt):
        raise RuntimeError("no llm")

    monkeypatch.setattr(parser, "_parse_with_llm", fail_llm)

    signals = await parser.parse("add a dark mode toggle")

    assert signals.task_type == TaskType.NEW_FEATURE
    assert signals.domain == "UI/styling"
    assert "darkMode" in signals.grep_terms
    assert "colorScheme" in signals.grep_terms
