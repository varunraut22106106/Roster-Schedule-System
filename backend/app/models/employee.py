import uuid

from sqlalchemy import (
    String, Boolean, ForeignKey, DateTime, Date, func,
    UniqueConstraint, Index, Uuid
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import EmployeeStatus, AssignmentStatus


class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    employee_code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    pod_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("pods.pod_id"), nullable=False
    )

    status: Mapped[EmployeeStatus] = mapped_column(
        default=EmployeeStatus.ACTIVE, nullable=False
    )

    joined_at: Mapped[Date] = mapped_column(Date, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    pod = relationship("Pod", foreign_keys=[pod_id])


class EmployeeAssignment(Base):
    __tablename__ = "employee_assignments"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False
    )

    process_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("processes.process_id", ondelete="CASCADE"),
        nullable=False
    )

    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    status: Mapped[AssignmentStatus] = mapped_column(
        default=AssignmentStatus.ACTIVE, nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    employee = relationship("Employee")
    process = relationship("Process")

    __table_args__ = (
        Index("ix_assignment_employee_dates", "employee_id", "start_date", "end_date"),
        Index("ix_assignment_process_dates", "process_id", "start_date", "end_date"),
    )
