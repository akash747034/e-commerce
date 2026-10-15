from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ShipmentCreate(BaseModel):
    order_id: int
    carrier: Annotated[str, Field(min_length=2, max_length=100, description="e.g. 'FedEx', 'BlueDart', 'Delhivery', 'DHL', 'India Post'")]
    tracking_number: Annotated[str, Field(min_length=2, max_length=100)]
    tracking_url: str | None = None
    estimated_delivery: datetime | None = None
    notes: str | None = None


class ShipmentStatusUpdate(BaseModel):
    status: Annotated[str, Field(min_length=2, max_length=50, description="'label_created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'returned'")]
    delivered_at: datetime | None = None
    notes: str | None = None


class ShipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    carrier: str
    tracking_number: str
    tracking_url: str | None
    status: str
    shipped_at: datetime | None
    estimated_delivery: datetime | None
    delivered_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
