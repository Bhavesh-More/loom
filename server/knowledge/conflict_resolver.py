import logging
from typing import Optional
from knowledge.schema import KnowledgeEntry

logger = logging.getLogger(__name__)

class ConflictResolver:
    @staticmethod
    def resolve(incoming: KnowledgeEntry, existing: Optional[KnowledgeEntry]) -> tuple[bool, str]:
        """
        Determines whether the incoming entry should overwrite the existing one.
        Returns: (should_write, action_or_reason)
        """
        if existing is None:
            return True, "stored"

        # 1. Higher version wins
        if incoming.version > existing.version:
            logger.info(
                "[ConflictResolver] Overwriting entry ID '%s': Incoming version %d is higher than existing version %d (Source: %s -> %s)",
                incoming.id, incoming.version, existing.version, existing.source_agent, incoming.source_agent
            )
            return True, "updated"
        
        if incoming.version < existing.version:
            logger.info(
                "[ConflictResolver] Rejecting entry ID '%s': Incoming version %d is lower than existing version %d",
                incoming.id, incoming.version, existing.version
            )
            return False, "rejected"

        # 2. If same version -> latest timestamp wins
        if incoming.timestamp > existing.timestamp:
            logger.info(
                "[ConflictResolver] Overwriting entry ID '%s' (equal version %d): Incoming timestamp %s is newer than existing timestamp %s (Source: %s -> %s)",
                incoming.id, incoming.version, incoming.timestamp, existing.timestamp, existing.source_agent, incoming.source_agent
            )
            return True, "updated"
        
        logger.info(
            "[ConflictResolver] Rejecting entry ID '%s' (equal version %d): Incoming timestamp %s is older than or equal to existing timestamp %s",
            incoming.id, incoming.version, incoming.timestamp, existing.timestamp
        )
        return False, "rejected"
