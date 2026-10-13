from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product


def list_products(
    db: Session,
    category_id: int | None = None,
    subcategory_id: int | None = None,
    brand_id: int | None = None,
    is_featured: bool | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Product]:
    query = select(Product).where(Product.status == "active")

    if category_id is not None:
        query = query.where(Product.category_id == category_id)
    if subcategory_id is not None:
        query = query.where(Product.subcategory_id == subcategory_id)
    if brand_id is not None:
        query = query.where(Product.brand_id == brand_id)
    if is_featured is not None:
        query = query.where(Product.is_featured == is_featured)
    if search:
        query = query.where(Product.title.ilike(f"%{search}%"))

    query = query.offset(skip).limit(limit)
    return list(db.scalars(query).all())


def get_product_by_id(product_id: int, db: Session) -> Product:
    product = db.scalars(
        select(Product)
        .options(
            selectinload(Product.product_images),
            selectinload(Product.variants),
        )
        .where(Product.id == product_id, Product.status == "active")
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def get_product_by_slug(slug: str, db: Session) -> Product:
    product = db.scalars(
        select(Product)
        .options(
            selectinload(Product.product_images),
            selectinload(Product.variants),
        )
        .where(Product.slug == slug, Product.status == "active")
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product
