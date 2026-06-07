from typing import Any

from ..config import config
from ..logger import get_logger
from .embedding_service import EmbeddingService


logger = get_logger(__name__)


class QdrantService:
    def __init__(
        self,
        collection_name: str | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.collection_name = collection_name or config.qdrant_collection
        self.embedding_service = embedding_service or EmbeddingService()
        self._client = None

    def _load_client(self):
        if self._client is not None:
            return self._client

        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise RuntimeError("qdrant-client is required for vector search.") from exc

        kwargs: dict[str, Any] = {"url": config.qdrant_url}
        if config.qdrant_api_key:
            kwargs["api_key"] = config.qdrant_api_key
        self._client = QdrantClient(**kwargs)
        return self._client

    def search_lyrics(self, lyrics: str, limit: int | None = None) -> list[dict]:
        limit = limit or config.vector_search_top_k
        client = self._load_client()

        if hasattr(client, "collection_exists") and not client.collection_exists(
            self.collection_name
        ):
            raise RuntimeError(
                f"Qdrant collection '{self.collection_name}' does not exist."
            )

        vector = self.embedding_service.embed_text(lyrics)

        try:
            result = client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=limit,
                with_payload=True,
            )
        except AttributeError:
            result = client.query_points(
                collection_name=self.collection_name,
                query=vector,
                limit=limit,
                with_payload=True,
            ).points

        matches: list[dict] = []
        for point in result:
            payload = point.payload or {}
            matches.append(
                {
                    "title": payload.get("title", ""),
                    "artist": payload.get("artist", ""),
                    "lyrics": payload.get("lyrics", ""),
                    "score": float(getattr(point, "score", 0.0)),
                }
            )
        return matches
