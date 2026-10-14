from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.schemas.brand import BrandCreate, BrandResponse, BrandUpdate
from app.schemas.response import ApiResponse
from app.services import brand as brand_service

router = APIRouter(prefix="/brands", tags=["Admin Brands"])


@router.get("", response_model=ApiResponse[list[BrandResponse]])
def admin_list_brands(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    include_inactive: bool = Query(default=True),
):
    """Admin: view all brands including inactive/drafts."""
    brands = brand_service.list_all_brands_admin(db, include_inactive=include_inactive)
    return ApiResponse(
        message="Brands retrieved successfully",
        data=[BrandResponse.model_validate(b) for b in brands],
    )


@router.get("/{brand_id}", response_model=ApiResponse[BrandResponse])
def admin_get_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: get brand by ID."""
    brand = brand_service.get_brand_by_id_admin(brand_id, db)
    return ApiResponse(
        message="Brand retrieved successfully",
        data=BrandResponse.model_validate(brand),
    )


@router.post("", response_model=ApiResponse[BrandResponse], status_code=status.HTTP_201_CREATED)
def admin_create_brand(
    payload: BrandCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: create brand."""
    brand = brand_service.create_brand(payload, db)
    return ApiResponse(
        message="Brand created successfully",
        data=BrandResponse.model_validate(brand),
    )


@router.patch("/{brand_id}", response_model=ApiResponse[BrandResponse])
def admin_update_brand(
    brand_id: int,
    payload: BrandUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: update brand."""
    brand = brand_service.update_brand(brand_id, payload, db)
    return ApiResponse(
        message="Brand updated successfully",
        data=BrandResponse.model_validate(brand),
    )


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: delete brand (only if no products are assigned)."""
    brand_service.delete_brand(brand_id, db)
