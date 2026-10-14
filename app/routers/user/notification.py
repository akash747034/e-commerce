from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.schemas.response import ApiResponse
from app.services import notification as notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=ApiResponse[list[NotificationResponse]])
def list_notifications(
    unread_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notifications = notification_service.list_notifications(current_user, db, unread_only=unread_only)
    return ApiResponse(
        message="Notifications retrieved successfully",
        data=[NotificationResponse.model_validate(n) for n in notifications],
    )


@router.post("/{notification_id}/read", response_model=ApiResponse[NotificationResponse])
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = notification_service.mark_as_read(notification_id, current_user, db)
    return ApiResponse(
        message="Notification marked as read",
        data=NotificationResponse.model_validate(notification) if notification else None,
    )


@router.post("/read-all", response_model=ApiResponse[dict])
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = notification_service.mark_all_as_read(current_user, db)
    return ApiResponse(
        message=f"{count} notification(s) marked as read",
        data={"marked_read": count},
    )
