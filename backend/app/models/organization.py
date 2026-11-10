import uuid

from sqlalchemy import (
    String, Boolean, ForeignKey, DateTime, func, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid

from app.database.base import Base


class Brand(Base):
    __tablename__ = "brands"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    brand_name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Pod(Base):
    __tablename__ = "pods"

    pod_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    pod_name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    pod_lead_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("employees.employee_id", use_alter=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Process(Base):
    __tablename__ = "processes"

    process_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("brands.brand_id", ondelete="CASCADE"), nullable=False
    )
    process_name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("brand_id", "process_name", name="uq_brand_process_name"),
    )

    brand = relationship("Brand")
