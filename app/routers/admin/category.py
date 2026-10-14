from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    SubCategoryCreate,
    SubCategoryResponse,
    SubCategoryUpdate,
)
from app.schemas.response import ApiResponse
from app.services import category as category_service

router = APIRouter(tags=["Admin Categories"])


# ---------------------------------------------------------------------------
# Category Management
# ---------------------------------------------------------------------------

@router.get("/categories", response_model=ApiResponse[list[CategoryResponse]])
def admin_list_categories(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    include_inactive: bool = Query(default=True),
):
    """Admin: view all categories (including inactive/drafts)."""
    categories = category_service.list_all_categories_admin(db, include_inactive=include_inactive)
    return ApiResponse(
        message="Categories retrieved successfully",
        data=[CategoryResponse.model_validate(c) for c in categories],
    )


@router.get("/categories/{category_id}", response_model=ApiResponse[CategoryResponse])
def admin_get_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: get category by ID."""
    category = category_service.get_category_by_id_admin(category_id, db)
    return ApiResponse(
        message="Category retrieved successfully",
        data=CategoryResponse.model_validate(category),
    )


@router.post("/categories", response_model=ApiResponse[CategoryResponse], status_code=status.HTTP_201_CREATED)
def admin_create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: create a new category."""
    category = category_service.create_category(payload, db)
    return ApiResponse(
        message="Category created successfully",
        data=CategoryResponse.model_validate(category),
    )


@router.patch("/categories/{category_id}", response_model=ApiResponse[CategoryResponse])
def admin_update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: update category title, slug, image, or active status."""
    category = category_service.update_category(category_id, payload, db)
    return ApiResponse(
        message="Category updated successfully",
        data=CategoryResponse.model_validate(category),
    )


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: delete category (only if no products are assigned)."""
    category_service.delete_category(category_id, db)


# ---------------------------------------------------------------------------
# SubCategory Management
# ---------------------------------------------------------------------------

@router.post(
    "/categories/{category_id}/subcategories",
    response_model=ApiResponse[SubCategoryResponse],
    status_code=status.HTTP_201_CREATED,
)
def admin_create_subcategory(
    category_id: int,
    payload: SubCategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: create a new subcategory under a category."""
    subcategory = category_service.create_subcategory(category_id, payload, db)
    return ApiResponse(
        message="Subcategory created successfully",
        data=SubCategoryResponse.model_validate(subcategory),
    )


@router.patch("/subcategories/{subcategory_id}", response_model=ApiResponse[SubCategoryResponse])
def admin_update_subcategory(
    subcategory_id: int,
    payload: SubCategoryUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: update subcategory title, slug, image, or active status."""
    subcategory = category_service.update_subcategory(subcategory_id, payload, db)
    return ApiResponse(
        message="Subcategory updated successfully",
        data=SubCategoryResponse.model_validate(subcategory),
    )


@router.delete("/subcategories/{subcategory_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_subcategory(
    subcategory_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: delete subcategory (only if no products are assigned)."""
    category_service.delete_subcategory(subcategory_id, db)
