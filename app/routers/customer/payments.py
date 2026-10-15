from typing import Any

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.payment import (
    PaymentInitiate,
    PaymentInitiateResponse,
    PaymentResponse,
    PaymentVerify,
)
from app.schemas.response import ApiResponse
from app.services import payment as payment_service

router = APIRouter(tags=["Payments"])


@router.post("/payments/initiate", response_model=ApiResponse[PaymentInitiateResponse], status_code=status.HTTP_201_CREATED)
def initiate_payment(
    payload: PaymentInitiate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Initiate payment for an order.
    - If gateway is 'stripe': Creates a Stripe PaymentIntent and returns client_secret & publishable_key.
    - If gateway is 'cod': Confirms order with Cash on Delivery.
    """
    res = payment_service.initiate_payment(payload, current_user, db)
    return ApiResponse(
        message=res.message,
        data=res,
    )


@router.post("/payments/{payment_id}/verify", response_model=ApiResponse[PaymentResponse])
def verify_payment(
    payment_id: int,
    payload: PaymentVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Verify payment completion with Stripe's servers.
    The backend queries Stripe to ensure the PaymentIntent succeeded, then marks the order as paid.
    """
    payment = payment_service.verify_payment(payment_id, payload, current_user, db)
    return ApiResponse(
        message="Payment verified successfully via Stripe",
        data=PaymentResponse.model_validate(payment),
    )


@router.get("/payments/{payment_id}", response_model=ApiResponse[PaymentResponse])
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get payment transaction details.
    """
    payment = payment_service.get_payment(payment_id, current_user, db)
    return ApiResponse(
        message="Payment details retrieved successfully",
        data=PaymentResponse.model_validate(payment),
    )


@router.get("/orders/{order_id}/payments", response_model=ApiResponse[list[PaymentResponse]])
def list_order_payments(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all payment attempts associated with an order.
    """
    payments = payment_service.list_order_payments(order_id, current_user, db)
    return ApiResponse(
        message="Order payments retrieved successfully",
        data=[PaymentResponse.model_validate(p) for p in payments],
    )


@router.post("/payments/webhook/stripe", response_model=ApiResponse[dict[str, Any]])
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    """
    Public Stripe Webhook receiver.
    Receives raw events from Stripe, cryptographically validates the signature, and updates payment/order status.
    """
    raw_body = await request.body()
    result = payment_service.handle_stripe_webhook(raw_body, stripe_signature, db)
    return ApiResponse(
        message="Stripe webhook processed",
        data=result,
    )
