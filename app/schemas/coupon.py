from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class CouponCreate(BaseModel):
    code: Annotated[str, Field(min_length=3, max_length=50)]
    description: str | None = None
    discount_type: Literal["percentage", "fixed_amount"]
    discount_value: Annotated[Decimal, Field(gt=0)]
    min_purchase_amount: Decimal = Decimal("0")
    max_discount_amount: Decimal | None = None
    usage_limit: int | None = None
    per_user_limit: int = 1
    valid_from: datetime
    valid_to: datetime
    is_active: bool = True


class CouponUpdate(BaseModel):
    description: str | None = None
    discount_value: Decimal | None = None
    min_purchase_amount: Decimal | None = None
    max_discount_amount: Decimal | None = None
    usage_limit: int | None = None
    per_user_limit: int | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    is_active: bool | None = None


class CouponResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    description: str | None
    discount_type: str
    discount_value: Decimal
    min_purchase_amount: Decimal
    max_discount_amount: Decimal | None
    usage_limit: int | None
    used_count: int
    per_user_limit: int
    valid_from: datetime
    valid_to: datetime
    is_active: bool
