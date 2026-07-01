-- Alter agent_memories table to support pgvector semantic retrieval

ALTER TABLE agent_memories ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS agent_memories_embedding_idx
  ON agent_memories USING hnsw (embedding vector_cosine_ops);
