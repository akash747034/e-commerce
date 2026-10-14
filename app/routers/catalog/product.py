from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin_or_seller
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
from app.schemas.review import ReviewResponse
from app.services import product as product_service
from app.services import review as review_service

router = APIRouter(prefix="/products", tags=["Products"])


# ---------------------------------------------------------------------------
# Public Storefront Endpoints
# ---------------------------------------------------------------------------

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
    """Public: Browse active products in the store."""
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


# ---------------------------------------------------------------------------
# Management Endpoints (Admin & Seller Shared)
# ---------------------------------------------------------------------------

@router.get("/manage", response_model=ApiResponse[list[ProductListResponse]])
def list_managed_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_seller),
    category_id: int | None = Query(default=None),
    subcategory_id: int | None = Query(default=None),
    brand_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, max_length=200),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """
    Management: List products for Admin/Seller.
    - Seller: views only their own products.
    - Admin: views all products across all sellers.
    """
    products = product_service.list_products_scoped(
        user=current_user,
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
        message="Managed products retrieved successfully",
        data=[ProductListResponse.model_validate(p) for p in products],
    )


@router.post("", response_model=ApiResponse[ProductDetailResponse], status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_seller),
):
    """
    Management: Create a new product.
    - Automatically attaches seller_id to current_user.id.
    """
    product = product_service.create_product_scoped(payload=payload, user=current_user, db=db)
    return ApiResponse(
        message="Product created successfully",
        data=ProductDetailResponse.model_validate(product),
    )


@router.patch("/{product_id}", response_model=ApiResponse[ProductDetailResponse])
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_seller),
):
    """
    Management: Update product details.
    - Seller: can only edit their own products.
    - Admin: can edit any product.
    """
    product = product_service.update_product_scoped(
        product_id=product_id,
        payload=payload,
        user=current_user,
        db=db,
    )
    return ApiResponse(
        message="Product updated successfully",
        data=ProductDetailResponse.model_validate(product),
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_seller),
):
    """
    Management: Delete product.
    - Seller: can only delete their own products.
    - Admin: can delete any product.
    """
    product_service.delete_product_scoped(product_id=product_id, user=current_user, db=db)


# ---------------------------------------------------------------------------
# Product Images Management Endpoints (Admin & Seller Shared)
# ---------------------------------------------------------------------------

@router.get("/{product_id}/images", response_model=ApiResponse[list[ProductImageResponse]])
def list_product_images(product_id: int, db: Session = Depends(get_db)):
    """List all images for a product."""
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
def add_product_image(
    product_id: int,
    payload: ProductImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_seller),
):
    """
    Add an image to a product.
    - Seller: can only add to their own products.
    - Admin: can add to any product.
    """
    image = product_service.add_product_image(
        product_id=product_id,
        payload=payload,
        user=current_user,
        db=db,
    )
    return ApiResponse(
        message="Product image added successfully",
        data=ProductImageResponse.model_validate(image),
    )


@router.patch("/{product_id}/images/{image_id}", response_model=ApiResponse[ProductImageResponse])
def update_product_image(
    product_id: int,
    image_id: int,
    payload: ProductImageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_seller),
):
    """
    Update product image (e.g., set as primary image, change URL).
    - Seller: can only update their own product's images.
    - Admin: can update any product's images.
    """
    image = product_service.update_product_image(
        product_id=product_id,
        image_id=image_id,
        payload=payload,
        user=current_user,
        db=db,
    )
    return ApiResponse(
        message="Product image updated successfully",
        data=ProductImageResponse.model_validate(image),
    )


@router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_seller),
):
    """
    Delete a product image.
    - Seller: can only delete their own product's images.
    - Admin: can delete any product's images.
    """
    product_service.delete_product_image(
        product_id=product_id,
        image_id=image_id,
        user=current_user,
        db=db,
    )


# ---------------------------------------------------------------------------
# Public Detail Endpoints
# ---------------------------------------------------------------------------

@router.get("/slug/{slug}", response_model=ApiResponse[ProductDetailResponse])
def get_product_by_slug(slug: str, db: Session = Depends(get_db)):
    """Public: View product details by URL slug."""
    product = product_service.get_product_by_slug(slug, db)
    return ApiResponse(
        message="Product retrieved successfully",
        data=ProductDetailResponse.model_validate(product),
    )


@router.get("/{product_id}", response_model=ApiResponse[ProductDetailResponse])
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    """Public: View product details by ID."""
    product = product_service.get_product_by_id(product_id, db)
    return ApiResponse(
        message="Product retrieved successfully",
        data=ProductDetailResponse.model_validate(product),
    )


@router.get("/{product_id}/reviews", response_model=ApiResponse[list[ReviewResponse]])
def list_product_reviews(product_id: int, db: Session = Depends(get_db)):
    """Public: View all reviews for a product."""
    reviews = review_service.list_product_reviews(product_id, db)
    return ApiResponse(
        message="Reviews retrieved successfully",
        data=[ReviewResponse.model_validate(r) for r in reviews],
    )
