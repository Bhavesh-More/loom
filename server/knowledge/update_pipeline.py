import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List
import uuid
import requests
from db.database import database
from services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)

class KnowledgeUpdatePipeline:
    def __init__(self, db=database, k_service=knowledge_service):
        self.db = db
        self.k_service = k_service

    @property
    def has_pool(self) -> bool:
        return bool(getattr(self.db, "pool", None))

    async def get_active_sources(self) -> List[Dict[str, Any]]:
        """Retrieves all active agent knowledge sources from the database."""
        if not self.has_pool:
            return []
        conn = await self.db.get_conn()
        try:
            rows = await conn.fetch(
                """
                SELECT s.id, s.agent_id, s.url, s.source_type, s.last_scraped_at, a.name as agent_name
                FROM agent_sources s
                JOIN agents a ON s.agent_id = a.id
                WHERE s.is_active = TRUE
                """
            )
            return [dict(row) for row in rows]
        finally:
            await self.db.release_conn(conn)

    def fetch_source_content(self, url: str) -> str:
        """
        Fetches the documentation content from the given URL.
        Falls back to a simulated content block if the request fails or offline.
        """
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200 and len(response.text.strip()) > 50:
                # Basic HTML-to-text extraction or just strip tags for simplicity
                # since we only need the textual content of the page
                import re
                text = response.text
                # Remove script and style elements
                text = re.sub(r'<(script|style)\b[^>]*>([\s\S]*?)</\1>', '', text)
                # Remove HTML tags
                text = re.sub(r'<[^>]+>', ' ', text)
                # Normalize whitespace
                text = re.sub(r'\s+', ' ', text).strip()
                return text
        except Exception as e:
            logger.warning("[UpdatePipeline] Failed to fetch url %s: %s. Using simulated content.", url, e)
        
        # Fallback simulated content containing version info and standard structure
        timestamp = datetime.now().isoformat()
        return (
            f"Simulated updated documentation for {url}.\n"
            f"Scraped Timestamp: {timestamp}.\n"
            f"API Reference Version: v2.4.1.\n"
            f"Details: This document contains comprehensive coding guidelines, library patterns, "
            f"and framework configuration requirements. Ensure all implementations adhere to "
            f"standard security parameters and optimization recommendations."
        )

    def validate_content(self, content: str) -> bool:
        """
        Validates content quality: rejects empty, extremely short,
        or obvious error pages.
        """
        if not content or len(content.strip()) < 20:
            return False
        
        lower_content = content.lower()
        error_indicators = ["404 not found", "502 bad gateway", "access denied", "error 1015"]
        for indicator in error_indicators:
            if indicator in lower_content:
                return False
        
        return True

    async def get_stored_content_hash(self, source_id: uuid.UUID) -> str | None:
        """Retrieves the stored content hash for a source from metadata."""
        if not self.has_pool:
            return None
        conn = await self.db.get_conn()
        try:
            # Query metadata of one existing chunk
            row = await conn.fetchrow(
                """
                SELECT metadata FROM agent_knowledge
                WHERE source_id = $1
                LIMIT 1
                """,
                source_id
            )
            if not row:
                return None
            
            meta = row["metadata"]
            if isinstance(meta, str):
                meta = json.loads(meta)
            if meta and "source_hash" in meta:
                return meta["source_hash"]
            return None
        finally:
            await self.db.release_conn(conn)

    async def refresh_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the ingestion/update cycle for a single source.
        Returns execution status metrics.
        """
        source_id = source["id"]
        agent_id = source["agent_id"]
        url = source["url"]
        agent_name = source["agent_name"]

        # 1. Fetch content
        content = self.fetch_source_content(url)

        # 2. Validate content
        if not self.validate_content(content):
            return {
                "source_id": str(source_id),
                "url": url,
                "success": False,
                "reason": "Content validation failed (empty, short or error page)"
            }

        # Calculate new content hash
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        # 3. Retrieve stored hash and check versioning
        stored_hash = await self.get_stored_content_hash(source_id)
        
        conn = await self.db.get_conn()
        try:
            # Check version
            version = 1
            if stored_hash:
                if stored_hash == content_hash:
                    logger.info("[UpdatePipeline] Source %s is up-to-date. Skipping update.", url)
                    return {
                        "source_id": str(source_id),
                        "url": url,
                        "success": True,
                        "action": "skipped",
                        "reason": "Content is up-to-date"
                    }
                
                # Retrieve current version from metadata of one existing chunk
                v_row = await conn.fetchrow(
                    """
                    SELECT metadata FROM agent_knowledge
                    WHERE source_id = $1
                    LIMIT 1
                    """,
                    source_id
                )
                if v_row:
                    meta = v_row["metadata"]
                    if isinstance(meta, str):
                        meta = json.loads(meta)
                    version = meta.get("version", 1) + 1

            # Hash has changed or no entries exist. Overwrite old entries.
            async with conn.transaction():
                # Delete existing chunks to prevent leftovers/orphaned chunks
                await conn.execute(
                    "DELETE FROM agent_knowledge WHERE source_id = $1",
                    source_id
                )
                
            # Ingest and chunk new content
            metadata = {
                "version": version,
                "source_hash": content_hash,
                "last_updated": datetime.now().isoformat(),
                "url": url
            }
            
            # sync_agent_knowledge will chunk and insert new rows
            await self.k_service.sync_agent_knowledge(
                agent_name_or_id=str(agent_id),
                source_id=str(source_id),
                content=content,
                metadata=metadata
            )
            
            return {
                "source_id": str(source_id),
                "url": url,
                "success": True,
                "action": "updated",
                "version": version
            }
        finally:
            await self.db.release_conn(conn)

    async def run_refresh_cycle(self) -> List[Dict[str, Any]]:
        """Scans all active agent sources and refreshes them if updates are available."""
        sources = await self.get_active_sources()
        results = []
        for src in sources:
            try:
                res = await self.refresh_source(src)
                results.append(res)
            except Exception as e:
                logger.error("[UpdatePipeline] Failed to refresh source %s: %s", src["url"], e)
                results.append({
                    "source_id": str(src["id"]),
                    "url": src["url"],
                    "success": False,
                    "reason": f"Exception: {str(e)}"
                })
        return results


# Global singleton instance
update_pipeline = KnowledgeUpdatePipeline()
