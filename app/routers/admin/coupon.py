from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.schemas.coupon import CouponCreate, CouponResponse, CouponUpdate
from app.schemas.response import ApiResponse
from app.services import coupon as coupon_service

router = APIRouter(prefix="/coupons", tags=["Admin Coupons"])


@router.get("", response_model=ApiResponse[list[CouponResponse]])
def admin_list_coupons(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    include_inactive: bool = Query(default=True),
):
    """Admin: view all coupons."""
    coupons = coupon_service.list_coupons_admin(db, include_inactive=include_inactive)
    return ApiResponse(
        message="Coupons retrieved successfully",
        data=[CouponResponse.model_validate(c) for c in coupons],
    )


@router.get("/{coupon_id}", response_model=ApiResponse[CouponResponse])
def admin_get_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: get coupon details."""
    coupon = coupon_service.get_coupon_by_id_admin(coupon_id, db)
    return ApiResponse(
        message="Coupon retrieved successfully",
        data=CouponResponse.model_validate(coupon),
    )


@router.post("", response_model=ApiResponse[CouponResponse], status_code=status.HTTP_201_CREATED)
def admin_create_coupon(
    payload: CouponCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: create a discount coupon."""
    coupon = coupon_service.create_coupon(payload, db)
    return ApiResponse(
        message="Coupon created successfully",
        data=CouponResponse.model_validate(coupon),
    )


@router.patch("/{coupon_id}", response_model=ApiResponse[CouponResponse])
def admin_update_coupon(
    coupon_id: int,
    payload: CouponUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: update coupon details."""
    coupon = coupon_service.update_coupon(coupon_id, payload, db)
    return ApiResponse(
        message="Coupon updated successfully",
        data=CouponResponse.model_validate(coupon),
    )


@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: delete coupon."""
    coupon_service.delete_coupon(coupon_id, db)
