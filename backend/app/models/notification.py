
import uuid

from datetime import datetime

from sqlalchemy import (
    String, Boolean, DateTime, ForeignKey, Text,
    func, Uuid, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import NotificationType


class Notification(Base):
    __tablename__ = "notifications"

    notification_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    notification_type: Mapped[NotificationType] = mapped_column(
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user_notifications = relationship(
        "UserNotification",
        back_populates="notification",
        cascade="all, delete-orphan"
    )


class UserNotification(Base):
    __tablename__ = "user_notifications"

    user_notification_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    notification_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("notifications.notification_id", ondelete="CASCADE"),
        nullable=False
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    notification = relationship(
        "Notification", back_populates="user_notifications"
    )

    employee = relationship("Employee")

    __table_args__ = (
        Index("ix_user_notification_employee_read", "employee_id", "is_read"),
    )
