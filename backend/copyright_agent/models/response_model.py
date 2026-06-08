from pydantic import BaseModel


class CopyrightCheckResponse(BaseModel):
    safe: bool
    risk: str
    confidence: float
    copyright_status: str
    song_title: str = ""
    artist: str = ""
    recommendation: str
    details: str
