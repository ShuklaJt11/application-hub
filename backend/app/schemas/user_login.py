from pydantic import EmailStr, Field, SecretStr, field_validator

from app.schemas.clean_input_model import CleanInputModel


class UserLogin(CleanInputModel):
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()
