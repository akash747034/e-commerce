
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class OrderItem(TimestampMixin, Base):
    __tablename__ = "order_items"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_order_items_quantity_positive",
        ),
        CheckConstraint(
            "mrp >= 0 AND selling_price >= 0",
            name="ck_order_items_prices_nonnegative",
        ),
        CheckConstraint(
            "line_total >= 0",
            name="ck_order_items_total_nonnegative",
        ),
        CheckConstraint(
            "item_discount >= 0",
            name="ck_order_items_item_discount_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Snapshots of names at order time so future product updates don't alter order history
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    variant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # MRP / original listed price per unit (compare_at_price if set, else product.price)
    mrp: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    # Actual price per unit the customer pays (after product-level discount)
    selling_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    # Total product-level discount for this line: (mrp - selling_price) * quantity
    item_discount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )

    # selling_price * quantity  (line subtotal before coupon discount)
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
        index=True,
    )

    order: Mapped["Order"] = relationship(
        back_populates="items",
    )

    product: Mapped["Product"] = relationship()
    variant: Mapped["ProductVariant | None"] = relationship()
