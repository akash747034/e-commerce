from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_seller
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.seller import SellerDashboardStatsResponse
from app.services import seller as seller_service

router = APIRouter(prefix="/dashboard", tags=["Seller Dashboard"])


@router.get("/stats", response_model=ApiResponse[SellerDashboardStatsResponse])
def get_seller_stats(
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """Seller: get real-time statistics on products, inventory, orders, and sales volume."""
    stats = seller_service.get_seller_dashboard_stats(seller, db)
    return ApiResponse(
        message="Seller stats retrieved successfully",
        data=stats,
    )
