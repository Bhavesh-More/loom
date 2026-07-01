-- Create shared_knowledge table for Phase 1
CREATE TABLE IF NOT EXISTS shared_knowledge (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    version INTEGER NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    source_agent TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('low','medium','high')),
    tags TEXT[] DEFAULT '{}'
);
