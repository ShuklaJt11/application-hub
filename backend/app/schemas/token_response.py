from typing import Literal

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: Literal["bearer"]
