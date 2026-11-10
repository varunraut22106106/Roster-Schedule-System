
from uuid import UUID
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    DayStatus,
    GenerationStatus,
    RosterStatus,
    RosterPeriodStatus,
    ConflictStatus,
    ConflictType,
    EditAction,
)


# ---------------- ROSTER ----------------

class RosterCreate(BaseModel):
    year: int = Field(ge=2000)
    month: int = Field(ge=1, le=12)


class RosterUpdate(BaseModel):
    status: RosterStatus | None = None
    period_status: RosterPeriodStatus | None = None


class RosterResponse(BaseModel):
    roster_id: UUID
    year: int
    month: int
    status: RosterStatus
    period_status: RosterPeriodStatus
    published_generation_id: UUID | None
    published_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- ROSTER GENERATION ----------------

class RosterGenerationCreate(BaseModel):
    roster_id: UUID
    generation_number: int = Field(ge=1)
    solver_status: GenerationStatus
    solver_time_limit_seconds: int = Field(gt=0)
    solver_parameters: dict = Field(default_factory=dict)
    objective_value: float | None = None
    started_at: datetime
    completed_at: datetime | None = None


class RosterGenerationResponse(BaseModel):
    generation_id: UUID
    roster_id: UUID
    generation_number: int
    solver_status: GenerationStatus
    solver_time_limit_seconds: int
    solver_parameters: dict
    objective_value: float | None
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- ROSTER EMPLOYEE DAY ----------------

class RosterEmployeeDayCreate(BaseModel):
    generation_id: UUID
    employee_id: UUID
    roster_date: date
    status: DayStatus
    notes: str | None = None


class RosterEmployeeDayUpdate(BaseModel):
    status: DayStatus | None = None
    notes: str | None = None


class RosterEmployeeDayResponse(BaseModel):
    employee_day_id: UUID
    generation_id: UUID
    employee_id: UUID
    roster_date: date
    status: DayStatus
    notes: str | None

    model_config = ConfigDict(from_attributes=True)


# ---------------- ROSTER ASSIGNMENT ----------------

class RosterAssignmentCreate(BaseModel):
    generation_id: UUID
    employee_day_id: UUID
    employee_id: UUID
    process_id: UUID
    shift_id: UUID
    starts_at: datetime
    ends_at: datetime
    allocation_minutes: int = Field(gt=0)


class RosterAssignmentUpdate(BaseModel):
    process_id: UUID | None = None
    shift_id: UUID | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    allocation_minutes: int | None = Field(default=None, gt=0)


class RosterAssignmentResponse(BaseModel):
    assignment_id: UUID
    generation_id: UUID
    employee_day_id: UUID
    employee_id: UUID
    process_id: UUID
    shift_id: UUID
    starts_at: datetime
    ends_at: datetime
    allocation_minutes: int

    model_config = ConfigDict(from_attributes=True)


# ---------------- ROSTER CONFLICT ----------------

class RosterConflictCreate(BaseModel):
    generation_id: UUID
    conflict_type: ConflictType
    employee_id: UUID | None = None
    process_id: UUID | None = None
    conflict_date: date | None = None
    description: str
    details: dict = Field(default_factory=dict)


class RosterConflictUpdate(BaseModel):
    status: ConflictStatus | None = None
    resolution_notes: str | None = None
    resolved_by: UUID | None = None


class RosterConflictResponse(BaseModel):
    conflict_id: UUID
    generation_id: UUID
    conflict_type: ConflictType
    status: ConflictStatus
    employee_id: UUID | None
    process_id: UUID | None
    conflict_date: date | None
    description: str
    details: dict
    resolution_notes: str | None
    resolved_by: UUID | None
    resolved_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- ROSTER CONFLICT HISTORY ----------------

class RosterConflictHistoryCreate(BaseModel):
    conflict_id: UUID
    previous_status: ConflictStatus | None = None
    new_status: ConflictStatus
    changed_by: UUID
    notes: str | None = None


class RosterConflictHistoryResponse(BaseModel):
    history_id: UUID
    conflict_id: UUID
    previous_status: ConflictStatus | None
    new_status: ConflictStatus
    changed_by: UUID
    notes: str | None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- ROSTER EDIT HISTORY ----------------

class RosterEditHistoryCreate(BaseModel):
    generation_id: UUID
    edited_by: UUID
    action: EditAction
    entity_type: str = Field(min_length=1, max_length=100)
    entity_id: UUID
    before_data: dict | None = None
    after_data: dict | None = None


class RosterEditHistoryResponse(BaseModel):
    edit_id: UUID
    generation_id: UUID
    edited_by: UUID
    action: EditAction
    entity_type: str
    entity_id: UUID
    before_data: dict | None
    after_data: dict | None
    edited_at: datetime

    model_config = ConfigDict(from_attributes=True)
