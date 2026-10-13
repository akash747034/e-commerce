from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.order import OrderCancel, OrderCreate, OrderResponse
from app.schemas.response import ApiResponse
from app.services import order as order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=ApiResponse[OrderResponse], status_code=status.HTTP_201_CREATED)
def place_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = order_service.place_order(payload, current_user, db)
    return ApiResponse(
        message="Order placed successfully",
        data=OrderResponse.model_validate(order),
    )


@router.get("", response_model=ApiResponse[list[OrderResponse]])
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orders = order_service.list_orders(current_user, db)
    return ApiResponse(
        message="Orders retrieved successfully",
        data=[OrderResponse.model_validate(o) for o in orders],
    )


@router.get("/{order_id}", response_model=ApiResponse[OrderResponse])
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = order_service.get_order(order_id, current_user, db)
    return ApiResponse(
        message="Order retrieved successfully",
        data=OrderResponse.model_validate(order),
    )


@router.post("/{order_id}/cancel", response_model=ApiResponse[OrderResponse])
def cancel_order(
    order_id: int,
    payload: OrderCancel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = order_service.cancel_order(order_id, payload.reason, current_user, db)
    return ApiResponse(
        message="Order cancelled successfully",
        data=OrderResponse.model_validate(order),
    )
