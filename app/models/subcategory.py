from app.core.database import Base
from sqlalchemy import DateTime, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

class SubCategory(Base):
    __tablename__="subcategories"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False,
    )
    created_at:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
        )
    updated_at:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
        )
    deleted_at:Mapped[datetime|None]=mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True
    )
    category = relationship(
        "Category",
        back_populates="subcategories",
    )

    products = relationship(
        "Product",
        back_populates="subcategory",
    )
