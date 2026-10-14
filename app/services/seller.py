from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.seller import SellerDashboardStatsResponse, SellerOrderItemResponse


def get_seller_dashboard_stats(seller: User, db: Session) -> SellerDashboardStatsResponse:
    """Fetch analytics, product counts, and order statistics scoped to this seller."""
    total_products = db.scalar(
        select(func.count(Product.id)).where(Product.seller_id == seller.id)
    ) or 0

    active_products = db.scalar(
        select(func.count(Product.id)).where(Product.seller_id == seller.id, Product.status == "active")
    ) or 0

    out_of_stock = db.scalar(
        select(func.count(Product.id)).where(Product.seller_id == seller.id, Product.quantity <= 0)
    ) or 0

    # Query all order items that belong to products created by this seller
    items_query = (
        select(OrderItem)
        .join(Product, OrderItem.product_id == Product.id)
        .where(Product.seller_id == seller.id)
    )
    all_seller_items = list(db.scalars(items_query).all())

    total_orders_received = len(all_seller_items)
    pending_fulfillment = len([i for i in all_seller_items if i.status in ("pending", "confirmed", "processing")])
    completed = len([i for i in all_seller_items if i.status == "delivered"])
    total_sales = sum(
        (i.line_total for i in all_seller_items if i.status != "cancelled"),
        Decimal("0"),
    )

    return SellerDashboardStatsResponse(
        total_products=total_products,
        active_products=active_products,
        out_of_stock_products=out_of_stock,
        total_orders_received=total_orders_received,
        pending_fulfillment_orders=pending_fulfillment,
        completed_orders=completed,
        total_sales_volume=total_sales,
    )


def list_seller_order_items(
    seller: User,
    db: Session,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[SellerOrderItemResponse]:
    """List customer order items for products owned by this seller."""
    query = (
        select(OrderItem, Order)
        .join(Product, OrderItem.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(Product.seller_id == seller.id)
    )

    if status_filter:
        query = query.where(OrderItem.status == status_filter)

    query = query.order_by(OrderItem.id.desc()).offset(skip).limit(limit)
    rows = db.execute(query).all()

    result = []
    for item, order in rows:
        result.append(
            SellerOrderItemResponse(
                order_item_id=item.id,
                order_id=order.id,
                order_number=order.order_number,
                product_id=item.product_id,
                product_name=item.product_name,
                variant_name=item.variant_name,
                quantity=item.quantity,
                mrp=item.mrp,
                selling_price=item.selling_price,
                item_discount=item.item_discount,
                line_total=item.line_total,
                status=item.status,
                created_at=item.created_at,
                shipping_address_id=order.shipping_address_id,
            )
        )
    return result


def get_seller_order_item(order_item_id: int, seller: User, db: Session) -> SellerOrderItemResponse:
    """Get single order item details verifying seller ownership."""
    query = (
        select(OrderItem, Order)
        .join(Product, OrderItem.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(OrderItem.id == order_item_id, Product.seller_id == seller.id)
    )
    row = db.execute(query).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found for this seller")

    item, order = row
    return SellerOrderItemResponse(
        order_item_id=item.id,
        order_id=order.id,
        order_number=order.order_number,
        product_id=item.product_id,
        product_name=item.product_name,
        variant_name=item.variant_name,
        quantity=item.quantity,
        mrp=item.mrp,
        selling_price=item.selling_price,
        item_discount=item.item_discount,
        line_total=item.line_total,
        status=item.status,
        created_at=item.created_at,
        shipping_address_id=order.shipping_address_id,
    )


def update_seller_order_item_status(
    order_item_id: int,
    new_status: str,
    seller: User,
    db: Session,
) -> SellerOrderItemResponse:
    """Update order item fulfillment status (e.g., 'processing', 'shipped', 'delivered')."""
    valid_statuses = {"confirmed", "processing", "shipped", "delivered", "cancelled"}
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Allowed statuses: {', '.join(sorted(valid_statuses))}",
        )

    # Verify ownership
    item = db.scalars(
        select(OrderItem)
        .join(Product, OrderItem.product_id == Product.id)
        .where(OrderItem.id == order_item_id, Product.seller_id == seller.id)
    ).first()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found for this seller")

    item.status = new_status
    db.commit()
    db.refresh(item)

    return get_seller_order_item(item.id, seller, db)
