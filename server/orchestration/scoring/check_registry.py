from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from db.database import database
from orchestration.scoring.core_checks import CORE_CHECKS
from orchestration.scoring.custom_check_validator import CheckValidator


CORE_WEIGHT = 1.0
CUSTOM_WEIGHT = 0.7
logger = logging.getLogger(__name__)


class CheckRegistry:
    def __init__(self) -> None:
        self.core_checks: dict[str, Callable[[dict[str, Any], Any], bool]] = dict(CORE_CHECKS)
        self.custom_checks: dict[str, Callable[[dict[str, Any], Any], bool]] = {}
        self.custom_check_agents: dict[str, set[str]] = {}
        self.validator = CheckValidator()

    async def register_custom_check(
        self,
        check_name: str,
        check_fn: Callable[[dict[str, Any], Any], bool],
        agent_id: str,
    ) -> tuple[bool, list[str]]:
        valid, errors = self.validator.validate_custom_check(check_fn, agent_id)
        if not valid:
            return False, errors
        self.custom_checks[check_name] = check_fn
        self.custom_check_agents.setdefault(check_name, set()).add(agent_id)
        await self._persist_registration(check_name, agent_id)
        await self._detect_promotion_candidate(check_name)
        return True, []

    def get_check(self, check_name: str) -> tuple[Callable[[dict[str, Any], Any], bool], float, str] | None:
        if check_name in self.core_checks:
            return self.core_checks[check_name], CORE_WEIGHT, "core"
        if check_name in self.custom_checks:
            return self.custom_checks[check_name], CUSTOM_WEIGHT, "custom"
        return None

    async def _persist_registration(self, check_name: str, agent_id: str) -> None:
        try:
            conn = await database.get_conn()
        except Exception as exc:
            logger.warning("custom_check_registration_persist_skipped", extra={"error": str(exc)})
            return
        try:
            await conn.execute(
                """
                INSERT INTO custom_check_adoption (check_name, agent_id)
                VALUES ($1, $2)
                ON CONFLICT (check_name, agent_id) DO NOTHING
                """,
                check_name,
                agent_id,
            )
            await conn.execute(
                """
                INSERT INTO agent_manifests (agent_id, manifest_json, updated_at)
                VALUES ($1, jsonb_build_object('custom_checks', jsonb_build_array($2::text)), now())
                ON CONFLICT (agent_id) DO UPDATE SET
                  manifest_json = jsonb_set(
                    COALESCE(agent_manifests.manifest_json, '{}'::jsonb),
                    '{custom_checks}',
                    (
                      SELECT jsonb_agg(DISTINCT value)
                      FROM jsonb_array_elements_text(
                        COALESCE(agent_manifests.manifest_json->'custom_checks', '[]'::jsonb) || jsonb_build_array($2::text)
                      ) AS value
                    )
                  ),
                  updated_at = now()
                """,
                agent_id,
                check_name,
            )
        except Exception as exc:
            logger.warning("custom_check_registration_persist_error", extra={"error": str(exc)})
        finally:
            await database.release_conn(conn)

    async def _detect_promotion_candidate(self, check_name: str) -> None:
        adoption_count = len(self.custom_check_agents.get(check_name, set()))
        try:
            conn = await database.get_conn()
        except Exception:
            conn = None
        if conn is not None:
            try:
                adoption_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM custom_check_adoption WHERE check_name = $1",
                    check_name,
                )
            except Exception:
                pass
            finally:
                await database.release_conn(conn)
        if int(adoption_count or 0) >= 5:
            logger.info(
                "PROMOTION CANDIDATE: '%s' adopted by 5+ agents - open a PR to add it to core_checks.py",
                check_name,
            )


default_registry = CheckRegistry()
