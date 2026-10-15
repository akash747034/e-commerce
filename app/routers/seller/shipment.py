from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_seller
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.shipment import ShipmentCreate, ShipmentResponse, ShipmentStatusUpdate
from app.services import shipment as shipment_service

router = APIRouter(prefix="/seller", tags=["Seller Shipments"])


@router.post("/shipments", response_model=ApiResponse[ShipmentResponse], status_code=status.HTTP_201_CREATED)
def create_order_shipment(
    payload: ShipmentCreate,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """
    Seller dispatches an order by adding a tracking number and logistics carrier.
    Automatically moves the order status to 'shipped'.
    """
    shipment = shipment_service.create_shipment(payload, seller, db)
    return ApiResponse(
        message="Shipment created and order marked as shipped",
        data=ShipmentResponse.model_validate(shipment),
    )


@router.patch("/shipments/{shipment_id}/status", response_model=ApiResponse[ShipmentResponse])
def update_shipment_status(
    shipment_id: int,
    payload: ShipmentStatusUpdate,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """
    Update tracking checkpoint (e.g. 'in_transit', 'out_for_delivery', 'delivered').
    """
    shipment = shipment_service.update_shipment_status(shipment_id, payload, seller, db)
    return ApiResponse(
        message=f"Shipment status updated to '{shipment.status}'",
        data=ShipmentResponse.model_validate(shipment),
    )


@router.get("/orders/{order_id}/shipments", response_model=ApiResponse[list[ShipmentResponse]])
def get_seller_order_shipments(
    order_id: int,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """
    View tracking details for a seller order.
    """
    shipments = shipment_service.list_order_shipments(order_id, seller, db)
    return ApiResponse(
        message="Shipments retrieved successfully",
        data=[ShipmentResponse.model_validate(s) for s in shipments],
    )
