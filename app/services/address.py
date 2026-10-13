from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.address import Address
from app.models.user import User
from app.schemas.address import AddressCreate, AddressUpdate


def list_addresses(user: User, db: Session) -> list[Address]:
    return list(db.scalars(select(Address).where(Address.user_id == user.id)).all())


def create_address(payload: AddressCreate, user: User, db: Session) -> Address:
    # If this address is being set as primary, unset all other primaries
    if payload.is_primary:
        db.execute(
            Address.__table__.update()
            .where(Address.user_id == user.id)
            .values(is_primary=False)
        )

    address = Address(user_id=user.id, **payload.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def get_address(address_id: int, user: User, db: Session) -> Address:
    address = db.scalars(
        select(Address).where(Address.id == address_id, Address.user_id == user.id)
    ).first()
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return address


def update_address(address_id: int, payload: AddressUpdate, user: User, db: Session) -> Address:
    address = get_address(address_id, user, db)
    update_data = payload.model_dump(exclude_none=True)

    # If setting as primary, unset all others
    if update_data.get("is_primary"):
        db.execute(
            Address.__table__.update()
            .where(Address.user_id == user.id, Address.id != address_id)
            .values(is_primary=False)
        )

    for field, value in update_data.items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)
    return address


def delete_address(address_id: int, user: User, db: Session) -> None:
    address = get_address(address_id, user, db)
    db.delete(address)
    db.commit()


def set_primary_address(address_id: int, user: User, db: Session) -> Address:
    address = get_address(address_id, user, db)
    # Unset all primaries for this user
    db.execute(
        Address.__table__.update()
        .where(Address.user_id == user.id)
        .values(is_primary=False)
    )
    address.is_primary = True
    db.commit()
    db.refresh(address)
    return address
