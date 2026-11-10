
import uuid

from sqlalchemy import (
    String, Boolean, Integer, Float, Date, Time, ForeignKey,
    DateTime, UniqueConstraint, CheckConstraint, func, Uuid
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import ShiftType, StaffingRuleScope


class Shift(Base):
    __tablename__ = "shifts"

    shift_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    shift_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    shift_type: Mapped[ShiftType] = mapped_column(nullable=False)

    start_time: Mapped[Time] = mapped_column(Time, nullable=False)
    end_time: Mapped[Time] = mapped_column(Time, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProcessOperatingDay(Base):
    __tablename__ = "process_operating_days"

    operating_day_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    process_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("processes.process_id", ondelete="CASCADE"),
        nullable=False
    )

    # Monday = 0, Sunday = 6
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    is_operating: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "process_id", "weekday",
            name="uq_process_operating_weekday"
        ),
        CheckConstraint("weekday BETWEEN 0 AND 6"),
    )

    process = relationship("Process")


class StaffingRequirement(Base):
    __tablename__ = "staffing_requirements"

    requirement_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    process_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("processes.process_id", ondelete="CASCADE"),
        nullable=False
    )

    # Optional shift: NULL means daily coverage requirement
    shift_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("shifts.shift_id"), nullable=True
    )

    scope: Mapped[StaffingRuleScope] = mapped_column(nullable=False)

    # Used when scope = WEEKDAY; Monday = 0, Sunday = 6
    weekday: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Used when scope = DATE
    effective_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    minimum_employees: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("minimum_employees >= 0"),
        CheckConstraint("weekday IS NULL OR weekday BETWEEN 0 AND 6"),
    )

    process = relationship("Process")
    shift = relationship("Shift")


class WeeklyOffPolicy(Base):
    __tablename__ = "weekly_off_policies"

    policy_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    policy_name: Mapped[str] = mapped_column(String(150), nullable=False)

    # NULL means organization-wide; otherwise applies to a pod
    pod_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("pods.pod_id", ondelete="CASCADE"), nullable=True
    )

    off_days_per_week: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2
    )

    rotation_cycle_weeks: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )

    effective_from: Mapped[Date] = mapped_column(Date, nullable=False)
    effective_until: Mapped[Date | None] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint("off_days_per_week BETWEEN 0 AND 7"),
        CheckConstraint("rotation_cycle_weeks >= 1"),
    )

    pod = relationship("Pod")


class WorkloadPolicy(Base):
    __tablename__ = "workload_policies"

    policy_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    policy_name: Mapped[str] = mapped_column(String(150), nullable=False)

    max_work_days_per_week: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    max_hours_per_day: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    max_hours_per_week: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    max_consecutive_work_days: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    minimum_rest_hours: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    effective_from: Mapped[Date] = mapped_column(Date, nullable=False)
    effective_until: Mapped[Date | None] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("max_work_days_per_week BETWEEN 1 AND 7"),
        CheckConstraint("max_hours_per_day > 0"),
        CheckConstraint("max_hours_per_week > 0"),
        CheckConstraint("max_consecutive_work_days > 0"),
        CheckConstraint("minimum_rest_hours >= 0"),
    )
