
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EmployeeStatus, AssignmentStatus


# ---------------- EMPLOYEE ----------------

class EmployeeCreate(BaseModel):
    employee_code: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=1, max_length=255)
    pod_id: UUID
    joined_at: date
    status: EmployeeStatus = EmployeeStatus.ACTIVE


class EmployeeUpdate(BaseModel):
    employee_code: str | None = Field(default=None, min_length=1, max_length=50)
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    email: str | None = Field(default=None, min_length=1, max_length=255)
    pod_id: UUID | None = None
    joined_at: date | None = None
    status: EmployeeStatus | None = None


class EmployeeResponse(BaseModel):
    employee_id: UUID
    employee_code: str
    full_name: str
    email: str
    pod_id: UUID
    status: EmployeeStatus
    joined_at: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- EMPLOYEE ASSIGNMENT ----------------

class EmployeeAssignmentCreate(BaseModel):
    employee_id: UUID
    process_id: UUID
    start_date: date
    end_date: date | None = None
    status: AssignmentStatus = AssignmentStatus.ACTIVE


class EmployeeAssignmentUpdate(BaseModel):
    employee_id: UUID | None = None
    process_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: AssignmentStatus | None = None


class EmployeeAssignmentResponse(BaseModel):
    assignment_id: UUID
    employee_id: UUID
    process_id: UUID
    start_date: date
    end_date: date | None
    status: AssignmentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
