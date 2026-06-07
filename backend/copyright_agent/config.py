import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CopyrightAgentConfig:
    qdrant_url: str = os.getenv("COPYRIGHT_QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str | None = os.getenv("COPYRIGHT_QDRANT_API_KEY")
    qdrant_collection: str = os.getenv("COPYRIGHT_QDRANT_COLLECTION", "song_lyrics")
    embedding_model: str = os.getenv("COPYRIGHT_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("COPYRIGHT_OPENAI_MODEL", "gpt-4o-mini")
    llm_retries: int = int(os.getenv("COPYRIGHT_LLM_RETRIES", "3"))
    local_similarity_top_k: int = int(os.getenv("COPYRIGHT_LOCAL_SIMILARITY_TOP_K", "5"))
    vector_search_top_k: int = int(os.getenv("COPYRIGHT_VECTOR_SEARCH_TOP_K", "5"))
    repetition_threshold: float = float(os.getenv("COPYRIGHT_REPETITION_THRESHOLD", "0.25"))


config = CopyrightAgentConfig()
