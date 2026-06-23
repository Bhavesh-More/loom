import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from main import app
from knowledge.schema import KnowledgeEntry
from knowledge.conflict_resolver import ConflictResolver
from knowledge.store import KnowledgeStore
from knowledge.sync_manager import SyncManager
from db.database import database

# 1. Test Schema Validation
def test_schema_validation():
    # Valid entry
    entry_dict = {
        "id": "test-1",
        "content": "some facts",
        "version": 1,
        "timestamp": "2026-06-21T12:00:00Z",
        "source_agent": "fastapi",
        "priority": "medium",
        "tags": ["api", "auth"]
    }
    entry = KnowledgeEntry(**entry_dict)
    assert entry.id == "test-1"
    assert entry.version == 1
    assert entry.priority == "medium"

    # Invalid empty fields
    with pytest.raises(ValueError):
        KnowledgeEntry(
            id="",
            content="ok",
            version=1,
            timestamp=datetime.now(),
            source_agent="fastapi",
            priority="medium"
        )

    # Invalid priority
    with pytest.raises(ValueError):
        KnowledgeEntry(
            id="test-1",
            content="ok",
            version=1,
            timestamp=datetime.now(),
            source_agent="fastapi",
            priority="ultra-high"  # invalid
        )

# 2. Test Conflict Resolution logic
def test_conflict_resolution():
    base_entry = KnowledgeEntry(
        id="test-conflict",
        content="original info",
        version=2,
        timestamp=datetime(2026, 6, 21, 12, 0, 0, tzinfo=timezone.utc),
        source_agent="fastapi",
        priority="medium",
        tags=[]
    )

    # Case A: Higher version wins
    higher_version = KnowledgeEntry(
        id="test-conflict",
        content="newer info",
        version=3,
        timestamp=datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc), # older timestamp but higher version
        source_agent="supabase",
        priority="high",
        tags=[]
    )
    should_write, action = ConflictResolver.resolve(higher_version, base_entry)
    assert should_write is True
    assert action == "updated"

    # Case B: Lower version rejects
    lower_version = KnowledgeEntry(
        id="test-conflict",
        content="older info",
        version=1,
        timestamp=datetime(2026, 6, 21, 14, 0, 0, tzinfo=timezone.utc), # newer timestamp but lower version
        source_agent="supabase",
        priority="low",
        tags=[]
    )
    should_write, action = ConflictResolver.resolve(lower_version, base_entry)
    assert should_write is False
    assert action == "rejected"

    # Case C: Same version, newer timestamp wins
    same_version_newer_ts = KnowledgeEntry(
        id="test-conflict",
        content="newer info same version",
        version=2,
        timestamp=datetime(2026, 6, 21, 13, 0, 0, tzinfo=timezone.utc), # newer timestamp
        source_agent="supabase",
        priority="medium",
        tags=[]
    )
    should_write, action = ConflictResolver.resolve(same_version_newer_ts, base_entry)
    assert should_write is True
    assert action == "updated"

    # Case D: Same version, older/equal timestamp rejects
    same_version_older_ts = KnowledgeEntry(
        id="test-conflict",
        content="older info same version",
        version=2,
        timestamp=datetime(2026, 6, 21, 11, 0, 0, tzinfo=timezone.utc), # older timestamp
        source_agent="supabase",
        priority="medium",
        tags=[]
    )
    should_write, action = ConflictResolver.resolve(same_version_older_ts, base_entry)
    assert should_write is False
    assert action == "rejected"

# 3. Test Database Integration (PostgreSQL)
@pytest.mark.asyncio
async def test_database_persistence():
    await database.connect()
    try:
        store = KnowledgeStore()
        
        # Clean up test entry if it exists
        conn = await database.get_conn()
        try:
            await conn.execute("DELETE FROM shared_knowledge WHERE id = $1", "test-db-id")
        finally:
            await database.release_conn(conn)

        entry = KnowledgeEntry(
            id="test-db-id",
            content="Database persistence test content",
            version=1,
            timestamp=datetime(2026, 6, 21, 12, 0, 0, tzinfo=timezone.utc),
            source_agent="tester",
            priority="low",
            tags=["test"]
        )

        # Save to DB
        await store.save_entry(entry)

        # Read from DB
        retrieved = await store.get_entry("test-db-id")
        assert retrieved is not None
        assert retrieved.id == "test-db-id"
        assert retrieved.content == "Database persistence test content"
        assert retrieved.version == 1
        assert retrieved.priority == "low"
        assert "test" in retrieved.tags

        # Read tags
        by_tag = await store.get_entries_by_tag("test")
        assert any(item.id == "test-db-id" for item in by_tag)

        # Cleanup
        conn = await database.get_conn()
        try:
            await conn.execute("DELETE FROM shared_knowledge WHERE id = $1", "test-db-id")
        finally:
            await database.release_conn(conn)
    finally:
        await database.disconnect()

# 4. Test Sync Manager Caching & Invalidation
@pytest.mark.asyncio
async def test_sync_manager_caching():
    await database.connect()
    try:
        mgr = SyncManager()

        # Invalidate cache first
        mgr.propagator.invalidate_cache()

        entry_data = {
            "id": "test-cache-id",
            "content": "Cache test info",
            "version": 1,
            "timestamp": "2026-06-21T12:00:00Z",
            "source_agent": "tester",
            "priority": "low",
            "tags": ["cache-tag"]
        }

        # Add entry
        res = await mgr.add_knowledge(entry_data)
        assert res["success"] is True

        # Read all (caches result)
        all_entries = await mgr.get_all()
        assert any(item.id == "test-cache-id" for item in all_entries)

        # Directly modify DB (bypassing sync manager/cache) to verify cache works
        conn = await database.get_conn()
        try:
            await conn.execute("UPDATE shared_knowledge SET content = 'dirty content' WHERE id = $1", "test-cache-id")
        finally:
            await database.release_conn(conn)

        # Read all again (should return cached original content, not 'dirty content')
        cached_entries = await mgr.get_all()
        test_item = next(item for item in cached_entries if item.id == "test-cache-id")
        assert test_item.content == "Cache test info"

        # Now add via sync manager again with higher version to trigger invalidation
        updated_entry_data = {
            "id": "test-cache-id",
            "content": "Updated cache info",
            "version": 2,
            "timestamp": "2026-06-21T13:00:00Z",
            "source_agent": "tester",
            "priority": "low",
            "tags": ["cache-tag"]
        }
        res2 = await mgr.add_knowledge(updated_entry_data)
        assert res2["success"] is True

        # Read all again (should return updated content 'Updated cache info')
        new_entries = await mgr.get_all()
        new_test_item = next(item for item in new_entries if item.id == "test-cache-id")
        assert new_test_item.content == "Updated cache info"

        # Cleanup
        conn = await database.get_conn()
        try:
            await conn.execute("DELETE FROM shared_knowledge WHERE id = $1", "test-cache-id")
        finally:
            await database.release_conn(conn)
    finally:
        await database.disconnect()

# 5. Test API Endpoints
@pytest.mark.asyncio
async def test_api_endpoints():
    from httpx import AsyncClient, ASGITransport
    await database.connect()
    try:
        entry_id = "test-api-id"

        # Cleanup in case of dirty run
        conn = await database.get_conn()
        try:
            await conn.execute("DELETE FROM shared_knowledge WHERE id = $1", entry_id)
        finally:
            await database.release_conn(conn)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Valid add
            entry_payload = {
                "id": entry_id,
                "content": "FastAPI router works",
                "version": 1,
                "timestamp": "2026-06-21T12:00:00Z",
                "source_agent": "api-tester",
                "priority": "high",
                "tags": ["api-tag"]
            }
            response = await client.post("/knowledge/add", json=entry_payload)
            assert response.status_code == 200
            assert response.json()["success"] is True

            # Outdated version add (should return 400 Bad Request)
            response_fail = await client.post("/knowledge/add", json={**entry_payload, "version": 0})
            assert response_fail.status_code == 400

            # Get all entries
            response_get = await client.get("/knowledge/get")
            assert response_get.status_code == 200
            items = response_get.json()
            assert any(item["id"] == entry_id for item in items)

            # Get by tag
            response_tag = await client.get("/knowledge/tags/api-tag")
            assert response_tag.status_code == 200
            tag_items = response_tag.json()
            assert any(item["id"] == entry_id for item in tag_items)

        # Cleanup at end
        conn = await database.get_conn()
        try:
            await conn.execute("DELETE FROM shared_knowledge WHERE id = $1", entry_id)
        finally:
            await database.release_conn(conn)
    finally:
        await database.disconnect()

