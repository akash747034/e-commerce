from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class CartItemAdd(BaseModel):
    product_id: int
    variant_id: int | None = None
    quantity: Annotated[int, Field(ge=1, le=100)] = 1


class CartItemUpdate(BaseModel):
    quantity: Annotated[int, Field(ge=1, le=100)]


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    variant_id: int | None
    quantity: int
    # Derived fields populated by the service
    unit_price: Decimal
    total_price: Decimal
    product_title: str
    variant_title: str | None


class CartResponse(BaseModel):
    id: int
    status: str
    items: list[CartItemResponse] = []
    subtotal: Decimal
    item_count: int
