import json

from ..config import config
from ..logger import get_logger
from ..services.brave_search_service import BraveSearchService
from ..services.preprocessing import preprocess_lyrics
from ..services.serper_service import SerperService
from ..services.tavily_service import TavilyService


logger = get_logger(__name__)


class SearchAgent:
    def __init__(self, providers: dict[str, object] | None = None) -> None:
        self.providers = providers or {
            "brave": BraveSearchService(),
            "serper": SerperService(),
            "tavily": TavilyService(),
        }
        self.local_songs_path = config.local_songs_path

    def build_queries(self, lyrics: str) -> list[str]:
        return [
            f'"{lyrics}" lyrics',
            f'"{lyrics}" song',
            f'"{lyrics}" genius',
            f'"{lyrics}" artist',
            f'"{lyrics}" spotify',
        ]

    def _local_reference_results(self, lyrics: str) -> list[dict]:
        try:
            with self.local_songs_path.open("r", encoding="utf-8") as songs_file:
                songs = json.load(songs_file)
        except Exception as exc:
            logger.info("Local reference search unavailable: %s", exc)
            return []

        cleaned_lyrics = preprocess_lyrics(lyrics).cleaned
        results: list[dict] = []
        for song in songs:
            song_lyrics = preprocess_lyrics(song.get("lyrics", "")).cleaned
            if cleaned_lyrics and cleaned_lyrics in song_lyrics:
                title = song.get("title", "")
                artist = song.get("artist", "")
                results.append(
                    {
                        "title": f"{title} lyrics - {artist}",
                        "snippet": f"{lyrics} appears in {title} by {artist}.",
                        "url": f"{config.evidence_local_url_prefix}songs/{title}",
                    }
                )
        return results

    def run(self, lyrics: str) -> list[dict]:
        results: list[dict] = []
        seen_urls: set[str] = set()

        for query in self.build_queries(lyrics):
            for provider_name in config.search_provider_priority:
                provider = self.providers.get(provider_name)
                if provider is None:
                    continue
                try:
                    provider_results = provider.search(query)
                except Exception as exc:
                    logger.info("%s search unavailable: %s", provider_name, exc)
                    continue
                for item in provider_results:
                    url = item.get("url", "")
                    identity = url or f"{item.get('title', '')}:{item.get('snippet', '')}"
                    if identity in seen_urls:
                        continue
                    seen_urls.add(identity)
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                            "url": url,
                        }
                    )

        for item in self._local_reference_results(lyrics):
            identity = item.get("url", "")
            if identity not in seen_urls:
                seen_urls.add(identity)
                results.append(item)

        return results
