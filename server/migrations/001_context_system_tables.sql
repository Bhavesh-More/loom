-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Symbol index
CREATE TABLE IF NOT EXISTS symbol_index (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  kind TEXT NOT NULL,
  file_path TEXT NOT NULL,
  repo_path TEXT NOT NULL,
  signature TEXT,
  description TEXT,
  first_seen TIMESTAMPTZ DEFAULT NOW(),
  last_verified TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(name, file_path, repo_path)
);

-- Import graph edges
CREATE TABLE IF NOT EXISTS import_graph_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_path TEXT NOT NULL,
  from_file TEXT NOT NULL,
  to_file TEXT NOT NULL,
  edge_type TEXT NOT NULL,
  verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(repo_path, from_file, to_file)
);

-- Embedding cache
CREATE TABLE IF NOT EXISTS embedding_cache (
  content_hash TEXT PRIMARY KEY,
  file_path TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  embedding vector(384),
  version INTEGER DEFAULT 1,
  valid_until TIMESTAMPTZ,
  active_task_refs TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Domain summaries
CREATE TABLE IF NOT EXISTS domain_summaries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_path TEXT NOT NULL,
  domain_name TEXT NOT NULL,
  summary TEXT NOT NULL,
  central_files TEXT[] NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(repo_path, domain_name)
);

-- Knowledge versions (MVCC)
CREATE TABLE IF NOT EXISTS knowledge_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_path TEXT NOT NULL,
  repo_path TEXT NOT NULL,
  version INTEGER NOT NULL,
  content_hash TEXT NOT NULL,
  is_current BOOLEAN DEFAULT TRUE,
  valid_from TIMESTAMPTZ DEFAULT NOW(),
  valid_until TIMESTAMPTZ,
  active_task_refs TEXT[] DEFAULT '{}'
);

-- Grep hit persistence for Layer 1 telemetry and reuse.
CREATE TABLE IF NOT EXISTS grep_hits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_path TEXT NOT NULL,
  task_id TEXT NOT NULL,
  prompt TEXT NOT NULL,
  file_path TEXT NOT NULL,
  score DOUBLE PRECISION NOT NULL DEFAULT 0,
  line_numbers INTEGER[] DEFAULT '{}',
  snippets TEXT[] DEFAULT '{}',
  matched_terms TEXT[] DEFAULT '{}',
  concepts TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(repo_path, task_id, file_path)
);

-- Persistent task/file memory learned from prior context runs.
CREATE TABLE IF NOT EXISTS context_memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_path TEXT NOT NULL,
  task_signature TEXT NOT NULL,
  prompt TEXT NOT NULL,
  domain TEXT NOT NULL,
  files TEXT[] NOT NULL,
  summary TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(repo_path, task_signature)
);

-- Indexes
CREATE INDEX IF NOT EXISTS embedding_cache_embedding_idx
  ON embedding_cache USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS import_graph_edges_from_idx ON import_graph_edges(repo_path, from_file);
CREATE INDEX IF NOT EXISTS import_graph_edges_to_idx ON import_graph_edges(repo_path, to_file);
CREATE INDEX IF NOT EXISTS symbol_index_name_idx ON symbol_index(repo_path, name);
CREATE INDEX IF NOT EXISTS knowledge_versions_current_idx ON knowledge_versions(repo_path, file_path, is_current);
CREATE INDEX IF NOT EXISTS grep_hits_repo_task_idx ON grep_hits(repo_path, task_id);
CREATE INDEX IF NOT EXISTS context_memories_repo_domain_idx ON context_memories(repo_path, domain);
