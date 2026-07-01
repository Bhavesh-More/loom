import logging
from context_system.semantic_searcher import embedding_provider

logger = logging.getLogger(__name__)

class MemoryEmbeddingService:
    @staticmethod
    async def generate_embedding(context: str, summary: str, learned_info: str) -> list[float]:
        """
        Combines summary, context, and learned_info into a single text block
        and generates a 384-dimensional vector embedding.
        """
        combined_text = f"Summary: {summary}\nContext: {context}\nLearned Info: {learned_info}"
        return await embedding_provider.encode(combined_text)

    @staticmethod
    async def generate_query_embedding(query: str) -> list[float]:
        """Generates embedding for search queries."""
        return await embedding_provider.encode(query)

memory_embedding_service = MemoryEmbeddingService()
