from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.schemas.payment import PaymentResponse, PaymentStatusUpdate
from app.schemas.response import ApiResponse
from app.services import payment as payment_service

router = APIRouter(prefix="/payments", tags=["Admin Payments"])


@router.get("", response_model=ApiResponse[list[PaymentResponse]])
def list_all_payments(
    order_id: int | None = Query(None, description="Filter by order ID"),
    user_id: int | None = Query(None, description="Filter by user/customer ID"),
    status: str | None = Query(None, description="Filter by payment status (e.g. 'pending', 'succeeded', 'failed', 'refunded')"),
    gateway: str | None = Query(None, description="Filter by payment gateway (e.g. 'cod', 'stripe', 'razorpay')"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List all platform payments with optional filters for order, user, gateway, and status.
    """
    payments = payment_service.list_all_payments_admin(
        db=db,
        order_id=order_id,
        user_id=user_id,
        status_filter=status,
        gateway_filter=gateway,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        message="Payments retrieved successfully",
        data=[PaymentResponse.model_validate(p) for p in payments],
    )


@router.get("/{payment_id}", response_model=ApiResponse[PaymentResponse])
def get_payment_details(
    payment_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Inspect full payment details including gateway transaction responses.
    """
    payment = payment_service.get_payment(payment_id, admin, db)
    return ApiResponse(
        message="Payment retrieved successfully",
        data=PaymentResponse.model_validate(payment),
    )


@router.patch("/{payment_id}/status", response_model=ApiResponse[PaymentResponse])
def update_payment_status(
    payment_id: int,
    payload: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Manually update a payment status (e.g. reconciliations or offline verification).
    Automatically synchronizes the associated order's payment_status.
    """
    payment = payment_service.admin_update_payment_status(payment_id, payload, db)
    return ApiResponse(
        message=f"Payment status updated to '{payment.status}'",
        data=PaymentResponse.model_validate(payment),
    )
