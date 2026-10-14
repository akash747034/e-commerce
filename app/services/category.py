import re
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.models.product import Product
from app.models.sub_category import SubCategory
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    SubCategoryCreate,
    SubCategoryUpdate,
)


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", cleaned)


# ---------------------------------------------------------------------------
# Public Storefront Services
# ---------------------------------------------------------------------------

def list_categories(db: Session) -> list[Category]:
    """Public: list all active categories with their active subcategories."""
    return list(
        db.scalars(
            select(Category)
            .options(selectinload(Category.subcategories))
            .where(Category.is_active == True)
        ).all()
    )


def get_category(slug: str, db: Session) -> Category:
    """Public: get an active category by its slug."""
    category = db.scalars(
        select(Category)
        .options(selectinload(Category.subcategories))
        .where(Category.slug == slug, Category.is_active == True)
    ).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


def list_subcategories(category_id: int, db: Session) -> list[SubCategory]:
    """Public: list active subcategories of a category."""
    category = db.get(Category, category_id)
    if not category or not category.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return list(
        db.scalars(
            select(SubCategory).where(
                SubCategory.category_id == category_id,
                SubCategory.is_active == True,
            )
        ).all()
    )


# ---------------------------------------------------------------------------
# Admin Category Management Services
# ---------------------------------------------------------------------------

def list_all_categories_admin(db: Session, include_inactive: bool = True) -> list[Category]:
    """Admin: list all categories (including inactive/draft if requested)."""
    query = select(Category).options(selectinload(Category.subcategories))
    if not include_inactive:
        query = query.where(Category.is_active == True)
    return list(db.scalars(query.order_by(Category.id.desc())).all())


def get_category_by_id_admin(category_id: int, db: Session) -> Category:
    """Admin: get a category by ID."""
    category = db.scalars(
        select(Category)
        .options(selectinload(Category.subcategories))
        .where(Category.id == category_id)
    ).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


def create_category(payload: CategoryCreate, db: Session) -> Category:
    """Admin: create a new category."""
    slug = payload.slug or _slugify(payload.title)

    # Ensure unique slug
    existing = db.scalars(select(Category).where(Category.slug == slug)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with slug '{slug}' already exists",
        )

    category = Category(
        title=payload.title,
        slug=slug,
        description=payload.description,
        image_url=payload.image_url,
        is_active=payload.is_active,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return get_category_by_id_admin(category.id, db)


def update_category(category_id: int, payload: CategoryUpdate, db: Session) -> Category:
    """Admin: update an existing category."""
    category = get_category_by_id_admin(category_id, db)

    update_data = payload.model_dump(exclude_unset=True)

    # If updating slug, ensure uniqueness
    if "slug" in update_data and update_data["slug"]:
        slug = update_data["slug"]
        existing = db.scalars(
            select(Category).where(Category.slug == slug, Category.id != category_id)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with slug '{slug}' already exists",
            )

    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return get_category_by_id_admin(category.id, db)


def delete_category(category_id: int, db: Session) -> None:
    """
    Admin: delete a category.
    Fails safely if products are currently linked to this category OR any of its subcategories.
    """
    category = get_category_by_id_admin(category_id, db)

    # 1. Check if products exist directly in this category
    product_in_cat = db.scalars(
        select(Product.id).where(Product.category_id == category_id)
    ).first()
    if product_in_cat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category: products are directly assigned to it. Reassign or delete products first.",
        )

    # 2. Check if products exist in any of this category's subcategories
    subcategory_ids = [sub.id for sub in category.subcategories]
    if subcategory_ids:
        product_in_subcat = db.scalars(
            select(Product.id).where(Product.subcategory_id.in_(subcategory_ids))
        ).first()
        if product_in_subcat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category: products are assigned to one or more of its subcategories. Reassign or delete those products first.",
            )

    db.delete(category)
    db.commit()


# ---------------------------------------------------------------------------
# Admin SubCategory Management Services
# ---------------------------------------------------------------------------

def create_subcategory(category_id: int, payload: SubCategoryCreate, db: Session) -> SubCategory:
    """Admin: create a subcategory under a parent category."""
    category = get_category_by_id_admin(category_id, db)

    slug = payload.slug or _slugify(payload.title)

    existing = db.scalars(select(SubCategory).where(SubCategory.slug == slug)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subcategory with slug '{slug}' already exists",
        )

    subcategory = SubCategory(
        title=payload.title,
        slug=slug,
        description=payload.description,
        image_url=payload.image_url,
        is_active=payload.is_active,
        category_id=category.id,
    )
    db.add(subcategory)
    db.commit()
    db.refresh(subcategory)
    return subcategory


def update_subcategory(subcategory_id: int, payload: SubCategoryUpdate, db: Session) -> SubCategory:
    """Admin: update a subcategory."""
    subcategory = db.get(SubCategory, subcategory_id)
    if not subcategory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcategory not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "slug" in update_data and update_data["slug"]:
        slug = update_data["slug"]
        existing = db.scalars(
            select(SubCategory).where(SubCategory.slug == slug, SubCategory.id != subcategory_id)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subcategory with slug '{slug}' already exists",
            )

    for field, value in update_data.items():
        setattr(subcategory, field, value)

    db.commit()
    db.refresh(subcategory)
    return subcategory


def delete_subcategory(subcategory_id: int, db: Session) -> None:
    """
    Admin: delete a subcategory.
    Fails safely if products are currently linked to this subcategory.
    """
    subcategory = db.get(SubCategory, subcategory_id)
    if not subcategory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcategory not found")

    product_count = db.scalars(
        select(Product).where(Product.subcategory_id == subcategory_id)
    ).first()
    if product_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete subcategory: existing products are assigned to it. Reassign or delete products first.",
        )

    db.delete(subcategory)
    db.commit()
