from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    compare_at_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", server_default=text("'active'"), nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True, nullable=False)
    subcategory_id: Mapped[int] = mapped_column(ForeignKey("subcategories.id"), index=True, nullable=False)
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"), index=True, nullable=True)
    seller_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)

    category: Mapped["Category"] = relationship(back_populates="products")
    subcategory: Mapped["SubCategory"] = relationship(back_populates="products")
    brand: Mapped["Brand | None"] = relationship(back_populates="products")
    seller: Mapped["User | None"] = relationship()
    product_images: Mapped[list["ProductImage"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="product", cascade="all, delete-orphan")
