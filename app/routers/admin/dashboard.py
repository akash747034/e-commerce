from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.schemas.dashboard import DashboardStatsResponse
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/dashboard", tags=["Admin Dashboard"])


@router.get("/stats", response_model=ApiResponse[DashboardStatsResponse])
def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: platform-wide business analytics and overview stats."""
    # Revenue (sum of total_amount for non-cancelled orders)
    revenue = db.scalar(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(Order.status != "cancelled")
    ) or Decimal("0")

    total_orders = db.scalar(select(func.count(Order.id))) or 0
    pending_orders = db.scalar(
        select(func.count(Order.id)).where(Order.status.in_(["pending", "confirmed", "processing"]))
    ) or 0
    completed_orders = db.scalar(
        select(func.count(Order.id)).where(Order.status == "delivered")
    ) or 0

    total_products = db.scalar(select(func.count(Product.id))) or 0
    out_of_stock_products = db.scalar(
        select(func.count(Product.id)).where(Product.quantity <= 0)
    ) or 0

    total_customers = db.scalar(
        select(func.count(User.id)).where(User.user_type == "customer")
    ) or 0
    total_sellers = db.scalar(
        select(func.count(User.id)).where(User.user_type == "seller")
    ) or 0

    data = DashboardStatsResponse(
        total_revenue=revenue,
        total_orders=total_orders,
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        total_products=total_products,
        out_of_stock_products=out_of_stock_products,
        total_customers=total_customers,
        total_sellers=total_sellers,
    )
    return ApiResponse(
        message="Dashboard stats retrieved successfully",
        data=data,
    )
