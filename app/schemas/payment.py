from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class PaymentInitiate(BaseModel):
    order_id: int
    payment_gateway: Annotated[str, Field(default="stripe", min_length=2, max_length=50, description="'stripe' or 'cod'")]
    currency: Annotated[str, Field(default="INR", max_length=10)] = "INR"
    success_url: str | None = None  # Optional redirect override for Stripe Checkout
    cancel_url: str | None = None   # Optional cancel override for Stripe Checkout


class PaymentVerify(BaseModel):
    # From Stripe Checkout URL redirect: ?session_id=cs_...
    session_id: Annotated[str | None, Field(default=None, max_length=255, description="Stripe Checkout Session ID (cs_...)")] = None
    # Or from Stripe Elements: payment_intent_id (pi_...)
    payment_intent_id: Annotated[str | None, Field(default=None, max_length=255, description="Stripe PaymentIntent ID (pi_...)")] = None


class PaymentStatusUpdate(BaseModel):
    status: Annotated[str, Field(min_length=3, max_length=30, description="'pending', 'succeeded', 'failed', 'refunded'")]
    payment_response: str | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    user_id: int
    payment_gateway: str
    transaction_id: str | None
    amount: Decimal
    currency: str
    status: str
    payment_response: str | None
    created_at: datetime
    updated_at: datetime


class PaymentInitiateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: int
    order_id: int
    order_number: str
    amount: Decimal
    currency: str
    payment_gateway: str
    status: str
    transaction_id: str | None

    # Hosted Checkout URL where frontend redirects the user (e.g. https://checkout.stripe.com/...)
    checkout_url: str | None = None
    session_id: str | None = None

    # Embedded Stripe Elements tokens
    client_secret: str | None = None
    publishable_key: str | None = None

    message: str
