from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.profile import ChangePasswordPayload, UserDetailResponse, UserUpdate
from app.schemas.response import ApiResponse
from app.services import profile as profile_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=ApiResponse[UserDetailResponse])
def get_my_profile(current_user: User = Depends(get_current_user)):
    return ApiResponse(
        message="Profile retrieved successfully",
        data=UserDetailResponse.model_validate(current_user),
    )


@router.patch("/me", response_model=ApiResponse[UserDetailResponse])
def update_my_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = profile_service.update_profile(payload, current_user, db)
    return ApiResponse(
        message="Profile updated successfully",
        data=UserDetailResponse.model_validate(user),
    )


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile_service.change_password(payload, current_user, db)
