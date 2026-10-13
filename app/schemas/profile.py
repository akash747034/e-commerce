from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserUpdate(BaseModel):
    name: Annotated[str | None, Field(min_length=1, max_length=255)] = None
    phone: Annotated[str | None, Field(max_length=30)] = None
    dob: date | None = None
    avatar_url: Annotated[str | None, Field(max_length=500)] = None
    country: Annotated[str | None, Field(max_length=50)] = None


class ChangePasswordPayload(BaseModel):
    current_password: Annotated[str, Field(min_length=1, max_length=200)]
    new_password: Annotated[str, Field(min_length=6, max_length=100)]


class UserDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: str | None
    dob: date | None
    status: str
    is_verified: bool
    avatar_url: str | None
    country: str | None
    user_type: str
