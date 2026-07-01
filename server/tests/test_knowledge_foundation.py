import pytest
import uuid
import hashlib
from datetime import datetime, timezone
from db.database import database
from knowledge.schema import KnowledgeEntry
from knowledge.store import KnowledgeStore
from knowledge.sync_manager import sync_manager
from knowledge.update_pipeline import update_pipeline
from knowledge.reflection import MemoryReflectionEngine
from services.knowledge_service import knowledge_service

# 1. Test Shared Knowledge Semantic Search & Storage
@pytest.mark.asyncio
async def test_shared_knowledge_semantic_search():
    await database.connect()
    id_db = f"test-shared-db-{uuid.uuid4()}"
    id_css = f"test-shared-css-{uuid.uuid4()}"
    
    entry_db = KnowledgeEntry(
        id=id_db,
        content="Always configure connection pooling for postgresql database with max size 20.",
        version=1,
        timestamp=datetime.now(timezone.utc),
        source_agent="postgresql",
        priority="high",
        tags=["database", "pool"]
    )
    
    entry_css = KnowledgeEntry(
        id=id_css,
        content="Use dark mode variables with CSS custom property overrides for component styling.",
        version=1,
        timestamp=datetime.now(timezone.utc),
        source_agent="streamlit",
        priority="low",
        tags=["css", "theme"]
    )
    
    try:
        # Save entries (which automatically generates embeddings in sync_manager.add_knowledge)
        res_db = await sync_manager.add_knowledge(entry_db.model_dump())
        res_css = await sync_manager.add_knowledge(entry_css.model_dump())
        
        assert res_db["success"] is True
        assert res_css["success"] is True
        
        # Test semantic search 1: Database query
        db_results = await sync_manager.semantic_search_shared_knowledge("database connection pool max size limit", limit=5)
        assert len(db_results) >= 1
        best_match_id = db_results[0][0].id
        assert best_match_id == id_db
        
        # Test semantic search 2: CSS query
        css_results = await sync_manager.semantic_search_shared_knowledge("component themes styling custom variable colors", limit=5)
        assert len(css_results) >= 1
        assert css_results[0][0].id == id_css
        
    finally:
        # Clean up
        try:
            conn = await database.get_conn()
            try:
                await conn.execute("DELETE FROM shared_knowledge WHERE id IN ($1, $2)", id_db, id_css)
            finally:
                await database.release_conn(conn)
        finally:
            await database.disconnect()

# 2. Test Continuous Update Pipeline
@pytest.mark.asyncio
async def test_knowledge_update_pipeline():
    await database.connect()
    
    # Register mock agent source
    source_id = uuid.uuid4()
    url = f"https://mock-docs-{uuid.uuid4()}.com"
    
    try:
        conn = await database.get_conn()
        try:
            # Fetch or create a test agent
            agent_row = await conn.fetchrow("SELECT id FROM agents LIMIT 1")
            if not agent_row:
                agent_id = uuid.uuid4()
                await conn.execute(
                    "INSERT INTO agents (id, name, is_core, version) VALUES ($1, 'Test Agent', TRUE, '1.0.0')",
                    agent_id
                )
            else:
                agent_id = agent_row["id"]
                
            await conn.execute(
                "INSERT INTO agent_sources (id, agent_id, url, source_type, is_active, last_scraped_at) VALUES ($1, $2, $3, 'website', TRUE, NULL)",
                source_id, agent_id, url
            )
        finally:
            await database.release_conn(conn)

        source_record = {
            "id": source_id,
            "agent_id": agent_id,
            "url": url,
            "agent_name": "Test Agent"
        }
        
        # Override fetch_source_content to return fixed strings
        original_fetch = update_pipeline.fetch_source_content
        
        try:
            # First scrape: Content A
            content_a = "FastAPI documentation chunk A: Use APIRouter for route modularity and fast execution."
            update_pipeline.fetch_source_content = lambda u: content_a
            
            res1 = await update_pipeline.refresh_source(source_record)
            assert res1["success"] is True
            assert res1["action"] == "updated"
            assert res1["version"] == 1
            
            # Verify chunks are inserted in DB
            conn = await database.get_conn()
            try:
                chunks = await conn.fetch("SELECT id, content_hash, metadata FROM agent_knowledge WHERE source_id = $1", source_id)
                assert len(chunks) >= 1
            finally:
                await database.release_conn(conn)
            
            # Second scrape: Identical content (should skip)
            res2 = await update_pipeline.refresh_source(source_record)
            assert res2["success"] is True
            assert res2["action"] == "skipped"
            
            # Third scrape: Content B (should update & increment version)
            content_b = "FastAPI documentation chunk B: Always declare query params with proper default Pydantic types."
            update_pipeline.fetch_source_content = lambda u: content_b
            
            res3 = await update_pipeline.refresh_source(source_record)
            assert res3["success"] is True
            assert res3["action"] == "updated"
            assert res3["version"] == 2
            
            # Verify old chunks were deleted and new chunks are inserted
            conn = await database.get_conn()
            try:
                new_chunks = await conn.fetch("SELECT content, metadata FROM agent_knowledge WHERE source_id = $1", source_id)
                assert len(new_chunks) >= 1
                assert any("Pydantic" in r["content"] for r in new_chunks)
            finally:
                await database.release_conn(conn)
            
            # Test Validation logic
            invalid_content = "404 Not Found error page"
            update_pipeline.fetch_source_content = lambda u: invalid_content
            res_invalid = await update_pipeline.refresh_source(source_record)
            assert res_invalid["success"] is False
            assert "validation" in res_invalid["reason"].lower()
            
        finally:
            update_pipeline.fetch_source_content = original_fetch
            
    finally:
        # Clean up database records
        try:
            conn = await database.get_conn()
            try:
                await conn.execute("DELETE FROM agent_knowledge WHERE source_id = $1", source_id)
                await conn.execute("DELETE FROM agent_sources WHERE id = $1", source_id)
            finally:
                await database.release_conn(conn)
        finally:
            await database.disconnect()

# 3. Test Reflection Engine
@pytest.mark.asyncio
async def test_memory_reflection_engine(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY_1", "")
    
    task = "Build a FastAPI POST endpoint to save review comments with postgresql integration."
    output = """
    @router.post("/reviews")
    async def create_review(review: ReviewSchema, db = Depends(get_db)):
        return await db.reviews.insert(review)
    """
    
    reflections = await MemoryReflectionEngine.extract_reflections(task, output)
    assert "learned_info" in reflections
    assert "decision" in reflections
    assert "reasoning" in reflections
    assert "outcome" in reflections
    
    assert len(reflections["learned_info"]) > 5
    assert len(reflections["decision"]) > 5

# 4. Test Graph and Service Integration
@pytest.mark.asyncio
async def test_agent_context_integration():
    await database.connect()
    
    # Insert a shared knowledge entry representing project conventions
    shared_id = f"test-context-shared-{uuid.uuid4()}"
    
    try:
        conn = await database.get_conn()
        try:
            # Fetch or create a test agent
            agent_row = await conn.fetchrow("SELECT id, name FROM agents LIMIT 1")
            if not agent_row:
                agent_id = uuid.uuid4()
                await conn.execute(
                    "INSERT INTO agents (id, name, is_core, version) VALUES ($1, 'Test Agent', TRUE, '1.0.0')",
                    agent_id
                )
                agent_name = "Test Agent"
            else:
                agent_name = agent_row["name"]
        finally:
            await database.release_conn(conn)

        shared_entry = KnowledgeEntry(
            id=shared_id,
            content="Convention: Use uppercase table names for all database creations in this project.",
            version=1,
            timestamp=datetime.now(timezone.utc),
            source_agent=agent_name,
            priority="medium",
            tags=["database", "convention"]
        )
        
        await sync_manager.add_knowledge(shared_entry.model_dump())
        
        # Prepare context for the agent doing a database task
        chat_session_id = str(uuid.uuid4())
        task_description = "Create database schema reviews table."
        
        context_block = await knowledge_service.prepare_agent_context(
            agent_name=agent_name,
            chat_session_id=chat_session_id,
            task=task_description
        )
        
        # Verify the context block contains the shared convention
        assert "Shared Project Understanding" in context_block
        assert "Convention: Use uppercase table names" in context_block
        
    finally:
        try:
            conn = await database.get_conn()
            try:
                await conn.execute("DELETE FROM shared_knowledge WHERE id = $1", shared_id)
            finally:
                await database.release_conn(conn)
        finally:
            await database.disconnect()
