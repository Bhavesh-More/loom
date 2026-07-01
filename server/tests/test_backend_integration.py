"""
test_backend_integration.py
===========================
Thorough integration tests for ALL backend services and API routes.
The `client` fixture is defined in conftest.py and runs the full app lifespan,
ensuring database.connect() is called in the same event loop as each test.

Covers:
  ✅ Health endpoint
  ✅ Project CRUD (create, get, list, validation)
  ✅ Agent routes (list, shape validation, download/uninstall toggle)
  ✅ Chat routes (list, 404 on unknown, 422 on bad UUID)
  ✅ Workspace routes (tree, file save/read round-trip, zip download)
  ✅ Shared knowledge API (add, get-all, tag-filter, semantic search)
  ✅ Agent memory API (add/get memory, execution, historical context)
  ✅ Audit ledger API (entries, summary, 404 handling)
  ✅ Orchestration route (status/graph/agent-output 404)
  ✅ Develop endpoint (no-agent error stream)
  ✅ Diff budget & patch generator (service-level unit integration)
  ✅ Ponytail adapter (preamble injection)
  ✅ Knowledge service (chunking, prepare_agent_context graceful fallback)
  ✅ Database connectivity (pool alive, all key tables present)

Run:
    .venv/Scripts/python.exe -m pytest tests/test_backend_integration.py -v --tb=short
"""
from __future__ import annotations

import json
import uuid
import pytest
from httpx import AsyncClient

from db.database import database


# ─────────────────────────────────────────────────────────────────────────────
# Helper fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
async def created_project(client: AsyncClient):
    """Creates a throwaway project for one test and deletes it afterwards."""
    name = f"itest-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/projects",
        json={"name": name, "description": "pytest integration", "agent_ids": []},
    )
    assert resp.status_code == 200, f"Project creation failed: {resp.text}"
    project = resp.json()
    # CreateProjectResponse uses 'project_id' as the key, not 'id'
    project_id = str(project["project_id"])
    yield {**project, "id": project_id}  # expose both keys for convenience
    # Best-effort cleanup
    try:
        conn = await database.get_conn()
        try:
            await conn.execute(
                "DELETE FROM projects WHERE id = $1", uuid.UUID(project_id)
            )
        finally:
            await database.release_conn(conn)
    except Exception:
        pass


@pytest.fixture()
async def first_agent_id(client: AsyncClient):
    resp = await client.get("/agents")
    agents = resp.json()
    if not agents:
        pytest.skip("No agents in database")
    return agents[0]["id"]


# ─────────────────────────────────────────────────────────────────────────────
# 1. Health
# ─────────────────────────────────────────────────────────────────────────────

async def test_health_check(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Projects
# ─────────────────────────────────────────────────────────────────────────────

async def test_create_project_success(created_project: dict):
    assert "project_id" in created_project
    assert created_project["name"].startswith("itest-")


async def test_get_project_by_id(client: AsyncClient, created_project: dict):
    resp = await client.get(f"/projects/{created_project['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created_project["id"]


async def test_get_project_not_found(client: AsyncClient):
    resp = await client.get(f"/projects/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_list_projects(client: AsyncClient):
    resp = await client.post("/projects/get-projects")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_create_project_missing_agent_ids_returns_422(client: AsyncClient):
    """agent_ids is a required field — omitting it must return 422."""
    resp = await client.post(
        "/projects",
        json={"name": "missing-agents", "description": "test"},
    )
    assert resp.status_code == 422


async def test_create_project_empty_agent_ids_is_valid(client: AsyncClient):
    """agent_ids=[] is valid. The project is created without any agents."""
    name = f"no-agents-{uuid.uuid4().hex[:6]}"
    resp = await client.post(
        "/projects",
        json={"name": name, "description": "empty agents", "agent_ids": []},
    )
    assert resp.status_code == 200
    project = resp.json()
    assert "project_id" in project
    # Cleanup
    try:
        conn = await database.get_conn()
        try:
            await conn.execute("DELETE FROM projects WHERE id = $1", uuid.UUID(str(project["project_id"])))
        finally:
            await database.release_conn(conn)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# 3. Agents
# ─────────────────────────────────────────────────────────────────────────────

async def test_list_agents_returns_list(client: AsyncClient):
    resp = await client.get("/agents")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_agents_have_expected_fields(client: AsyncClient):
    resp = await client.get("/agents")
    agents = resp.json()
    if not agents:
        pytest.skip("No agents in database")
    first = agents[0]
    for field in ("id", "name", "version", "type", "icon", "rating", "downloaded"):
        assert field in first, f"Missing field '{field}' in agent response"


async def test_download_and_uninstall_agent(client: AsyncClient):
    """Download then immediately uninstall an agent — round-trip toggle."""
    resp = await client.get("/agents")
    agents = resp.json()
    if not agents:
        pytest.skip("No agents in database")
    agent_id = agents[0]["id"]

    dl = await client.post(f"/agents/{agent_id}/download")
    assert dl.status_code == 200
    assert dl.json()["status"] == "downloaded"

    un = await client.delete(f"/agents/{agent_id}/download")
    assert un.status_code == 200
    assert un.json()["status"] == "uninstalled"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Chats
# ─────────────────────────────────────────────────────────────────────────────

async def test_list_chats(client: AsyncClient):
    resp = await client.post("/chats/get-chats")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_get_chat_not_found(client: AsyncClient):
    resp = await client.get(f"/chats/get-chat/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_get_chat_invalid_uuid_returns_422(client: AsyncClient):
    resp = await client.get("/chats/get-chat/not-a-valid-uuid")
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 5. Workspace
# ─────────────────────────────────────────────────────────────────────────────

async def test_workspace_tree_unknown_project(client: AsyncClient):
    resp = await client.get(f"/workspace/{uuid.uuid4()}/tree")
    assert resp.status_code == 404


async def test_workspace_tree_new_project_is_empty_list(client: AsyncClient, created_project: dict):
    resp = await client.get(f"/workspace/{created_project['id']}/tree")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_workspace_file_not_found(client: AsyncClient, created_project: dict):
    resp = await client.get(
        f"/workspace/{created_project['id']}/file",
        params={"path": "nonexistent.py"},
    )
    assert resp.status_code == 404


async def test_workspace_save_and_read_file(client: AsyncClient, created_project: dict):
    """Write a file, then read it back — full round-trip."""
    save = await client.put(
        f"/workspace/{created_project['id']}/file",
        json={"path": "hello_itest.py", "content": "# integration test marker"},
    )
    assert save.status_code == 200
    assert save.json()["status"] == "success"

    read = await client.get(
        f"/workspace/{created_project['id']}/file",
        params={"path": "hello_itest.py"},
    )
    assert read.status_code == 200
    assert "integration test marker" in read.json()["content"]


async def test_workspace_download_zip(client: AsyncClient, created_project: dict):
    # Ensure workspace directory exists by saving a file first
    await client.put(
        f"/workspace/{created_project['id']}/file",
        json={"path": "dummy.txt", "content": "dummy"},
    )
    resp = await client.get(f"/workspace/{created_project['id']}/download")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert len(resp.content) > 0


# ─────────────────────────────────────────────────────────────────────────────
# 6. Shared Knowledge API
# ─────────────────────────────────────────────────────────────────────────────

async def test_shared_knowledge_add_entry(client: AsyncClient):
    entry_id = f"itest-sk-{uuid.uuid4()}"
    resp = await client.post(
        "/knowledge/add",
        json={
            "id": entry_id,
            "content": "Integration test: Always use connection pooling for databases.",
            "version": 1,
            "timestamp": "2026-01-01T00:00:00Z",
            "source_agent": "postgresql",
            "priority": "high",
            "tags": ["integration", "database"],
        },
    )
    assert resp.status_code == 200
    assert resp.json().get("success") is True
    # Cleanup
    try:
        conn = await database.get_conn()
        try:
            await conn.execute("DELETE FROM shared_knowledge WHERE id = $1", entry_id)
        finally:
            await database.release_conn(conn)
    except Exception:
        pass


async def test_shared_knowledge_get_all(client: AsyncClient):
    resp = await client.get("/knowledge/get")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_shared_knowledge_tag_filter(client: AsyncClient):
    resp = await client.get("/knowledge/tags/database")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_shared_knowledge_semantic_search(client: AsyncClient):
    resp = await client.get(
        "/knowledge/search",
        params={"query": "database connection pool", "limit": 5},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_shared_knowledge_sources_list(client: AsyncClient):
    resp = await client.get("/knowledge/sources")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Agent Memory API
# ─────────────────────────────────────────────────────────────────────────────

async def test_add_and_get_memory(client: AsyncClient, first_agent_id: str):
    resp = await client.post(
        "/knowledge/memory/add",
        json={
            "agent_id": first_agent_id,
            "context": "integration test context",
            "summary": "Completed integration test task",
            "learned_info": "Always validate agent ID before memory save.",
            "tags": ["integration", "test"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["agent_id"] == first_agent_id

    resp2 = await client.get("/knowledge/memory/get", params={"agent_id": first_agent_id})
    assert resp2.status_code == 200
    memories = resp2.json()
    assert isinstance(memories, list)
    assert any(m["agent_id"] == first_agent_id for m in memories)


async def test_add_execution_entry(client: AsyncClient, first_agent_id: str):
    resp = await client.post(
        "/knowledge/execution/add",
        json={
            "agent_id": first_agent_id,
            "task_id": "integration-test-task",
            "input_data": "build a test endpoint",
            "output_data": "# FILE: test.py\nprint('done')",
            "status": "success",
            "metadata": {"session": "test"},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


async def test_get_executions(client: AsyncClient, first_agent_id: str):
    resp = await client.get(
        "/knowledge/execution/get",
        params={"agent_id": first_agent_id, "status": "success"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_semantic_search_memories(client: AsyncClient, first_agent_id: str):
    resp = await client.get(
        "/knowledge/memory/semantic-search",
        params={"query": "validate agent memory", "agent_id": first_agent_id, "limit": 3},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_historical_context(client: AsyncClient, first_agent_id: str):
    resp = await client.get(
        "/knowledge/historical-context",
        params={"agent_id": first_agent_id, "task": "integration test task"},
    )
    assert resp.status_code == 200
    ctx = resp.json()
    assert any(k in ctx for k in ("memories", "executions", "decisions"))


# ─────────────────────────────────────────────────────────────────────────────
# 8. Audit Ledger API
# ─────────────────────────────────────────────────────────────────────────────

async def test_audit_entries_not_found(client: AsyncClient):
    resp = await client.get(f"/audit/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_audit_summary_not_found(client: AsyncClient):
    resp = await client.get(f"/audit/{uuid.uuid4()}/summary")
    assert resp.status_code == 404


async def test_audit_entries_after_ledger_record(client: AsyncClient):
    from orchestration.observability.audit_ledger import AuditLedger

    ledger = AuditLedger()
    run_id = f"itest-run-{uuid.uuid4()}"
    await ledger.record(
        run_id=run_id,
        agent_id="fastapi",
        task_description="build REST API",
        patch_metadata={
            "task_type": "small_feature",
            "total_files": 2,
            "total_lines": 40,
            "within_budget": True,
            "requires_approval": False,
            "violation_reason": None,
            "risk_level": "medium",
            "semantic_summary": ["✅ Added 2 route(s) in routes/items.py"],
            "search_replace_blocks": "",
        },
        validation_passed=True,
        confidence_score=0.91,
    )

    resp = await client.get(f"/audit/{run_id}")
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) >= 1
    assert entries[0]["run_id"] == run_id
    assert entries[0]["agent_id"] == "fastapi"


async def test_audit_summary_shape(client: AsyncClient):
    from orchestration.observability.audit_ledger import AuditLedger

    ledger = AuditLedger()
    run_id = f"itest-summary-{uuid.uuid4()}"
    await ledger.record(
        run_id=run_id,
        agent_id="postgresql",
        task_description="create schema",
        patch_metadata={
            "task_type": "bug_fix",
            "total_files": 1,
            "total_lines": 10,
            "within_budget": True,
            "requires_approval": False,
            "violation_reason": None,
            "risk_level": "low",
            "semantic_summary": ["✅ Added schema migration"],
            "search_replace_blocks": "",
        },
        validation_passed=True,
        confidence_score=0.95,
    )

    resp = await client.get(f"/audit/{run_id}/summary")
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["run_id"] == run_id
    assert summary["total_agents"] >= 1
    assert "risk_distribution" in summary


# ─────────────────────────────────────────────────────────────────────────────
# 9. Orchestration Routes
# ─────────────────────────────────────────────────────────────────────────────

async def test_orchestration_status_not_found(client: AsyncClient):
    resp = await client.get(f"/api/orchestration/status/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_orchestration_agent_output_not_found(client: AsyncClient):
    resp = await client.get(f"/api/orchestration/agent/{uuid.uuid4()}/fastapi/output")
    assert resp.status_code == 404


async def test_orchestration_task_graph_not_found(client: AsyncClient):
    resp = await client.get(f"/api/orchestration/plan/{uuid.uuid4()}/task-graph")
    assert resp.status_code == 404


async def test_develop_project_no_agents_streams_error(client: AsyncClient, created_project: dict):
    """POST /projects/develop with no agents must stream a JSON-line error."""
    resp = await client.post(
        "/projects/develop",
        json={
            "project_id": created_project["id"],
            "prompt": "build an app",
            "selected_agent_ids": [],
        },
    )
    assert resp.status_code == 200
    lines = [ln for ln in resp.text.strip().splitlines() if ln]
    assert len(lines) >= 1
    last = json.loads(lines[-1])
    assert last["type"] == "error"
    assert "agent" in last["message"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# 10. Diff Budget & Patch Generator (pure service-level — no DB)
# ─────────────────────────────────────────────────────────────────────────────

def test_patch_generator_full_pipeline():
    from orchestration.generation.patch_generator import PatchGenerator

    agent_output = (
        "# FILE: models/user.py\n"
        "from pydantic import BaseModel\n\n"
        "class User(BaseModel):\n"
        "    id: int\n"
        "    name: str\n\n"
        "# FILE: routes/user_route.py\n"
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n\n"
        "@router.get('/users')\n"
        "async def list_users():\n"
        "    return []\n"
    )
    gen = PatchGenerator()
    result = gen.process(
        agent_output=agent_output,
        task_description="add user model and API route",
    )

    assert result.total_files == 2
    assert result.total_lines > 0
    assert result.budget is not None
    assert "<<<<<<< SEARCH" in result.search_replace_blocks
    assert len(result.semantic_summary) >= 1


def test_bug_fix_budget_exceeded():
    from orchestration.generation.diff_budget import DiffBudget, TaskType

    budget = DiffBudget()
    result = budget.check(files_changed=3, lines_changed=50, task_type=TaskType.BUG_FIX)
    assert result.within_budget is False
    assert result.requires_approval is True
    assert result.overage_pct > 1.0


def test_risk_level_inference():
    from orchestration.generation.patch_generator import PatchGenerator, FilePatch

    gen = PatchGenerator()
    assert gen.infer_risk_level([FilePatch(filename="auth/token.py", content="SECRET=1")]) == "high"
    assert gen.infer_risk_level([FilePatch(filename="routes/api.py", content="@router.get('/')")]) == "medium"
    assert gen.infer_risk_level([FilePatch(filename="docs/README.md", content="# docs")]) == "low"


# ─────────────────────────────────────────────────────────────────────────────
# 11. Ponytail Adapter (pure service-level — no DB)
# ─────────────────────────────────────────────────────────────────────────────

def test_ponytail_preamble_full_mode():
    from orchestration.agents.ponytail_adapter import get_ponytail_preamble

    preamble = get_ponytail_preamble("full")
    assert "Ponytail" in preamble
    assert len(preamble) > 100


def test_ponytail_preamble_off_returns_empty():
    from orchestration.agents.ponytail_adapter import get_ponytail_preamble

    assert get_ponytail_preamble("off") == ""


def test_ponytail_inject_into_prompt():
    from orchestration.agents.ponytail_adapter import inject_into_prompt

    result = inject_into_prompt("You are a FastAPI agent.", mode="full")
    assert "You are a FastAPI agent." in result
    assert "Ponytail" in result


# ─────────────────────────────────────────────────────────────────────────────
# 12. Knowledge Service (service-level — no DB needed for chunking)
# ─────────────────────────────────────────────────────────────────────────────

def test_chunk_text_small():
    from services.knowledge_service import KnowledgeService

    svc = KnowledgeService()
    assert svc.chunk_text("short text") == ["short text"]


def test_chunk_text_large_splits_correctly():
    from services.knowledge_service import KnowledgeService

    svc = KnowledgeService()
    chunks = svc.chunk_text("x" * 2000, max_chars=800, overlap=100)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 800


async def test_prepare_agent_context_unknown_agent_does_not_raise(client: AsyncClient):
    """
    prepare_agent_context with an unknown agent name should return '' or a fallback string.
    The `client` fixture ensures the DB is connected.
    """
    from services.knowledge_service import KnowledgeService

    svc = KnowledgeService()
    ctx = await svc.prepare_agent_context(
        agent_name="nonexistent_agent_xyz_99",
        chat_session_id=str(uuid.uuid4()),
        task="do something useful",
    )
    assert isinstance(ctx, str)


# ─────────────────────────────────────────────────────────────────────────────
# 13. Database Connectivity (via the lifespan-managed pool)
# ─────────────────────────────────────────────────────────────────────────────

async def test_database_basic_query(client: AsyncClient):
    """SELECT 1 — confirms pool is alive inside the current event loop."""
    conn = await database.get_conn()
    try:
        result = await conn.fetchval("SELECT 1")
        assert result == 1
    finally:
        await database.release_conn(conn)


async def test_agents_table_exists(client: AsyncClient):
    conn = await database.get_conn()
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM agents")
        assert isinstance(count, int)
    finally:
        await database.release_conn(conn)


async def test_shared_knowledge_table_exists(client: AsyncClient):
    conn = await database.get_conn()
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM shared_knowledge")
        assert isinstance(count, int)
    finally:
        await database.release_conn(conn)


async def test_chat_sessions_table_exists(client: AsyncClient):
    conn = await database.get_conn()
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM chat_sessions")
        assert isinstance(count, int)
    finally:
        await database.release_conn(conn)


async def test_pipeline_execution_plans_table_exists(client: AsyncClient):
    conn = await database.get_conn()
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM pipeline_execution_plans")
        assert isinstance(count, int)
    finally:
        await database.release_conn(conn)


async def test_audit_ledger_table_exists(client: AsyncClient):
    conn = await database.get_conn()
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM agent_audit_log")
        assert isinstance(count, int)
    finally:
        await database.release_conn(conn)


async def test_agent_memories_table_exists(client: AsyncClient):
    conn = await database.get_conn()
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM agent_memories")
        assert isinstance(count, int)
    finally:
        await database.release_conn(conn)


async def test_agent_executions_table_exists(client: AsyncClient):
    conn = await database.get_conn()
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM agent_executions")
        assert isinstance(count, int)
    finally:
        await database.release_conn(conn)
