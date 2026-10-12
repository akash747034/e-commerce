
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class CartItem(TimestampMixin, Base):
    __tablename__ = "cart_items"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_cart_items_quantity_positive",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"),
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

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    # Relationships
    cart: Mapped["Cart"] = relationship(
        back_populates="items",
    )

    product: Mapped["Product"] = relationship()
    variant: Mapped["ProductVariant | None"] = relationship()
