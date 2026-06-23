import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from main import app
from db.database import database
from knowledge.memory_models import AgentMemoryEntry, AgentExecutionEntry, AgentDecisionEntry
from knowledge.memory_service import memory_service

# Setup DB connection helper
async def init_db():
    if database.pool is None:
        await database.connect()

async def cleanup_db():
    await database.disconnect()

# 1. Test Pydantic Models validation
def test_pydantic_validation():
    # Valid Memory Entry
    m = AgentMemoryEntry(
        agent_id="test-agent",
        context="some context",
        summary="some summary",
        learned_info="learned code patterns",
        tags=["tag1", "tag2"]
    )
    assert m.agent_id == "test-agent"
    assert "tag1" in m.tags

    # Invalid empty agent_id
    with pytest.raises(ValueError):
        AgentMemoryEntry(
            agent_id="",
            context="c",
            summary="s",
            learned_info="l"
        )

    # Valid Execution Entry
    e = AgentExecutionEntry(
        agent_id="test-agent",
        task_id="task-1",
        input_data="input json",
        output_data="output code",
        status="success"
    )
    assert e.status == "success"

    # Invalid status
    with pytest.raises(ValueError):
        AgentExecutionEntry(
            agent_id="test-agent",
            task_id="task-1",
            input_data="input json",
            output_data="output code",
            status="running" # invalid
        )

# 2. Test Memory Service Layer CRUD
@pytest.mark.asyncio
async def test_memory_service_crud():
    await init_db()
    # Pre-clean DB
    conn = await database.get_conn()
    try:
        await conn.execute("DELETE FROM agent_decisions WHERE agent_id = $1", "test-service-agent")
        await conn.execute("DELETE FROM agent_executions WHERE agent_id = $1", "test-service-agent")
        await conn.execute("DELETE FROM agent_memories WHERE agent_id = $1", "test-service-agent")
    finally:
        await database.release_conn(conn)

    try:
        # Create Memory
        m_entry = AgentMemoryEntry(
            agent_id="test-service-agent",
            context="This is a project setup context.",
            summary="Setup FastAPI structure",
            learned_info="Use CORS middleware always.",
            tags=["service-test", "fastapi"]
        )
        saved_m = await memory_service.save_memory(m_entry)
        assert saved_m.id is not None
        assert saved_m.learned_info == "Use CORS middleware always."

        # Fetch Memory by Agent
        fetched_m = await memory_service.get_memories(agent_id="test-service-agent")
        assert len(fetched_m) >= 1
        assert fetched_m[0].id == saved_m.id

        # Fetch Memory by Tag
        tagged_m = await memory_service.get_memories(tags=["service-test"])
        assert len(tagged_m) >= 1
        assert any(item.id == saved_m.id for item in tagged_m)

        # Create Execution
        exec_entry = AgentExecutionEntry(
            agent_id="test-service-agent",
            task_id="service-task-1",
            input_data="setup fastapi route details",
            output_data="api code output snippet",
            status="success",
            metadata={"time_elapsed": 4.5}
        )
        saved_e = await memory_service.save_execution(exec_entry)
        assert saved_e.id is not None
        assert saved_e.metadata.get("time_elapsed") == 4.5

        # Fetch Executions
        fetched_e = await memory_service.get_executions(agent_id="test-service-agent", status="success")
        assert len(fetched_e) >= 1
        assert fetched_e[0].id == saved_e.id

        # Create Decision linked to Execution
        dec_entry = AgentDecisionEntry(
            execution_id=saved_e.id,
            agent_id="test-service-agent",
            decision="Select uvicorn over hypercorn",
            reasoning="Uvicorn performs better in single-core windows setups.",
            outcome="Successful fastapi backend startup."
        )
        saved_d = await memory_service.save_decision(dec_entry)
        assert saved_d.id is not None
        assert saved_d.execution_id == saved_e.id

        # Fetch Decisions
        fetched_d = await memory_service.get_decisions(execution_id=saved_e.id)
        assert len(fetched_d) == 1
        assert fetched_d[0].decision == "Select uvicorn over hypercorn"

        # Cleanup DB
        conn = await database.get_conn()
        try:
            await conn.execute("DELETE FROM agent_decisions WHERE agent_id = $1", "test-service-agent")
            await conn.execute("DELETE FROM agent_executions WHERE agent_id = $1", "test-service-agent")
            await conn.execute("DELETE FROM agent_memories WHERE agent_id = $1", "test-service-agent")
        finally:
            await database.release_conn(conn)
    finally:
        await cleanup_db()

# 3. Test Historical Context & Learning Lookup
@pytest.mark.asyncio
async def test_historical_context_lookup():
    await init_db()
    agent_id = "test-learner-agent"
    # Pre-clean DB
    conn = await database.get_conn()
    try:
        await conn.execute("DELETE FROM agent_decisions WHERE agent_id = $1", agent_id)
        await conn.execute("DELETE FROM agent_executions WHERE agent_id = $1", agent_id)
        await conn.execute("DELETE FROM agent_memories WHERE agent_id = $1", agent_id)
    finally:
        await database.release_conn(conn)

    try:
        task_id = "learn-task-1"
        
        # Setup mock memories and executions
        m_entry = AgentMemoryEntry(
            agent_id=agent_id,
            context="FastAPI learning template",
            summary="FastAPI setup",
            learned_info="Ensure uvicorn is used.",
            tags=["learn-tag"]
        )
        saved_m = await memory_service.save_memory(m_entry)

        exec_entry = AgentExecutionEntry(
            agent_id=agent_id,
            task_id=task_id,
            input_data="input details",
            output_data="output details",
            status="success"
        )
        saved_e = await memory_service.save_execution(exec_entry)

        dec_entry = AgentDecisionEntry(
            execution_id=saved_e.id,
            agent_id=agent_id,
            decision="Use postgres adapter",
            reasoning="Fastpg is not standard",
            outcome="Successful database connection"
        )
        saved_d = await memory_service.save_decision(dec_entry)

        # Lookup historical context
        history = await memory_service.get_historical_context(agent_id=agent_id, task=task_id, tags=["learn-tag"])
        assert len(history["memories"]) >= 1
        assert any(item.id == saved_m.id for item in history["memories"])
        assert len(history["executions"]) >= 1
        assert any(item.id == saved_e.id for item in history["executions"])
        assert len(history["decisions"]) >= 1
        assert any(item.id == saved_d.id for item in history["decisions"])

        # Cleanup DB
        conn = await database.get_conn()
        try:
            await conn.execute("DELETE FROM agent_decisions WHERE agent_id = $1", agent_id)
            await conn.execute("DELETE FROM agent_executions WHERE agent_id = $1", agent_id)
            await conn.execute("DELETE FROM agent_memories WHERE agent_id = $1", agent_id)
        finally:
            await database.release_conn(conn)
    finally:
        await cleanup_db()

# 4. Test API Endpoints
@pytest.mark.asyncio
async def test_memory_api_endpoints():
    await init_db()
    agent_id = "test-api-agent"
    # Pre-clean DB
    conn = await database.get_conn()
    try:
        await conn.execute("DELETE FROM agent_decisions WHERE agent_id = $1", agent_id)
        await conn.execute("DELETE FROM agent_executions WHERE agent_id = $1", agent_id)
        await conn.execute("DELETE FROM agent_memories WHERE agent_id = $1", agent_id)
    finally:
        await database.release_conn(conn)

    try:
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Add memory
            m_payload = {
                "agent_id": agent_id,
                "context": "API endpoint memory context",
                "summary": "API endpoints",
                "learned_info": "Use AsyncClient for tests.",
                "tags": ["api-test-tag"]
            }
            res_m = await client.post("/knowledge/memory/add", json=m_payload)
            assert res_m.status_code == 200
            m_data = res_m.json()
            assert m_data["id"] is not None

            # Get memory
            res_get_m = await client.get(f"/knowledge/memory/get?agent_id={agent_id}")
            assert res_get_m.status_code == 200
            assert len(res_get_m.json()) >= 1

            # Semantic Search API
            res_sem = await client.get(f"/knowledge/memory/semantic-search?query=AsyncClient&agent_id={agent_id}")
            assert res_sem.status_code == 200
            sem_results = res_sem.json()
            assert len(sem_results) >= 1
            assert sem_results[0]["memory"]["id"] == m_data["id"]
            assert "similarity_score" in sem_results[0]

            # Add execution
            e_payload = {
                "agent_id": agent_id,
                "task_id": "api-task-1",
                "input_data": "raw inputs",
                "output_data": "raw outputs",
                "status": "success",
                "metadata": {"roundtrip": 1.2}
            }
            res_e = await client.post("/knowledge/execution/add", json=e_payload)
            assert res_e.status_code == 200
            e_data = res_e.json()
            assert e_data["id"] is not None

            # Add decision
            d_payload = {
                "execution_id": e_data["id"],
                "agent_id": agent_id,
                "decision": "Use httpx",
                "reasoning": "Standard python tool",
                "outcome": "Tests execute fast"
            }
            res_d = await client.post("/knowledge/decision/add", json=d_payload)
            assert res_d.status_code == 200
            d_data = res_d.json()
            assert d_data["id"] is not None

            # Get historical context
            res_hist = await client.get(f"/knowledge/historical-context?agent_id={agent_id}&task=api-task-1&tags=api-test-tag")
            assert res_hist.status_code == 200
            hist_data = res_hist.json()
            assert len(hist_data["memories"]) >= 1
            assert len(hist_data["executions"]) >= 1
            assert len(hist_data["decisions"]) >= 1

        # Cleanup DB
        conn = await database.get_conn()
        try:
            await conn.execute("DELETE FROM agent_decisions WHERE agent_id = $1", agent_id)
            await conn.execute("DELETE FROM agent_executions WHERE agent_id = $1", agent_id)
            await conn.execute("DELETE FROM agent_memories WHERE agent_id = $1", agent_id)
        finally:
            await database.release_conn(conn)
    finally:
        await cleanup_db()

# 5. Test Semantic Similarity Search & Ranking
@pytest.mark.asyncio
async def test_semantic_similarity_search():
    await init_db()
    agent_id = "test-semantic-ranking"
    # Pre-clean DB
    conn = await database.get_conn()
    try:
        await conn.execute("DELETE FROM agent_memories WHERE agent_id = $1", agent_id)
    finally:
        await database.release_conn(conn)

    try:
        
        # Insert DB-related memory
        m_db = AgentMemoryEntry(
            agent_id=agent_id,
            context="Connecting to postgresql via asyncpg",
            summary="Postgres setup",
            learned_info="Always close pool connections properly."
        )
        saved_db = await memory_service.save_memory(m_db)

        # Insert UI/CSS-related memory
        m_ui = AgentMemoryEntry(
            agent_id=agent_id,
            context="Styling components with custom colors",
            summary="CSS theme setup",
            learned_info="Avoid generic blue color templates."
        )
        saved_ui = await memory_service.save_memory(m_ui)

        # Generate embeddings
        assert saved_db.embedding is not None
        assert len(saved_db.embedding) == 384
        assert saved_ui.embedding is not None
        assert len(saved_ui.embedding) == 384

        # Search for database query
        db_results = await memory_service.semantic_search_memories("asyncpg postgresql pool config", agent_id=agent_id)
        assert len(db_results) >= 1
        assert db_results[0][0].id == saved_db.id
        
        # Search for UI/CSS query
        ui_results = await memory_service.semantic_search_memories("styling css color templates theme", agent_id=agent_id)
        assert len(ui_results) >= 1
        assert ui_results[0][0].id == saved_ui.id

        # Cleanup DB
        conn = await database.get_conn()
        try:
            await conn.execute("DELETE FROM agent_memories WHERE agent_id = $1", agent_id)
        finally:
            await database.release_conn(conn)
    finally:
        await cleanup_db()

