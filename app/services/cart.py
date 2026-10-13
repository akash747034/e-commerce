from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemResponse, CartItemUpdate, CartResponse


def _get_or_create_active_cart(user: User, db: Session) -> Cart:
    """Return the user's active cart, creating one if needed."""
    cart = db.scalars(
        select(Cart)
        .options(selectinload(Cart.items))
        .where(Cart.user_id == user.id, Cart.status == "active")
    ).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
        # Re-load with items relationship
        cart = db.scalars(
            select(Cart)
            .options(selectinload(Cart.items))
            .where(Cart.id == cart.id)
        ).first()
    return cart


def _resolve_unit_price(product: Product, variant: ProductVariant | None) -> Decimal:
    if variant and variant.price is not None:
        return variant.price
    return product.price


def _build_item_response(item: CartItem, db: Session) -> CartItemResponse:
    product = db.get(Product, item.product_id)
    variant = db.get(ProductVariant, item.variant_id) if item.variant_id else None
    unit_price = _resolve_unit_price(product, variant)
    return CartItemResponse(
        id=item.id,
        product_id=item.product_id,
        variant_id=item.variant_id,
        quantity=item.quantity,
        unit_price=unit_price,
        total_price=unit_price * item.quantity,
        product_title=product.title,
        variant_title=variant.title if variant else None,
    )


def _build_cart_response(cart: Cart, db: Session) -> CartResponse:
    items = [_build_item_response(i, db) for i in cart.items]
    subtotal = sum(i.total_price for i in items)
    return CartResponse(
        id=cart.id,
        status=cart.status,
        items=items,
        subtotal=subtotal,
        item_count=sum(i.quantity for i in items),
    )


def get_cart(user: User, db: Session) -> CartResponse:
    cart = _get_or_create_active_cart(user, db)
    return _build_cart_response(cart, db)


def add_item(payload: CartItemAdd, user: User, db: Session) -> CartResponse:
    # Validate product
    product = db.get(Product, payload.product_id)
    if not product or product.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Validate variant if provided
    variant = None
    if payload.variant_id:
        variant = db.get(ProductVariant, payload.variant_id)
        if not variant or variant.product_id != product.id or not variant.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product variant not found")

    # Check stock
    available_stock = variant.quantity if variant else product.quantity
    if available_stock < payload.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {available_stock} item(s) available in stock",
        )

    cart = _get_or_create_active_cart(user, db)

    # Check if item already exists in cart
    existing = db.scalars(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == payload.product_id,
            CartItem.variant_id == payload.variant_id,
        )
    ).first()

    if existing:
        new_qty = existing.quantity + payload.quantity
        if new_qty > available_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add {payload.quantity} more. Only {available_stock - existing.quantity} additional item(s) available.",
            )
        existing.quantity = new_qty
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            quantity=payload.quantity,
        )
        db.add(cart_item)

    db.commit()
    # Reload cart with updated items
    db.refresh(cart)
    cart = db.scalars(
        select(Cart)
        .options(selectinload(Cart.items))
        .where(Cart.id == cart.id)
    ).first()
    return _build_cart_response(cart, db)


def update_item(item_id: int, payload: CartItemUpdate, user: User, db: Session) -> CartResponse:
    cart = _get_or_create_active_cart(user, db)
    item = db.scalars(
        select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    # Stock check
    product = db.get(Product, item.product_id)
    variant = db.get(ProductVariant, item.variant_id) if item.variant_id else None
    available_stock = variant.quantity if variant else product.quantity
    if payload.quantity > available_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {available_stock} item(s) available in stock",
        )

    item.quantity = payload.quantity
    db.commit()
    cart = db.scalars(
        select(Cart).options(selectinload(Cart.items)).where(Cart.id == cart.id)
    ).first()
    return _build_cart_response(cart, db)


def remove_item(item_id: int, user: User, db: Session) -> CartResponse:
    cart = _get_or_create_active_cart(user, db)
    item = db.scalars(
        select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    db.delete(item)
    db.commit()
    cart = db.scalars(
        select(Cart).options(selectinload(Cart.items)).where(Cart.id == cart.id)
    ).first()
    return _build_cart_response(cart, db)


def clear_cart(user: User, db: Session) -> CartResponse:
    cart = _get_or_create_active_cart(user, db)
    for item in cart.items:
        db.delete(item)
    db.commit()
    cart = db.scalars(
        select(Cart).options(selectinload(Cart.items)).where(Cart.id == cart.id)
    ).first()
    return _build_cart_response(cart, db)
