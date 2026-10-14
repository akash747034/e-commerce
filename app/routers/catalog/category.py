from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.category import CategoryResponse, SubCategoryResponse
from app.schemas.response import ApiResponse
from app.services import category as category_service

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=ApiResponse[list[CategoryResponse]])
def list_categories(db: Session = Depends(get_db)):
    categories = category_service.list_categories(db)
    return ApiResponse(
        message="Categories retrieved successfully",
        data=[CategoryResponse.model_validate(c) for c in categories],
    )


@router.get("/{slug}", response_model=ApiResponse[CategoryResponse])
def get_category(slug: str, db: Session = Depends(get_db)):
    category = category_service.get_category(slug, db)
    return ApiResponse(
        message="Category retrieved successfully",
        data=CategoryResponse.model_validate(category),
    )


@router.get("/{category_id}/subcategories", response_model=ApiResponse[list[SubCategoryResponse]])
def list_subcategories(category_id: int, db: Session = Depends(get_db)):
    subcategories = category_service.list_subcategories(category_id, db)
    return ApiResponse(
        message="Subcategories retrieved successfully",
        data=[SubCategoryResponse.model_validate(s) for s in subcategories],
    )
