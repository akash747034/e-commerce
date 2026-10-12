from sqlalchemy import Boolean, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Address(TimestampMixin, Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line_2: Mapped[str | None] = mapped_column(String(255))
    landmark: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(170), nullable=False)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(56), nullable=False)
    pincode: Mapped[str] = mapped_column(String(20), nullable=False)
    address_type: Mapped[str] = mapped_column(
        String(30), default="shipping", server_default=text("'shipping'"), nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="addresses")
