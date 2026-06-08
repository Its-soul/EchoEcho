from pydantic import BaseModel, constr


class CopyrightCheckRequest(BaseModel):
    lyrics: constr(strip_whitespace=True, min_length=1)
