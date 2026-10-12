from app.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, func, ForeignKey,Text,text,Boolean
from datetime import datetime

class Address(Base):
    __tablename__="addresses"
    id:Mapped[int]=mapped_column(
        primary_key=True
        )

    user_id:Mapped[int]=mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    addressline1: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    addressline2: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    landmark: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    city:Mapped[str|None] = mapped_column(
        String(170),
        nullable=False,
    )
    country:Mapped[str|None] = mapped_column(
        String(56),
        nullable=False,
    )
    pincode: Mapped[str] = mapped_column(
        String(6),
        nullable=False,
    )
    address:Mapped[str|None]=mapped_column(
        String(30)
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
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
 
  
    user: Mapped["User"] = relationship(
     back_populates="addresses"
    )