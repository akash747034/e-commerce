from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.sub_category import SubCategory


def list_categories(db: Session) -> list[Category]:
    return list(
        db.scalars(
            select(Category).where(Category.is_active == True)
        ).all()
    )


def get_category(slug: str, db: Session) -> Category:
    category = db.scalars(
        select(Category).where(Category.slug == slug, Category.is_active == True)
    ).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


def list_subcategories(category_id: int, db: Session) -> list[SubCategory]:
    # Verify the parent category exists
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return list(
        db.scalars(
            select(SubCategory).where(
                SubCategory.category_id == category_id,
                SubCategory.is_active == True,
            )
        ).all()
    )
