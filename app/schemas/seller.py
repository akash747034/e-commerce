from datetime import datetime
from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Seller Dashboard Overview
# ---------------------------------------------------------------------------

class SellerDashboardStatsResponse(BaseModel):
    total_products: int
    active_products: int
    out_of_stock_products: int
    total_orders_received: int
    pending_fulfillment_orders: int
    completed_orders: int
    total_sales_volume: Decimal


# ---------------------------------------------------------------------------
# Seller Order Items
# ---------------------------------------------------------------------------

class SellerOrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_item_id: int
    order_id: int
    order_number: str
    product_id: int
    product_name: str | None
    variant_name: str | None
    quantity: int
    mrp: Decimal
    selling_price: Decimal
    item_discount: Decimal
    line_total: Decimal
    status: str
    created_at: datetime
    shipping_address_id: int


class SellerItemStatusUpdate(BaseModel):
    status: Annotated[str, Field(min_length=1, max_length=30)]  # e.g. "confirmed", "processing", "shipped", "delivered"
