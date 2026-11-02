from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserPublic(BaseModel):
    id: int
    email: str
    full_name: str
    status: str
    is_email_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
