from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    title: str
    price: Decimal | None
    quantity: int
    attributes: str | None
    is_active: bool


class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image: str
    is_primary: bool


class ProductListResponse(BaseModel):
    """Lightweight product schema for list views."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str | None
    sku: str | None
    price: Decimal
    compare_at_price: Decimal | None
    quantity: int
    status: str
    is_featured: bool
    category_id: int
    subcategory_id: int
    brand_id: int | None


class ProductDetailResponse(ProductListResponse):
    """Full product schema with nested relations."""
    description: str | None
    product_images: list[ProductImageResponse] = []
    variants: list[ProductVariantResponse] = []
