
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.models.roster import Roster, RosterAllocationRule
from app.models.employee import Employee, EmployeeAssignment
from app.models.organization import Process
from app.models.policies import WorkloadPolicy

from app.models.enums import (
    AllocationMode,
    AssignmentStatus,
    EmployeeStatus,
    RosterStatus,
    RosterPeriodStatus,
)


def validate_roster_date(roster: Roster, roster_date):
    if roster.year != roster_date.year or roster.month != roster_date.month:
        raise ValueError(
            "Allocation date must belong to the selected roster month"
        )

    if roster.status != RosterStatus.DRAFT:
        raise ValueError("Allocation rules can only be changed in a draft roster")

    if roster.period_status != RosterPeriodStatus.ACTIVE:
        raise ValueError("Cannot modify an archived roster")


def validate_employee_process(
    db: Session,
    employee_id: UUID,
    process_id: UUID,
    roster_date
):
    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()

    if not employee:
        raise ValueError("Employee not found")

    if employee.status != EmployeeStatus.ACTIVE:
        raise ValueError("Employee is inactive")

    process = db.query(Process).filter(
        Process.process_id == process_id
    ).first()

    if not process:
        raise ValueError("Process not found")

    if not process.is_active:
        raise ValueError("Process is inactive")

    assignment = db.query(EmployeeAssignment).filter(
        EmployeeAssignment.employee_id == employee_id,
        EmployeeAssignment.process_id == process_id,
        EmployeeAssignment.status == AssignmentStatus.ACTIVE,
        EmployeeAssignment.start_date <= roster_date,
        (
            EmployeeAssignment.end_date.is_(None)
            | (EmployeeAssignment.end_date >= roster_date)
        )
    ).first()

    if not assignment:
        raise ValueError(
            "Employee is not assigned to this process on the selected date"
        )

    return employee, process


def validate_allocation_values(
    allocation_mode,
    fixed_minutes,
    minimum_minutes,
    maximum_minutes
):
    if allocation_mode == AllocationMode.FIXED:
        if fixed_minutes is None or fixed_minutes <= 0:
            raise ValueError(
                "Fixed allocation requires positive fixed_minutes"
            )

        if minimum_minutes is not None or maximum_minutes is not None:
            raise ValueError(
                "Flexible allocation fields must be empty for fixed mode"
            )

    elif allocation_mode == AllocationMode.FLEXIBLE:
        if fixed_minutes is not None:
            raise ValueError(
                "fixed_minutes must be empty for flexible mode"
            )

        if minimum_minutes is None or maximum_minutes is None:
            raise ValueError(
                "Flexible allocation requires minimum and maximum minutes"
            )

        if minimum_minutes <= 0 or maximum_minutes <= 0:
            raise ValueError("Allocation minutes must be positive")

        if minimum_minutes > maximum_minutes:
            raise ValueError(
                "Minimum allocation cannot exceed maximum allocation"
            )


def validate_daily_allocation_limit(
    db: Session,
    employee_id: UUID,
    roster_date,
    allocation_mode,
    fixed_minutes,
    maximum_minutes,
    exclude_rule_id: UUID | None = None
):
    """
    Check the sum of maximum possible allocations against
    the employee's applicable daily workload limit.
    """

    policy = db.query(WorkloadPolicy).filter(
        WorkloadPolicy.is_active.is_(True),
        WorkloadPolicy.effective_from <= roster_date,
        (
            WorkloadPolicy.effective_until.is_(None)
            | (WorkloadPolicy.effective_until >= roster_date)
        )
    ).order_by(
        WorkloadPolicy.effective_from.desc()
    ).first()

    if not policy:
        return

    existing_query = db.query(RosterAllocationRule).filter(
        RosterAllocationRule.employee_id == employee_id,
        RosterAllocationRule.roster_date == roster_date
    )

    if exclude_rule_id:
        existing_query = existing_query.filter(
            RosterAllocationRule.allocation_rule_id != exclude_rule_id
        )

    existing_rules = existing_query.all()

    total_minutes = 0

    for rule in existing_rules:
        if rule.allocation_mode == AllocationMode.FIXED:
            total_minutes += rule.fixed_minutes
        else:
            total_minutes += rule.maximum_minutes

    if allocation_mode == AllocationMode.FIXED:
        total_minutes += fixed_minutes
    else:
        total_minutes += maximum_minutes

    daily_limit_minutes = int(policy.max_hours_per_day * 60)

    if total_minutes > daily_limit_minutes:
        raise ValueError(
            f"Total allocation ({total_minutes} minutes) exceeds "
            f"the daily workload limit ({daily_limit_minutes} minutes)"
        )


def create_allocation_rule(
    db: Session,
    data
):
    roster = db.query(Roster).filter(
        Roster.roster_id == data.roster_id
    ).first()

    if not roster:
        raise ValueError("Roster not found")

    validate_roster_date(roster, data.roster_date)

    validate_employee_process(
        db,
        data.employee_id,
        data.process_id,
        data.roster_date
    )

    validate_allocation_values(
        data.allocation_mode,
        data.fixed_minutes,
        data.minimum_minutes,
        data.maximum_minutes
    )

    validate_daily_allocation_limit(
        db,
        data.employee_id,
        data.roster_date,
        data.allocation_mode,
        data.fixed_minutes,
        data.maximum_minutes
    )

    rule = RosterAllocationRule(
        roster_id=data.roster_id,
        employee_id=data.employee_id,
        roster_date=data.roster_date,
        process_id=data.process_id,
        allocation_mode=data.allocation_mode,
        fixed_minutes=data.fixed_minutes,
        minimum_minutes=data.minimum_minutes,
        maximum_minutes=data.maximum_minutes
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    return rule


def get_allocation_rules(
    db: Session,
    roster_id: UUID | None = None,
    employee_id: UUID | None = None,
    roster_date=None
):
    query = db.query(RosterAllocationRule)

    if roster_id:
        query = query.filter(
            RosterAllocationRule.roster_id == roster_id
        )

    if employee_id:
        query = query.filter(
            RosterAllocationRule.employee_id == employee_id
        )

    if roster_date:
        query = query.filter(
            RosterAllocationRule.roster_date == roster_date
        )

    return query.order_by(
        RosterAllocationRule.roster_date,
        RosterAllocationRule.employee_id
    ).all()


def get_allocation_rule_by_id(
    db: Session,
    rule_id: UUID
):
    return db.query(RosterAllocationRule).filter(
        RosterAllocationRule.allocation_rule_id == rule_id
    ).first()


def update_allocation_rule(
    db: Session,
    rule: RosterAllocationRule,
    data
):
    roster = db.query(Roster).filter(
        Roster.roster_id == rule.roster_id
    ).first()

    if not roster:
        raise ValueError("Roster not found")

    validate_roster_date(roster, rule.roster_date)

    update_data = data.model_dump(exclude_unset=True)

    allocation_mode = update_data.get(
        "allocation_mode", rule.allocation_mode
    )
    fixed_minutes = update_data.get(
        "fixed_minutes", rule.fixed_minutes
    )
    minimum_minutes = update_data.get(
        "minimum_minutes", rule.minimum_minutes
    )
    maximum_minutes = update_data.get(
        "maximum_minutes", rule.maximum_minutes
    )

    validate_allocation_values(
        allocation_mode,
        fixed_minutes,
        minimum_minutes,
        maximum_minutes
    )

    validate_employee_process(
        db,
        rule.employee_id,
        rule.process_id,
        rule.roster_date
    )

    validate_daily_allocation_limit(
        db,
        rule.employee_id,
        rule.roster_date,
        allocation_mode,
        fixed_minutes,
        maximum_minutes,
        exclude_rule_id=rule.allocation_rule_id
    )

    for key, value in update_data.items():
        setattr(rule, key, value)

    db.commit()
    db.refresh(rule)

    return rule


def delete_allocation_rule(
    db: Session,
    rule: RosterAllocationRule
):
    roster = db.query(Roster).filter(
        Roster.roster_id == rule.roster_id
    ).first()

    if not roster:
        raise ValueError("Roster not found")

    validate_roster_date(roster, rule.roster_date)

    db.delete(rule)
    db.commit()

    return {"message": "Allocation rule deleted successfully"}
