from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class EmailSchema(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserCreate(EmailSchema):
    name: Annotated[str, Field(min_length=1, max_length=200)]
    password: Annotated[str, Field(min_length=6, max_length=100)]


class UserResponse(EmailSchema):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class LoginPayload(EmailSchema):
    password: Annotated[str, Field(min_length=1, max_length=200)]


class LoginResponse(UserResponse):
    access_token: str
    token_type: str = "bearer"
