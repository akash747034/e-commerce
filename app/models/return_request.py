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


class ReturnRequest(TimestampMixin, Base):
    """
    Customer return request for an order or specific order item (RMA: Return Merchandise Authorization).
    """
    __tablename__ = "return_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # e.g., 'defective', 'wrong_item', 'size_fit', 'not_needed'
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    # e.g., 'pending', 'approved', 'rejected', 'item_received', 'completed'
    status: Mapped[str] = mapped_column(
        String(30), default="pending", server_default=text("'pending'"), nullable=False, index=True
    )

    # Admin rejection or review note
    admin_notes: Mapped[str | None] = mapped_column(Text)

    order: Mapped["Order"] = relationship(back_populates="return_requests")
    order_item: Mapped["OrderItem | None"] = relationship()
    user: Mapped["User"] = relationship()
    refund: Mapped["Refund | None"] = relationship(back_populates="return_request")
