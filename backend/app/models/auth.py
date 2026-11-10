import uuid
from datetime import datetime

from sqlalchemy import (
    Uuid, String, Boolean, DateTime, ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import UserRole


class UserAccount(Base):
    __tablename__ = "user_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    employee = relationship("Employee")