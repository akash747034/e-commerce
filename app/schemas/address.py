from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    full_name: Annotated[str | None, Field(max_length=100)] = None
    phone: Annotated[str | None, Field(max_length=30)] = None
    address_line_1: Annotated[str, Field(min_length=1, max_length=255)]
    address_line_2: Annotated[str | None, Field(max_length=255)] = None
    landmark: Annotated[str | None, Field(max_length=100)] = None
    city: Annotated[str, Field(min_length=1, max_length=170)]
    state: Annotated[str | None, Field(max_length=100)] = None
    country: Annotated[str, Field(min_length=1, max_length=56)]
    pincode: Annotated[str, Field(min_length=1, max_length=20)]
    address_type: Annotated[str, Field(pattern="^(shipping|billing|both)$")] = "shipping"
    is_primary: bool = False


class AddressUpdate(BaseModel):
    full_name: Annotated[str | None, Field(max_length=100)] = None
    phone: Annotated[str | None, Field(max_length=30)] = None
    address_line_1: Annotated[str | None, Field(min_length=1, max_length=255)] = None
    address_line_2: Annotated[str | None, Field(max_length=255)] = None
    landmark: Annotated[str | None, Field(max_length=100)] = None
    city: Annotated[str | None, Field(min_length=1, max_length=170)] = None
    state: Annotated[str | None, Field(max_length=100)] = None
    country: Annotated[str | None, Field(min_length=1, max_length=56)] = None
    pincode: Annotated[str | None, Field(min_length=1, max_length=20)] = None
    address_type: Annotated[str | None, Field(pattern="^(shipping|billing|both)$")] = None
    is_primary: bool | None = None


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    full_name: str | None
    phone: str | None
    address_line_1: str
    address_line_2: str | None
    landmark: str | None
    city: str
    state: str | None
    country: str
    pincode: str
    address_type: str
    is_primary: bool
