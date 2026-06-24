-- Alter shared_knowledge table to support pgvector semantic retrieval

ALTER TABLE shared_knowledge ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS shared_knowledge_embedding_idx
  ON shared_knowledge USING hnsw (embedding vector_cosine_ops);
