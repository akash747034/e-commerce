from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    product_id: int
    rating: Annotated[int, Field(ge=1, le=5)]
    title: Annotated[str | None, Field(max_length=150)] = None
    comment: str | None = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    rating: int
    title: str | None
    comment: str | None
    is_verified_purchase: bool
    status: str
