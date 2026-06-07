import json
from pathlib import Path

from ..config import config
from ..services.preprocessing import PreprocessedLyrics, preprocess_lyrics
from ..utils.similarity_utils import classify_similarity


class SimilarityAgent:
    def __init__(self, songs_path: Path | None = None, top_k: int | None = None) -> None:
        self.songs_path = songs_path or (
            Path(__file__).resolve().parents[1] / "database" / "songs.json"
        )
        self.top_k = top_k or config.local_similarity_top_k
        self.songs = self._load_songs()

    def _load_songs(self) -> list[dict]:
        if not self.songs_path.exists():
            return []
        with self.songs_path.open("r", encoding="utf-8") as songs_file:
            return json.load(songs_file)

    def run(self, lyrics: str | PreprocessedLyrics) -> dict:
        try:
            from rapidfuzz import fuzz
        except ImportError as exc:
            return {"matches": [], "error": f"rapidfuzz is required: {exc}"}

        preprocessed = (
            lyrics if isinstance(lyrics, PreprocessedLyrics) else preprocess_lyrics(lyrics)
        )
        matches: list[dict] = []
        for song in self.songs:
            song_lyrics = preprocess_lyrics(song.get("lyrics", "")).cleaned
            score = float(fuzz.token_set_ratio(preprocessed.cleaned, song_lyrics))
            matches.append(
                {
                    "title": song.get("title", ""),
                    "artist": song.get("artist", ""),
                    "score": round(score, 2),
                    "risk": classify_similarity(score),
                }
            )

        matches.sort(key=lambda item: item["score"], reverse=True)
        return {"matches": matches[: self.top_k]}
