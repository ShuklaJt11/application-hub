from typing import Literal

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator

from app.schemas.clean_input_model import CleanInputModel


class UserCreate(CleanInputModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class UserLogin(CleanInputModel):
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: Literal["bearer"]


class RefreshTokenRequest(CleanInputModel):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(CleanInputModel):
    refresh_token: str = Field(min_length=1)


class MessageResponse(BaseModel):
    message: str


class TokenPayload(BaseModel):
    sub: str
    type: Literal["access", "refresh"]
    exp: int
    jti: str | None = None
