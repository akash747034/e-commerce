from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.return_refund import (
    RefundCreate,
    RefundResponse,
    ReturnRequestResponse,
    ReturnRequestStatusUpdate,
)
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentResponse,
    ShipmentStatusUpdate,
)
from app.services import return_refund as return_service
from app.services import shipment as shipment_service

router = APIRouter(tags=["Admin Fulfillment & Returns"])


# ---------------------------------------------------------------------------
# Shipments (Logistics)
# ---------------------------------------------------------------------------

@router.get("/shipments", response_model=ApiResponse[list[ShipmentResponse]])
def list_all_shipments(
    status: str | None = Query(None, description="Filter by shipment status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List all platform shipments and tracking records.
    """
    shipments = shipment_service.list_all_shipments_admin(db, status, skip, limit)
    return ApiResponse(
        message="Shipments retrieved successfully",
        data=[ShipmentResponse.model_validate(s) for s in shipments],
    )


@router.post("/shipments", response_model=ApiResponse[ShipmentResponse], status_code=status.HTTP_201_CREATED)
def admin_create_shipment(
    payload: ShipmentCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Admin directly creates or reassigns shipment tracking for an order.
    """
    shipment = shipment_service.create_shipment(payload, admin, db)
    return ApiResponse(
        message="Shipment created successfully",
        data=ShipmentResponse.model_validate(shipment),
    )


@router.patch("/shipments/{shipment_id}/status", response_model=ApiResponse[ShipmentResponse])
def admin_update_shipment_status(
    shipment_id: int,
    payload: ShipmentStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Admin updates shipment checkpoint (e.g. marked as 'delivered').
    """
    shipment = shipment_service.update_shipment_status(shipment_id, payload, admin, db)
    return ApiResponse(
        message=f"Shipment status updated to '{shipment.status}'",
        data=ShipmentResponse.model_validate(shipment),
    )


# ---------------------------------------------------------------------------
# Returns (RMA)
# ---------------------------------------------------------------------------

@router.get("/returns", response_model=ApiResponse[list[ReturnRequestResponse]])
def list_all_returns(
    status: str | None = Query(None, description="Filter by status (e.g. 'pending', 'approved', 'rejected')"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List customer return requests awaiting review or completed.
    """
    returns = return_service.admin_list_returns(db, status, skip, limit)
    return ApiResponse(
        message="Return requests retrieved successfully",
        data=[ReturnRequestResponse.model_validate(r) for r in returns],
    )


@router.patch("/returns/{return_id}/status", response_model=ApiResponse[ReturnRequestResponse])
def update_return_status(
    return_id: int,
    payload: ReturnRequestStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Approve, reject, or mark a return request completed.
    """
    return_req = return_service.admin_update_return_status(return_id, payload, db)
    return ApiResponse(
        message=f"Return request status updated to '{return_req.status}'",
        data=ReturnRequestResponse.model_validate(return_req),
    )


# ---------------------------------------------------------------------------
# Refunds
# ---------------------------------------------------------------------------

@router.post("/refunds", response_model=ApiResponse[RefundResponse], status_code=status.HTTP_201_CREATED)
def issue_refund(
    payload: RefundCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Process a financial refund for an order (tied to Payment or ReturnRequest).
    """
    refund = return_service.process_refund(payload, db)
    return ApiResponse(
        message="Refund processed successfully",
        data=RefundResponse.model_validate(refund),
    )


@router.get("/refunds", response_model=ApiResponse[list[RefundResponse]])
def list_all_refunds(
    order_id: int | None = Query(None, description="Filter by order ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List all processed refunds.
    """
    refunds = return_service.admin_list_refunds(db, order_id, skip, limit)
    return ApiResponse(
        message="Refunds retrieved successfully",
        data=[RefundResponse.model_validate(r) for r in refunds],
    )
