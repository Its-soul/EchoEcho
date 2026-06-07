import json
from pathlib import Path

from ..services.preprocessing import PreprocessedLyrics, preprocess_lyrics


DEFAULT_PHRASES = [
    "happy birthday to you",
    "jingle bells",
    "we wish you a merry christmas",
    "silent night",
    "twinkle twinkle little star",
    "mary had a little lamb",
    "old macdonald had a farm",
    "abc song",
]


class PhraseBagAgent:
    def __init__(self, phrase_bag_path: Path | None = None) -> None:
        self.phrase_bag_path = phrase_bag_path or (
            Path(__file__).resolve().parents[1] / "database" / "phrase_bag.json"
        )
        self.phrases = self._load_phrases()

    def _load_phrases(self) -> list[str]:
        if not self.phrase_bag_path.exists():
            return DEFAULT_PHRASES
        with self.phrase_bag_path.open("r", encoding="utf-8") as phrase_file:
            phrases = json.load(phrase_file)
        return [preprocess_lyrics(phrase).cleaned for phrase in phrases]

    def run(self, lyrics: str | PreprocessedLyrics) -> dict:
        preprocessed = (
            lyrics if isinstance(lyrics, PreprocessedLyrics) else preprocess_lyrics(lyrics)
        )
        for phrase in self.phrases:
            if phrase and phrase in preprocessed.cleaned:
                return {"matched": True, "phrase": phrase}
        return {"matched": False, "phrase": ""}
