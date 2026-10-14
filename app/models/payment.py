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


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payments_amount_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # e.g., 'stripe', 'razorpay', 'paypal', 'cod' (Cash on Delivery)
    payment_gateway: Mapped[str] = mapped_column(String(50), nullable=False)

    # Gateway Transaction/Order ID (e.g. Stripe charge_id / Razorpay payment_id)
    transaction_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", server_default=text("'INR'"), nullable=False)

    # e.g. 'pending', 'succeeded', 'failed', 'refunded'
    status: Mapped[str] = mapped_column(
        String(30), default="pending", server_default=text("'pending'"), nullable=False, index=True
    )

    # Raw gateway response or failure message
    payment_response: Mapped[str | None] = mapped_column(Text)

    order: Mapped["Order"] = relationship(back_populates="payments")
    user: Mapped["User"] = relationship()
    refunds: Mapped[list["Refund"]] = relationship(back_populates="payment", cascade="all, delete-orphan")
