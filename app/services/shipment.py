from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.shipment import Shipment
from app.models.user import User
from app.schemas.shipment import ShipmentCreate, ShipmentStatusUpdate


def _can_manage_order_shipment(order: Order, user: User, db: Session) -> bool:
    """Admins can manage any shipment; sellers can manage if order has their products."""
    if user.user_type == "admin":
        return True
    if user.user_type == "seller":
        has_seller_item = db.scalars(
            select(OrderItem)
            .join(Product, OrderItem.product_id == Product.id)
            .where(OrderItem.order_id == order.id, Product.seller_id == user.id)
        ).first()
        return bool(has_seller_item)
    return False


def create_shipment(payload: ShipmentCreate, current_user: User, db: Session) -> Shipment:
    order = db.get(Order, payload.order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if not _can_manage_order_shipment(order, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if order.status == "cancelled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot ship a cancelled order")

    # Check tracking number unique
    existing = db.scalars(
        select(Shipment).where(Shipment.tracking_number == payload.tracking_number)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tracking number '{payload.tracking_number}' is already registered",
        )

    now = datetime.now(timezone.utc)
    shipment = Shipment(
        order_id=order.id,
        carrier=payload.carrier,
        tracking_number=payload.tracking_number,
        tracking_url=payload.tracking_url,
        status="in_transit",
        shipped_at=now,
        estimated_delivery=payload.estimated_delivery,
        notes=payload.notes,
    )
    db.add(shipment)

    # Transition order status to shipped
    if order.status in ("pending", "confirmed", "processing"):
        order.status = "shipped"

    # Send shipping notification to customer
    db.add(
        Notification(
            user_id=order.user_id,
            title="Order Shipped",
            message=f"Order {order.order_number} has been shipped via {payload.carrier}. Tracking: {payload.tracking_number}",
            notification_type="shipment",
            action_url=f"/orders/{order.id}",
        )
    )

    db.commit()
    db.refresh(shipment)
    return shipment


def update_shipment_status(
    shipment_id: int,
    payload: ShipmentStatusUpdate,
    current_user: User,
    db: Session,
) -> Shipment:
    shipment = db.get(Shipment, shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")

    order = db.get(Order, shipment.order_id)
    if not order or not _can_manage_order_shipment(order, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    new_status = payload.status.lower().strip()
    shipment.status = new_status
    if payload.notes:
        shipment.notes = payload.notes

    now = datetime.now(timezone.utc)
    if new_status == "delivered":
        shipment.delivered_at = payload.delivered_at or now
        order.status = "delivered"

        # Customer alert
        db.add(
            Notification(
                user_id=order.user_id,
                title="Order Delivered",
                message=f"Order {order.order_number} was successfully delivered by {shipment.carrier}.",
                notification_type="shipment",
                action_url=f"/orders/{order.id}",
            )
        )

    db.commit()
    db.refresh(shipment)
    return shipment


def get_shipment(shipment_id: int, current_user: User, db: Session) -> Shipment:
    shipment = db.get(Shipment, shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")

    order = db.get(Order, shipment.order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.user_type == "customer" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if current_user.user_type == "seller" and not _can_manage_order_shipment(order, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return shipment


def list_order_shipments(order_id: int, current_user: User, db: Session) -> list[Shipment]:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.user_type == "customer" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if current_user.user_type == "seller" and not _can_manage_order_shipment(order, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return list(
        db.scalars(
            select(Shipment)
            .where(Shipment.order_id == order_id)
            .order_by(Shipment.created_at.desc())
        ).all()
    )


def list_all_shipments_admin(
    db: Session,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Shipment]:
    query = select(Shipment)
    if status_filter:
        query = query.where(Shipment.status == status_filter.lower())
    query = query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())
