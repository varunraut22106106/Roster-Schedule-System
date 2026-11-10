
from uuid import UUID
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    HolidayScope,
    LeaveStatus,
    CompOffStatus,
    CompOffAction,
    AvailabilityType,
)


# ---------------- PUBLIC HOLIDAY ----------------

class PublicHolidayCreate(BaseModel):
    holiday_name: str = Field(min_length=1, max_length=150)
    holiday_date: date
    scope: HolidayScope
    brand_id: UUID | None = None
    is_active: bool = True


class PublicHolidayUpdate(BaseModel):
    holiday_name: str | None = Field(default=None, min_length=1, max_length=150)
    holiday_date: date | None = None
    scope: HolidayScope | None = None
    brand_id: UUID | None = None
    is_active: bool | None = None


class PublicHolidayResponse(BaseModel):
    holiday_id: UUID
    holiday_name: str
    holiday_date: date
    scope: HolidayScope
    brand_id: UUID | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- LEAVE ----------------

class LeaveCreate(BaseModel):
    employee_id: UUID
    requested_by: UUID
    start_date: date
    end_date: date
    reason: str | None = None


class LeaveReview(BaseModel):
    status: LeaveStatus
    reviewed_by: UUID
    # Only APPROVED or REJECTED should be accepted
    review_notes: str | None = None


class LeaveResponse(BaseModel):
    leave_id: UUID
    employee_id: UUID
    requested_by: UUID
    start_date: date
    end_date: date
    reason: str | None
    status: LeaveStatus
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- COMP-OFF TRANSACTION ----------------

class CompOffCreate(BaseModel):
    employee_id: UUID
    action: CompOffAction
    balance_change: int
    requested_date: date | None = None
    reason: str | None = None
    created_by: UUID


class CompOffReview(BaseModel):
    status: CompOffStatus
    reviewed_by: UUID


class CompOffResponse(BaseModel):
    transaction_id: UUID
    employee_id: UUID
    action: CompOffAction
    status: CompOffStatus
    balance_change: int
    requested_date: date | None
    reason: str | None
    created_by: UUID
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- AVAILABILITY RESTRICTION ----------------

class AvailabilityRestrictionCreate(BaseModel):
    employee_id: UUID
    restriction_type: AvailabilityType
    restriction_date: date
    start_time: time | None = None
    end_time: time | None = None
    reason: str | None = Field(default=None, max_length=255)
    is_active: bool = True


class AvailabilityRestrictionUpdate(BaseModel):
    restriction_type: AvailabilityType | None = None
    restriction_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    reason: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class AvailabilityRestrictionResponse(BaseModel):
    restriction_id: UUID
    employee_id: UUID
    restriction_type: AvailabilityType
    restriction_date: date
    start_time: time | None
    end_time: time | None
    reason: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
