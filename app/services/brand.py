from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.brand import Brand


def list_brands(db: Session) -> list[Brand]:
    return list(
        db.scalars(select(Brand).where(Brand.is_active == True)).all()
    )


def get_brand(slug: str, db: Session) -> Brand:
    brand = db.scalars(
        select(Brand).where(Brand.slug == slug, Brand.is_active == True)
    ).first()
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return brand
