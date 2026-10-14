from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# SubCategory Schemas
# ---------------------------------------------------------------------------

class SubCategoryCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=100)]
    slug: Annotated[str | None, Field(max_length=100)] = None
    description: str | None = None
    image_url: Annotated[str | None, Field(max_length=500)] = None
    is_active: bool = True


class SubCategoryUpdate(BaseModel):
    title: Annotated[str | None, Field(max_length=100)] = None
    slug: Annotated[str | None, Field(max_length=100)] = None
    description: str | None = None
    image_url: Annotated[str | None, Field(max_length=500)] = None
    is_active: bool | None = None


class SubCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    description: str | None
    image_url: str | None
    is_active: bool
    category_id: int


# ---------------------------------------------------------------------------
# Category Schemas
# ---------------------------------------------------------------------------

class CategoryCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=100)]
    slug: Annotated[str | None, Field(max_length=120)] = None
    description: str | None = None
    image_url: Annotated[str | None, Field(max_length=500)] = None
    is_active: bool = True


class CategoryUpdate(BaseModel):
    title: Annotated[str | None, Field(max_length=100)] = None
    slug: Annotated[str | None, Field(max_length=120)] = None
    description: str | None = None
    image_url: Annotated[str | None, Field(max_length=500)] = None
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    description: str | None
    image_url: str | None
    is_active: bool
    subcategories: list[SubCategoryResponse] = []
