-- Create agent_knowledge table for Phase 1 (Knowledge & Learning Infrastructure)
CREATE TABLE IF NOT EXISTS agent_knowledge (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  source_id UUID REFERENCES agent_sources(id) ON DELETE SET NULL, -- NULL for self-generated memories
  source_type TEXT NOT NULL CHECK (source_type IN ('sync_source', 'long_term_memory')),
  content TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  embedding vector(384),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(agent_id, content_hash)
);

-- Index for semantic search using pgvector ivfflat with cosine operations
CREATE INDEX IF NOT EXISTS agent_knowledge_embedding_idx
  ON agent_knowledge USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
