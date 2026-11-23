
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import (
    require_employee,
    require_operations_manager,
)

from app.models.enums import LeaveStatus, CompOffStatus

from app.schemas.availability_schema import (
    LeaveCreate,
    LeaveReview,
    LeaveResponse,
    CompOffCreate,
    CompOffReview,
    CompOffResponse,
)

from app.services import leave_policy_service as service


router = APIRouter(
    prefix="/requests",
    tags=["Leave and Comp-Off"]
)


# =====================================================
# LEAVE REQUESTS - EMPLOYEE
# =====================================================

@router.post(
    "/leaves",
    response_model=LeaveResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_employee)]
)
def create_leave(
    data: LeaveCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return service.create_leave_request(
            db, current_user.employee_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/my-leaves",
    response_model=list[LeaveResponse],
    dependencies=[Depends(require_employee)]
)
def get_my_leaves(
    status_filter: LeaveStatus | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return service.get_leave_requests(
        db,
        employee_id=current_user.employee_id,
        status_filter=status_filter
    )


@router.patch(
    "/leaves/{leave_id}/cancel",
    response_model=LeaveResponse,
    dependencies=[Depends(require_employee)]
)
def cancel_my_leave(
    leave_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    leave = service.get_leave_by_id(db, leave_id)

    if not leave:
        raise HTTPException(
            status_code=404,
            detail="Leave request not found"
        )

    try:
        return service.cancel_leave_request(
            db, leave, current_user.employee_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =====================================================
# LEAVE REQUESTS - OPERATIONS MANAGER
# =====================================================

@router.get(
    "/leaves",
    response_model=list[LeaveResponse],
    dependencies=[Depends(require_operations_manager)]
)
def get_all_leaves(
    employee_id: UUID | None = None,
    status_filter: LeaveStatus | None = None,
    db: Session = Depends(get_db)
):
    return service.get_leave_requests(
        db, employee_id, status_filter
    )


@router.get(
    "/leaves/{leave_id}",
    response_model=LeaveResponse,
    dependencies=[Depends(require_operations_manager)]
)
def get_leave(
    leave_id: UUID,
    db: Session = Depends(get_db)
):
    leave = service.get_leave_by_id(db, leave_id)

    if not leave:
        raise HTTPException(
            status_code=404,
            detail="Leave request not found"
        )

    return leave


@router.patch(
    "/leaves/{leave_id}/review",
    response_model=LeaveResponse,
    dependencies=[Depends(require_operations_manager)]
)
def review_leave(
    leave_id: UUID,
    data: LeaveReview,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    leave = service.get_leave_by_id(db, leave_id)

    if not leave:
        raise HTTPException(
            status_code=404,
            detail="Leave request not found"
        )

    try:
        return service.review_leave_request(
            db,
            leave,
            current_user.employee_id,
            data.status
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =====================================================
# COMP-OFF - EMPLOYEE
# =====================================================

@router.post(
    "/comp-offs",
    response_model=CompOffResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_employee)]
)
def request_compoff(
    data: CompOffCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return service.create_compoff_request(
            db, current_user.employee_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/my-comp-offs",
    response_model=list[CompOffResponse],
    dependencies=[Depends(require_employee)]
)
def get_my_compoffs(
    status_filter: CompOffStatus | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return service.get_compoff_transactions(
        db,
        employee_id=current_user.employee_id,
        status_filter=status_filter
    )


@router.get(
    "/my-comp-offs/balance",
    dependencies=[Depends(require_employee)]
)
def get_my_compoff_balance(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    balance = service.get_compoff_balance(
        db, current_user.employee_id
    )

    return {
        "employee_id": str(current_user.employee_id),
        "balance": balance
    }


# =====================================================
# COMP-OFF - OPERATIONS MANAGER
# =====================================================

@router.post(
    "/comp-offs/credit",
    response_model=CompOffResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_operations_manager)]
)
def credit_employee_compoff(
    data: CompOffCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return service.credit_compoff(
            db,
            data.employee_id,
            current_user.employee_id,
            data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/comp-offs",
    response_model=list[CompOffResponse],
    dependencies=[Depends(require_operations_manager)]
)
def get_all_compoffs(
    employee_id: UUID | None = None,
    status_filter: CompOffStatus | None = None,
    db: Session = Depends(get_db)
):
    return service.get_compoff_transactions(
        db, employee_id, status_filter
    )


@router.get(
    "/comp-offs/{transaction_id}",
    response_model=CompOffResponse,
    dependencies=[Depends(require_operations_manager)]
)
def get_compoff(
    transaction_id: UUID,
    db: Session = Depends(get_db)
):
    transaction = service.get_compoff_transaction_by_id(
        db, transaction_id
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Comp-off transaction not found"
        )

    return transaction


@router.patch(
    "/comp-offs/{transaction_id}/review",
    response_model=CompOffResponse,
    dependencies=[Depends(require_operations_manager)]
)
def review_compoff(
    transaction_id: UUID,
    data: CompOffReview,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    transaction = service.get_compoff_transaction_by_id(
        db, transaction_id
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Comp-off transaction not found"
        )

    try:
        return service.review_compoff_request(
            db,
            transaction,
            current_user.employee_id,
            data.status
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
