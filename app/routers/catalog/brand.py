from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.brand import BrandResponse
from app.schemas.response import ApiResponse
from app.services import brand as brand_service

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get("", response_model=ApiResponse[list[BrandResponse]])
def list_brands(db: Session = Depends(get_db)):
    brands = brand_service.list_brands(db)
    return ApiResponse(
        message="Brands retrieved successfully",
        data=[BrandResponse.model_validate(b) for b in brands],
    )


@router.get("/{slug}", response_model=ApiResponse[BrandResponse])
def get_brand(slug: str, db: Session = Depends(get_db)):
    brand = brand_service.get_brand(slug, db)
    return ApiResponse(
        message="Brand retrieved successfully",
        data=BrandResponse.model_validate(brand),
    )
