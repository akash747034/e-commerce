from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.schemas.profile import UserDetailResponse
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/users", tags=["Admin Users"])


class AdminUserUpdate(BaseModel):
    status: str | None = None  # e.g. "active", "suspended", "banned"
    user_type: str | None = None  # e.g. "customer", "seller", "admin"
    is_verified: bool | None = None


@router.get("", response_model=ApiResponse[list[UserDetailResponse]])
def admin_list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    user_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, max_length=200),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Admin: view all users on the platform with filtering."""
    query = select(User)

    if user_type:
        query = query.where(User.user_type == user_type)
    if status_filter:
        query = query.where(User.status == status_filter)
    if search:
        query = query.where((User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%")))

    query = query.order_by(User.id.desc()).offset(skip).limit(limit)
    users = list(db.scalars(query).all())

    return ApiResponse(
        message="Users retrieved successfully",
        data=[UserDetailResponse.model_validate(u) for u in users],
    )


@router.get("/{user_id}", response_model=ApiResponse[UserDetailResponse])
def admin_get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: get full details of a specific user."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return ApiResponse(
        message="User retrieved successfully",
        data=UserDetailResponse.model_validate(user),
    )


@router.patch("/{user_id}", response_model=ApiResponse[UserDetailResponse])
def admin_update_user(
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: update user status (suspend, activate) or change user_type (role)."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return ApiResponse(
        message="User updated successfully",
        data=UserDetailResponse.model_validate(user),
    )
