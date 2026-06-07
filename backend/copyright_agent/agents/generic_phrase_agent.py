from ..services.preprocessing import PreprocessedLyrics, preprocess_lyrics


GENERIC_PHRASES = [
    "happy birthday",
    "happy new year",
    "merry christmas",
    "good morning",
    "good night",
    "thank you",
    "hello",
    "welcome home",
    "see you soon",
    "i love you",
]


class GenericPhraseAgent:
    def __init__(self, phrases: list[str] | None = None) -> None:
        self.phrases = [
            preprocess_lyrics(phrase).cleaned for phrase in (phrases or GENERIC_PHRASES)
        ]

    def run(self, lyrics: str | PreprocessedLyrics) -> dict:
        preprocessed = (
            lyrics if isinstance(lyrics, PreprocessedLyrics) else preprocess_lyrics(lyrics)
        )
        for phrase in self.phrases:
            if phrase and phrase in preprocessed.cleaned:
                return {"is_generic": True, "matched_phrase": phrase}
        return {"is_generic": False, "matched_phrase": ""}
