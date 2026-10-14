from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.schemas.order import OrderResponse, OrderStatusUpdate
from app.schemas.response import ApiResponse
from app.services import order as order_service

router = APIRouter(prefix="/orders", tags=["Admin Orders"])


@router.get("", response_model=ApiResponse[list[OrderResponse]])
def admin_list_orders(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    status_filter: str | None = Query(default=None, alias="status"),
    payment_status: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Admin: view all platform orders."""
    orders = order_service.list_all_orders_admin(
        db=db,
        status_filter=status_filter,
        payment_status=payment_status,
        user_id=user_id,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        message="Orders retrieved successfully",
        data=[OrderResponse.model_validate(o) for o in orders],
    )


@router.get("/{order_id}", response_model=ApiResponse[OrderResponse])
def admin_get_order(
    order_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: inspect full details of an order."""
    order = order_service.get_order_by_id_admin(order_id, db)
    return ApiResponse(
        message="Order retrieved successfully",
        data=OrderResponse.model_validate(order),
    )


@router.patch("/{order_id}/status", response_model=ApiResponse[OrderResponse])
def admin_update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: update order delivery/processing status and payment status."""
    order = order_service.update_order_status_admin(
        order_id=order_id,
        new_status=payload.status,
        new_payment_status=payload.payment_status,
        db=db,
    )
    return ApiResponse(
        message="Order status updated successfully",
        data=OrderResponse.model_validate(order),
    )
