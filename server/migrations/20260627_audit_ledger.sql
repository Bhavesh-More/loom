-- Semantic audit ledger for the Loom orchestration pipeline.
-- Records every agent change with full provenance: who, what, why, risk.
-- Created: 2026-06-27 (Phase 4 of Final Research implementation)

CREATE TABLE IF NOT EXISTS agent_audit_log (
    id              BIGSERIAL PRIMARY KEY,
    run_id          TEXT        NOT NULL,
    agent_id        TEXT        NOT NULL,
    task_id         TEXT,
    task_description TEXT,

    -- What changed
    files_changed   INTEGER     NOT NULL DEFAULT 0,
    lines_changed   INTEGER     NOT NULL DEFAULT 0,
    task_type       TEXT        NOT NULL DEFAULT 'uncategorized',

    -- Risk & compliance
    risk_level      TEXT        NOT NULL DEFAULT 'low'   CHECK (risk_level IN ('low', 'medium', 'high')),
    within_budget   BOOLEAN     NOT NULL DEFAULT TRUE,
    requires_approval BOOLEAN   NOT NULL DEFAULT FALSE,
    violation_reason TEXT,

    -- Integration status
    integration_status TEXT     NOT NULL DEFAULT 'pending'
                                CHECK (integration_status IN ('pending', 'merged', 'rejected', 'needs_review')),
    build_status    TEXT        NOT NULL DEFAULT 'unknown'
                                CHECK (build_status IN ('unknown', 'passed', 'failed', 'skipped')),
    validation_passed BOOLEAN   NOT NULL DEFAULT FALSE,
    confidence_score NUMERIC(5,4),

    -- Human-readable output
    semantic_summary JSONB       NOT NULL DEFAULT '[]',

    -- Full patch output (SEARCH/REPLACE blocks)
    patch_blocks    TEXT,

    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_audit_log_run_id   ON agent_audit_log (run_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_agent_id ON agent_audit_log (agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created  ON agent_audit_log (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_risk     ON agent_audit_log (risk_level);
