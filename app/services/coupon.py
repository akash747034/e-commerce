from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.coupon import Coupon
from app.schemas.coupon import CouponCreate, CouponUpdate


def list_coupons_admin(db: Session, include_inactive: bool = True) -> list[Coupon]:
    """Admin: list all coupons."""
    query = select(Coupon)
    if not include_inactive:
        query = query.where(Coupon.is_active == True)
    return list(db.scalars(query.order_by(Coupon.id.desc())).all())


def get_coupon_by_id_admin(coupon_id: int, db: Session) -> Coupon:
    """Admin: get coupon by ID."""
    coupon = db.get(Coupon, coupon_id)
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")
    return coupon


def create_coupon(payload: CouponCreate, db: Session) -> Coupon:
    """Admin: create a discount coupon."""
    code_upper = payload.code.strip().upper()

    existing = db.scalars(select(Coupon).where(Coupon.code == code_upper)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Coupon with code '{code_upper}' already exists",
        )

    if payload.valid_to <= payload.valid_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="valid_to date must be greater than valid_from date",
        )

    coupon = Coupon(
        code=code_upper,
        description=payload.description,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        min_purchase_amount=payload.min_purchase_amount,
        max_discount_amount=payload.max_discount_amount,
        usage_limit=payload.usage_limit,
        per_user_limit=payload.per_user_limit,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        is_active=payload.is_active,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def update_coupon(coupon_id: int, payload: CouponUpdate, db: Session) -> Coupon:
    """Admin: update coupon details."""
    coupon = get_coupon_by_id_admin(coupon_id, db)
    update_data = payload.model_dump(exclude_unset=True)

    valid_from = update_data.get("valid_from", coupon.valid_from)
    valid_to = update_data.get("valid_to", coupon.valid_to)
    if valid_to <= valid_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="valid_to date must be greater than valid_from date",
        )

    for field, value in update_data.items():
        setattr(coupon, field, value)

    db.commit()
    db.refresh(coupon)
    return coupon


def delete_coupon(coupon_id: int, db: Session) -> None:
    """Admin: delete coupon."""
    coupon = get_coupon_by_id_admin(coupon_id, db)
    db.delete(coupon)
    db.commit()
