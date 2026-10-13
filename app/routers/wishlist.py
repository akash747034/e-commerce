from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.wishlist import WishlistItemResponse
from app.services import wishlist as wishlist_service

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


@router.get("", response_model=ApiResponse[list[WishlistItemResponse]])
def list_wishlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = wishlist_service.list_wishlist(current_user, db)
    return ApiResponse(
        message="Wishlist retrieved successfully",
        data=[WishlistItemResponse.model_validate(i) for i in items],
    )


@router.post("/{product_id}", response_model=ApiResponse[WishlistItemResponse], status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = wishlist_service.add_to_wishlist(product_id, current_user, db)
    return ApiResponse(
        message="Product added to wishlist",
        data=WishlistItemResponse.model_validate(item),
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wishlist_service.remove_from_wishlist(product_id, current_user, db)
