import re
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.product import Product
from app.schemas.brand import BrandCreate, BrandUpdate


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", cleaned)


# ---------------------------------------------------------------------------
# Public Storefront Services
# ---------------------------------------------------------------------------

def list_brands(db: Session) -> list[Brand]:
    """Public: list all active brands."""
    return list(
        db.scalars(select(Brand).where(Brand.is_active == True).order_by(Brand.name.asc())).all()
    )


def get_brand(slug: str, db: Session) -> Brand:
    """Public: get brand by slug."""
    brand = db.scalars(
        select(Brand).where(Brand.slug == slug, Brand.is_active == True)
    ).first()
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return brand


# ---------------------------------------------------------------------------
# Admin Brand Management Services
# ---------------------------------------------------------------------------

def list_all_brands_admin(db: Session, include_inactive: bool = True) -> list[Brand]:
    """Admin: list all brands including inactive ones."""
    query = select(Brand)
    if not include_inactive:
        query = query.where(Brand.is_active == True)
    return list(db.scalars(query.order_by(Brand.id.desc())).all())


def get_brand_by_id_admin(brand_id: int, db: Session) -> Brand:
    """Admin: get brand by ID."""
    brand = db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return brand


def create_brand(payload: BrandCreate, db: Session) -> Brand:
    """Admin: create brand."""
    slug = payload.slug or _slugify(payload.name)

    existing = db.scalars(select(Brand).where((Brand.slug == slug) | (Brand.name == payload.name))).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Brand with name '{payload.name}' or slug '{slug}' already exists",
        )

    brand = Brand(
        name=payload.name,
        slug=slug,
        description=payload.description,
        logo_url=payload.logo_url,
        website=payload.website,
        is_active=payload.is_active,
    )
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


def update_brand(brand_id: int, payload: BrandUpdate, db: Session) -> Brand:
    """Admin: update brand."""
    brand = get_brand_by_id_admin(brand_id, db)
    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"]:
        existing = db.scalars(
            select(Brand).where(Brand.name == update_data["name"], Brand.id != brand_id)
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Brand name already in use")

    if "slug" in update_data and update_data["slug"]:
        existing = db.scalars(
            select(Brand).where(Brand.slug == update_data["slug"], Brand.id != brand_id)
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Brand slug already in use")

    for field, value in update_data.items():
        setattr(brand, field, value)

    db.commit()
    db.refresh(brand)
    return brand


def delete_brand(brand_id: int, db: Session) -> None:
    """Admin: delete brand safely if no products are currently linked."""
    brand = get_brand_by_id_admin(brand_id, db)

    product_count = db.scalars(select(Product.id).where(Product.brand_id == brand_id)).first()
    if product_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete brand: products are currently assigned to it. Reassign or delete products first.",
        )

    db.delete(brand)
    db.commit()
