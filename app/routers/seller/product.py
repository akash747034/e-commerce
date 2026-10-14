from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_seller
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductDetailResponse,
    ProductImageCreate,
    ProductImageResponse,
    ProductImageUpdate,
    ProductListResponse,
    ProductUpdate,
)
from app.schemas.response import ApiResponse
from app.services import product as product_service

router = APIRouter(prefix="/products", tags=["Seller Products"])


# ---------------------------------------------------------------------------
# Seller Product Management Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=ApiResponse[list[ProductListResponse]])
def list_seller_products(
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
    category_id: int | None = Query(default=None),
    subcategory_id: int | None = Query(default=None),
    brand_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, max_length=200),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """
    Seller: View all products created by this seller.
    Never exposes other sellers' products.
    """
    products = product_service.list_products_scoped(
        user=seller,
        db=db,
        category_id=category_id,
        subcategory_id=subcategory_id,
        brand_id=brand_id,
        status_filter=status_filter,
        search=search,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        message="Seller products retrieved successfully",
        data=[ProductListResponse.model_validate(p) for p in products],
    )


@router.get("/{product_id}", response_model=ApiResponse[ProductDetailResponse])
def get_seller_product(
    product_id: int,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """Seller: View full details of own product."""
    product = product_service.get_product_scoped(product_id=product_id, user=seller, db=db)
    return ApiResponse(
        message="Seller product retrieved successfully",
        data=ProductDetailResponse.model_validate(product),
    )


@router.post("", response_model=ApiResponse[ProductDetailResponse], status_code=status.HTTP_201_CREATED)
def create_seller_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """
    Seller: Create a new product.
    - Automatically binds seller_id = current logged-in seller.
    - Supports initial images and variants array directly in the payload.
    """
    product = product_service.create_product_scoped(payload=payload, user=seller, db=db)
    return ApiResponse(
        message="Product created successfully",
        data=ProductDetailResponse.model_validate(product),
    )


@router.patch("/{product_id}", response_model=ApiResponse[ProductDetailResponse])
def update_seller_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """
    Seller: Update details of own product.
    (Guards prevent modifying products belonging to other sellers).
    """
    product = product_service.update_product_scoped(
        product_id=product_id,
        payload=payload,
        user=seller,
        db=db,
    )
    return ApiResponse(
        message="Product updated successfully",
        data=ProductDetailResponse.model_validate(product),
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seller_product(
    product_id: int,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """
    Seller: Delete own product.
    """
    product_service.delete_product_scoped(product_id=product_id, user=seller, db=db)


# ---------------------------------------------------------------------------
# Seller Product Images Endpoints
# ---------------------------------------------------------------------------

@router.get("/{product_id}/images", response_model=ApiResponse[list[ProductImageResponse]])
def list_seller_product_images(
    product_id: int,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """Seller: List all images for own product."""
    # Enforces ownership check first
    product_service.get_product_scoped(product_id=product_id, user=seller, db=db)
    images = product_service.list_product_images(product_id=product_id, db=db)
    return ApiResponse(
        message="Product images retrieved successfully",
        data=[ProductImageResponse.model_validate(img) for img in images],
    )


@router.post(
    "/{product_id}/images",
    response_model=ApiResponse[ProductImageResponse],
    status_code=status.HTTP_201_CREATED,
)
def add_seller_product_image(
    product_id: int,
    payload: ProductImageCreate,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """
    Seller: Add a new image to own product.
    """
    image = product_service.add_product_image(
        product_id=product_id,
        payload=payload,
        user=seller,
        db=db,
    )
    return ApiResponse(
        message="Product image added successfully",
        data=ProductImageResponse.model_validate(image),
    )


@router.patch("/{product_id}/images/{image_id}", response_model=ApiResponse[ProductImageResponse])
def update_seller_product_image(
    product_id: int,
    image_id: int,
    payload: ProductImageUpdate,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """
    Seller: Update image (e.g. set as primary thumbnail or change URL).
    """
    image = product_service.update_product_image(
        product_id=product_id,
        image_id=image_id,
        payload=payload,
        user=seller,
        db=db,
    )
    return ApiResponse(
        message="Product image updated successfully",
        data=ProductImageResponse.model_validate(image),
    )


@router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seller_product_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    """
    Seller: Delete image from own product.
    """
    product_service.delete_product_image(
        product_id=product_id,
        image_id=image_id,
        user=seller,
        db=db,
    )
