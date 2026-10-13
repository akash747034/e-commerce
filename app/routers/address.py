from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate
from app.schemas.response import ApiResponse
from app.services import address as address_service

router = APIRouter(prefix="/users/me/addresses", tags=["Addresses"])


@router.get("", response_model=ApiResponse[list[AddressResponse]])
def list_addresses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    addresses = address_service.list_addresses(current_user, db)
    return ApiResponse(
        message="Addresses retrieved successfully",
        data=[AddressResponse.model_validate(a) for a in addresses],
    )


@router.post("", response_model=ApiResponse[AddressResponse], status_code=status.HTTP_201_CREATED)
def create_address(
    payload: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    address = address_service.create_address(payload, current_user, db)
    return ApiResponse(
        message="Address created successfully",
        data=AddressResponse.model_validate(address),
    )


@router.get("/{address_id}", response_model=ApiResponse[AddressResponse])
def get_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    address = address_service.get_address(address_id, current_user, db)
    return ApiResponse(
        message="Address retrieved successfully",
        data=AddressResponse.model_validate(address),
    )


@router.patch("/{address_id}", response_model=ApiResponse[AddressResponse])
def update_address(
    address_id: int,
    payload: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    address = address_service.update_address(address_id, payload, current_user, db)
    return ApiResponse(
        message="Address updated successfully",
        data=AddressResponse.model_validate(address),
    )


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    address_service.delete_address(address_id, current_user, db)


@router.post("/{address_id}/set-primary", response_model=ApiResponse[AddressResponse])
def set_primary(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    address = address_service.set_primary_address(address_id, current_user, db)
    return ApiResponse(
        message="Primary address updated",
        data=AddressResponse.model_validate(address),
    )
