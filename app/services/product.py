import re
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.sub_category import SubCategory
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", cleaned)


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
    """Public product listing (active products only)."""
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


# ---------------------------------------------------------------------------
# Reusable Scoped Product Operations (Admin & Seller)
# ---------------------------------------------------------------------------

def list_products_scoped(
    user: User,
    db: Session,
    category_id: int | None = None,
    subcategory_id: int | None = None,
    brand_id: int | None = None,
    status_filter: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Product]:
    """
    Returns products scoped to the current user:
    - Seller: only products where seller_id == user.id
    - Admin: all products across all sellers
    """
    query = select(Product)

    if user.user_type == "seller":
        query = query.where(Product.seller_id == user.id)

    if status_filter:
        query = query.where(Product.status == status_filter)
    if category_id is not None:
        query = query.where(Product.category_id == category_id)
    if subcategory_id is not None:
        query = query.where(Product.subcategory_id == subcategory_id)
    if brand_id is not None:
        query = query.where(Product.brand_id == brand_id)
    if search:
        query = query.where(Product.title.ilike(f"%{search}%"))

    query = query.order_by(Product.id.desc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())


def get_product_scoped(product_id: int, user: User, db: Session) -> Product:
    """Fetch a single product ensuring seller ownership (or unrestricted if admin)."""
    product = db.scalars(
        select(Product)
        .options(
            selectinload(Product.product_images),
            selectinload(Product.variants),
        )
        .where(Product.id == product_id)
    ).first()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if user.user_type == "seller" and product.seller_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this product")

    return product


def create_product_scoped(payload: ProductCreate, user: User, db: Session) -> Product:
    """
    Create a product:
    - Automatically attaches seller_id = user.id for sellers
    - Admin can also create products (seller_id can be user.id or None)
    """
    # Validate category & subcategory
    cat = db.get(Category, payload.category_id)
    if not cat or not cat.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category")

    subcat = db.get(SubCategory, payload.subcategory_id)
    if not subcat or not subcat.is_active or subcat.category_id != cat.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subcategory for this category")

    slug = payload.slug or _slugify(payload.title)

    # Check slug uniqueness if provided
    if slug:
        existing = db.scalars(select(Product).where(Product.slug == slug)).first()
        if existing:
            slug = f"{slug}-{user.id}"

    product = Product(
        title=payload.title,
        slug=slug,
        sku=payload.sku,
        description=payload.description,
        price=payload.price,
        compare_at_price=payload.compare_at_price,
        quantity=payload.quantity,
        status=payload.status,
        is_featured=payload.is_featured,
        category_id=payload.category_id,
        subcategory_id=payload.subcategory_id,
        brand_id=payload.brand_id,
        seller_id=user.id,
    )
    db.add(product)
    db.flush()

    for v in payload.variants:
        variant = ProductVariant(
            product_id=product.id,
            sku=v.sku,
            title=v.title,
            price=v.price,
            quantity=v.quantity,
            attributes=v.attributes,
            is_active=v.is_active,
        )
        db.add(variant)

    db.commit()
    db.refresh(product)
    return get_product_scoped(product.id, user, db)


def update_product_scoped(product_id: int, payload: ProductUpdate, user: User, db: Session) -> Product:
    """
    Update a product with ownership validation.
    """
    product = get_product_scoped(product_id, user, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return get_product_scoped(product.id, user, db)


def delete_product_scoped(product_id: int, user: User, db: Session) -> None:
    """
    Delete a product with ownership validation.
    """
    product = get_product_scoped(product_id, user, db)
    db.delete(product)
    db.commit()
