from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class ProductVariant(TimestampMixin, Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_product_variants_quantity_nonnegative"),
        CheckConstraint("price IS NULL OR price >= 0", name="ck_product_variants_price_nonnegative"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"), nullable=False)
    attributes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )

    product: Mapped["Product"] = relationship(back_populates="variants")
