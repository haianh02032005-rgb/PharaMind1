from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.core.security import normalize_email


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_and_normalize_email(value: str) -> str:
    normalized = normalize_email(value)
    if not normalized or len(normalized) > 255 or not EMAIL_REGEX.match(normalized):
        raise ValueError("Invalid email address")
    return normalized


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(
        min_length=8,
        max_length=128,
    )
    full_name: str = Field(
        min_length=1,
        max_length=150,
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_and_normalize_email(value)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("full_name must not be empty")
        return stripped


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(
        min_length=1,
        max_length=128,
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_and_normalize_email(value)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    status: str
    is_email_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
