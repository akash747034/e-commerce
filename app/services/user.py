from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.models.user import User
from app.schemas.user import UserCreate,LoginPayload
from fastapi import HTTPException,Depends,HTTPException, status
from pwdlib import PasswordHash
from app.core.config import settings
import jwt
# from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.database import get_db
from datetime import datetime, timedelta, timezone

password_hash = PasswordHash.recommended()
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
bearer_scheme = HTTPBearer()

def hash_password(password: str) -> str:
    return password_hash.hash(password)
def register(user: UserCreate, db: Session):
    exist_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if exist_user:
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    except SQLAlchemyError:
        db.rollback()
        raise


def login(payload:LoginPayload,db:Session):
      user=db.query(User).filter(User.email==payload.email).first()

      if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
      
      is_valid = password_hash.verify(
        payload.password,
        user.hashed_password
        )

      if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
      payload = {
        "sub": str(user.id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
       }
      token =jwt.encode(payload,settings.secret_key,settings.algorithm)



      return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "access_token": token,
        "token_type": "bearer"
       }




def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    try:
        data = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        user_id = data.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )   

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user




