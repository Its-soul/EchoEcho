from ..config import config
from ..logger import get_logger
from ..services.qdrant_service import QdrantService


logger = get_logger(__name__)


class VectorSearchAgent:
    def __init__(self, qdrant_service: QdrantService | None = None) -> None:
        self.qdrant_service = qdrant_service or QdrantService()

    def run(self, lyrics: str) -> dict:
        try:
            matches = self.qdrant_service.search_lyrics(
                lyrics,
                limit=config.vector_search_top_k,
            )
            return {"matches": matches}
        except Exception as exc:
            logger.info("Vector search unavailable: %s", exc)
            return {
                "matches": [],
                "error": str(exc),
            }
