"""
Tests for the semantic audit ledger (Phase 4).
Uses a temporary directory for local JSONL writes — no DB required.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from orchestration.observability.audit_ledger import AuditEntry, AuditLedger


@pytest.fixture
def tmp_ledger(tmp_path: Path) -> AuditLedger:
    """Return an AuditLedger that writes to a temp directory."""
    return AuditLedger(log_dir=tmp_path)


class TestAuditEntry:

    def test_entry_defaults(self):
        entry = AuditEntry(run_id="run-1", agent_id="fastapi")
        assert entry.risk_level == "low"
        assert entry.within_budget is True
        assert entry.integration_status == "pending"
        assert entry.build_status == "unknown"
        assert entry.semantic_summary == []

    def test_entry_to_dict(self):
        entry = AuditEntry(
            run_id="run-1",
            agent_id="postgresql",
            files_changed=2,
            lines_changed=40,
            risk_level="medium",
        )
        d = entry.to_dict()
        assert d["agent_id"] == "postgresql"
        assert d["files_changed"] == 2
        assert d["risk_level"] == "medium"

    def test_entry_has_timestamp(self):
        entry = AuditEntry(run_id="run-1", agent_id="auth")
        assert "T" in entry.created_at  # ISO 8601 format


class TestAuditLedger:

    async def test_record_writes_local_jsonl(self, tmp_ledger: AuditLedger, tmp_path: Path):
        """record() should create a JSONL file with the entry."""
        with patch.object(tmp_ledger, "_write_supabase", new=AsyncMock()):
            entry = await tmp_ledger.record(
                run_id="run-test-1",
                agent_id="fastapi",
                task_description="Build REST API",
                patch_metadata={
                    "total_files": 2,
                    "total_lines": 45,
                    "task_type": "small_feature",
                    "risk_level": "medium",
                    "within_budget": True,
                    "requires_approval": False,
                    "semantic_summary": ["✅ Added 3 API routes in routers/items.py"],
                },
                validation_passed=True,
                confidence_score=0.91,
            )

        log_file = tmp_path / "run-test-1.jsonl"
        assert log_file.exists()
        with log_file.open() as f:
            data = json.loads(f.read().strip())

        assert data["agent_id"] == "fastapi"
        assert data["files_changed"] == 2
        assert data["risk_level"] == "medium"
        assert data["validation_passed"] is True
        assert data["confidence_score"] == pytest.approx(0.91)
        assert len(data["semantic_summary"]) == 1

    async def test_record_returns_audit_entry(self, tmp_ledger: AuditLedger):
        with patch.object(tmp_ledger, "_write_supabase", new=AsyncMock()):
            entry = await tmp_ledger.record(
                run_id="run-test-2",
                agent_id="postgresql",
                task_description="Design database schema",
            )
        assert isinstance(entry, AuditEntry)
        assert entry.agent_id == "postgresql"

    async def test_record_with_no_patch_metadata(self, tmp_ledger: AuditLedger):
        """Should not crash when patch_metadata is None."""
        with patch.object(tmp_ledger, "_write_supabase", new=AsyncMock()):
            entry = await tmp_ledger.record(
                run_id="run-test-3",
                agent_id="all_rounder",
                task_description="Generate README",
                patch_metadata=None,
            )
        assert entry.files_changed == 0
        assert entry.risk_level == "low"

    async def test_get_entries_from_local_jsonl(self, tmp_ledger: AuditLedger, tmp_path: Path):
        """get_entries() should fall back to JSONL if DB is unavailable."""
        with patch.object(tmp_ledger, "_write_supabase", new=AsyncMock()):
            await tmp_ledger.record(
                run_id="run-read-test",
                agent_id="fastapi",
                task_description="task 1",
            )
            await tmp_ledger.record(
                run_id="run-read-test",
                agent_id="postgresql",
                task_description="task 2",
            )

        # Patch database import inside get_entries so it raises, forcing JSONL fallback
        with patch("db.database.database") as mock_db:
            mock_db.get_conn = AsyncMock(side_effect=Exception("no DB"))
            entries = await tmp_ledger.get_entries("run-read-test")

        assert len(entries) == 2
        agent_ids = [e["agent_id"] for e in entries]
        assert "fastapi" in agent_ids
        assert "postgresql" in agent_ids

    async def test_get_entries_returns_empty_for_missing_run(self, tmp_ledger: AuditLedger):
        with patch("db.database.database") as mock_db:
            mock_db.get_conn = AsyncMock(side_effect=Exception("no DB"))
            entries = await tmp_ledger.get_entries("nonexistent-run")
        assert entries == []

    async def test_supabase_failure_does_not_crash(self, tmp_ledger: AuditLedger):
        """DB write failure should be silently swallowed — pipeline must not stop."""
        with patch.object(
            tmp_ledger, "_write_supabase",
            new=AsyncMock(side_effect=Exception("DB is down"))
        ):
            entry = await tmp_ledger.record(
                run_id="run-db-fail",
                agent_id="fastapi",
                task_description="test resilience",
            )
        assert entry.agent_id == "fastapi"

    async def test_local_write_creates_dir(self, tmp_path: Path):
        """Log directory should be auto-created if it doesn't exist."""
        deep_dir = tmp_path / "deep" / "nested" / "logs"
        ledger = AuditLedger(log_dir=deep_dir)
        assert not deep_dir.exists()

        await ledger._write_local("test-run", AuditEntry(run_id="test-run", agent_id="x"))
        assert deep_dir.exists()
        assert (deep_dir / "test-run.jsonl").exists()
