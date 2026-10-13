from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.profile import ChangePasswordPayload, UserUpdate


def update_profile(payload: UserUpdate, user: User, db: Session) -> User:
    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def change_password(payload: ChangePasswordPayload, user: User, db: Session) -> None:
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
