from typing import Any

from pydantic import BaseModel, Field


class CopyrightCheckResponse(BaseModel):
    safe: bool
    risk: str
    copyright_status: str
    top_match: str = ""
    artist: str = ""
    similarity_score: float = 0.0
    recommendation: str
    details: str
    developer_details: dict[str, Any] | None = Field(default=None)
