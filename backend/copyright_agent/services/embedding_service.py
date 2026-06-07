from ..config import config


class EmbeddingService:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or config.embedding_model
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required for embedding generation."
            ) from exc

        self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_text(self, text: str) -> list[float]:
        model = self._load_model()
        vector = model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        model = self._load_model()
        vectors = model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]
