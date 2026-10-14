
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint(
            "subtotal >= 0",
            name="ck_orders_subtotal_nonnegative",
        ),
        CheckConstraint(
            "product_discount_total >= 0",
            name="ck_orders_product_discount_nonnegative",
        ),
        CheckConstraint(
            "coupon_discount >= 0",
            name="ck_orders_coupon_discount_nonnegative",
        ),
        CheckConstraint(
            "shipping_amount >= 0",
            name="ck_orders_shipping_nonnegative",
        ),
        CheckConstraint(
            "tax_amount >= 0",
            name="ck_orders_tax_nonnegative",
        ),
        CheckConstraint(
            "total_amount >= 0",
            name="ck_orders_total_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    order_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
        index=True,
    )

    # Sum of all line_total values (selling_price * qty per item, after product discounts)
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    # Sum of all item_discount values — total saved via product-level pricing
    product_discount_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )

    # Discount applied by a coupon code on top of subtotal
    coupon_discount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )

    shipping_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )

    # Final amount the customer actually paid
    # = subtotal - coupon_discount + shipping_amount + tax_amount
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    payment_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
        index=True,
    )

    payment_method: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    shipping_address_id: Mapped[int] = mapped_column(
        ForeignKey("addresses.id", ondelete="RESTRICT"),
        nullable=False,
    )

    billing_address_id: Mapped[int | None] = mapped_column(
        ForeignKey("addresses.id", ondelete="RESTRICT"),
        nullable=True,
    )

    coupon_id: Mapped[int | None] = mapped_column(
        ForeignKey("coupons.id", ondelete="SET NULL"),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="orders",
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    shipping_address: Mapped["Address"] = relationship(foreign_keys=[shipping_address_id])
    billing_address: Mapped["Address | None"] = relationship(foreign_keys=[billing_address_id])
    coupon: Mapped["Coupon | None"] = relationship()
    payments: Mapped[list["Payment"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    shipments: Mapped[list["Shipment"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    return_requests: Mapped[list["ReturnRequest"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    refunds: Mapped[list["Refund"]] = relationship(back_populates="order", cascade="all, delete-orphan")


