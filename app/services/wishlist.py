from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.user import User
from app.models.wishlist import WishlistItem


def list_wishlist(user: User, db: Session) -> list[WishlistItem]:
    return list(
        db.scalars(select(WishlistItem).where(WishlistItem.user_id == user.id)).all()
    )


def add_to_wishlist(product_id: int, user: User, db: Session) -> WishlistItem:
    # Ensure product exists
    product = db.get(Product, product_id)
    if not product or product.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    existing = db.scalars(
        select(WishlistItem).where(
            WishlistItem.user_id == user.id,
            WishlistItem.product_id == product_id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product already in wishlist")

    item = WishlistItem(user_id=user.id, product_id=product_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_wishlist(product_id: int, user: User, db: Session) -> None:
    item = db.scalars(
        select(WishlistItem).where(
            WishlistItem.user_id == user.id,
            WishlistItem.product_id == product_id,
        )
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not in wishlist")
    db.delete(item)
    db.commit()
