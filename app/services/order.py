import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.address import Address
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.coupon import Coupon, CouponUsage
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.schemas.order import OrderCreate


def _generate_order_number() -> str:
    return f"ORD-{uuid.uuid4().hex[:10].upper()}"


def _validate_coupon(code: str, user_id: int, subtotal: Decimal, db: Session) -> tuple[Coupon, Decimal]:
    coupon = db.scalars(select(Coupon).where(Coupon.code == code.upper())).first()
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")

    now = datetime.now(timezone.utc)
    if not coupon.is_active or now < coupon.valid_from or now > coupon.valid_to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon is expired or inactive")

    if subtotal < coupon.min_purchase_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum purchase amount is {coupon.min_purchase_amount}",
        )

    if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon usage limit reached")

    # Per-user limit check
    user_usage_count = db.scalar(
        select(func.count(CouponUsage.id)).where(
            CouponUsage.coupon_id == coupon.id,
            CouponUsage.user_id == user_id,
        )
    )
    if user_usage_count >= coupon.per_user_limit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already used this coupon")

    # Calculate discount
    if coupon.discount_type == "percentage":
        discount = (subtotal * coupon.discount_value) / Decimal("100")
        if coupon.max_discount_amount:
            discount = min(discount, coupon.max_discount_amount)
    else:
        discount = min(coupon.discount_value, subtotal)

    return coupon, discount


def place_order(payload: OrderCreate, user: User, db: Session) -> Order:
    # 1. Validate shipping address belongs to user
    shipping_address = db.scalars(
        select(Address).where(Address.id == payload.shipping_address_id, Address.user_id == user.id)
    ).first()
    if not shipping_address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping address not found")

    if payload.billing_address_id:
        billing_address = db.scalars(
            select(Address).where(Address.id == payload.billing_address_id, Address.user_id == user.id)
        ).first()
        if not billing_address:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing address not found")

    # 2. Get active cart with items
    cart = db.scalars(
        select(Cart)
        .options(selectinload(Cart.items))
        .where(Cart.user_id == user.id, Cart.status == "active")
    ).first()

    if not cart or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty")

    # 3. Build order items and calculate subtotal
    order_items = []
    subtotal = Decimal("0")
    product_discount_total = Decimal("0")

    for cart_item in cart.items:
        product = db.get(Product, cart_item.product_id)
        variant = db.get(ProductVariant, cart_item.variant_id) if cart_item.variant_id else None

        if not product or product.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.title if product else cart_item.product_id}' is no longer available",
            )
        available_stock = variant.quantity if variant else product.quantity
        if cart_item.quantity > available_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for '{product.title}'. Only {available_stock} available.",
            )

        # MRP: use compare_at_price as original price if set, otherwise product.price
        if variant:
            # Variants don't have compare_at_price — fall back to product's compare_at_price or price
            mrp = product.compare_at_price if product.compare_at_price else product.price
        else:
            mrp = product.compare_at_price if product.compare_at_price else product.price

        # Selling price: actual price the customer pays
        selling_price = variant.price if variant and variant.price is not None else product.price

        # Per-line product discount
        item_discount = max(mrp - selling_price, Decimal("0")) * cart_item.quantity
        line_total = selling_price * cart_item.quantity

        subtotal += line_total
        product_discount_total += item_discount

        order_items.append(
            OrderItem(
                product_id=product.id,
                variant_id=cart_item.variant_id,
                product_name=product.title,
                variant_name=variant.title if variant else None,
                quantity=cart_item.quantity,
                mrp=mrp,
                selling_price=selling_price,
                item_discount=item_discount,
                line_total=line_total,
            )
        )

    # 4. Apply coupon
    coupon = None
    coupon_discount = Decimal("0")
    if payload.coupon_code:
        coupon, coupon_discount = _validate_coupon(payload.coupon_code, user.id, subtotal, db)

    shipping_amount = Decimal("0")  # Can be made dynamic later
    tax_amount = Decimal("0")       # Can be made dynamic later
    total_amount = subtotal - coupon_discount + shipping_amount + tax_amount

    # 5. Create order
    order = Order(
        order_number=_generate_order_number(),
        user_id=user.id,
        subtotal=subtotal,
        product_discount_total=product_discount_total,
        coupon_discount=coupon_discount,
        shipping_amount=shipping_amount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        payment_method=payload.payment_method,
        shipping_address_id=payload.shipping_address_id,
        billing_address_id=payload.billing_address_id,
        coupon_id=coupon.id if coupon else None,
        notes=payload.notes,
    )
    db.add(order)
    db.flush()  # get order.id without committing yet

    # 6. Attach order items and deduct stock
    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)

        # Deduct stock
        product = db.get(Product, oi.product_id)
        if oi.variant_id:
            variant = db.get(ProductVariant, oi.variant_id)
            variant.quantity -= oi.quantity
        else:
            product.quantity -= oi.quantity

    # 7. Record coupon usage and increment counter
    if coupon:
        coupon.used_count += 1
        usage = CouponUsage(
            coupon_id=coupon.id,
            user_id=user.id,
            order_id=order.id,
            discount_amount=coupon_discount,
        )
        db.add(usage)

    # 8. Mark cart as ordered
    cart.status = "ordered"

    db.commit()
    db.refresh(order)

    # Reload with items
    return db.scalars(
        select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
    ).first()


def list_orders(user: User, db: Session) -> list[Order]:
    return list(
        db.scalars(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user.id)
            .order_by(Order.created_at.desc())
        ).all()
    )


def get_order(order_id: int, user: User, db: Session) -> Order:
    order = db.scalars(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id, Order.user_id == user.id)
    ).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def cancel_order(order_id: int, reason: str, user: User, db: Session) -> Order:
    order = get_order(order_id, user, db)
    cancellable_statuses = {"pending", "confirmed"}
    if order.status not in cancellable_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be cancelled (current status: {order.status})",
        )

    # Restore stock
    for item in order.items:
        product = db.get(Product, item.product_id)
        if item.variant_id:
            variant = db.get(ProductVariant, item.variant_id)
            if variant:
                variant.quantity += item.quantity
        elif product:
            product.quantity += item.quantity
        item.status = "cancelled"

    order.status = "cancelled"
    order.cancellation_reason = reason

    db.commit()
    db.refresh(order)
    return db.scalars(
        select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
    ).first()


# ---------------------------------------------------------------------------
# Admin Order Management Services
# ---------------------------------------------------------------------------

def list_all_orders_admin(
    db: Session,
    status_filter: str | None = None,
    payment_status: str | None = None,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Order]:
    """Admin: view all orders across all customers with filtering."""
    query = select(Order).options(selectinload(Order.items))

    if status_filter:
        query = query.where(Order.status == status_filter)
    if payment_status:
        query = query.where(Order.payment_status == payment_status)
    if user_id:
        query = query.where(Order.user_id == user_id)

    query = query.order_by(Order.id.desc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())


def get_order_by_id_admin(order_id: int, db: Session) -> Order:
    """Admin: get any order by ID."""
    order = db.scalars(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    ).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def update_order_status_admin(
    order_id: int,
    new_status: str,
    new_payment_status: str | None,
    db: Session,
) -> Order:
    """Admin: update order status (e.g. processing, shipped, delivered) and payment status."""
    order = get_order_by_id_admin(order_id, db)

    valid_statuses = {"pending", "confirmed", "processing", "shipped", "delivered", "cancelled"}
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid order status. Allowed: {', '.join(sorted(valid_statuses))}",
        )

    # If cancelling, restore stock
    if new_status == "cancelled" and order.status != "cancelled":
        for item in order.items:
            product = db.get(Product, item.product_id)
            if item.variant_id:
                variant = db.get(ProductVariant, item.variant_id)
                if variant:
                    variant.quantity += item.quantity
            elif product:
                product.quantity += item.quantity
            item.status = "cancelled"

    order.status = new_status
    if new_payment_status:
        order.payment_status = new_payment_status

    db.commit()
    db.refresh(order)
    return order

