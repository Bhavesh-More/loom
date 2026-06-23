import logging
from typing import Any, Dict, List
from knowledge.schema import KnowledgeEntry
from knowledge.store import KnowledgeStore
from knowledge.conflict_resolver import ConflictResolver
from knowledge.propagator import KnowledgePropagator

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, store: KnowledgeStore = None, resolver: ConflictResolver = None, propagator: KnowledgePropagator = None):
        self.store = store or KnowledgeStore()
        self.resolver = resolver or ConflictResolver()
        self.propagator = propagator or KnowledgePropagator()

    async def add_knowledge(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the Sync Flow Pipeline:
        Schema Validation -> Conflict Check -> Version Resolution -> Store in DB -> Propagate -> Log
        """
        # 1. Schema Validation
        try:
            incoming = KnowledgeEntry(**entry_data)
        except Exception as e:
            logger.warning("[SyncManager] Validation failed: %s for data %s", e, entry_data)
            return {
                "success": False,
                "reason": f"validation error: {str(e)}",
                "action": "rejected"
            }

        # 2. Retrieve existing & Resolve Conflicts
        existing = await self.store.get_entry(incoming.id)
        should_write, action = self.resolver.resolve(incoming, existing)

        if not should_write:
            return {
                "success": False,
                "reason": "conflict check: version or timestamp is outdated",
                "action": "rejected"
            }

        # 3. Store in DB
        await self.store.save_entry(incoming)

        # 4. Propagate Update
        await self.propagator.propagate(incoming)

        # 5. Return success PASS Response
        return {
            "success": True,
            "action": action,
            "version": incoming.version
        }

    async def get_all(self) -> List[KnowledgeEntry]:
        """Gets all entries via cached read."""
        return await self.propagator.get_cached_all(self.store.get_all_entries)

    async def get_by_tag(self, tag: str) -> List[KnowledgeEntry]:
        """Gets tag filtered entries via cached read."""
        return await self.propagator.get_cached_tag(tag, self.store.get_entries_by_tag)


# Global singleton sync manager
sync_manager = SyncManager()
