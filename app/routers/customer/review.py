from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services import review as review_service

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("", response_model=ApiResponse[ReviewResponse], status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = review_service.create_review(payload, current_user, db)
    return ApiResponse(
        message="Review submitted successfully",
        data=ReviewResponse.model_validate(review),
    )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review_service.delete_review(review_id, current_user, db)
