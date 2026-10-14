from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Refund(TimestampMixin, Base):
    """
    Financial refunds linked to a Payment and/or ReturnRequest.
    """
    __tablename__ = "refunds"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_refunds_amount_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    return_request_id: Mapped[int | None] = mapped_column(
        ForeignKey("return_requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # e.g. 'gateway', 'store_credit', 'manual_bank_transfer'
    refund_method: Mapped[str] = mapped_column(String(50), default="gateway", server_default=text("'gateway'"), nullable=False)

    # Refund reference ID returned by gateway (e.g. re_xxxx from Stripe / rfn_xxxx from Razorpay)
    gateway_refund_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)

    # e.g., 'pending', 'processed', 'failed'
    status: Mapped[str] = mapped_column(
        String(30), default="pending", server_default=text("'pending'"), nullable=False, index=True
    )

    reason: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)

    order: Mapped["Order"] = relationship(back_populates="refunds")
    payment: Mapped["Payment | None"] = relationship(back_populates="refunds")
    return_request: Mapped["ReturnRequest | None"] = relationship(back_populates="refund")
