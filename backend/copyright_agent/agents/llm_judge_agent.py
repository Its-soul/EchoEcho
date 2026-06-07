import json
import time
from typing import Any

from ..config import config
from ..logger import get_logger


logger = get_logger(__name__)


class LLMJudgeAgent:
    def __init__(self, model: str | None = None, retries: int | None = None) -> None:
        self.model = model or config.openai_model
        self.retries = retries if retries is not None else config.llm_retries

    def _build_prompt(self, lyrics: str, songs: list[dict]) -> str:
        return f"""You are an expert music copyright analyst.

Input lyrics:
{lyrics}

Retrieved songs:
{json.dumps(songs, ensure_ascii=True)}

Determine:

1. copyright risk
2. similar song
3. artist
4. explanation
5. recommendation

Return valid JSON."""

    def _parse_json(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise
            return json.loads(content[start : end + 1])

    def _fallback_response(self, error: str | None = None) -> dict:
        response = {
            "copyright_risk": "unknown",
            "similar_song": "",
            "artist": "",
            "explanation": "LLM judge was not available, so no model-based legal analysis was produced.",
            "recommendation": "Review local similarity and vector search results manually.",
        }
        if error:
            response["error"] = error
        return response

    def run(self, lyrics: str, songs: list[dict]) -> dict:
        if not config.openai_api_key:
            return self._fallback_response("OPENAI_API_KEY is not configured.")

        try:
            from openai import OpenAI
        except ImportError as exc:
            return self._fallback_response(f"openai is required: {exc}")

        client = OpenAI(api_key=config.openai_api_key)
        prompt = self._build_prompt(lyrics, songs)
        last_error: Exception | None = None

        for attempt in range(1, self.retries + 1):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Return only valid JSON. Do not include markdown.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content or "{}"
                parsed = self._parse_json(content)
                return parsed
            except Exception as exc:
                last_error = exc
                logger.info("LLM judge attempt %s failed: %s", attempt, exc)
                if attempt < self.retries:
                    time.sleep(min(2 ** (attempt - 1), 4))

        return self._fallback_response(str(last_error))
