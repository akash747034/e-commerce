from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

password_hasher = PasswordHash.recommended()
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": subject, "type": "access", "exp": expire},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode(
        {"sub": subject, "type": "refresh", "exp": expire},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def verify_refresh_token(token: str) -> str:
    try:
        data = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        if data.get("type") != "refresh":
            raise jwt.InvalidTokenError
        user_id = data.get("sub")
        if not user_id:
            raise jwt.InvalidTokenError
        return str(user_id)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        data = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id = data.get("sub")
        if not user_id or data.get("type") == "refresh":
            raise jwt.InvalidTokenError
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalars(select(User).where(User.id == int(user_id))).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is inactive")
    return user


# ---------------------------------------------------------------------------
# Role-based dependency guards
# ---------------------------------------------------------------------------

def _require_role(*allowed_roles: str):
    """Factory that returns a FastAPI dependency enforcing one of the given roles."""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.user_type not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {' or '.join(allowed_roles)}.",
            )
        return current_user
    return dependency


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Allow only admins."""
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admins only.",
        )
    return current_user


def require_seller(current_user: User = Depends(get_current_user)) -> User:
    """Allow only sellers."""
    if current_user.user_type != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Sellers only.",
        )
    return current_user


def require_customer(current_user: User = Depends(get_current_user)) -> User:
    """Allow only customers."""
    if current_user.user_type != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Customers only.",
        )
    return current_user


# Convenience: admin OR seller (e.g. product management)
require_admin_or_seller = _require_role("admin", "seller")
