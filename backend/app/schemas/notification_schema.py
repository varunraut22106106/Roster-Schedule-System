
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import NotificationType


# ---------------- NOTIFICATION ----------------

class NotificationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    message: str
    notification_type: NotificationType


class NotificationResponse(BaseModel):
    notification_id: UUID
    title: str
    message: str
    notification_type: NotificationType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- USER NOTIFICATION ----------------

class UserNotificationCreate(BaseModel):
    notification_id: UUID
    employee_id: UUID


class UserNotificationUpdate(BaseModel):
    is_read: bool


class UserNotificationResponse(BaseModel):
    user_notification_id: UUID
    notification_id: UUID
    employee_id: UUID
    is_read: bool
    read_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
