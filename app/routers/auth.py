from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.user import (
    LoginPayload,
    LoginResponse,
    RefreshTokenPayload,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services import user as user_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    user = user_service.register(payload, db)
    return ApiResponse(
        message="User registered successfully",
        data=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=ApiResponse[LoginResponse])
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    result = user_service.login(payload, db)
    return ApiResponse(
        message="Login successful",
        data=LoginResponse(**result),
    )


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
def refresh_token(payload: RefreshTokenPayload, db: Session = Depends(get_db)):
    result = user_service.refresh_token(payload, db)
    return ApiResponse(
        message="Token refreshed successfully",
        data=TokenResponse(**result),
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
def me(current_user: User = Depends(get_current_user)):
    return ApiResponse(
        message="User profile retrieved successfully",
        data=UserResponse.model_validate(current_user),
    )