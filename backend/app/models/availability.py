
import uuid

from sqlalchemy import (
    String, Boolean, Integer, Date, Time, ForeignKey,
    DateTime, Text, CheckConstraint, func, Uuid
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import (
    LeaveStatus, AvailabilityType, HolidayScope,
    CompOffStatus, CompOffAction
)


class PublicHoliday(Base):
    __tablename__ = "public_holidays"

    holiday_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    holiday_name: Mapped[str] = mapped_column(String(150), nullable=False)
    holiday_date: Mapped[Date] = mapped_column(Date, nullable=False)

    scope: Mapped[HolidayScope] = mapped_column(nullable=False)

    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("brands.brand_id", ondelete="CASCADE"),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    brand = relationship("Brand")


class Leave(Base):
    __tablename__ = "leaves"

    leave_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False
    )

    requested_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.employee_id"), nullable=False
    )

    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[LeaveStatus] = mapped_column(
        default=LeaveStatus.PENDING, nullable=False
    )

    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("employees.employee_id"), nullable=True
    )

    reviewed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    employee = relationship("Employee", foreign_keys=[employee_id])
    requester = relationship("Employee", foreign_keys=[requested_by])
    reviewer = relationship("Employee", foreign_keys=[reviewed_by])


class CompOffTransaction(Base):
    __tablename__ = "comp_off_transactions"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False
    )

    action: Mapped[CompOffAction] = mapped_column(nullable=False)

    status: Mapped[CompOffStatus] = mapped_column(
        default=CompOffStatus.PENDING, nullable=False
    )

    # Positive = credit, negative = approved usage
    balance_change: Mapped[int] = mapped_column(Integer, nullable=False)

    requested_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.employee_id"), nullable=False
    )

    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("employees.employee_id"), nullable=True
    )

    reviewed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    employee = relationship("Employee", foreign_keys=[employee_id])
    creator = relationship("Employee", foreign_keys=[created_by])
    reviewer = relationship("Employee", foreign_keys=[reviewed_by])

    __table_args__ = (
        CheckConstraint("balance_change != 0"),
    )


class AvailabilityRestriction(Base):
    __tablename__ = "availability_restrictions"

    restriction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False
    )

    restriction_type: Mapped[AvailabilityType] = mapped_column(nullable=False)

    restriction_date: Mapped[Date] = mapped_column(Date, nullable=False)

    start_time: Mapped[Time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[Time | None] = mapped_column(Time, nullable=True)

    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    employee = relationship("Employee")
