import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _optional_env(name: str) -> str | None:
    value = _env(name)
    return value or None


def _int_env(name: str, default: int) -> int:
    value = _env(name, str(default))
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc


def _float_env(name: str, default: float) -> float:
    value = _env(name, str(default))
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a float.") from exc


def _bool_env(name: str, default: bool = False) -> bool:
    value = _env(name, str(default)).lower()
    return value in {"1", "true", "yes", "on"}


def _tuple_env(name: str, default: str) -> tuple[str, ...]:
    return tuple(
        item.strip().lower()
        for item in _env(name, default).split(",")
        if item.strip()
    )


def _path_env(name: str, default: Path) -> Path:
    value = _env(name)
    return Path(value) if value else default


@dataclass(frozen=True)
class CopyrightAgentConfig:
    app_title: str = _env("APP_TITLE", "Inspiration Safety Advisor")
    app_version: str = _env("APP_VERSION", "2.0.0")
    copyright_check_route: str = _env("COPYRIGHT_CHECK_ROUTE", "/check-copyright")
    log_level: str = _env("LOG_LEVEL", "INFO").upper()

    brave_api_key: str | None = _optional_env("BRAVE_API_KEY")
    serper_api_key: str | None = _optional_env("SERPER_API_KEY")
    tavily_api_key: str | None = _optional_env("TAVILY_API_KEY")
    gemini_api_key: str | None = _optional_env("GEMINI_API_KEY") or _optional_env(
        "GOOGLE_API_KEY"
    )
    google_api_key: str | None = _optional_env("GOOGLE_API_KEY")

    brave_search_url: str = _env(
        "BRAVE_SEARCH_URL",
        "https://api.search.brave.com/res/v1/web/search",
    )
    serper_search_url: str = _env(
        "SERPER_SEARCH_URL",
        "https://google.serper.dev/search",
    )
    tavily_search_url: str = _env("TAVILY_SEARCH_URL", "https://api.tavily.com/search")
    search_provider_priority: tuple[str, ...] = _tuple_env(
        "SEARCH_PROVIDER_PRIORITY",
        "brave,serper,tavily",
    )
    search_timeout_seconds: int = _int_env("SEARCH_TIMEOUT_SECONDS", 8)
    brave_search_count: int = _int_env("BRAVE_SEARCH_COUNT", 5)
    serper_search_count: int = _int_env("SERPER_SEARCH_COUNT", 5)
    tavily_max_results: int = _int_env("TAVILY_MAX_RESULTS", 5)
    tavily_search_depth: str = _env("TAVILY_SEARCH_DEPTH", "basic")

    gemini_model: str = _env("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_retries: int = _int_env("GEMINI_RETRIES", 3)
    gemini_backoff_max_seconds: int = _int_env("GEMINI_BACKOFF_MAX_SECONDS", 4)

    qdrant_url: str = _env("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str | None = _optional_env("QDRANT_API_KEY")
    qdrant_collection: str = _env("QDRANT_COLLECTION", "song_lyrics")
    embedding_model: str = _env("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    local_songs_path: Path = _path_env(
        "LOCAL_SONGS_PATH",
        BASE_DIR / "database" / "songs.json",
    )
    public_domain_phrases_path: Path = _path_env(
        "PUBLIC_DOMAIN_PHRASES_PATH",
        BASE_DIR / "database" / "public_domain_phrases.json",
    )
    public_domain_songs_path: Path = _path_env(
        "PUBLIC_DOMAIN_SONGS_PATH",
        BASE_DIR / "database" / "public_domain_songs.json",
    )

    input_title_or_phrase_max_words: int = _int_env("INPUT_TITLE_OR_PHRASE_MAX_WORDS", 3)
    input_short_lyric_max_words: int = _int_env("INPUT_SHORT_LYRIC_MAX_WORDS", 10)
    input_analysis_confidence: float = _float_env("INPUT_ANALYSIS_CONFIDENCE", 0.95)

    evidence_base_confidence: float = _float_env("EVIDENCE_BASE_CONFIDENCE", 0.35)
    evidence_source_weight: float = _float_env("EVIDENCE_SOURCE_WEIGHT", 0.12)
    evidence_source_ratio_weight: float = _float_env("EVIDENCE_SOURCE_RATIO_WEIGHT", 0.40)
    evidence_max_confidence: float = _float_env("EVIDENCE_MAX_CONFIDENCE", 0.99)
    evidence_local_confidence: float = _float_env("EVIDENCE_LOCAL_CONFIDENCE", 0.97)
    evidence_local_url_prefix: str = _env("EVIDENCE_LOCAL_URL_PREFIX", "local://")

    llm_evidence_override_confidence: float = _float_env(
        "LLM_EVIDENCE_OVERRIDE_CONFIDENCE",
        0.95,
    )

    risk_high_confidence: float = _float_env("RISK_HIGH_CONFIDENCE", 0.95)
    risk_medium_confidence: float = _float_env("RISK_MEDIUM_CONFIDENCE", 0.75)
    risk_low_confidence: float = _float_env("RISK_LOW_CONFIDENCE", 0.40)
    public_domain_confidence: float = _float_env("PUBLIC_DOMAIN_CONFIDENCE", 0.98)
    original_confidence_floor: float = _float_env("ORIGINAL_CONFIDENCE_FLOOR", 0.91)
    risk_max_confidence: float = _float_env("RISK_MAX_CONFIDENCE", 0.99)

    require_external_service_keys: bool = _bool_env("REQUIRE_EXTERNAL_SERVICE_KEYS", False)

    def validate(self) -> None:
        valid_providers = {"brave", "serper", "tavily"}
        unknown_providers = set(self.search_provider_priority) - valid_providers
        if unknown_providers:
            raise ValueError(
                "SEARCH_PROVIDER_PRIORITY contains unknown providers: "
                + ", ".join(sorted(unknown_providers))
            )
        if not self.copyright_check_route.startswith("/"):
            raise ValueError("COPYRIGHT_CHECK_ROUTE must start with '/'.")
        if self.log_level not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}:
            raise ValueError("LOG_LEVEL must be a valid Python logging level.")

        positive_ints = {
            "SEARCH_TIMEOUT_SECONDS": self.search_timeout_seconds,
            "BRAVE_SEARCH_COUNT": self.brave_search_count,
            "SERPER_SEARCH_COUNT": self.serper_search_count,
            "TAVILY_MAX_RESULTS": self.tavily_max_results,
            "GEMINI_RETRIES": self.gemini_retries,
            "GEMINI_BACKOFF_MAX_SECONDS": self.gemini_backoff_max_seconds,
        }
        for name, value in positive_ints.items():
            if value < 1:
                raise ValueError(f"{name} must be greater than zero.")

        confidence_values = {
            "INPUT_ANALYSIS_CONFIDENCE": self.input_analysis_confidence,
            "EVIDENCE_BASE_CONFIDENCE": self.evidence_base_confidence,
            "EVIDENCE_SOURCE_WEIGHT": self.evidence_source_weight,
            "EVIDENCE_SOURCE_RATIO_WEIGHT": self.evidence_source_ratio_weight,
            "EVIDENCE_MAX_CONFIDENCE": self.evidence_max_confidence,
            "EVIDENCE_LOCAL_CONFIDENCE": self.evidence_local_confidence,
            "LLM_EVIDENCE_OVERRIDE_CONFIDENCE": self.llm_evidence_override_confidence,
            "RISK_HIGH_CONFIDENCE": self.risk_high_confidence,
            "RISK_MEDIUM_CONFIDENCE": self.risk_medium_confidence,
            "RISK_LOW_CONFIDENCE": self.risk_low_confidence,
            "PUBLIC_DOMAIN_CONFIDENCE": self.public_domain_confidence,
            "ORIGINAL_CONFIDENCE_FLOOR": self.original_confidence_floor,
            "RISK_MAX_CONFIDENCE": self.risk_max_confidence,
        }
        for name, value in confidence_values.items():
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1.")

        if self.input_title_or_phrase_max_words < 1:
            raise ValueError("INPUT_TITLE_OR_PHRASE_MAX_WORDS must be greater than zero.")
        if self.input_short_lyric_max_words < self.input_title_or_phrase_max_words:
            raise ValueError(
                "INPUT_SHORT_LYRIC_MAX_WORDS must be greater than or equal to "
                "INPUT_TITLE_OR_PHRASE_MAX_WORDS."
            )

        if self.require_external_service_keys:
            missing = []
            provider_keys = {
                "brave": self.brave_api_key,
                "serper": self.serper_api_key,
                "tavily": self.tavily_api_key,
            }
            for provider in self.search_provider_priority:
                if not provider_keys.get(provider):
                    missing.append(f"{provider.upper()}_API_KEY")
            if not self.gemini_api_key:
                missing.append("GEMINI_API_KEY")
            if missing:
                raise ValueError("Missing required environment variables: " + ", ".join(missing))


config = CopyrightAgentConfig()
config.validate()
