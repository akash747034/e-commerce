from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.return_refund import ReturnRequestCreate, ReturnRequestResponse
from app.schemas.shipment import ShipmentResponse
from app.services import return_refund as return_service
from app.services import shipment as shipment_service

router = APIRouter(tags=["Returns & Tracking"])


@router.post("/returns", response_model=ApiResponse[ReturnRequestResponse], status_code=status.HTTP_201_CREATED)
def submit_return_request(
    payload: ReturnRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a return request (RMA) for an order or specific item.
    """
    return_req = return_service.create_return_request(payload, current_user, db)
    return ApiResponse(
        message="Return request submitted successfully",
        data=ReturnRequestResponse.model_validate(return_req),
    )


@router.get("/returns", response_model=ApiResponse[list[ReturnRequestResponse]])
def list_my_return_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all return requests submitted by the logged-in customer.
    """
    returns = return_service.list_user_returns(current_user, db)
    return ApiResponse(
        message="Return requests retrieved successfully",
        data=[ReturnRequestResponse.model_validate(r) for r in returns],
    )


@router.get("/returns/{return_id}", response_model=ApiResponse[ReturnRequestResponse])
def get_return_request_details(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    View status and details of a specific return request.
    """
    return_req = return_service.get_return_request(return_id, current_user, db)
    return ApiResponse(
        message="Return request details retrieved successfully",
        data=ReturnRequestResponse.model_validate(return_req),
    )


@router.get("/orders/{order_id}/shipments", response_model=ApiResponse[list[ShipmentResponse]])
def get_order_tracking(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get carrier tracking details and delivery timeline for an order.
    """
    shipments = shipment_service.list_order_shipments(order_id, current_user, db)
    return ApiResponse(
        message="Order shipments retrieved successfully",
        data=[ShipmentResponse.model_validate(s) for s in shipments],
    )
