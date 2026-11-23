
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.availability import Leave, CompOffTransaction
from app.models.employee import Employee
from app.models.enums import (
    EmployeeStatus,
    LeaveStatus,
    CompOffStatus,
    CompOffAction,
)


def get_active_employee(db: Session, employee_id: UUID):
    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()

    if not employee:
        raise ValueError("Employee not found")

    if employee.status != EmployeeStatus.ACTIVE:
        raise ValueError("Employee is inactive")

    return employee


# =====================================================
# LEAVE MANAGEMENT
# =====================================================

def create_leave_request(db: Session, employee_id: UUID, data):
    get_active_employee(db, employee_id)

    if data.start_date > data.end_date:
        raise ValueError("Start date cannot be after end date")

    # Prevent overlapping pending or approved leave requests
    overlapping = db.query(Leave).filter(
        Leave.employee_id == employee_id,
        Leave.status.in_([
            LeaveStatus.PENDING,
            LeaveStatus.APPROVED
        ]),
        Leave.start_date <= data.end_date,
        Leave.end_date >= data.start_date
    ).first()

    if overlapping:
        raise ValueError(
            "An overlapping pending or approved leave request already exists"
        )

    leave = Leave(
        employee_id=employee_id,
        requested_by=employee_id,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
        status=LeaveStatus.PENDING
    )

    db.add(leave)
    db.commit()
    db.refresh(leave)

    return leave


def get_leave_requests(
    db: Session,
    employee_id: UUID | None = None,
    status_filter: LeaveStatus | None = None
):
    query = db.query(Leave)

    if employee_id:
        query = query.filter(Leave.employee_id == employee_id)

    if status_filter:
        query = query.filter(Leave.status == status_filter)

    return query.order_by(Leave.created_at.desc()).all()


def get_leave_by_id(db: Session, leave_id: UUID):
    return db.query(Leave).filter(
        Leave.leave_id == leave_id
    ).first()


def review_leave_request(
    db: Session,
    leave: Leave,
    reviewer_id: UUID,
    new_status: LeaveStatus
):
    if leave.status != LeaveStatus.PENDING:
        raise ValueError("Only pending leave requests can be reviewed")

    if new_status not in (LeaveStatus.APPROVED, LeaveStatus.REJECTED):
        raise ValueError("Review status must be approved or rejected")

    if new_status == LeaveStatus.APPROVED:
        # Recheck for another approved leave request in case
        # another request was approved after this one was submitted.
        overlapping = db.query(Leave).filter(
            Leave.employee_id == leave.employee_id,
            Leave.leave_id != leave.leave_id,
            Leave.status == LeaveStatus.APPROVED,
            Leave.start_date <= leave.end_date,
            Leave.end_date >= leave.start_date
        ).first()

        if overlapping:
            raise ValueError(
                "Another approved leave request overlaps these dates"
            )

    leave.status = new_status
    leave.reviewed_by = reviewer_id
    leave.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(leave)

    return leave


def cancel_leave_request(
    db: Session,
    leave: Leave,
    employee_id: UUID
):
    if leave.employee_id != employee_id:
        raise ValueError("You can only cancel your own leave requests")

    if leave.status != LeaveStatus.PENDING:
        raise ValueError("Only pending leave requests can be cancelled")

    leave.status = LeaveStatus.CANCELLED

    db.commit()
    db.refresh(leave)

    return leave


# =====================================================
# COMP-OFF MANAGEMENT
# =====================================================

def get_compoff_balance(db: Session, employee_id: UUID):
    transactions = db.query(CompOffTransaction).filter(
        CompOffTransaction.employee_id == employee_id,
        CompOffTransaction.status.in_([
            CompOffStatus.CREDITED,
            CompOffStatus.APPROVED
        ])
    ).all()

    return sum(transaction.balance_change for transaction in transactions)


def create_compoff_request(
    db: Session,
    employee_id: UUID,
    data
):
    get_active_employee(db, employee_id)

    if data.action != CompOffAction.USE_REQUEST:
        raise ValueError("Employees can only submit comp-off usage requests")

    if data.balance_change >= 0:
        raise ValueError("Comp-off usage must have a negative balance_change")

    current_balance = get_compoff_balance(db, employee_id)
    requested_days = abs(data.balance_change)

    # Also account for other pending usage requests so the same
    # available balance cannot be requested multiple times.
    pending_usage = db.query(CompOffTransaction).filter(
        CompOffTransaction.employee_id == employee_id,
        CompOffTransaction.action == CompOffAction.USE_REQUEST,
        CompOffTransaction.status == CompOffStatus.PENDING
    ).all()

    already_requested = sum(
        abs(item.balance_change) for item in pending_usage
    )

    if requested_days > current_balance - already_requested:
        raise ValueError("Insufficient comp-off balance")

    transaction = CompOffTransaction(
        employee_id=employee_id,
        action=CompOffAction.USE_REQUEST,
        status=CompOffStatus.PENDING,
        balance_change=data.balance_change,
        requested_date=data.requested_date,
        reason=data.reason,
        created_by=employee_id
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction



def credit_compoff(
    db: Session,
    employee_id: UUID,
    creator_id: UUID,
    data
):
    if not data.employee_id:
        raise ValueError("Employee ID is required")
    
    get_active_employee(db, employee_id)

    if data.action != CompOffAction.CREDIT:
        raise ValueError("Action must be CREDIT")

    if data.balance_change <= 0:
        raise ValueError("Comp-off credit must be positive")

    transaction = CompOffTransaction(
        employee_id=employee_id,
        action=CompOffAction.CREDIT,
        status=CompOffStatus.CREDITED,
        balance_change=data.balance_change,
        requested_date=data.requested_date,
        reason=data.reason,
        created_by=creator_id
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


def get_compoff_transactions(
    db: Session,
    employee_id: UUID | None = None,
    status_filter: CompOffStatus | None = None
):
    query = db.query(CompOffTransaction)

    if employee_id:
        query = query.filter(
            CompOffTransaction.employee_id == employee_id
        )

    if status_filter:
        query = query.filter(
            CompOffTransaction.status == status_filter
        )

    return query.order_by(
        CompOffTransaction.created_at.desc()
    ).all()


def get_compoff_transaction_by_id(
    db: Session,
    transaction_id: UUID
):
    return db.query(CompOffTransaction).filter(
        CompOffTransaction.transaction_id == transaction_id
    ).first()


def review_compoff_request(
    db: Session,
    transaction: CompOffTransaction,
    reviewer_id: UUID,
    new_status: CompOffStatus
):
    if transaction.action != CompOffAction.USE_REQUEST:
        raise ValueError("Only comp-off usage requests can be reviewed")

    if transaction.status != CompOffStatus.PENDING:
        raise ValueError("Only pending comp-off requests can be reviewed")

    if new_status not in (
        CompOffStatus.APPROVED,
        CompOffStatus.REJECTED
    ):
        raise ValueError("Review status must be approved or rejected")

    if new_status == CompOffStatus.APPROVED:
        current_balance = get_compoff_balance(
            db, transaction.employee_id
        )

        pending_usage = db.query(CompOffTransaction).filter(
            CompOffTransaction.employee_id == transaction.employee_id,
            CompOffTransaction.transaction_id != transaction.transaction_id,
            CompOffTransaction.action == CompOffAction.USE_REQUEST,
            CompOffTransaction.status == CompOffStatus.PENDING
        ).all()

        pending_total = sum(
            abs(item.balance_change) for item in pending_usage
        )

        if abs(transaction.balance_change) > current_balance:
            raise ValueError("Insufficient comp-off balance")

        if pending_total > current_balance:
            raise ValueError(
                "Other pending requests have reserved the available balance"
            )

        transaction.action = CompOffAction.USE_APPROVED

    else:
        transaction.action = CompOffAction.USE_REJECTED

    transaction.status = new_status
    transaction.reviewed_by = reviewer_id
    transaction.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(transaction)

    return transaction
