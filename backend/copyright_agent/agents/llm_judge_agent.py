from ..config import config
from ..services.gemini_service import GeminiService


class LLMJudgeAgent:
    def __init__(self, gemini_service: GeminiService | None = None) -> None:
        self.gemini_service = gemini_service or GeminiService()

    def run(self, lyrics: str, evidence: dict) -> dict:
        result = self.gemini_service.judge(lyrics, evidence)
        if (
            not result.get("supports_existing_song")
            and float(evidence.get("confidence", 0.0)) > config.llm_evidence_override_confidence
            and evidence.get("song_title")
        ):
            return {
                "supports_existing_song": True,
                "confidence": float(evidence.get("confidence", 0.0)),
                "reason": "Structured evidence supports an existing song match.",
            }
        return result
