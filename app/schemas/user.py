from typing import Annotated
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Annotated


class User(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=200)]
    email: EmailStr
    @field_validator("email")
    @classmethod
    def validate_email(cls,value):
        if not value.strip():
            raise ValueError("email can not be empty")
        return value


class UserCreate(User):
    password: Annotated[str, Field(min_length=6, max_length=100)]

class UserResponse(User):
    id: int
    model_config = ConfigDict(from_attributes=True)


class LoginPayload(BaseModel):
    email:Annotated[EmailStr,Field(min_length=1,max_length=200)]
    password:Annotated[str,Field(min_length=1,max_length=200)]

class LoginResponse(User):
     id:int 
     access_token:str 
     token_type:str
   


