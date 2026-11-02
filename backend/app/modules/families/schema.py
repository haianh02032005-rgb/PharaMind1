from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.core.security import normalize_email
from backend.app.shared.enums import FamilyRole


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _strip_and_validate_name(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Family name must not be empty")
    return stripped


class FamilyCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _strip_and_validate_name(value)


class FamilyUpdateRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_and_validate_name(value)


class FamilyResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    status: str
    my_role: str
    created_at: datetime
    updated_at: datetime


class FamilyListItem(BaseModel):
    id: int
    name: str
    description: str | None = None
    status: str
    my_role: str
    created_at: datetime


class FamilyListResponse(BaseModel):
    items: list[FamilyListItem]


class FamilyMemberUserSummary(BaseModel):
    id: int
    email: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class FamilyMembershipCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    role: FamilyRole

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = normalize_email(value)
        if not normalized or len(normalized) > 255 or not EMAIL_REGEX.match(normalized):
            raise ValueError("Invalid email address")
        return normalized


class FamilyMembershipUpdateRequest(BaseModel):
    role: FamilyRole


class FamilyMembershipResponse(BaseModel):
    id: int
    family_id: int
    user: FamilyMemberUserSummary
    role: str
    created_at: datetime


class FamilyMembershipListResponse(BaseModel):
    items: list[FamilyMembershipResponse]
