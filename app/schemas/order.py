from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    variant_id: int | None
    product_name: str | None
    variant_name: str | None
    quantity: int
    mrp: Decimal           # Original / listed price per unit
    selling_price: Decimal  # Actual price per unit after product discount
    item_discount: Decimal  # Total product-level saving for this line (mrp - selling_price) * qty
    line_total: Decimal     # selling_price * quantity
    status: str


class OrderCreate(BaseModel):
    shipping_address_id: int
    billing_address_id: int | None = None
    payment_method: Annotated[str | None, Field(max_length=30)] = None
    coupon_code: str | None = None
    notes: Annotated[str | None, Field(max_length=500)] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    status: str
    subtotal: Decimal               # Sum of line_totals (after product discounts)
    product_discount_total: Decimal  # Total saved via product-level pricing
    coupon_discount: Decimal         # Discount applied by coupon code
    shipping_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal            # Final amount paid
    payment_status: str
    payment_method: str | None
    shipping_address_id: int
    billing_address_id: int | None
    coupon_id: int | None
    notes: str | None
    cancellation_reason: str | None
    items: list[OrderItemResponse] = []


class OrderCancel(BaseModel):
    reason: Annotated[str, Field(min_length=1, max_length=255)]
