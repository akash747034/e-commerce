import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.return_request import ReturnRequest
from app.models.user import User
from app.schemas.return_refund import (
    RefundCreate,
    ReturnRequestCreate,
    ReturnRequestStatusUpdate,
)


def create_return_request(payload: ReturnRequestCreate, user: User, db: Session) -> ReturnRequest:
    order = db.scalars(
        select(Order).where(Order.id == payload.order_id, Order.user_id == user.id)
    ).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.status not in ("delivered", "shipped", "confirmed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot request return for order in '{order.status}' status",
        )

    if payload.order_item_id:
        item = db.scalars(
            select(OrderItem).where(
                OrderItem.id == payload.order_item_id, OrderItem.order_id == order.id
            )
        ).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found")

    return_req = ReturnRequest(
        order_id=order.id,
        order_item_id=payload.order_item_id,
        user_id=user.id,
        reason=payload.reason,
        comment=payload.comment,
        status="pending",
    )
    db.add(return_req)

    # Customer notification
    db.add(
        Notification(
            user_id=user.id,
            title="Return Request Submitted",
            message=f"Your return request for order {order.order_number} has been received and is under review.",
            notification_type="order",
            action_url=f"/orders/{order.id}",
        )
    )

    db.commit()
    db.refresh(return_req)
    return return_req


def list_user_returns(user: User, db: Session) -> list[ReturnRequest]:
    return list(
        db.scalars(
            select(ReturnRequest)
            .where(ReturnRequest.user_id == user.id)
            .order_by(ReturnRequest.created_at.desc())
        ).all()
    )


def get_return_request(return_id: int, user: User, db: Session) -> ReturnRequest:
    return_req = db.get(ReturnRequest, return_id)
    if not return_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return request not found")

    if user.user_type != "admin" and return_req.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return return_req


def admin_list_returns(
    db: Session,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[ReturnRequest]:
    query = select(ReturnRequest)
    if status_filter:
        query = query.where(ReturnRequest.status == status_filter.lower())
    query = query.order_by(ReturnRequest.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())


def admin_update_return_status(
    return_id: int,
    payload: ReturnRequestStatusUpdate,
    db: Session,
) -> ReturnRequest:
    return_req = db.get(ReturnRequest, return_id)
    if not return_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return request not found")

    new_status = payload.status.lower().strip()
    return_req.status = new_status
    if payload.admin_notes:
        return_req.admin_notes = payload.admin_notes

    order = db.get(Order, return_req.order_id)
    order_num = order.order_number if order else "your order"

    # Notify customer of decision
    db.add(
        Notification(
            user_id=return_req.user_id,
            title=f"Return Request {new_status.title()}",
            message=f"Your return request for {order_num} was marked as {new_status}.",
            notification_type="order",
            action_url=f"/orders/{return_req.order_id}",
        )
    )

    db.commit()
    db.refresh(return_req)
    return return_req


def process_refund(payload: RefundCreate, db: Session) -> Refund:
    order = db.get(Order, payload.order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if payload.amount > order.total_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund amount ₹{payload.amount} cannot exceed order total ₹{order.total_amount}",
        )

    gateway_refund_id = f"rf_{uuid.uuid4().hex[:16]}"
    refund = Refund(
        order_id=order.id,
        payment_id=payload.payment_id,
        return_request_id=payload.return_request_id,
        amount=payload.amount,
        refund_method=payload.refund_method,
        gateway_refund_id=gateway_refund_id,
        status="processed",
        reason=payload.reason,
        notes=payload.notes,
    )
    db.add(refund)

    # Update order payment_status
    order.payment_status = "refunded"

    # Customer alert
    db.add(
        Notification(
            user_id=order.user_id,
            title="Refund Processed",
            message=f"A refund of ₹{payload.amount} has been processed for order {order.order_number}.",
            notification_type="payment",
            action_url=f"/orders/{order.id}",
        )
    )

    db.commit()
    db.refresh(refund)
    return refund


def admin_list_refunds(
    db: Session,
    order_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Refund]:
    query = select(Refund)
    if order_id:
        query = query.where(Refund.order_id == order_id)
    query = query.order_by(Refund.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())
