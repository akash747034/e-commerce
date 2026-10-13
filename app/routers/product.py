from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import ProductDetailResponse, ProductListResponse
from app.schemas.response import ApiResponse
from app.schemas.review import ReviewResponse
from app.services import product as product_service
from app.services import review as review_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ApiResponse[list[ProductListResponse]])
def list_products(
    db: Session = Depends(get_db),
    category_id: int | None = Query(default=None),
    subcategory_id: int | None = Query(default=None),
    brand_id: int | None = Query(default=None),
    is_featured: bool | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    products = product_service.list_products(
        db,
        category_id=category_id,
        subcategory_id=subcategory_id,
        brand_id=brand_id,
        is_featured=is_featured,
        search=search,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        message="Products retrieved successfully",
        data=[ProductListResponse.model_validate(p) for p in products],
    )


@router.get("/{product_id}", response_model=ApiResponse[ProductDetailResponse])
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    product = product_service.get_product_by_id(product_id, db)
    return ApiResponse(
        message="Product retrieved successfully",
        data=ProductDetailResponse.model_validate(product),
    )


@router.get("/slug/{slug}", response_model=ApiResponse[ProductDetailResponse])
def get_product_by_slug(slug: str, db: Session = Depends(get_db)):
    product = product_service.get_product_by_slug(slug, db)
    return ApiResponse(
        message="Product retrieved successfully",
        data=ProductDetailResponse.model_validate(product),
    )


@router.get("/{product_id}/reviews", response_model=ApiResponse[list[ReviewResponse]])
def list_product_reviews(product_id: int, db: Session = Depends(get_db)):
    reviews = review_service.list_product_reviews(product_id, db)
    return ApiResponse(
        message="Reviews retrieved successfully",
        data=[ReviewResponse.model_validate(r) for r in reviews],
    )
