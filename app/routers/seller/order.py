from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_seller
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.seller import SellerItemStatusUpdate, SellerOrderItemResponse
from app.services import seller as seller_service

router = APIRouter(prefix="/orders", tags=["Seller Orders"])


@router.get("", response_model=ApiResponse[list[SellerOrderItemResponse]])
def list_seller_orders(
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
    status_filter: str | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """
    Seller: view orders for items sold by this seller.
    Never exposes other sellers' items from the same order.
    """
    items = seller_service.list_seller_order_items(
        seller=seller,
        db=db,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        message="Seller order items retrieved successfully",
        data=items,
    )


@router.get("/{order_item_id}", response_model=ApiResponse[SellerOrderItemResponse])
def get_seller_order_item(
    order_item_id: int,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """Seller: view details of a specific item ordered from their store."""
    item = seller_service.get_seller_order_item(order_item_id=order_item_id, seller=seller, db=db)
    return ApiResponse(
        message="Seller order item retrieved successfully",
        data=item,
    )


@router.patch("/{order_item_id}/status", response_model=ApiResponse[SellerOrderItemResponse])
def update_seller_order_item_status(
    order_item_id: int,
    payload: SellerItemStatusUpdate,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """
    Seller: update fulfillment status of an item (e.g. 'processing', 'shipped', 'delivered').
    """
    item = seller_service.update_seller_order_item_status(
        order_item_id=order_item_id,
        new_status=payload.status,
        seller=seller,
        db=db,
    )
    return ApiResponse(
        message="Order item status updated successfully",
        data=item,
    )
