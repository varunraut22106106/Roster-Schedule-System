
from uuid import UUID
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ShiftType, StaffingRuleScope


# ---------------- SHIFT ----------------

class ShiftCreate(BaseModel):
    shift_name: str = Field(min_length=1, max_length=100)
    shift_type: ShiftType
    start_time: time
    end_time: time
    is_active: bool = True


class ShiftUpdate(BaseModel):
    shift_name: str | None = Field(default=None, min_length=1, max_length=100)
    shift_type: ShiftType | None = None
    start_time: time | None = None
    end_time: time | None = None
    is_active: bool | None = None


class ShiftResponse(BaseModel):
    shift_id: UUID
    shift_name: str
    shift_type: ShiftType
    start_time: time
    end_time: time
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- PROCESS OPERATING DAY ----------------

class ProcessOperatingDayCreate(BaseModel):
    process_id: UUID
    weekday: int = Field(ge=0, le=6)
    is_operating: bool = True


class ProcessOperatingDayUpdate(BaseModel):
    weekday: int | None = Field(default=None, ge=0, le=6)
    is_operating: bool | None = None


class ProcessOperatingDayResponse(BaseModel):
    operating_day_id: UUID
    process_id: UUID
    weekday: int
    is_operating: bool

    model_config = ConfigDict(from_attributes=True)


# ---------------- STAFFING REQUIREMENT ----------------

class StaffingRequirementCreate(BaseModel):
    process_id: UUID
    shift_id: UUID | None = None
    scope: StaffingRuleScope
    weekday: int | None = Field(default=None, ge=0, le=6)
    effective_date: date | None = None
    minimum_employees: int = Field(default=1, ge=0)
    is_active: bool = True


class StaffingRequirementUpdate(BaseModel):
    process_id: UUID | None = None
    shift_id: UUID | None = None
    scope: StaffingRuleScope | None = None
    weekday: int | None = Field(default=None, ge=0, le=6)
    effective_date: date | None = None
    minimum_employees: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class StaffingRequirementResponse(BaseModel):
    requirement_id: UUID
    process_id: UUID
    shift_id: UUID | None
    scope: StaffingRuleScope
    weekday: int | None
    effective_date: date | None
    minimum_employees: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- WEEKLY OFF POLICY ----------------

class WeeklyOffPolicyCreate(BaseModel):
    policy_name: str = Field(min_length=1, max_length=150)
    pod_id: UUID | None = None
    off_days_per_week: int = Field(default=2, ge=0, le=7)
    rotation_cycle_weeks: int = Field(default=1, ge=1)
    effective_from: date
    effective_until: date | None = None
    is_active: bool = True


class WeeklyOffPolicyUpdate(BaseModel):
    policy_name: str | None = Field(default=None, min_length=1, max_length=150)
    pod_id: UUID | None = None
    off_days_per_week: int | None = Field(default=None, ge=0, le=7)
    rotation_cycle_weeks: int | None = Field(default=None, ge=1)
    effective_from: date | None = None
    effective_until: date | None = None
    is_active: bool | None = None


class WeeklyOffPolicyResponse(BaseModel):
    policy_id: UUID
    policy_name: str
    pod_id: UUID | None
    off_days_per_week: int
    rotation_cycle_weeks: int
    effective_from: date
    effective_until: date | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ---------------- WORKLOAD POLICY ----------------

class WorkloadPolicyCreate(BaseModel):
    policy_name: str = Field(min_length=1, max_length=150)
    max_work_days_per_week: int = Field(ge=1, le=7)
    max_hours_per_day: float = Field(gt=0)
    max_hours_per_week: float = Field(gt=0)
    max_consecutive_work_days: int = Field(gt=0)
    minimum_rest_hours: float = Field(ge=0)
    effective_from: date
    effective_until: date | None = None
    is_active: bool = True


class WorkloadPolicyUpdate(BaseModel):
    policy_name: str | None = Field(default=None, min_length=1, max_length=150)
    max_work_days_per_week: int | None = Field(default=None, ge=1, le=7)
    max_hours_per_day: float | None = Field(default=None, gt=0)
    max_hours_per_week: float | None = Field(default=None, gt=0)
    max_consecutive_work_days: int | None = Field(default=None, gt=0)
    minimum_rest_hours: float | None = Field(default=None, ge=0)
    effective_from: date | None = None
    effective_until: date | None = None
    is_active: bool | None = None


class WorkloadPolicyResponse(BaseModel):
    policy_id: UUID
    policy_name: str
    max_work_days_per_week: int
    max_hours_per_day: float
    max_hours_per_week: float
    max_consecutive_work_days: int
    minimum_rest_hours: float
    effective_from: date
    effective_until: date | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
