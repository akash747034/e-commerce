from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import LoginPayload, UserCreate


def register(payload: UserCreate, db: Session) -> User:
    if db.scalars(select(User).where(User.email == payload.email)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(name=payload.name, email=payload.email, hashed_password=hash_password(payload.password))
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")


def login(payload: LoginPayload, db: Session) -> dict:
    user = db.scalars(select(User).where(User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "access_token": create_access_token(str(user.id)),
        "token_type": "bearer",
    }
