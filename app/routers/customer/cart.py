from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse
from app.schemas.response import ApiResponse
from app.services import cart as cart_service

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=ApiResponse[CartResponse])
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = cart_service.get_cart(current_user, db)
    return ApiResponse(message="Cart retrieved successfully", data=cart)


@router.post("/items", response_model=ApiResponse[CartResponse])
def add_item(
    payload: CartItemAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = cart_service.add_item(payload, current_user, db)
    return ApiResponse(message="Item added to cart", data=cart)


@router.patch("/items/{item_id}", response_model=ApiResponse[CartResponse])
def update_item(
    item_id: int,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = cart_service.update_item(item_id, payload, current_user, db)
    return ApiResponse(message="Cart item updated", data=cart)


@router.delete("/items/{item_id}", response_model=ApiResponse[CartResponse])
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = cart_service.remove_item(item_id, current_user, db)
    return ApiResponse(message="Item removed from cart", data=cart)


@router.delete("", response_model=ApiResponse[CartResponse])
def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = cart_service.clear_cart(current_user, db)
    return ApiResponse(message="Cart cleared", data=cart)
