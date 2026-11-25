
from uuid import UUID
from datetime import date, datetime , time

from pydantic import BaseModel, ConfigDict, Field,model_validator

from app.models.enums import (
    DayStatus,
    GenerationStatus,
    RosterStatus,
    RosterPeriodStatus,
    ConflictStatus,
    ConflictType,
    EditAction,
    AllocationMode,
    StaffingRuleScope
)


# ---------------- ROSTER ----------------

class RosterCreate(BaseModel):
    year: int = Field(ge=2000)
    month: int = Field(ge=1, le=12)

'''
class RosterUpdate(BaseModel):
    pass
'''

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
    

# ---------------- ROSTER ALLOCATION RULE ----------------

class RosterAllocationRuleCreate(BaseModel):
    roster_id: UUID
    employee_id: UUID
    roster_date: date
    process_id: UUID

    allocation_mode: AllocationMode

    fixed_minutes: int | None = Field(default=None, gt=0)
    minimum_minutes: int | None = Field(default=None, gt=0)
    maximum_minutes: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_allocation_mode(self):
        if self.allocation_mode == AllocationMode.FIXED:
            if self.fixed_minutes is None:
                raise ValueError(
                    "fixed_minutes is required for fixed allocation"
                )

            if self.minimum_minutes is not None or self.maximum_minutes is not None:
                raise ValueError(
                    "Flexible allocation fields must be null for fixed allocation"
                )

        elif self.allocation_mode == AllocationMode.FLEXIBLE:
            if self.fixed_minutes is not None:
                raise ValueError(
                    "fixed_minutes must be null for flexible allocation"
                )

            if self.minimum_minutes is None or self.maximum_minutes is None:
                raise ValueError(
                    "Both minimum_minutes and maximum_minutes are required"
                )

            if self.minimum_minutes > self.maximum_minutes:
                raise ValueError(
                    "minimum_minutes cannot exceed maximum_minutes"
                )

        return self


class RosterAllocationRuleUpdate(BaseModel):
    allocation_mode: AllocationMode | None = None
    fixed_minutes: int | None = Field(default=None, gt=0)
    minimum_minutes: int | None = Field(default=None, gt=0)
    maximum_minutes: int | None = Field(default=None, gt=0)


class RosterAllocationRuleResponse(BaseModel):
    allocation_rule_id: UUID
    roster_id: UUID
    employee_id: UUID
    roster_date: date
    process_id: UUID
    allocation_mode: AllocationMode
    fixed_minutes: int | None
    minimum_minutes: int | None
    maximum_minutes: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- TIME-SLOT STAFFING REQUIREMENT ----------------

class StaffingTimeSlotCreate(BaseModel):
    process_id: UUID
    shift_id: UUID | None = None

    scope: StaffingRuleScope
    weekday: int | None = Field(default=None, ge=0, le=6)
    effective_date: date | None = None

    start_time: time | None = None
    end_time: time | None = None

    minimum_employees: int = Field(ge=0)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_time_slot(self):
        if (self.start_time is None) != (self.end_time is None):
            raise ValueError(
                "Both start_time and end_time must be supplied together"
            )

        if self.start_time is not None and self.end_time <= self.start_time:
            raise ValueError("end_time must be later than start_time")

        if self.scope == StaffingRuleScope.DEFAULT:
            if self.weekday is not None or self.effective_date is not None:
                raise ValueError(
                    "DEFAULT scope cannot have weekday or effective_date"
                )

        elif self.scope == StaffingRuleScope.WEEKDAY:
            if self.weekday is None or self.effective_date is not None:
                raise ValueError(
                    "WEEKDAY scope requires weekday only"
                )

        elif self.scope == StaffingRuleScope.DATE:
            if self.effective_date is None or self.weekday is not None:
                raise ValueError(
                    "DATE scope requires effective_date only"
                )

        return self


class StaffingTimeSlotUpdate(BaseModel):
    shift_id: UUID | None = None
    scope: StaffingRuleScope | None = None
    weekday: int | None = Field(default=None, ge=0, le=6)
    effective_date: date | None = None

    start_time: time | None = None
    end_time: time | None = None

    minimum_employees: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class StaffingTimeSlotResponse(BaseModel):
    requirement_id: UUID
    process_id: UUID
    shift_id: UUID | None
    scope: StaffingRuleScope
    weekday: int | None
    effective_date: date | None
    start_time: time | None
    end_time: time | None
    minimum_employees: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
    
class RosterGenerationRequest(BaseModel):
    time_limit_seconds: int = Field(default=60, gt=0, le=600)
    relax_coverage: bool = True


class RosterGenerationResult(BaseModel):
    generation_id: UUID
    roster_id: UUID
    generation_number: int
    solver_status: GenerationStatus
    objective_value: float | None
    assignments_created: int
    unmet_coverage_count: int
    solver_time_seconds: float
