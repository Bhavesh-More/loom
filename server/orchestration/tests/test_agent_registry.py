from __future__ import annotations

from orchestration.planning.agent_registry import (
    AGENT_REGISTRY,
    AgentProfile,
    get_agent_profile,
    list_agent_profiles,
)


def test_registry_size() -> None:
    # Ensure all 15 agents are registered (14 specified in Step 1 + langgraph)
    assert len(AGENT_REGISTRY) == 15
    profiles = list_agent_profiles()
    assert len(profiles) == 15


def test_get_agent_profile() -> None:
    profile = get_agent_profile("postgresql")
    assert profile is not None
    assert profile.id == "postgresql"
    assert profile.name == "PostgreSQL Database Agent"
    assert profile.category == "database"
    assert "sql" in profile.capabilities
    assert profile.model_profile == "qwen/qwen3-32b"
    assert profile.cost_category == "medium"


def test_get_invalid_agent_profile() -> None:
    profile = get_agent_profile("invalid_agent")
    assert profile is None


def test_agent_profile_validation() -> None:
    for profile in list_agent_profiles():
        assert isinstance(profile, AgentProfile)
        assert profile.id in AGENT_REGISTRY
        assert len(profile.capabilities) > 0
        assert profile.category in ["database", "backend", "frontend", "infrastructure", "general"]
        assert profile.cost_category in ["low", "medium", "high"]
