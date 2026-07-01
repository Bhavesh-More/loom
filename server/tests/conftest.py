"""
conftest.py for integration tests
==================================
Provides a session-scoped async HTTP client and database pool for integration testing.
This avoids establishing new connections to Supabase for every test, preventing
rate limits, socket errors, and closed event loop issues.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from db.database import database
from context_system.service import context_system

# Save the original disconnect method to close the pool at the very end of the session
_original_disconnect = database.disconnect


@pytest.fixture(scope="session", autouse=True)
async def session_db_setup():
    """Connect to the database once for the entire test session."""
    # Override database.disconnect to be a no-op during the test session
    # so individual tests don't close the global pool mid-session.
    async def mock_disconnect():
        pass
    database.disconnect = mock_disconnect

    await database.connect()
    await context_system.startup()
    yield
    # Restore and call the original disconnect at session end
    database.disconnect = _original_disconnect
    await database.disconnect()


@pytest.fixture(scope="session")
async def client_session():
    """Async HTTP client sharing the session lifespan."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture()
def client(client_session):
    """Function-scoped helper that returns the session client."""
    return client_session
