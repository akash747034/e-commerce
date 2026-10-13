from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate


def create_review(payload: ReviewCreate, user: User, db: Session) -> Review:
    # Check if user already reviewed this product
    existing = db.scalars(
        select(Review).where(Review.user_id == user.id, Review.product_id == payload.product_id)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already reviewed this product")

    # Check if user has a delivered order containing this product
    verified_purchase = db.scalars(
        select(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .where(
            Order.user_id == user.id,
            Order.status == "delivered",
            OrderItem.product_id == payload.product_id,
        )
    ).first() is not None

    review = Review(
        user_id=user.id,
        product_id=payload.product_id,
        rating=payload.rating,
        title=payload.title,
        comment=payload.comment,
        is_verified_purchase=verified_purchase,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def list_product_reviews(product_id: int, db: Session) -> list[Review]:
    return list(
        db.scalars(
            select(Review).where(
                Review.product_id == product_id,
                Review.status == "approved",
            ).order_by(Review.created_at.desc())
        ).all()
    )


def delete_review(review_id: int, user: User, db: Session) -> None:
    review = db.scalars(
        select(Review).where(Review.id == review_id, Review.user_id == user.id)
    ).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    db.delete(review)
    db.commit()
