
import uuid

from datetime import datetime, date

from sqlalchemy import (
    String, Boolean, Integer, Float, Date, DateTime, Time,
    ForeignKey, Text, JSON, UniqueConstraint, CheckConstraint,
    Index, func, Uuid
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import (
    DayStatus, GenerationStatus, RosterStatus,
    ConflictStatus, ConflictType, EditAction,
    RosterPeriodStatus
)


class Roster(Base):
    __tablename__ = "rosters"

    roster_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[RosterStatus] = mapped_column(
        default=RosterStatus.DRAFT, nullable=False
    )

    period_status: Mapped[RosterPeriodStatus] = mapped_column(
        default=RosterPeriodStatus.ACTIVE, nullable=False
    )

    published_generation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("roster_generations.generation_id", use_alter=True),
        nullable=True
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    generations = relationship(
        "RosterGeneration",
        foreign_keys="RosterGeneration.roster_id",
        back_populates="roster"
    )

    published_generation = relationship(
        "RosterGeneration",
        foreign_keys=[published_generation_id]
    )

    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_roster_year_month"),
        CheckConstraint("month BETWEEN 1 AND 12"),
        CheckConstraint("year >= 2000"),
    )


class RosterGeneration(Base):
    __tablename__ = "roster_generations"

    generation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    roster_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("rosters.roster_id", ondelete="CASCADE"),
        nullable=False
    )

    generation_number: Mapped[int] = mapped_column(Integer, nullable=False)

    solver_status: Mapped[GenerationStatus] = mapped_column(nullable=False)

    solver_time_limit_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    solver_parameters: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )

    objective_value: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    roster = relationship(
        "Roster",
        foreign_keys=[roster_id],
        back_populates="generations"
    )

    employee_days = relationship(
        "RosterEmployeeDay", back_populates="generation",
        cascade="all, delete-orphan"
    )

    assignments = relationship(
        "RosterAssignment", back_populates="generation",
        cascade="all, delete-orphan"
    )

    conflicts = relationship(
        "RosterConflict", back_populates="generation",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "roster_id", "generation_number",
            name="uq_roster_generation_number"
        ),
        CheckConstraint("generation_number >= 1"),
        CheckConstraint("solver_time_limit_seconds > 0"),
    )


class RosterEmployeeDay(Base):
    __tablename__ = "roster_employee_days"

    employee_day_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    generation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roster_generations.generation_id", ondelete="CASCADE"),
        nullable=False
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.employee_id"), nullable=False
    )

    roster_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[DayStatus] = mapped_column(nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    generation = relationship(
        "RosterGeneration", back_populates="employee_days"
    )

    employee = relationship("Employee")

    __table_args__ = (
        UniqueConstraint(
            "generation_id", "employee_id", "roster_date",
            name="uq_generation_employee_day"
        ),
        Index("ix_employee_day_date", "employee_id", "roster_date"),
    )


class RosterAssignment(Base):
    __tablename__ = "roster_assignments"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    generation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roster_generations.generation_id", ondelete="CASCADE"),
        nullable=False
    )

    employee_day_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roster_employee_days.employee_day_id", ondelete="CASCADE"),
        nullable=False
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.employee_id"), nullable=False
    )

    process_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("processes.process_id"), nullable=False
    )

    shift_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("shifts.shift_id"), nullable=False
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    allocation_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    generation = relationship(
        "RosterGeneration", back_populates="assignments"
    )

    employee_day = relationship("RosterEmployeeDay")
    employee = relationship("Employee")
    process = relationship("Process")
    shift = relationship("Shift")

    __table_args__ = (
        CheckConstraint("ends_at > starts_at"),
        CheckConstraint("allocation_minutes > 0"),
        Index("ix_roster_assignment_employee_time", "employee_id", "starts_at", "ends_at"),
        Index("ix_roster_assignment_process_time", "process_id", "starts_at", "ends_at"),
    )


class RosterConflict(Base):
    __tablename__ = "roster_conflicts"

    conflict_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    generation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roster_generations.generation_id", ondelete="CASCADE"),
        nullable=False
    )

    conflict_type: Mapped[ConflictType] = mapped_column(nullable=False)

    status: Mapped[ConflictStatus] = mapped_column(
        default=ConflictStatus.OPEN, nullable=False
    )

    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("employees.employee_id"), nullable=True
    )

    process_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("processes.process_id"), nullable=True
    )

    conflict_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    details: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )

    resolution_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("employees.employee_id"), nullable=True
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    generation = relationship(
        "RosterGeneration", back_populates="conflicts"
    )

    employee = relationship("Employee", foreign_keys=[employee_id])
    process = relationship("Process")
    resolver = relationship("Employee", foreign_keys=[resolved_by])

    history = relationship(
        "RosterConflictHistory",
        back_populates="conflict",
        cascade="all, delete-orphan"
    )


class RosterConflictHistory(Base):
    __tablename__ = "roster_conflict_history"

    history_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    conflict_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roster_conflicts.conflict_id", ondelete="CASCADE"),
        nullable=False
    )

    previous_status: Mapped[ConflictStatus | None] = mapped_column(nullable=True)
    new_status: Mapped[ConflictStatus] = mapped_column(nullable=False)

    changed_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.employee_id"), nullable=False
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    conflict = relationship("RosterConflict", back_populates="history")
    actor = relationship("Employee")


class RosterEditHistory(Base):
    __tablename__ = "roster_edit_history"

    edit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    generation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roster_generations.generation_id", ondelete="CASCADE"),
        nullable=False
    )

    edited_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.employee_id"), nullable=False
    )

    action: Mapped[EditAction] = mapped_column(nullable=False)

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)

    before_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    edited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    generation = relationship("RosterGeneration")
    editor = relationship("Employee")
