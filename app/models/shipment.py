from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Shipment(TimestampMixin, Base):
    """
    Shipment and tracking model for order fulfillment.
    """
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # e.g., 'FedEx', 'BlueDart', 'Delhivery', 'DHL', 'India Post'
    carrier: Mapped[str] = mapped_column(String(100), nullable=False)

    tracking_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    tracking_url: Mapped[str | None] = mapped_column(String(500))

    # e.g. 'label_created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'returned'
    status: Mapped[str] = mapped_column(
        String(50), default="label_created", server_default=text("'label_created'"), nullable=False, index=True
    )

    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    order: Mapped["Order"] = relationship(back_populates="shipments")
