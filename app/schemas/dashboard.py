from decimal import Decimal
from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_revenue: Decimal
    total_orders: int
    pending_orders: int
    completed_orders: int
    total_products: int
    out_of_stock_products: int
    total_customers: int
    total_sellers: int
