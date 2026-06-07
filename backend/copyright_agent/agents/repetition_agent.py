from collections import Counter

from ..config import config
from ..services.preprocessing import PreprocessedLyrics, preprocess_lyrics


class RepetitionAgent:
    def __init__(self, threshold: float | None = None) -> None:
        self.threshold = threshold if threshold is not None else config.repetition_threshold

    def _word_repetition_score(self, tokens: list[str]) -> float:
        if not tokens:
            return 0.0
        counts = Counter(tokens)
        repeated_count = sum(count - 1 for count in counts.values() if count > 1)
        return repeated_count / len(tokens)

    def _phrase_repetition_score(self, tokens: list[str]) -> float:
        if len(tokens) < 4:
            return 0.0

        scores: list[float] = []
        for size in range(2, min(6, len(tokens) + 1)):
            phrases = [tuple(tokens[index : index + size]) for index in range(len(tokens) - size + 1)]
            counts = Counter(phrases)
            repeated_count = sum(count - 1 for count in counts.values() if count > 1)
            if phrases:
                scores.append(repeated_count / len(phrases))
        return max(scores, default=0.0)

    def run(self, lyrics: str | PreprocessedLyrics) -> dict:
        preprocessed = (
            lyrics if isinstance(lyrics, PreprocessedLyrics) else preprocess_lyrics(lyrics)
        )
        word_score = self._word_repetition_score(preprocessed.tokens)
        phrase_score = self._phrase_repetition_score(preprocessed.tokens)
        repetition_score = round(max(word_score, phrase_score), 4)
        return {
            "repetition_score": repetition_score,
            "is_repetitive": repetition_score >= self.threshold,
        }
