from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field


class BrandCreate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    slug: Annotated[str | None, Field(max_length=120)] = None
    description: str | None = None
    logo_url: str | None = None
    website: str | None = None
    is_active: bool = True


class BrandUpdate(BaseModel):
    name: Annotated[str | None, Field(max_length=100)] = None
    slug: Annotated[str | None, Field(max_length=120)] = None
    description: str | None = None
    logo_url: str | None = None
    website: str | None = None
    is_active: bool | None = None


# Backward-compatible alias
CreateBrand = BrandCreate


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    logo_url: str | None
    website: str | None
    is_active: bool