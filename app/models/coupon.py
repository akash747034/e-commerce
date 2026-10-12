from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Coupon(TimestampMixin, Base):
    __tablename__ = "coupons"

    __table_args__ = (
        CheckConstraint("discount_value > 0", name="ck_coupons_discount_value_positive"),
        CheckConstraint("min_purchase_amount >= 0", name="ck_coupons_min_purchase_nonnegative"),
        CheckConstraint(
            "discount_type IN ('percentage', 'fixed_amount')",
            name="ck_coupons_discount_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    discount_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'percentage' or 'fixed_amount'
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    min_purchase_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, server_default=text("0"), nullable=False
    )
    max_discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"), nullable=False)
    per_user_limit: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )

    usages: Mapped[list["CouponUsage"]] = relationship(back_populates="coupon", cascade="all, delete-orphan")


class CouponUsage(TimestampMixin, Base):
    __tablename__ = "coupon_usages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    coupon_id: Mapped[int] = mapped_column(
        ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    coupon: Mapped["Coupon"] = relationship(back_populates="usages")
    user: Mapped["User"] = relationship()
    order: Mapped["Order"] = relationship()
