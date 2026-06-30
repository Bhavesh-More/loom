import os
import pytest


# ---------------------------------------------------------------------------
# Event-loop backend — required by tests decorated with @pytest.mark.anyio.
# pytest-asyncio auto mode handles @pytest.mark.asyncio automatically.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def anyio_backend():
    return "asyncio"


# ---------------------------------------------------------------------------
# Clear GROQ_API_KEY_1 for every test so no real LLM calls are made and
# lingering httpx transports don't leave an open event loop after teardown.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clear_env_api_keys(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY_1", raising=False)

