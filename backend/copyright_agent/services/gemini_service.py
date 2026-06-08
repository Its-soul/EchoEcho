import json
import time
from typing import Any

from ..config import config
from ..logger import get_logger


logger = get_logger(__name__)


class GeminiService:
    def __init__(self, model: str | None = None, retries: int | None = None) -> None:
        self.model = model or config.gemini_model
        self.retries = retries if retries is not None else config.gemini_retries

    def parse_json(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise
            return json.loads(content[start : end + 1])

    def neutral_response(self) -> dict:
        return {
            "supports_existing_song": False,
            "confidence": 0.0,
            "reason": "Gemini analysis unavailable.",
        }

    def judge(self, lyrics: str, evidence: dict) -> dict:
        if not config.gemini_api_key:
            logger.info("Gemini API key is not configured.")
            return self.neutral_response()

        try:
            from google import genai
        except ImportError:
            logger.info("google-genai is not installed.")
            return self.neutral_response()

        client = genai.Client(api_key=config.gemini_api_key)
        prompt = (
            "You are an evidence interpreter for an inspiration safety advisor.\n"
            "Do not decide legal risk.\n"
            "Answer only valid JSON with keys: supports_existing_song, confidence, reason.\n\n"
            f"Lyrics: {lyrics}\n"
            f"Evidence: {json.dumps(evidence, ensure_ascii=True)}"
        )
        last_error: Exception | None = None

        for attempt in range(1, self.retries + 1):
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )
                parsed = self.parse_json(getattr(response, "text", "") or "{}")
                return {
                    "supports_existing_song": bool(
                        parsed.get("supports_existing_song", False)
                    ),
                    "confidence": float(parsed.get("confidence", 0.0)),
                    "reason": str(parsed.get("reason", "")),
                }
            except Exception as exc:
                last_error = exc
                logger.info("Gemini judge attempt %s failed: %s", attempt, exc)
                if attempt < self.retries:
                    time.sleep(min(2 ** (attempt - 1), config.gemini_backoff_max_seconds))

        logger.info("Gemini judge unavailable after retries: %s", last_error)
        return self.neutral_response()
