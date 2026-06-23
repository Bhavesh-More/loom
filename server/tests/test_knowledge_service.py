import pytest
import uuid
import json
from datetime import datetime
from services.knowledge_service import KnowledgeService

class FakeConnection:
    def __init__(self):
        self.queries = []
        self.fetch_results = {}
        self.fetchrow_results = {}
        self.transaction_entered = False

    async def fetch(self, query, *args):
        self.queries.append(("fetch", query, args))
        normalized = " ".join(query.strip().split())
        for key, res in self.fetch_results.items():
            if key in normalized:
                return res
        return []

    async def fetchrow(self, query, *args):
        self.queries.append(("fetchrow", query, args))
        normalized = " ".join(query.strip().split())
        for key, res in self.fetchrow_results.items():
            if key in normalized:
                return res
        return None

    async def execute(self, query, *args):
        self.queries.append(("execute", query, args))
        return "OK"

    async def __aenter__(self):
        self.transaction_entered = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def transaction(self):
        return self


class FakeDatabase:
    def __init__(self, conn):
        self.conn = conn

    async def get_conn(self):
        return self.conn

    async def release_conn(self, conn):
        pass


@pytest.mark.asyncio
async def test_chunk_text():
    service = KnowledgeService(db=None)
    text = "A" * 1500
    chunks = service.chunk_text(text, max_chars=800, overlap=100)
    
    assert len(chunks) == 2
    assert chunks[0] == "A" * 800
    assert chunks[1] == "A" * 800


@pytest.mark.asyncio
async def test_sync_agent_knowledge():
    conn = FakeConnection()
    # Mock resolve_agent_id call
    agent_uuid = str(uuid.uuid4())
    conn.fetchrow_results["SELECT id FROM agents"] = {"id": uuid.UUID(agent_uuid)}

    db = FakeDatabase(conn)
    service = KnowledgeService(db=db)

    source_uuid = str(uuid.uuid4())
    content = "This is a test content that is longer and will be synchronized."

    await service.sync_agent_knowledge(
        agent_name_or_id="fastapi",
        source_id=source_uuid,
        content=content,
        metadata={"version": "1.0"},
    )

    assert conn.transaction_entered is True
    # Verify we resolved agent, inserted knowledge chunk, and updated timestamps
    execute_queries = [q for q in conn.queries if q[0] == "execute"]
    assert any("INSERT INTO agent_knowledge" in q[1] for q in execute_queries)
    assert any("UPDATE agents SET last_kb_update" in q[1] for q in execute_queries)
    assert any("UPDATE agent_sources SET last_scraped_at" in q[1] for q in execute_queries)


@pytest.mark.asyncio
async def test_retrieve_knowledge():
    conn = FakeConnection()
    agent_uuid = str(uuid.uuid4())
    conn.fetchrow_results["SELECT id FROM agents"] = {"id": uuid.UUID(agent_uuid)}
    conn.fetch_results["source_type = 'sync_source'"] = [
        {"content": "Chunk 1", "metadata": "{}", "similarity": 0.9},
        {"content": "Chunk 2", "metadata": "{}", "similarity": 0.8},
    ]

    db = FakeDatabase(conn)
    service = KnowledgeService(db=db)

    results = await service.retrieve_knowledge("fastapi", "test query", limit=2)
    assert len(results) == 2
    assert results[0]["content"] == "Chunk 1"
    assert results[1]["content"] == "Chunk 2"


@pytest.mark.asyncio
async def test_record_agent_memory():
    conn = FakeConnection()
    agent_uuid = str(uuid.uuid4())
    conn.fetchrow_results["SELECT id FROM agents"] = {"id": uuid.UUID(agent_uuid)}

    db = FakeDatabase(conn)
    service = KnowledgeService(db=db)

    await service.record_agent_memory("fastapi", "Success learning reflection")
    
    execute_queries = [q for q in conn.queries if q[0] == "execute"]
    assert any("long_term_memory" in q[1] for q in execute_queries)


@pytest.mark.asyncio
async def test_retrieve_agent_memories():
    conn = FakeConnection()
    agent_uuid = str(uuid.uuid4())
    conn.fetchrow_results["SELECT id FROM agents"] = {"id": uuid.UUID(agent_uuid)}
    conn.fetch_results["source_type = 'long_term_memory'"] = [
        {"content": "Memory 1", "metadata": "{}", "similarity": 0.95}
    ]

    db = FakeDatabase(conn)
    service = KnowledgeService(db=db)

    results = await service.retrieve_agent_memories("fastapi", "query", limit=1)
    assert len(results) == 1
    assert results[0]["content"] == "Memory 1"


@pytest.mark.asyncio
async def test_retrieve_execution_history():
    conn = FakeConnection()
    project_uuid = uuid.uuid4()
    conn.fetchrow_results["SELECT project_id FROM chat_sessions"] = {"project_id": project_uuid}
    conn.fetch_results["FROM pipeline_agent_results"] = [
        {"agent_id": "fastapi", "output_json": {"output": "Prior code output"}, "score": 1.0, "created_at": datetime.now()}
    ]

    db = FakeDatabase(conn)
    service = KnowledgeService(db=db)

    chat_session_uuid = str(uuid.uuid4())
    history = await service.retrieve_execution_history("fastapi", chat_session_uuid, limit=1)
    
    assert len(history) == 1
    assert history[0]["output_json"]["output"] == "Prior code output"


@pytest.mark.asyncio
async def test_record_agent_run():
    conn = FakeConnection()
    conn.fetchrow_results["SELECT title FROM chat_sessions"] = {"title": "Test Chat Session"}

    db = FakeDatabase(conn)
    service = KnowledgeService(db=db)

    chat_session_uuid = str(uuid.uuid4())
    await service.record_agent_run("fastapi", chat_session_uuid, "Successful agent generated code")

    execute_queries = [q for q in conn.queries if q[0] == "execute"]
    assert any("INSERT INTO pipeline_execution_plans" in q[1] for q in execute_queries)
    assert any("INSERT INTO pipeline_agent_results" in q[1] for q in execute_queries)


@pytest.mark.asyncio
async def test_prepare_agent_context():
    conn = FakeConnection()
    agent_uuid = str(uuid.uuid4())
    project_uuid = uuid.uuid4()
    conn.fetchrow_results["SELECT id FROM agents"] = {"id": uuid.UUID(agent_uuid)}
    conn.fetchrow_results["SELECT project_id FROM chat_sessions"] = {"project_id": project_uuid}
    
    # Setup mock data for parallel fetches
    conn.fetch_results["source_type = 'sync_source'"] = [
        {"content": "Documentation Chunk Content", "metadata": "{}", "similarity": 0.85}
    ]
    conn.fetch_results["source_type = 'long_term_memory'"] = [
        {"content": "Success learning memory", "metadata": "{}", "similarity": 0.9}
    ]
    conn.fetch_results["FROM pipeline_agent_results"] = [
        {"agent_id": "fastapi", "output_json": {"output": "Past output code block"}, "score": 1.0, "created_at": "2026-06-21"}
    ]

    db = FakeDatabase(conn)
    service = KnowledgeService(db=db)

    chat_session_uuid = str(uuid.uuid4())
    context = await service.prepare_agent_context("fastapi", chat_session_uuid, "Build FastAPI app")

    assert "## Relevant Documentation:" in context
    assert "Documentation Chunk Content" in context
    assert "## Long-Term Learnings & Reflections:" in context
    assert "Success learning memory" in context
    assert "## Successful Prior Outputs:" in context
    assert "Past output code block" in context


def test_vector_literal_formatting():
    from services.knowledge_service import _vector_literal
    assert _vector_literal([0.123456789, -1.5]) == "[0.12345679,-1.50000000]"


@pytest.mark.asyncio
async def test_sync_agent_knowledge_missing_agent():
    conn = FakeConnection()
    conn.fetchrow_results["SELECT id FROM agents"] = None
    db = FakeDatabase(conn)
    service = KnowledgeService(db=db)
    with pytest.raises(ValueError, match="Could not resolve agent"):
        await service.sync_agent_knowledge("invalid_agent", None, "content")


@pytest.mark.asyncio
async def test_sync_agent_knowledge_empty_content():
    conn = FakeConnection()
    agent_uuid = str(uuid.uuid4())
    conn.fetchrow_results["SELECT id FROM agents"] = {"id": uuid.UUID(agent_uuid)}
    db = FakeDatabase(conn)
    service = KnowledgeService(db=db)
    await service.sync_agent_knowledge("fastapi", None, "")
    execute_queries = [q for q in conn.queries if q[0] == "execute"]
    assert len(execute_queries) == 0


@pytest.mark.asyncio
async def test_duplicate_knowledge_on_conflict():
    conn = FakeConnection()
    agent_uuid = str(uuid.uuid4())
    conn.fetchrow_results["SELECT id FROM agents"] = {"id": uuid.UUID(agent_uuid)}
    db = FakeDatabase(conn)
    service = KnowledgeService(db=db)
    await service.sync_agent_knowledge("fastapi", None, "Duplicate content")
    execute_queries = [q for q in conn.queries if q[0] == "execute"]
    upsert_query = next(q[1] for q in execute_queries if "INSERT INTO agent_knowledge" in q[1])
    assert "ON CONFLICT (agent_id, content_hash)" in upsert_query
    assert "DO UPDATE SET" in upsert_query


@pytest.mark.asyncio
async def test_embedding_failure_propagation(monkeypatch):
    async def mock_encode(text):
        raise RuntimeError("Embedding error")
    import services.knowledge_service as ks
    monkeypatch.setattr(ks.embedding_provider, "encode", mock_encode)
    conn = FakeConnection()
    agent_uuid = str(uuid.uuid4())
    conn.fetchrow_results["SELECT id FROM agents"] = {"id": uuid.UUID(agent_uuid)}
    db = FakeDatabase(conn)
    service = KnowledgeService(db=db)
    with pytest.raises(RuntimeError, match="Embedding error"):
        await service.sync_agent_knowledge("fastapi", None, "Some content")


@pytest.mark.asyncio
async def test_transaction_rollback_on_failure():
    class FailingConnection(FakeConnection):
        async def execute(self, query, *args):
            if "INSERT INTO pipeline_agent_results" in query:
                raise RuntimeError("DB Failure")
            return await super().execute(query, *args)
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                self.rolled_back = True

    conn = FailingConnection()
    db = FakeDatabase(conn)
    service = KnowledgeService(db=db)
    conn.fetchrow_results["SELECT title FROM chat_sessions"] = {"title": "Test Title"}
    
    with pytest.raises(RuntimeError, match="DB Failure"):
        await service.record_agent_run("fastapi", str(uuid.uuid4()), "output code")
    
    assert getattr(conn, "rolled_back", False) is True


@pytest.mark.asyncio
async def test_chunker_realistic_input():
    service = KnowledgeService(db=None)
    text = (
        "Loom is a multi-agent Python workspace. "
        "It supports FastAPI backend, React frontend and LangGraph orchestration. "
        "This is the third sentence to increase length. "
        "Fourth sentence provides more characters for testing chunking bounds."
    )
    chunks = service.chunk_text(text, max_chars=80, overlap=20)
    assert len(chunks) > 1
    for idx in range(len(chunks) - 1):
        assert chunks[idx + 1][:10] in chunks[idx]


@pytest.mark.asyncio
async def test_after_agent_execution():
    conn = FakeConnection()
    agent_uuid = str(uuid.uuid4())
    conn.fetchrow_results["SELECT id FROM agents"] = {"id": uuid.UUID(agent_uuid)}
    conn.fetchrow_results["SELECT title FROM chat_sessions"] = {"title": "Session Title"}
    db = FakeDatabase(conn)
    service = KnowledgeService(db=db)
    
    await service.after_agent_execution("fastapi", str(uuid.uuid4()), "task description", "code output")
    
    # Verify execution was recorded and memory saved
    execute_queries = [q for q in conn.queries if q[0] == "execute"]
    assert any("INSERT INTO pipeline_execution_plans" in q[1] for q in execute_queries)
    assert any("INSERT INTO pipeline_agent_results" in q[1] for q in execute_queries)
    assert any("long_term_memory" in q[1] for q in execute_queries)
