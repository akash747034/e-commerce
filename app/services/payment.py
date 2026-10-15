import json
import logging
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.order import Order
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import (
    PaymentInitiate,
    PaymentInitiateResponse,
    PaymentStatusUpdate,
    PaymentVerify,
)
from app.services.gateways import stripe_gateway

logger = logging.getLogger("payment_service")


def initiate_payment(payload: PaymentInitiate, user: User, db: Session) -> PaymentInitiateResponse:
    """
    Initiates payment for an order.
    - If gateway is 'stripe':
        Creates a hosted Stripe Checkout Session returning `checkout_url`
        AND creates an embedded PaymentIntent returning `client_secret`.
    - If gateway is 'cod':
        Immediately confirms order with payment pending on delivery.
    """
    order = db.scalars(
        select(Order).where(Order.id == payload.order_id, Order.user_id == user.id)
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot initiate payment for a cancelled order",
        )

    if order.payment_status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order has already been paid",
        )

    gateway = payload.payment_gateway.lower().strip()
    checkout_url = None
    session_id = None
    client_secret = None
    publishable_key = None
    transaction_id = None
    initial_status = "pending"
    message = "Payment initiated successfully"

    if gateway == "cod":
        transaction_id = f"COD-{order.order_number}"
        order.payment_method = "cod"
        order.payment_status = "pending"
        if order.status == "pending":
            order.status = "confirmed"
        message = "Order confirmed with Cash on Delivery (payment due upon delivery)"

        db.add(
            Notification(
                user_id=user.id,
                title="Order Placed (COD)",
                message=f"Order {order.order_number} confirmed with Cash on Delivery for ₹{order.total_amount}.",
                notification_type="order",
                action_url=f"/orders/{order.id}",
            )
        )
    elif gateway == "stripe":
        # 1. Create hosted Stripe Checkout Session (produces the hosted checkout_url)
        session_data = stripe_gateway.create_checkout_session(
            amount=order.total_amount,
            currency=payload.currency,
            order_id=order.id,
            order_number=order.order_number,
            user_id=user.id,
            customer_email=user.email,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
        )
        checkout_url = session_data["checkout_url"]
        session_id = session_data["session_id"]
        transaction_id = session_id

        # 2. Also create embedded PaymentIntent for clients that prefer embedded forms
        intent_data = stripe_gateway.create_payment_intent(
            amount=order.total_amount,
            currency=payload.currency,
            order_id=order.id,
            order_number=order.order_number,
            user_id=user.id,
            customer_email=user.email,
        )
        client_secret = intent_data["client_secret"]
        publishable_key = intent_data["publishable_key"]

        order.payment_method = "stripe"
        message = "Stripe checkout session initialized. Redirect user to checkout_url or use client_secret."
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported payment gateway '{payload.payment_gateway}'. Supported: 'stripe', 'cod'.",
        )

    # Record payment attempt in payments table
    payment = Payment(
        order_id=order.id,
        user_id=user.id,
        payment_gateway=gateway,
        transaction_id=transaction_id,
        amount=order.total_amount,
        currency=payload.currency.upper(),
        status=initial_status,
        payment_response=json.dumps(
            {
                "gateway": gateway,
                "transaction_id": transaction_id,
                "checkout_url": checkout_url,
                "session_id": session_id,
            },
            default=str,
        ),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    db.refresh(order)

    return PaymentInitiateResponse(
        payment_id=payment.id,
        order_id=order.id,
        order_number=order.order_number,
        amount=payment.amount,
        currency=payment.currency,
        payment_gateway=gateway,
        status=payment.status,
        transaction_id=payment.transaction_id,
        checkout_url=checkout_url,
        session_id=session_id,
        client_secret=client_secret,
        publishable_key=publishable_key,
        message=message,
    )


def verify_payment(payment_id: int, payload: PaymentVerify, user: User, db: Session) -> Payment:
    """
    Verifies payment completion directly against Stripe's servers.
    Supports verification via:
      - `session_id` (from Stripe Checkout URL redirect)
      - `payment_intent_id` (from embedded Stripe Elements)
      - fallback to payment.transaction_id stored during initiation
    """
    payment = db.scalars(
        select(Payment).where(Payment.id == payment_id, Payment.user_id == user.id)
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    if payment.status == "succeeded":
        return payment  # Idempotent return

    order = db.get(Order, payment.order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated order not found")

    session_id = payload.session_id or (payment.transaction_id if payment.transaction_id and payment.transaction_id.startswith("cs_") else None)
    intent_id = payload.payment_intent_id or (payment.transaction_id if payment.transaction_id and payment.transaction_id.startswith("pi_") else None)

    verification_data = None

    if session_id:
        # Verify Stripe Checkout Session
        session_verification = stripe_gateway.retrieve_and_verify_checkout_session(session_id)
        if session_verification["payment_status"] != "paid" and session_verification["status"] != "complete":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe Checkout Session status is '{session_verification['payment_status']}', payment not completed",
            )
        verification_data = session_verification
        payment.transaction_id = session_verification.get("payment_intent_id") or session_id
    elif intent_id:
        # Verify Stripe PaymentIntent
        intent_verification = stripe_gateway.retrieve_and_verify_payment_intent(intent_id)
        if intent_verification["status"] != "succeeded":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe PaymentIntent status is '{intent_verification['status']}', not completed",
            )
        verification_data = intent_verification
        payment.transaction_id = intent_id
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either session_id or payment_intent_id to verify payment",
        )

    # Update payment record
    payment.status = "succeeded"
    payment.payment_response = json.dumps(verification_data, default=str)

    # Mark order as paid & confirmed
    order.payment_status = "paid"
    if order.status == "pending":
        order.status = "confirmed"

    # In-app notification
    db.add(
        Notification(
            user_id=user.id,
            title="Payment Successful",
            message=f"Your payment of ₹{payment.amount} for order {order.order_number} succeeded via Stripe.",
            notification_type="payment",
            action_url=f"/orders/{order.id}",
        )
    )

    db.commit()
    db.refresh(payment)
    return payment


def get_payment(payment_id: int, user: User, db: Session) -> Payment:
    """
    Retrieves a single payment. Customers can only view their own; admins can view any.
    """
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if user.user_type != "admin" and payment.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return payment


def list_order_payments(order_id: int, user: User, db: Session) -> list[Payment]:
    """
    Retrieves all payment attempts associated with a specific order.
    """
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if user.user_type != "admin" and order.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return list(
        db.scalars(
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(Payment.created_at.desc())
        ).all()
    )


def list_all_payments_admin(
    db: Session,
    order_id: int | None = None,
    user_id: int | None = None,
    status_filter: str | None = None,
    gateway_filter: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Payment]:
    """
    Admin listing of all platform payments with filtering and pagination.
    """
    query = select(Payment)

    if order_id:
        query = query.where(Payment.order_id == order_id)
    if user_id:
        query = query.where(Payment.user_id == user_id)
    if status_filter:
        query = query.where(Payment.status == status_filter.lower())
    if gateway_filter:
        query = query.where(Payment.payment_gateway == gateway_filter.lower())

    query = query.order_by(Payment.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())


def admin_update_payment_status(
    payment_id: int,
    payload: PaymentStatusUpdate,
    db: Session,
) -> Payment:
    """
    Admin manual override for payment status (e.g. offline bank transfer reconciliation).
    Synchronizes the related Order's payment_status.
    """
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    new_status = payload.status.lower().strip()
    valid_statuses = {"pending", "succeeded", "failed", "refunded"}
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Must be one of: {', '.join(sorted(valid_statuses))}",
        )

    payment.status = new_status
    if payload.payment_response:
        payment.payment_response = payload.payment_response

    order = db.get(Order, payment.order_id)
    if order:
        if new_status == "succeeded":
            order.payment_status = "paid"
            if order.status == "pending":
                order.status = "confirmed"
        elif new_status == "failed":
            order.payment_status = "failed"
        elif new_status == "refunded":
            order.payment_status = "refunded"

    db.commit()
    db.refresh(payment)
    return payment


def handle_stripe_webhook(raw_payload: bytes, signature_header: str | None, db: Session) -> dict[str, Any]:
    """
    Processes asynchronous Stripe webhooks with cryptographic signature verification.
    Handles 'checkout.session.completed', 'payment_intent.succeeded', and 'payment_intent.payment_failed'.
    """
    event = stripe_gateway.construct_webhook_event(raw_payload, signature_header)
    event_type = event.get("type", "")
    event_data = event.get("data", {}).get("object", {})

    target_id = event_data.get("id")
    if not target_id:
        return {"received": True, "processed": False, "message": "No id found in event"}

    # Find payment by session_id, payment_intent_id, or transaction_id
    payment = db.scalars(
        select(Payment).where(Payment.transaction_id == target_id)
    ).first()

    if not payment and event_data.get("payment_intent"):
        payment = db.scalars(
            select(Payment).where(Payment.transaction_id == str(event_data.get("payment_intent")))
        ).first()

    if not payment:
        logger.warning("Webhook: Payment with transaction %s not found in database", target_id)
        return {"received": True, "processed": False, "message": f"Payment {target_id} not found"}

    if event_type in ("checkout.session.completed", "payment_intent.succeeded"):
        payment.status = "succeeded"
        payment.payment_response = json.dumps(event_data, default=str)
        order = db.get(Order, payment.order_id)
        if order:
            order.payment_status = "paid"
            if order.status == "pending":
                order.status = "confirmed"
        db.commit()
        return {"received": True, "processed": True, "status": "succeeded", "payment_id": payment.id}

    elif event_type in ("payment_intent.payment_failed", "checkout.session.expired"):
        payment.status = "failed"
        payment.payment_response = json.dumps(event_data, default=str)
        order = db.get(Order, payment.order_id)
        if order and order.payment_status != "paid":
            order.payment_status = "failed"
        db.commit()
        return {"received": True, "processed": True, "status": "failed", "payment_id": payment.id}

    return {"received": True, "processed": False, "message": f"Ignored event type '{event_type}'"}
