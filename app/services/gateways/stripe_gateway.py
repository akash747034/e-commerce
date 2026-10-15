import json
import logging
import uuid
from decimal import Decimal
from typing import Any

import stripe
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger("stripe_gateway")


def is_live_stripe_configured() -> bool:
    """
    Returns True if a real Stripe secret key is configured (not a mock placeholder).
    """
    key = settings.stripe_secret_key.strip()
    return bool(
        key
        and not key.startswith("sk_test_mock")
        and (key.startswith("sk_test_") or key.startswith("sk_live_"))
    )


def create_checkout_session(
    amount: Decimal,
    currency: str,
    order_id: int,
    order_number: str,
    user_id: int,
    customer_email: str | None = None,
    success_url: str | None = None,
    cancel_url: str | None = None,
) -> dict[str, Any]:
    """
    Creates a hosted Stripe Checkout Session.
    Returns the `checkout_url` where the customer enters card/UPI/Apple Pay on Stripe's hosted page.
    """
    amount_in_smallest_unit = int(amount * 100)
    curr = currency.lower()

    base_frontend = settings.frontend_url.rstrip("/")
    succ_url = success_url or f"{base_frontend}/orders/{order_id}/success?session_id={{CHECKOUT_SESSION_ID}}"
    canc_url = cancel_url or f"{base_frontend}/orders/{order_id}/cancel"

    if is_live_stripe_configured():
        stripe.api_key = settings.stripe_secret_key
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": curr,
                            "product_data": {
                                "name": f"Order {order_number}",
                            },
                            "unit_amount": amount_in_smallest_unit,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=succ_url,
                cancel_url=canc_url,
                customer_email=customer_email,
                metadata={
                    "order_id": str(order_id),
                    "order_number": order_number,
                    "user_id": str(user_id),
                },
            )
            return {
                "checkout_url": session.url,
                "session_id": session.id,
                "payment_intent_id": session.payment_intent,
                "status": session.status,
                "is_mock": False,
            }
        except stripe.StripeError as e:
            logger.error("Stripe Checkout Session creation failed: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {e.user_message or str(e)}",
            )
    else:
        # Development Sandbox Simulation
        simulated_session_id = f"cs_mock_{uuid.uuid4().hex[:20]}"
        simulated_checkout_url = (
            f"https://checkout.stripe.com/c/pay/{simulated_session_id}"
        )
        logger.info(
            "Stripe is in sandbox mode. Generated simulated checkout URL: %s",
            simulated_checkout_url,
        )
        return {
            "checkout_url": simulated_checkout_url,
            "session_id": simulated_session_id,
            "payment_intent_id": f"pi_mock_{uuid.uuid4().hex[:20]}",
            "status": "open",
            "is_mock": True,
        }


def retrieve_and_verify_checkout_session(session_id: str) -> dict[str, Any]:
    """
    Queries Stripe directly to verify that a Checkout Session was successfully paid.
    """
    if is_live_stripe_configured():
        stripe.api_key = settings.stripe_secret_key
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                "session_id": session.id,
                "payment_intent_id": session.payment_intent,
                "payment_status": session.payment_status,  # 'paid', 'unpaid'
                "status": session.status,  # 'complete', 'open', 'expired'
                "amount_total": Decimal(session.amount_total or 0) / 100,
                "currency": (session.currency or "INR").upper(),
                "is_mock": False,
            }
        except stripe.StripeError as e:
            logger.error("Stripe Checkout Session retrieval failed: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe verification failed: {e.user_message or str(e)}",
            )
    else:
        # Sandbox simulation
        return {
            "session_id": session_id,
            "payment_intent_id": f"pi_mock_{uuid.uuid4().hex[:16]}",
            "payment_status": "paid",
            "status": "complete",
            "amount_total": Decimal("0"),
            "currency": "INR",
            "is_mock": True,
        }


def create_payment_intent(
    amount: Decimal,
    currency: str,
    order_id: int,
    order_number: str,
    user_id: int,
    customer_email: str | None = None,
) -> dict[str, Any]:
    """
    Creates an embedded Stripe PaymentIntent (for Stripe Elements custom embedded UI).
    """
    amount_in_smallest_unit = int(amount * 100)
    curr = currency.lower()

    if is_live_stripe_configured():
        stripe.api_key = settings.stripe_secret_key
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_in_smallest_unit,
                currency=curr,
                metadata={
                    "order_id": str(order_id),
                    "order_number": order_number,
                    "user_id": str(user_id),
                },
                description=f"Payment for Order {order_number}",
                receipt_email=customer_email,
                automatic_payment_methods={"enabled": True},
            )
            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
                "publishable_key": settings.stripe_publishable_key,
                "is_mock": False,
            }
        except stripe.StripeError as e:
            logger.error("Stripe PaymentIntent creation failed: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {e.user_message or str(e)}",
            )
    else:
        simulated_intent_id = f"pi_mock_{uuid.uuid4().hex[:20]}"
        simulated_client_secret = f"{simulated_intent_id}_secret_{uuid.uuid4().hex[:16]}"
        return {
            "payment_intent_id": simulated_intent_id,
            "client_secret": simulated_client_secret,
            "status": "requires_payment_method",
            "publishable_key": settings.stripe_publishable_key or "pk_test_mock",
            "is_mock": True,
        }


def retrieve_and_verify_payment_intent(payment_intent_id: str) -> dict[str, Any]:
    """
    Queries Stripe's servers directly to verify the real status of a PaymentIntent.
    """
    if is_live_stripe_configured():
        stripe.api_key = settings.stripe_secret_key
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount_received": Decimal(intent.amount_received) / 100,
                "currency": intent.currency.upper(),
                "is_mock": False,
            }
        except stripe.StripeError as e:
            logger.error("Stripe PaymentIntent verification failed: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe verification failed: {e.user_message or str(e)}",
            )
    else:
        return {
            "payment_intent_id": payment_intent_id,
            "status": "succeeded",
            "amount_received": Decimal("0"),
            "currency": "INR",
            "is_mock": True,
        }


def construct_webhook_event(payload: bytes, signature_header: str | None) -> dict[str, Any]:
    """
    Verifies cryptographic webhook signature from Stripe.
    """
    if is_live_stripe_configured() and settings.stripe_webhook_secret:
        if not signature_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe-Signature header",
            )
        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, settings.stripe_webhook_secret
            )
            return event
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook payload")
        except stripe.SignatureVerificationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Stripe webhook signature"
            )
    else:
        try:
            return json.loads(payload.decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON in webhook payload")
