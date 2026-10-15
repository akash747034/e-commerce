from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ReturnRequestCreate(BaseModel):
    order_id: int
    order_item_id: int | None = None
    reason: Annotated[str, Field(min_length=2, max_length=100, description="e.g. 'defective', 'wrong_item', 'damaged', 'size_fit', 'not_needed'")]
    comment: str | None = None


class ReturnRequestStatusUpdate(BaseModel):
    status: Annotated[str, Field(min_length=2, max_length=30, description="'pending', 'approved', 'rejected', 'item_received', 'completed'")]
    admin_notes: str | None = None


class ReturnRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    order_item_id: int | None
    user_id: int
    reason: str
    comment: str | None
    status: str
    admin_notes: str | None
    created_at: datetime
    updated_at: datetime


class RefundCreate(BaseModel):
    order_id: int
    payment_id: int | None = None
    return_request_id: int | None = None
    amount: Annotated[Decimal, Field(gt=0)]
    refund_method: Annotated[str, Field(default="gateway", max_length=50, description="'gateway', 'store_credit', 'manual_bank_transfer'")] = "gateway"
    reason: str | None = None
    notes: str | None = None


class RefundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    payment_id: int | None
    return_request_id: int | None
    amount: Decimal
    refund_method: str
    gateway_refund_id: str | None
    status: str
    reason: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
