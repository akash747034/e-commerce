from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Product Image Schemas
# ---------------------------------------------------------------------------

class ProductImageCreate(BaseModel):
    image: Annotated[str, Field(min_length=1, max_length=500)]
    is_primary: bool = False


class ProductImageUpdate(BaseModel):
    image: Annotated[str | None, Field(max_length=500)] = None
    is_primary: bool | None = None


class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    image: str
    is_primary: bool


# ---------------------------------------------------------------------------
# Product Variant Schemas
# ---------------------------------------------------------------------------

class ProductVariantCreate(BaseModel):
    sku: Annotated[str, Field(min_length=1, max_length=100)]
    title: Annotated[str, Field(min_length=1, max_length=100)]
    price: Decimal | None = None
    quantity: int = 0
    attributes: str | None = None
    is_active: bool = True


class ProductVariantUpdate(BaseModel):
    sku: Annotated[str | None, Field(max_length=100)] = None
    title: Annotated[str | None, Field(max_length=100)] = None
    price: Decimal | None = None
    quantity: int | None = None
    attributes: str | None = None
    is_active: bool | None = None


class ProductVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    title: str
    price: Decimal | None
    quantity: int
    attributes: str | None
    is_active: bool


# ---------------------------------------------------------------------------
# Product Create / Update / Response Schemas
# ---------------------------------------------------------------------------

class ProductCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=255)]
    slug: Annotated[str | None, Field(max_length=255)] = None
    sku: Annotated[str | None, Field(max_length=100)] = None
    description: str | None = None
    price: Annotated[Decimal, Field(gt=0)]
    compare_at_price: Decimal | None = None
    quantity: int = 0
    status: str = "active"
    is_featured: bool = False
    category_id: int
    subcategory_id: int
    brand_id: int | None = None
    images: list[ProductImageCreate] = []       # <-- Support adding images during product creation!
    variants: list[ProductVariantCreate] = []


class ProductUpdate(BaseModel):
    title: Annotated[str | None, Field(max_length=255)] = None
    slug: Annotated[str | None, Field(max_length=255)] = None
    sku: Annotated[str | None, Field(max_length=100)] = None
    description: str | None = None
    price: Decimal | None = None
    compare_at_price: Decimal | None = None
    quantity: int | None = None
    status: str | None = None
    is_featured: bool | None = None
    category_id: int | None = None
    subcategory_id: int | None = None
    brand_id: int | None = None


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
    seller_id: int | None


class ProductDetailResponse(ProductListResponse):
    """Full product schema with nested relations."""
    description: str | None
    product_images: list[ProductImageResponse] = []
    variants: list[ProductVariantResponse] = []
