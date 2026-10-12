from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", server_default=text("'active'"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True, nullable=False)
    subcategory_id: Mapped[int] = mapped_column(ForeignKey("subcategories.id"), index=True, nullable=False)

    category: Mapped["Category"] = relationship(back_populates="products")
    subcategory: Mapped["SubCategory"] = relationship(back_populates="products")
    product_images: Mapped[list["ProductImage"]] = relationship(back_populates="product",cascade="all, delete-orphan")
