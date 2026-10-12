from app.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, func
from datetime import datetime

class Category(Base):
    __tablename__="categories"
    id:Mapped[int]=mapped_column(
        primary_key=True
        )
    title:Mapped[str]=mapped_column(
        String(50)
        )
    slug:Mapped[str]=mapped_column(
        String(100)
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
    subcategories = relationship(
        "Subcategory",
        back_populates="category"
    )
    products = relationship(
        "Product",
        back_populates="category"
    )