import pytest


# Use a fresh asyncio event loop per test function to prevent httpx / anyio
# teardown "Event loop is closed" errors that occur when a prior test leaves
# lingering transport handles.
@pytest.fixture(scope="function")
def anyio_backend():
    return "asyncio"
