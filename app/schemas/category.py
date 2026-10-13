from pydantic import BaseModel, ConfigDict


class SubCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    description: str | None
    image_url: str | None
    is_active: bool
    category_id: int


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    description: str | None
    image_url: str | None
    is_active: bool
    subcategories: list[SubCategoryResponse] = []
