
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.core.permissions import require_operations_manager

from app.schemas.employee_schema import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeAssignmentCreate,
    EmployeeAssignmentUpdate,
    EmployeeAssignmentResponse
)

from app.services import employee_service


router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)


# ---------------- EMPLOYEE ROUTES ----------------

@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_operations_manager)]
)
def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db)
):
    try:
        return employee_service.create_employee(
            db, employee_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Employee code or email already exists"
        )


@router.get(
    "",
    response_model=list[EmployeeResponse],
    dependencies=[Depends(require_operations_manager)]
)
def get_all_employees(db: Session = Depends(get_db)):
    return employee_service.get_all_employees(db)

# ---------------- ASSIGNMENT ROUTES ----------------

@router.post(
    "/assignments",
    response_model=EmployeeAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_operations_manager)]
)
def create_employee_assignment(
    assignment_data: EmployeeAssignmentCreate,
    db: Session = Depends(get_db)
):
    try:
        return employee_service.create_employee_assignment(
            db, assignment_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to create employee assignment"
        )


@router.get(
    "/assignments",
    response_model=list[EmployeeAssignmentResponse],
    dependencies=[Depends(require_operations_manager)]
)
def get_all_employee_assignments(
    db: Session = Depends(get_db)
):
    return employee_service.get_all_employee_assignments(db)


@router.get(
    "/assignments/{assignment_id}",
    response_model=EmployeeAssignmentResponse,
    dependencies=[Depends(require_operations_manager)]
)
def get_employee_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db)
):
    assignment = employee_service.get_employee_assignment_by_id(
        db, assignment_id
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Employee assignment not found"
        )

    return assignment


@router.patch(
    "/assignments/{assignment_id}",
    response_model=EmployeeAssignmentResponse,
    dependencies=[Depends(require_operations_manager)]
)
def update_employee_assignment(
    assignment_id: UUID,
    assignment_data: EmployeeAssignmentUpdate,
    db: Session = Depends(get_db)
):
    assignment = employee_service.get_employee_assignment_by_id(
        db, assignment_id
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Employee assignment not found"
        )

    try:
        return employee_service.update_employee_assignment(
            db, assignment, assignment_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to update employee assignment"
        )


@router.delete(
    "/assignments/{assignment_id}",
    response_model=EmployeeAssignmentResponse,
    dependencies=[Depends(require_operations_manager)]
)
def delete_employee_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db)
):
    assignment = employee_service.get_employee_assignment_by_id(
        db, assignment_id
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Employee assignment not found"
        )

    return employee_service.delete_employee_assignment(
        db, assignment
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    dependencies=[Depends(require_operations_manager)]
)
def get_employee(
    employee_id: UUID,
    db: Session = Depends(get_db)
):
    employee = employee_service.get_employee_by_id(
        db, employee_id
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return employee


@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
    dependencies=[Depends(require_operations_manager)]
)
def update_employee(
    employee_id: UUID,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    employee = employee_service.get_employee_by_id(
        db, employee_id
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    try:
        return employee_service.update_employee(
            db, employee, employee_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Employee code or email already exists"
        )


@router.delete(
    "/{employee_id}",
    response_model=EmployeeResponse,
    dependencies=[Depends(require_operations_manager)]
)
def delete_employee(
    employee_id: UUID,
    db: Session = Depends(get_db)
):
    employee = employee_service.get_employee_by_id(
        db, employee_id
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return employee_service.delete_employee(db, employee)



