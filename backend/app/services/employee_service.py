
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError

from app.models.employee import Employee, EmployeeAssignment
from app.models.organization import Pod, Process, Brand
from app.models.enums import EmployeeStatus, AssignmentStatus

from app.schemas.employee_schema import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeAssignmentCreate,
    EmployeeAssignmentUpdate
)


# ---------------- EMPLOYEE SERVICES ----------------

def create_employee(db: Session, employee_data: EmployeeCreate):
    pod = db.query(Pod).filter(
        Pod.pod_id == employee_data.pod_id,
        Pod.is_active == True
    ).first()

    if not pod:
        raise ValueError("Pod not found or inactive")

    employee = Employee(**employee_data.model_dump())

    db.add(employee)
    db.commit()
    db.refresh(employee)

    return employee


def get_all_employees(db: Session):
    return db.query(Employee).order_by(
        Employee.created_at.desc()
    ).all()


def get_employee_by_id(db: Session, employee_id: UUID):
    return db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()


def update_employee(
    db: Session,
    employee: Employee,
    employee_data: EmployeeUpdate
):
    update_data = employee_data.model_dump(exclude_unset=True)

    if "pod_id" in update_data and update_data["pod_id"]:
        pod = db.query(Pod).filter(
            Pod.pod_id == update_data["pod_id"],
            Pod.is_active == True
        ).first()

        if not pod:
            raise ValueError("Pod not found or inactive")

    for key, value in update_data.items():
        setattr(employee, key, value)
        
    if employee.status == EmployeeStatus.INACTIVE:
            db.query(EmployeeAssignment).filter(
                EmployeeAssignment.employee_id == employee.employee_id,
                EmployeeAssignment.status == AssignmentStatus.ACTIVE
            ).update(
                {EmployeeAssignment.status: AssignmentStatus.INACTIVE},
                synchronize_session=False
            )

    db.commit()
    db.refresh(employee)

    return employee


def delete_employee(db: Session, employee: Employee):
    employee.status = EmployeeStatus.INACTIVE

    # Deactivate current assignments too
    db.query(EmployeeAssignment).filter(
        EmployeeAssignment.employee_id == employee.employee_id,
        EmployeeAssignment.status == AssignmentStatus.ACTIVE
    ).update(
        {EmployeeAssignment.status: AssignmentStatus.INACTIVE},
        synchronize_session=False
    )

    db.commit()
    db.refresh(employee)

    return employee


# ---------------- ASSIGNMENT VALIDATION ----------------

def validate_assignment_entities(
    db: Session,
    employee_id: UUID,
    process_id: UUID
):
    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id,
        Employee.status == EmployeeStatus.ACTIVE
    ).first()

    if not employee:
        raise ValueError("Employee not found or inactive")

    process = db.query(Process).join(
        Brand,
        Process.brand_id == Brand.brand_id
    ).filter(
        Process.process_id == process_id,
        Process.is_active == True,
        Brand.is_active == True
    ).first()

    if not process:
        raise ValueError("Process or its brand not found or inactive")

    return employee, process


def validate_assignment_dates(start_date, end_date):
    if end_date is not None and end_date < start_date:
        raise ValueError("End date cannot be before start date")


def validate_assignment_overlap(
    db: Session,
    employee_id: UUID,
    process_id: UUID,
    start_date,
    end_date,
    exclude_assignment_id=None
):
    query = db.query(EmployeeAssignment).filter(
        EmployeeAssignment.employee_id == employee_id,
        EmployeeAssignment.process_id == process_id,
        EmployeeAssignment.status == AssignmentStatus.ACTIVE,

        # Existing assignment ends on or after new start date
        or_(
            EmployeeAssignment.end_date.is_(None),
            EmployeeAssignment.end_date >= start_date
        )
    )

    # New assignment ends on or after existing start date
    if end_date is not None:
        query = query.filter(
            EmployeeAssignment.start_date <= end_date
        )

    if exclude_assignment_id:
        query = query.filter(
            EmployeeAssignment.assignment_id != exclude_assignment_id
        )

    if query.first():
        raise ValueError(
            "Employee already has an overlapping active assignment "
            "for this process"
        )


# ---------------- ASSIGNMENT SERVICES ----------------

def create_employee_assignment(
    db: Session,
    assignment_data: EmployeeAssignmentCreate
):
    data = assignment_data.model_dump()

    validate_assignment_dates(
        data["start_date"],
        data["end_date"]
    )

    validate_assignment_entities(
        db,
        data["employee_id"],
        data["process_id"]
    )

    if data["status"] == AssignmentStatus.ACTIVE:
        validate_assignment_overlap(
            db,
            data["employee_id"],
            data["process_id"],
            data["start_date"],
            data["end_date"]
        )

    assignment = EmployeeAssignment(**data)

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


def get_all_employee_assignments(db: Session):
    return db.query(EmployeeAssignment).order_by(
        EmployeeAssignment.created_at.desc()
    ).all()


def get_employee_assignment_by_id(
    db: Session,
    assignment_id: UUID
):
    return db.query(EmployeeAssignment).filter(
        EmployeeAssignment.assignment_id == assignment_id
    ).first()


def update_employee_assignment(
    db: Session,
    assignment: EmployeeAssignment,
    assignment_data: EmployeeAssignmentUpdate
):
    update_data = assignment_data.model_dump(exclude_unset=True)

    employee_id = update_data.get(
        "employee_id", assignment.employee_id
    )

    process_id = update_data.get(
        "process_id", assignment.process_id
    )

    start_date = update_data.get(
        "start_date", assignment.start_date
    )

    end_date = update_data.get(
        "end_date", assignment.end_date
    )

    new_status = update_data.get(
        "status", assignment.status
    )

    validate_assignment_dates(start_date, end_date)

    if new_status == AssignmentStatus.ACTIVE:
        validate_assignment_entities(
            db, employee_id, process_id
        )

        validate_assignment_overlap(
            db,
            employee_id,
            process_id,
            start_date,
            end_date,
            exclude_assignment_id=assignment.assignment_id
        )

    for key, value in update_data.items():
        setattr(assignment, key, value)
        

    return assignment


def delete_employee_assignment(
    db: Session,
    assignment: EmployeeAssignment
):
    assignment.status = AssignmentStatus.INACTIVE

    db.commit()
    db.refresh(assignment)

    return assignment
