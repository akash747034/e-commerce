from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User


def list_notifications(user: User, db: Session, unread_only: bool = False) -> list[Notification]:
    query = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    return list(db.scalars(query.order_by(Notification.created_at.desc())).all())


def mark_as_read(notification_id: int, user: User, db: Session) -> Notification | None:
    notification = db.scalars(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user.id,
        )
    ).first()
    if notification:
        notification.is_read = True
        db.commit()
        db.refresh(notification)
    return notification


def mark_all_as_read(user: User, db: Session) -> int:
    notifications = db.scalars(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.is_read == False,
        )
    ).all()
    count = 0
    for n in notifications:
        n.is_read = True
        count += 1
    db.commit()
    return count
